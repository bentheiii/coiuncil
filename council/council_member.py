from __future__ import annotations

from typing import TypeVar, Generic, Callable, Union, TYPE_CHECKING
from abc import abstractmethod
from functools import update_wrapper
from inspect import signature

if TYPE_CHECKING:
    from council import MemberAction

R = TypeVar('R')


class CouncilMember(Generic[R]):
    """
    A council member that can participate in councils
    """

    @abstractmethod
    def call(self, args, kwargs, council_state) -> Union[R, MemberAction]:
        """
        called when the member is processed

        :param args: arguments passed to the council
        :param kwargs: keyword arguments passed to the council
        :param council_state: the CouncilCallState instance of the current council call
        :return: a value to append to the council's result or a MemberAction to issue special instructions
        """
        pass

    @classmethod
    def coerce(cls, x):
        """
        convert x to a CouncilMember, if needed
        """
        if isinstance(x, cls):
            return x
        if isinstance(x, Callable):
            return council_member(x)
        else:
            raise TypeError(f'cannot coerce {x} to a council member')


class FuncMember(Generic[R], CouncilMember[R]):
    """
    A council member that wraps a function
    """

    def __init__(self, func):
        self.func = func
        update_wrapper(self, self.func)

    def call(self, args, kwargs, council_state):
        return self(*args, council_state=council_state, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f'{type(self).__name__}({self.func!r})'


class SimpleFuncMember(FuncMember[R], Generic[R]):
    """
    A FuncMember that ignores the council state provided
    """

    def call(self, args, kwargs, council_state=None):
        return self(*args, **kwargs)


def council_member(func: Callable[..., R]) -> CouncilMember[R]:
    """
    a function decorator to create an appropriate member

    :param func: the function to wrap
    :return: a CouncilMember that will call func, ignoring council_state unless a parameter of that name exists
     in func's signature
    """
    sig = signature(func)
    if 'council_state' in sig.parameters:
        return FuncMember(func)
    return SimpleFuncMember(func)
