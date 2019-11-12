from __future__ import annotations

from functools import partial, update_wrapper, reduce
from typing import TypeVar, Generic, Tuple, Any, Dict, Set, Callable, List, Union, Iterable

from council.council_member import CouncilMember
from council.return_value import MemberAction, Append

R = TypeVar('R')
R2 = TypeVar('R2')

_no_initial = object()


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
        self.partial_result = []

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
            out = Append(out)
        return out(member, self)

    def __call__(self):
        while self.call_next():
            pass
        return self.partial_result


class Council(Generic[R]):
    """
    The central class, an aggregate of council members that processes them all for a call
    """

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
    def from_template(cls, template=None, *, update_annotations=True, **kwargs) \
            -> Union[Council[R], Callable[..., Council[R]]]:
        """
        will create a council based on a wrapped callable, usable as decorator
        :param template: the object to base on, most likely a function. Will never be called.
        :param update_annotations: Whether to ensure that the council's __annotations__ are correct
        :param kwargs: forwarded to Council.__init__
        """
        if template is None:
            return partial(cls.from_template, update_annotations=update_annotations, **kwargs)

        name = getattr(template, '__name__', None)
        ret = cls(name, **kwargs)
        update_wrapper(ret, template)

        if update_annotations:
            ret_annotations = getattr(ret, '__annotations__', None)
            if ret_annotations:
                globns = getattr(ret, '__globals__', {})
                globns.update(getattr(template, '__globals__', {}))
                r = ret_annotations.get('return')
                if r:
                    ret_annotations['return'] = List[r]
                else:
                    ret_annotations['return'] = 'list'
                ret.__globals__ = globns
            else:
                ret.__annotations__ = {'return': 'list'}
        return ret

    def __set_name__(self, owner, name):
        ex_name = getattr(self, '__name__', None)
        if ex_name is None:
            self.__name__ = name
        elif ex_name != name:
            raise ValueError(f'this council already has an assigned name {ex_name}')

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self, instance)

    def call_state(self, args, kwargs):
        """
        Generate a new call state for the council
        """
        return CouncilCallState(self, args, kwargs)

    def __call__(self, *args, **kwargs) -> List[R]:
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
        return member

    def remove_member(self, member):
        """
        remove a member from the council
        """
        self.members.remove(member)

    def join_temporary(self, member):
        """
        add a member as add_member to the council, and get a callback that removes it
        :return: a callable that removes the new member from the council. Has a value __member__ that stores the member.
        """
        member = self.add_member(member)
        ret = partial(self.remove_member, member)
        ret.__member__ = member
        return ret

    def __str__(self):
        try:
            return f'{type(self).__name__}({self.__name__!r})'
        except AttributeError:
            return super().__str__()

    def aggregate(self, func: Callable[[List[R]], R2]) -> Callable[..., R2]:
        """
        :return: a callaback that converts the council's output according to func
        """
        return lambda *a, **k: func(self(*a, **k))

    def reduce(self, func: Callable[[R2, R], R2], initial: R2 = _no_initial) -> Callable[..., R2]:
        """
        :return: a callaback that converts the council's output according to func (using reduction)
        """
        if initial is _no_initial:
            return self.aggregate(
                lambda a: reduce(func, a)
            )
        else:
            return self.aggregate(
                lambda a: reduce(func, a, initial)
            )
