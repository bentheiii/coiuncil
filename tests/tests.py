from unittest import TestCase

from council import *


class CouncilTests(TestCase):
    def test_simple(self):
        c = ListCouncil()

        @c.add_member
        @none_continues
        def fizz(x):
            if x % 3 == 0:
                return 'Fizz'

        @c.add_member
        @always_after(fizz)
        @none_continues
        def buzz(x):
            if x % 5 == 0:
                return 'Buzz'

        @c.add_member
        @always_last
        @none_continues
        def blank(x, council_state):
            if not council_state.partial_result:
                return str(x)

        def fizzbuzz(x):
            return ''.join(c(x))

        self.assertEqual(fizzbuzz(5), 'Buzz')
        self.assertEqual(fizzbuzz(1), '1')
        self.assertEqual(fizzbuzz(15), 'FizzBuzz')
        self.assertEqual(fizzbuzz(91), '91')
        self.assertEqual(fizzbuzz(93), 'Fizz')

    def test_decorator(self):
        @ListCouncil.from_template(decorators=[truth_breaks, non_truth_continues])
        def seven_boom(x: int) -> bool:
            pass

        @seven_boom.add_member
        def divisible(x) -> bool:
            return x % 7 == 0

        @seven_boom.add_member
        def has_7(x) -> bool:
            return '7' in str(x)

        seven_boom = seven_boom.map(bool)

        for x in (7, 78, 0, 84):
            self.assertTrue(seven_boom(x), x)

        for x in (8, 99, -1, 85):
            self.assertFalse(seven_boom(x), x)
