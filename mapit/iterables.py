import io


def defaultiter(it, default):
    """This wraps an iterable so that if it's empty,
    it will return a default value instead."""
    empty = True
    for i in it:
        yield i
        empty = False
    if empty:
        yield default


# If you wanted iterdict() to be more generic, it'd be something like:
# import itertools
# if not args:
#     self.ITERABLE = iter()
# elif isinstance(args[0], dict):
#     self.ITERABLE = args[0].items()
# else:
#     self.ITERABLE = args[0]
# if kwargs:
#     self.ITERABLE = itertools.chain(self.ITERABLE, kwargs.items())


class iterdict(dict):
    """This is a fake dict that sticks an iterable on items/iteritems. Why on
    earth would you want to do such a thing, I hear you cry? Well, if you want
    to output what you'd like to be a dict of c. 200,000 objects from a
    database, currently held in a lovely iterable, as JSON, but discover that
    json.iterencode() doesn't work with iterators, and that wouldn't be much
    help with a dict anyway, you either need to write your own iterator to
    output a JSON object, or trick iterencode() into thinking you're passing it
    a dict when you're not."""

    def __init__(self, *args, **kwargs):
        self.ITERABLE = args[0]
        # Create a dict so that "if X" passes.
        super(iterdict, self).__init__({'Hack': True})

    def iteritems(self):
        return self.ITERABLE

    def items(self):
        return self.ITERABLE


class iterlist(list):
    """This is a fake list that uses its own stored iterable. The built in json
    package, though it can work as an iterator using iterencode() or indeed
    dump(), can't take one as input, which is annoying if you're trying to save
    memory. This class can be passed to iterencode() and will work the same as
    a list, but won't require the list to exist first."""

    def __init__(self, lst):
        self.ITERABLE = lst
        # Create a list so that "if X" passes.
        super(iterlist, self).__init__("Hack")

    def __iter__(self):
        return self.ITERABLE


# From https://stackoverflow.com/a/20260030
def iterable_to_stream(iterable, buffer_size=io.DEFAULT_BUFFER_SIZE):
    """
    Lets you use an iterable (e.g. a generator) that yields bytestrings as a read-only
    input stream. For efficiency, the stream is buffered.
    """
    class IterStream(io.RawIOBase):
        def __init__(self):
            self.leftover = None

        def readable(self):
            return True

        def readinto(self, b):
            try:
                ll = len(b)  # We're supposed to return at most this much
                chunk = self.leftover or next(iterable)
                output, self.leftover = chunk[:ll], chunk[ll:]
                b[:len(output)] = output
                return len(output)
            except StopIteration:
                return 0    # indicate EOF
    return io.BufferedReader(IterStream(), buffer_size=buffer_size)
