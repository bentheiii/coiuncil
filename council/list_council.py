from __future__ import annotations

from functools import partial, update_wrapper, reduce
from itertools import chain
from typing import TypeVar, Generic, Tuple, Any, Dict, Set, Callable, List, Union, Iterable

from council.abstract_council import CouncilCallState, Council
from council.council_member import CouncilMember
from council.return_value import MemberAction

R = TypeVar('R')
R2 = TypeVar('R2')

_no_initial = object()


class ListCouncil(Council[List[R]], Generic[R]):
    class CallState(CouncilCallState):
        def make_result(self):
            return []

        def default_action(self, out):
            return ListCouncil.Append(out)

    def reduce(self, func: Callable[[R2, R], R2], initial: R2 = _no_initial) -> Callable[..., R2]:
        """
        :return: a callaback that converts the council's output according to func (using reduction)
        """
        if initial is _no_initial:
            return self.map(
                lambda a: reduce(func, a)
            )
        else:
            return self.map(
                lambda a: reduce(func, a, initial)
            )

    class Extend(MemberAction):
        """
        Extend the result list by iterables
        """

        def __init__(self, *args: Iterable):
            self.args = args

        def __call__(self, current, state):
            state.partial_result.extend(chain.from_iterable(self.args))
            return True

    class Append(MemberAction):
        """
        Append members to the result list
        """

        def __init__(self, *args):
            self.args = args

        def __call__(self, current, state):
            state.partial_result.extend(self.args)
            return True

    class Insert(MemberAction):
        """
        Insert members into the result at index
        """

        def __init__(self, index: int, *items):
            self.index = index
            self.items = items

        def __call__(self, current, state):
            state.partial_result[self.index:self.index] = self.items
            return True

    class RemoveResult(MemberAction):
        """
        Remove elements from the result list
        """

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
        """
        Remove elements from the result list by index
        """

        def __init__(self, *indices: Union[int, slice]):
            self.args = indices

        def __call__(self, current, state):
            for a in sorted(self.args,
                            key=lambda k: (k.stop if isinstance(k, slice) else k) % len(state.partial_result),
                            reverse=True):
                state.partial_result.pop(a)
            return True
