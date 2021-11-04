from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, Generator, List, Optional, Tuple, Union, TYPE_CHECKING

from .base import DeadlineItem, DeadlineList
from .core.symbol import NOT_SET
from .utils import api

if TYPE_CHECKING:
    from .groups import Group
    from .pools import Pool


logger = logging.getLogger(__name__)


class Status(Enum):
    """Possible slave statuses.

    https://docs.thinkboxsoftware.com/products/deadline/10.0/1_User%20Manual/manual/rest-slaves.html#slave-property-values
    """
    Unknown = 0
    Rendering = 1
    Idle = 2
    Offline = 3
    Stalled = 4
    StartingJob = 5
    HouseCleaning = 9  # Note: This is just a guess, it's not documented


class ExtraInfo(object):
    """Create a lazy list for the extra info columns."""

    def __init__(self, slave: Slave) -> None:
        self.slave = slave

    def __getitem__(self, item: Union[str, int]) -> str:
        """Get an extra info value."""
        if isinstance(item, int):
            return self.slave.settings[f'Ex{item}']
        return self.slave.settings['ExDic'][item]

    def __setitem__(self, item: Union[str, int], value: str) -> None:
        """Set a new extra info value."""
        if isinstance(item, int):
            self.slave.update_settings(**{f'Ex{item}': value})
        else:
            self.slave.update_settings(ExDic={item: value})

    def __delitem__(self, item: Union[str, int]):
        """Delete an extra info value."""
        self.__setitem__(item, '')

    def keys(self) -> Tuple[Union[int, str]]:
        """Get all the extra info keys."""
        return tuple(range(0, 10)) + tuple(self.slave.settings['ExDic'])

    def values(self) -> Tuple[str]:
        """Get all the extra info values."""
        return tuple(self.__getitem__(key) for key in self.keys())

    def items(self) -> Generator[Tuple[Union[int, str], str], None, None]:
        """Get the extra info keys and values."""
        for key in self.keys():
            yield key, self.__getitemm__(key)


class Slave(DeadlineItem):
    """Control Deadline slaves."""

    _SLAVES_CACHE = NOT_SET
    _INFO_CACHE = defaultdict(lambda: NOT_SET)
    _SETTINGS_CACHE = defaultdict(lambda: NOT_SET)

    def __init__(self, name: str):
        """Setup the cache."""
        super(Slave, self).__init__(name)

        self._info = Slave._INFO_CACHE[self.name]
        self._settings = Slave._SETTINGS_CACHE[self.name]

    @classmethod
    def _all(cls) -> List[str]:
        """Get all the slave names.
        The value is cached.
        """
        if Slave._SLAVES_CACHE is NOT_SET:
            Slave._SLAVES_CACHE = api.Slaves.GetSlaveNames()
        return Slave._SLAVES_CACHE

    @classmethod
    def all(cls) -> Iterable[Slave]:
        """Get all the slaves."""
        return map(cls, cls._all())

    @property
    def info(self) -> Dict[str, Any]:
        """Get the raw slave info."""
        if self._info is NOT_SET:
            self._info = api.Slaves.GetSlaveInfo(self.name) or None
        return self._info

    @property
    def settings(self) -> Dict[str, Any]:
        """Get the raw slave settings."""
        if self._settings is NOT_SET:
            self._settings = api.Slaves.GetSlaveSettings(self.name) or None
        return self._settings[0]

    def _write_settings(self, kwargs: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> bool:
        """Write any new settings.
        This does not update Deadline.

        Returns:
            bool: If any settings were updated.

        Raises:
            KeyError: If the option doesn't exist in the settings.
        """
        if settings is None:
            settings = self.settings

        updated = False
        for k, v in kwargs.items():
            # Recursively set settings
            if isinstance(v, dict):
                if self._write_settings(v, settings[k]):
                    updated = True

            # Set top level settings
            elif settings[k] != v:
                settings[k] = v
                updated = True
        return updated

    def update_settings(self, **kwargs: Any) -> bool:
        """Update an existing setting and save to Deadline.

        Returns:
            bool: If the update was successful or not

        Raises:
            KeyError: If the option doesn't exist in the settings.
        """
        logger.info('[%s] Updating settings: %r', self.name, kwargs)
        update_required = self._write_settings(kwargs)

        if update_required:
            result = api.Slaves.SaveSlaveSettings(self.settings)
        else:
            result = 'No updates required'

        logger.info(result)
        return result in ('Success', 'No updates required')

    @property
    def exists(self) -> bool:
        """Check if the slave exists."""
        if self._setting is NOT_SET:
            return self.info is not None
        return self.setting is not None

    @property
    def status(self) -> Status:
        """Get the current status of the slave."""
        return Status(self.data['Stat'])

    @property
    def offline(self) -> bool:
        """Determine if the slave is offline."""
        return self.status == Status.Offline

    @property
    def idle(self) -> bool:
        """Determine if the slave is idle."""
        return self.status in (Status.Idle, Status.HouseCleaning)

    @property
    def rendering(self) -> bool:
        """Determine if the slave is rendering."""
        return self.status == Status.Rendering

    @property
    def stalled(self) -> bool:
        """Determine if the slave is stalled."""
        return self.status == Status.Stalled

    @property
    def enabled(self) -> bool:
        """Get if the slave is enabled."""
        return self.settings['Enable']

    @property
    def disabled(self) -> bool:
        """Get if the slave is disabled."""
        return not self.enabled

    def enable(self) -> bool:
        """Enable the slave."""
        return self.update_settings(Enable=True)

    def disable(self) -> bool:
        """Disnable the slave."""
        return self.update_settings(Enable=False)

    @property
    def pools(self) -> Iterable[Pool]:
        """Get all the pools assigned to the slave."""
        from .pools import SlavePools
        return SlavePools(self, self.info['Pools'].split(','))

    @pools.setter
    def pools(self, pools) -> None:
        """Set new pools from a list."""
        self.pools[:] = pools

    @property
    def groups(self) -> Iterable[Group]:
        """Get all the groups assigned to the slave."""
        from .groups import SlaveGroups
        return SlaveGroups(self, self.info['Grps'].split(','))

    @groups.setter
    def groups(self, groups) -> None:
        """Set new groups from a list."""
        self.groups[:] = groups

    @property
    def extra_info(self) -> ExtraInfo:
        """Return a dict of the slave extra info."""
        return ExtraInfo(self)


class GroupSlaves(DeadlineList):
    """Mapping of slaves for each group."""

    def __init__(self, group: Group, slaves: List[str]) -> None:
        super().__init__(Slave, group, slaves)

    @property
    def group(self) -> Group:
        """Map `source` to `group`."""
        return self.source

    @property
    def slaves(self) -> List[str]:
        """Map `items` to `slaves`."""
        return self.items

    def trigger_add(self, slave: DeadlineItem) -> None:
        """A new slaves was added."""
        return Slave(slave).groups.append(self.group)

    def trigger_remove(self, slave: DeadlineItem) -> None:
        """A slaves was removed."""
        return Slave(slave).groups.remove(self.group)

    def trigger_set(self, previous: List[DeadlineItem]) -> None:
        """The slaves were changed."""
        super().trigger_set(previous)
        old = set(previous)
        new = set(self.slaves)

        # Add slaves to group
        result = api.Slaves.SetGroupsForSlave(
            slave=[str(item) for item in new - old],
            group=str(self.group),
        )
        logger.info(result)

        # Remove slaves from group
        for slave in map(Slave, old - new):
            slave.groups.remove(self.group)
