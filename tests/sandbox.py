from council import *

seven_boom: Council


@Council.from_template
def seven_boom(x: int) -> bool:
    pass


@seven_boom.add_member
@truth_breaks
def divisible(x) -> bool:
    return x % 7 == 0


@seven_boom.add_member
@truth_breaks
def has_7(x) -> bool:
    return '7' in str(x)


seven_boom = seven_boom.compose(any)
print(seven_boom(56))
