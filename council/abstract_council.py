from __future__ import annotations

from abc import abstractmethod
from functools import partial, update_wrapper, lru_cache
from typing import Set, Iterable, TypeVar, Callable, Generic, Tuple, Dict, Any

from council.return_value import MemberAction
from council.council_member import CouncilMember

R = TypeVar('R')
R2 = TypeVar('R2')


class AbstractCouncil(Generic[R]):
    @abstractmethod
    def __call__(self, *args, **kwargs) -> R:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self, instance)

    @abstractmethod
    def add_member(self, member):
        pass

    @abstractmethod
    def remove_member(self, member):
        pass

    def on_member_change(self, member):
        pass

    def join_temporary(self, member):
        """
        add a member as add_member to the council, and get a callback that removes it
        :return: a callable that removes the new member from the council. Has a value __member__ that stores the member.
        """
        member = self.add_member(member)
        ret = partial(self.remove_member, member)
        ret.__member__ = member
        return ret

    def map(self, func: Callable[[R], R2]) -> MappedCouncil[R, R2]:
        """
        :return: a callaback that converts the council's output according to func
        """
        return MappedCouncil(self, func)

    def lru_cache(self, *args, **kwargs):
        return CachedCouncil(self, *args, **kwargs)


class CouncilCallState(Generic[R]):
    """
    Representing a state of calling a council object, passed to members as they are called
    """

    def __init__(self, council: Council[R], args: Tuple, kwargs: Dict[str, Any]):
        self.council = council
        self.args = args
        self.kwargs = kwargs

        self.dependency_stack = []
        self.pending_members = set(self.council.members)
        self.partial_result = self.council.initial_result()

    def call_next(self):
        """
        process a member of the council

        :return: whether to continue with the call
        """
        if self.dependency_stack:
            member = self.dependency_stack.pop()
        elif self.pending_members:
            member = self.pending_members.pop()
        else:
            return False

        out = member.call(self.args, self.kwargs, self)
        if not isinstance(out, MemberAction):
            out = self.council.default_action(out)
        return out(member, self)

    def __call__(self) -> R:
        while self.call_next():
            pass
        return self.partial_result


class Council(AbstractCouncil[R], Generic[R]):
    def __init__(self, name: str = None, decorators=()):
        """
        :param name: the name of the council
        :param decorators: these decorators will be applied, in reverse order, to all members added
        """
        self.members: Set[CouncilMember[R]] = set()
        if not isinstance(decorators, Iterable):
            decorators = decorators,
        self.member_wrappers = decorators
        if name:
            self.__name__ = name

    @classmethod
    def from_template(cls, template=None, **kwargs):
        """
        will create a council based on a wrapped callable, usable as decorator
        :param template: the object to base on, most likely a function. Will never be called.
        :param kwargs: forwarded to Council.__init__
        """
        if template is None:
            return partial(cls.from_template, **kwargs)

        name = getattr(template, '__name__', None)
        ret = cls(name, **kwargs)
        update_wrapper(ret, template)
        return ret

    def __set_name__(self, owner, name):
        ex_name = getattr(self, '__name__', None)
        if ex_name is None:
            self.__name__ = name
        elif ex_name != name:
            raise ValueError(f'this council already has an assigned name {ex_name}')

    def call_state(self, args, kwargs):
        """
        Generate a new call state for the council
        """
        return CouncilCallState(self, args, kwargs)

    @abstractmethod
    def initial_result(self) -> R:
        pass

    @abstractmethod
    def default_action(self, out) -> MemberAction:
        pass

    def __call__(self, *args, **kwargs) -> R:
        call_state = self.call_state(args, kwargs)
        return call_state()

    def add_member(self, member):
        """
        Add a member, applying all the decorators, can be used as decorator

        :param member: the object to convert to member, decorate, and add to the council
        :return: the member added, including all conversions and decorations
        """
        if not isinstance(member, CouncilMember):
            member = CouncilMember.coerce(member)
        for ad in reversed(self.member_wrappers):
            member = ad(member)
        self.members.add(member)
        member.introduce(self)
        return member

    def remove_member(self, member):
        """
        remove a member from the council
        """
        self.members.remove(member)
        member.depart(self)

    def __repr__(self):
        try:
            return f'{type(self).__name__}({self.__name__!r})'
        except AttributeError:
            return super().__repr__()

    class Modify(MemberAction):
        def __init__(self, func):
            self.func = func

        def __call__(self, current, state) -> bool:
            state.partial_result = self.func(state.partial_result)
            return True

    class Mutate(MemberAction):
        def __init__(self, func):
            self.func = func

        def __call__(self, current, state) -> bool:
            self.func(state.partial_result)
            return True

    class ResetClass(MemberAction):
        def __call__(self, current, state) -> bool:
            state.partial_result = state.council.initial_result()
            return True

    Reset = ResetClass()


class MappedCouncil(AbstractCouncil[R2], Generic[R, R2]):
    def __init__(self, council: AbstractCouncil[R], conv: Callable[..., R2]):
        self.council = council
        self.conv = conv
        update_wrapper(self, council)

    def __call__(self, *args, **kwargs):
        ret = self.council(*args, **kwargs)
        return self.conv(ret)

    def __repr__(self):
        return f'{self.council!r}.map({self.conv!r})'

    def add_member(self, member):
        return self.council.add_member(member)

    def remove_member(self, member):
        return self.council.remove_member(member)

    def on_member_change(self, member):
        return self.council.on_member_change(member)


class CachedCouncil(Generic[R], AbstractCouncil[R]):
    """
    A council that caches its results. Note that the council returns tuples, not lists.
    """

    def __init__(self, inner: AbstractCouncil[R], *args, **kwargs):
        self.inner = inner
        self.cache = lru_cache(*args, **kwargs)(inner)
        update_wrapper(self, inner)

    def __call__(self, *args, **kwargs) -> Tuple[R]:
        return self.cache(*args, **kwargs)

    def add_member(self, member):
        ret = super().add_member(member)
        self.cache_clear()
        return ret

    def remove_member(self, member):
        ret = super().remove_member(member)
        self.cache_clear()
        return ret

    def cache_clear(self):
        self.cache.cache_clear()

    def on_member_change(self, member):
        self.cache_clear()
        return self.inner.on_member_change(member)
