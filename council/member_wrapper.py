from abc import ABC, abstractmethod

from council import CouncilMember, Postpone, Continue, Break, MemberAction


class MemberWrapper(CouncilMember):
    def __init__(self, inner: CouncilMember):
        self.inner = CouncilMember.coerce(inner)

    def call(self, args, kwargs, council_state):
        return self.inner.call(args, kwargs, council_state)

    def __repr__(self):
        return f'{type(self).__name__}({self.inner!r})'


class AlwaysAfter(MemberWrapper):
    def __init__(self, inner, after):
        super().__init__(inner)
        self.after = after

    def call(self, args, kwargs, council_state):
        intersect = council_state.pending_members.intersection(self.after)
        if intersect:
            return Postpone(*intersect)
        return super().call(args, kwargs, council_state)

    def __repr__(self):
        return f'{type(self).__name__}({self.inner!r}, {self.after!r})'


class AlwaysLast(MemberWrapper):
    def call(self, args, kwargs, council_state):
        other_member = next(iter(council_state.pending_members), None)
        if other_member:
            return Postpone(other_member)
        return super().call(args, kwargs, council_state)


class AutoContinues(MemberWrapper, ABC):
    @abstractmethod
    def is_continue(self, x) -> bool:
        pass

    def call(self, args, kwargs, council_state):
        ret = super().call(args, kwargs, council_state)
        if self.is_continue(ret):
            ret = Continue
        return ret


class NoneContinues(AutoContinues):
    def is_continue(self, x) -> bool:
        return x is None


class TruthContinues(AutoContinues):
    def is_continue(self, x) -> bool:
        return x


class NonTruthContinues(AutoContinues):
    def is_continue(self, x) -> bool:
        return not x


class AutoBreaks(MemberWrapper, ABC):
    @abstractmethod
    def is_break(self, x) -> bool:
        pass

    def call(self, args, kwargs, council_state):
        ret = super().call(args, kwargs, council_state)
        if self.is_break(ret):
            ret = ret + Break
        return ret


class NotNoneBreaks(AutoBreaks):
    def is_break(self, x) -> bool:
        return x is not None


class TruthBreaks(AutoBreaks):
    def is_break(self, x) -> bool:
        return x and not isinstance(x, MemberAction)


class NonTruthBreaks(AutoBreaks):
    def is_break(self, x) -> bool:
        return not x


always_last = AlwaysLast

none_continues = NoneContinues
truth_continues = TruthContinues
non_truth_continues = NonTruthContinues

not_none_breaks = NotNoneBreaks
truth_breaks = TruthBreaks
non_truth_breaks = NonTruthBreaks


def always_after(*members):
    def ret(member):
        return AlwaysAfter(member, members)

    return ret


__all__ = [
    'always_last', 'always_after',
    'none_continues', 'truth_continues', 'non_truth_continues',
    'not_none_breaks', 'truth_breaks', 'non_truth_breaks'
]
