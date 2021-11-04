import logging
from collections.abc import MutableSequence
from typing import Any, List, Type, Union


logger = logging.getLogger(__name__)


class DeadlineItem(object):
    """Base Deadline item class.
    An item represented by this may not yet exist.
    """

    def __init__(self, name: str):
        if isinstance(name, DeadlineItem):
            name = name.name
        self.name = name

    def __repr__(self) -> None:
        return f'{type(self).__name__}({self.name.lower()!r})'

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.__repr__())

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, type(self)):
            return self.name.lower() == value.name.lower()
        return self.name.lower() == str(value).lower()

    def __ne__(self, value: Any) -> bool:
        return not self.__eq__(value)

    def __gt__(self, value: Any)-> bool:
        return self.name > value

    def __lt__(self, value: Any)-> bool:
        return self.name < value

    def __ge__(self, value: Any)-> bool:
        return self.name >= value

    def __le__(self, value: Any)-> bool:
        return self.name <= value

    def lower(self) -> str:
        """Convert the name to lowercase."""
        return self.__str__().lower()

    def upper(self) -> str:
        """Convert the name to uppercase."""
        return self.__str__().upper()

    def all(self):
        """Find all items."""
        return []

    def exists(self) -> bool:
        """Determine if an item exists."""
        return self in self.all()


class DeadlineList(MutableSequence):
    """List to connect different Deadline entites.

    This is designed to look like a normal list, but run commands on
    Deadline when anything is changed.
    """
    def __init__(self, item_type: Type[DeadlineItem], source: DeadlineItem, items: List[Union[DeadlineItem, str]]) -> None:
        self.item_type = item_type
        self.source = source
        self.items = list(map(self.item_type, items))

    def __repr__(self) -> str:
        """Return as a list containing DeadlineItems."""
        return repr(self.items)

    def __getitem__(self, index: int) -> DeadlineItem:
        """Get a DeadlineItem from an index or slice."""
        return self.items[index]

    def __setitem__(self, index: int, child: Union[List, DeadlineItem, str]) -> None:
        """Create a new DeadlineItem from an index or slice.
        TODO: typing override
        """
        items_old = list(self.items)
        if isinstance(index, slice):
            self.items[index] = list(map(self.item_type, child))
        else:
            self.items[index] = self.item_type(child)
        self.trigger_set(items_old)

    def __delitem__(self, index: int) -> None:
        """Delete an item."""
        items_old = list(self.items)
        del self.items[index]
        self.trigger_set(items_old)

    def __len__(self) -> int:
        """Get number of items."""
        return len(self.items)

    def append(self, item: Union[DeadlineItem, str]) -> None:
        """Add a new item."""
        item = self.item_type(item)
        self.items.append(item)
        self.trigger_add(item)

    def insert(self, index: int, item: Union[DeadlineItem, str]) -> None:
        """Insert a new item."""
        items_old = list(self.items)
        self.items.insert(index, self.item_type(item))
        self.trigger_set(items_old)

    def remove(self, item: Union[DeadlineItem, str]) -> None:
        """Remove an item."""
        self.items.remove(self.item_type(item))
        self.trigger_remove(item)

    def pop(self, index: int) -> DeadlineItem:
        """Pop an item."""
        items_old = list(self.items)
        item = self.items.pop(index)
        self.trigger_set(items_old)
        return item

    def index(self, item: Union[DeadlineItem, str]) ->  int:
        """Get the index of an item."""
        item = self.item_type(item)
        return self.items.index(item)

    def trigger_add(self, item: DeadlineItem) -> None:
        """Run this when a new item is added."""
        logger.info('Adding %r to %r', item, self.source)

    def trigger_remove(self, item: DeadlineItem) -> None:
        """Run this when an existing item is removed."""
        logger.info('Removing %r from %r', item, self.source)

    def trigger_set(self, previous: List[DeadlineItem]) -> None:
        """Run this when new child items are set."""
        logger.info('Setting %r to use %r', self.source, self.items)
