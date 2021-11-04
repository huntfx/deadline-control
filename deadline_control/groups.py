from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, Generator, List, Optional, Tuple, Union, TYPE_CHECKING

from .base import DeadlineItem, DeadlineList
from .core.symbol import NOT_SET
from .utils import api

if TYPE_CHECKING:
    from .slaves import Slave


logger = logging.getLogger(__name__)


class Group(DeadlineItem):
    """Control Deadline groups."""

    _GROUPS_CACHE = NOT_SET
    _SLAVES_CACHE = defaultdict(lambda: NOT_SET)

    def __init__(self, name: str):
        """Setup the cache."""
        super(Group, self).__init__(name)

        self._slaves_cache = Group._SLAVES_CACHE[self.name]

    @classmethod
    def _all(cls) -> List[str]:
        """Get all the group names.
        The value is cached.
        """
        if Group._GROUPS_CACHE is NOT_SET:
            Group._GROUPS_CACHE = api.Groups.GetGroupNames()
        return Group._GROUPS_CACHE

    @classmethod
    def all(cls) -> Iterable[Slave]:
        """Get all the slaves."""
        return map(cls, cls._all())

    @property
    def _slaves(self) -> List[str]:
        """Get all of the slave names assigned to the group.
        The value is cached.
        """
        if self._slaves_cache is NOT_SET:
            self._slaves_cache = api.Slaves.GetSlaveNamesInGroup(self.name)
        return self._slaves_cache

    @property
    def slaves(self) -> Iterable[Group]:
        """Get all the slaves assigned to the group."""
        from .slaves import GroupSlaves
        return GroupSlaves(self, self._slaves)

    @slaves.setter
    def slaves(self, slaves) -> None:
        """Set new slaves from a list."""
        self.slaves[:] = slaves

    def create(self) -> bool:
        """Create the current group if it doesn't exist."""
        logger.info('Creating group: %s', self.name)
        result = api.Group.AddGroup(self.name)
        logger.info(result)

        # Update cache
        if result == 'Success' and Group._GROUPS_CACHE is not NOT_SET:
            Group._GROUPS_CACHE.append(self.name)
        return result == 'Success'

    def delete(self, force: bool = False) -> bool:
        """Delete a group."""
        logger.info('Deleting group: %s', self.name)

        # Check if assigned to any slaves
        if not force:
            try:
                next(self.slaves)
            except StopIteration:
                pass
            else:
                logger.warning(
                    'Preventing deletion as slaves are currently assigned. '
                    'Use `force=True` to bypass this check.'
                )
                return False

        # Delete group
        result = api.Groups.DeleteGroup(self.name)
        logger.info(result)

        # Update cache
        if result == 'Success' and Group._GROUPS_CACHE is not NOT_SET:
            Group._GROUPS_CACHE.remove(self.name)
        return result == 'Success'


class SlaveGroups(DeadlineList):
    """Mapping of groups for each slave."""

    def __init__(self, slave: Slave, groups: List[str]) -> None:
        super().__init__(Group, slave, groups)

    @property
    def slave(self) -> Slave:
        """Map `source` to `slave`."""
        return self.source

    @property
    def groups(self) -> List[str]:
        """Map `items` to `groups`."""
        return self.items

    def trigger_add(self, item: DeadlineItem) -> None:
        """A new group was added."""
        super().trigger_add(item)
        result = api.Slaves.AddGroupToSlave(str(self.slave), str(item))
        logger.info(result)
        self.slave.info['Grps'] = ','.join(map(str, self.groups))

    def trigger_remove(self, item: DeadlineItem) -> None:
        """A group was removed."""
        super().trigger_remove(item)
        result = api.Slaves.RemoveGroupFromSlave(str(self.slave), str(item))
        logger.info(result)
        self.slave.info['Grps'] = ','.join(map(str, self.groups))

    def trigger_set(self, previous: List[DeadlineItem]) -> None:
        """The groups were changed."""
        super().trigger_set(previous)
        result = api.Slaves.SetGroupsForSlave(str(self.slave), list(map(str, self.groups)))
        logger.info(result)
        self.slave.info['Grps'] = ','.join(map(str, self.groups))
