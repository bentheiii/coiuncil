from __future__ import annotations

from abc import abstractmethod
from typing import TypeVar, Generic, NamedTuple, List, Iterable, Collection, Set

from council.util import Skip, Delay

R = TypeVar('R')


class CouncilMember(Generic[R]):
    @abstractmethod
    def call(self, args, kwargs, call_state: CouncilCallState) -> R:
        pass


class CouncilCallState(Generic[R], NamedTuple):
    council: Council
    pending: Set[CouncilMember[R]]
    delayed: Set[CouncilMember[R]]
    partial_result: List[R]


class Council(Generic[R]):
    def __init__(self):
        self.members: Collection[CouncilMember] = set()

    def __call__(self, *args, **kwargs):
        pending = set(self.members)
        delayed = set()
        result = []
        call_state = CouncilCallState(self, pending, delayed, result)
        while pending:
            while pending:
                member = pending.pop()
                out = member.call(args, kwargs, call_state)
                if out is Skip:
                    continue
                elif out is Delay:
                    delayed.add(member)
                else:
                    result.append(out)
            pending.update(delayed)
            delayed.clear()
