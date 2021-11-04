"""Symbols are primitive data types which have a human readable form.

Example:
    def func(x=symbol.NOT_SET):
        if x is symbol.NOT_SET:
            raise ValueError('no input')
        return x

    >>> func(4)
    4
    >>> func(None)
    None
    >>> func()
    ValueError('no input')

Source: https://bitbucket.org/ftrack/ftrack-python-api/src/master/source/ftrack_api/symbol.py
"""


class Symbol(object):
    """A constant symbol."""

    def __init__(self, name, value=True):
        """Initialise symbol.

        Parameters:
            name (str): Unique name of the symbol.
            value (bool): Used for nonzero testing.
        """
        self.name = name
        self.value = value

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def __bool__(self):
        return bool(self.value)


NOT_SET = Symbol('NOT_SET', False)
