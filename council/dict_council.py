from __future__ import annotations

from functools import partial, update_wrapper, reduce
from itertools import chain
from typing import TypeVar, Generic, Tuple, Any, Dict, Set, Callable, List, Union, Iterable, Sized

from council.abstract_council import CouncilCallState, Council
from council.council_member import CouncilMember
from council.return_value import MemberAction

K = TypeVar('K')
V = TypeVar('V')


class DictCouncil(Council[Dict[K, V]], Generic[K, V]):
    class CallState(CouncilCallState):
        def make_result(self):
            return {}

        def default_action(self, out):
            if not isinstance(out, Sized) or not isinstance(out, Iterable) or len(out) != 2:
                raise TypeError('')
            return DictCouncil.SetMissing(*out)

    class SetMissing(MemberAction):
        def __init__(self, ):