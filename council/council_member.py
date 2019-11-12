from typing import TypeVar, Generic

from council.council_class import CouncilMember

R = TypeVar('R')

class SimpleFuncMember(Generic[R], CouncilMember[R]):
    def __init__(self, func):
        self.func = func

    def call(self, args, kwargs, state):
        return self.func()

    def __str__(self):
        return str(self.func)