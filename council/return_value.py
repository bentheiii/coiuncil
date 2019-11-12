from __future__ import annotations

from abc import abstractmethod
from itertools import chain
from typing import Protocol, runtime_checkable, Iterable

from council.council_class import CouncilMember


@runtime_checkable
class ReturnValue(Protocol):
    @abstractmethod
    def __call__(self, current, state):
        pass

    def __add__(self, other):
        return Joined((self, other))


class SkipClass(ReturnValue):
    def __call__(self, *args, **kwargs):
        pass


Skip = SkipClass()


class DelayClass(ReturnValue):
    def __call__(self, current, state):
        state.delayed.add(current)


Delay = DelayClass()


class Enqueue(ReturnValue):
    def __init__(self, *args: CouncilMember):
        self.args = args

    def __call__(self, current, state):
        state.delayed.update(self.args)


class Extend(ReturnValue):
    def __init__(self, *args: Iterable):
        self.args = args

    def __call__(self, current, state):
        state.partial_result.extend(chain.from_iterable(self.args))


class Append(ReturnValue):
    def __init__(self, *args):
        self.args = args

    def __call__(self, current, state):
        state.partial_result.extend(self.args)


class Joined(ReturnValue):
    def __init__(self, parts: Iterable[ReturnValue]):
        self.parts = parts

    def __call__(self, *args, **kwargs):
        for p in self.parts:
            p(*args, **kwargs)

    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)(chain(self.parts, other.parts))
        return type(self)((*self.parts, other))

    def __radd__(self, other):
        return self + other
