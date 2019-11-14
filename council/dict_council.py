from __future__ import annotations

from enum import Enum, auto
from typing import TypeVar, Generic, Dict, Iterable, Sized

from council.abstract_council import Council
from council.return_value import MemberAction

K = TypeVar('K')
V = TypeVar('V')

_no_default = object()


class OnExistAction(Enum):
    Update = auto()
    Skip = auto()
    Raise = auto()


class DictCouncil(Council[Dict[K, V]], Generic[K, V]):
    def initial_result(self):
        return {}

    def default_action(self, out):
        if not isinstance(out, Sized) or not isinstance(out, Iterable) or len(out) != 2:
            raise TypeError('raw return values must be a 2-iterable')
        return self.Set(*out, on_exist=OnExistAction.Raise)

    class Set(MemberAction):
        def __init__(self, key, value, *, on_exist=OnExistAction.Update):
            self.key = key
            self.value = value
            self.on_exist = on_exist

        def __call__(self, current, state):
            d = state.partial_result
            if self.key in d:
                if self.on_exist == OnExistAction.Raise:
                    raise Exception(f'result already contains key {self.key}')
                elif self.on_exist == OnExistAction.Skip:
                    pass
                elif self.on_exist == OnExistAction.Update:
                    d[self.key] = self.value
                else:
                    raise Exception('bad on_exist value')
            else:
                d[self.key] = self.value
            return True

    # noinspection PyPep8Naming
    @classmethod
    def SetDefault(cls, *args):
        return cls.Set(*args, on_exist=OnExistAction.Skip)

    class ModifyValue(MemberAction):
        def __init__(self, key, func, default=_no_default):
            self.key = key
            self.func = func
            self.default = default

        def __call__(self, current, state):
            d = state.partial_result
            old_val = d.get(self.key, _no_default)
            if old_val is _no_default:
                if self.default is _no_default:
                    raise KeyError(self.key)
                new_val = self.default
            else:
                new_val = self.func(old_val)
            old_val[self.key] = new_val
            return True

    class MutateValue(MemberAction):
        def __init__(self, key, func, default=_no_default):
            self.key = key
            self.func = func
            self.default = default

        def __call__(self, current, state):
            d = state.partial_result
            old_val = d.get(self.key, _no_default)
            if old_val is not _no_default:
                self.func(old_val)
            elif self.default is _no_default:
                raise KeyError(self.key)
            else:
                d[self.key] = self.default
            return True

    class Pop(MemberAction):
        def __init__(self, *keys, allow_missing=False):
            self.keys = keys
            self.allow_missing = allow_missing

        def __call__(self, current, state):
            for k in self.keys:
                try:
                    del state.partial_result[k]
                except KeyError:
                    if not self.allow_missing:
                        raise
            return True

    class Update(MemberAction):
        def __init__(self, iterable=(), **kwargs):
            self.map = iterable
            self.kwargs = kwargs

        def __call__(self, current, state):
            state.partial_result.update(self.map, **self.kwargs)
            return True

    class ResetClass(MemberAction):
        def __call__(self, current, state) -> bool:
            state.partial_result.clear()
            return True

    Reset = ResetClass()
