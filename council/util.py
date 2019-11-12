

Delay = object()
Skip = object()


class Transparent:
    def __init__(self, *args):
        self.args = args


class Enqueue(Transparent):
    pass


class Extend(Transparent):
    pass


class Append(Transparent):
    pass
