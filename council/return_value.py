from __future__ import annotations

from abc import abstractmethod
from itertools import chain
from typing import Iterable

from council.council_member import CouncilMember


class MemberAction:
    """
    A member action is an object that, when returned by a member, may influence the computation of the council
    """

    @abstractmethod
    def __call__(self, current, state) -> bool:
        """
        is called when returned by a member

        :param current: the member that returned self
        :param state: the CallState
        :return: whether to continue the computation
        """
        pass

    def __add__(self, other):
        if not isinstance(other, MemberAction):
            other = DefaultWrapper(other)
        return Joined((self, other))

    def __radd__(self, other):
        if not isinstance(other, MemberAction):
            other = DefaultWrapper(other)
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
    """
    Request that the member be called again after certain other members have been called
    """

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
    """
    Add other members to the council call. Note that the members are not added to the council
    """

    def __init__(self, *args: CouncilMember):
        self.args = args

    def __call__(self, current, state):
        state.pending_members.update(self.args)
        return True


class DefaultWrapper(MemberAction):
    def __init__(self, val):
        self.val = val

    def __call__(self, current, state):
        return state.council.default_action(self.val)(current, state)


class Joined(MemberAction):
    """
    Perform multiple member actions
    """

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


__all__ = ['Continue', 'Break', 'Postpone', 'Enqueue', 'MemberAction']
