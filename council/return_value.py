from __future__ import annotations

from abc import abstractmethod
from itertools import chain
from typing import Protocol, runtime_checkable, Iterable

from council.council_class import CouncilMember


@runtime_checkable
class MemberAction(Protocol):
    """
    A member action is an object that, when returned by a member, may influence the computation of the council
    """

    @abstractmethod
    def __call__(self, current, state) -> bool:
        """
        is called when returned by a member

        :param current: the member that returned self
        :param state: the CouncilCallState
        :return: whether to continue the computation
        """
        pass

    def __add__(self, other):
        if not isinstance(other, MemberAction):
            other = Append(other)
        return Joined((self, other))

    def __radd__(self, other):
        if not isinstance(other, MemberAction):
            other = Append(other)
        return other + self


class ContinueClass(MemberAction):
    """
    Ignore the member and add nothing to the result
    """
    def __call__(self, *args, **kwargs):
        return True


Continue = ContinueClass()


class BreakClass(MemberAction):
    """
    End the computation, no other members will be processed
    """
    def __call__(self, current, state):
        return False


Break = BreakClass()


class Postpone(MemberAction):
    def __init__(self, *wait_for: CouncilMember):
        if not wait_for:
            raise ValueError('must specify a member to wait for')
        self.wait_for = wait_for

    def __call__(self, current, state):
        state.dependency_stack.append(current)
        for wf in self.wait_for:
            try:
                state.pending_members.remove(wf)
            except KeyError:
                raise KeyError(f'cannot wait for member outside of the pending set {wf}')
            state.dependency_stack.append(wf)
        return True


class Enqueue(MemberAction):
    def __init__(self, *args: CouncilMember):
        self.args = args

    def __call__(self, current, state):
        state.pending_members.update(self.args)
        return True


class Extend(MemberAction):
    def __init__(self, *args: Iterable):
        self.args = args

    def __call__(self, current, state):
        state.partial_result.extend(chain.from_iterable(self.args))
        return True


class Append(MemberAction):
    def __init__(self, *args):
        self.args = args

    def __call__(self, current, state):
        state.partial_result.extend(self.args)
        return True


class RemoveResult(MemberAction):
    def __init__(self, *args):
        self.args = args

    def __call__(self, current, state):
        for a in self.args:
            try:
                state.partial_result.remove(a)
            except ValueError:
                raise ValueError(f'value {a} not found in results')
        return True


class PopResult(MemberAction):
    def __init__(self, *indices: int):
        self.args = indices

    def __call__(self, current, state):
        for a in sorted(self.args,
                        key=lambda k: k % len(state.partial_result),
                        reverse=True):
            state.partial_result.pop(a)
        return True


class ClearResultClass(MemberAction):
    def __call__(self, current, state):
        state.partial_result.clear()
        return True


ClearResult = ClearResultClass()


class Joined(MemberAction):
    def __init__(self, parts: Iterable[MemberAction]):
        self.parts = parts

    def __call__(self, *args, **kwargs):
        ret = True
        for p in self.parts:
            ret &= p(*args, **kwargs)
        return ret

    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)(chain(self.parts, other.parts))
        return type(self)((*self.parts, other))

    def __radd__(self, other):
        return type(self)((other, *self.parts))


__all__ = ['MemberAction', 'Continue', 'Break', 'Postpone', 'Enqueue', 'Extend', 'Append', 'RemoveResult', 'PopResult',
           'ClearResult']
