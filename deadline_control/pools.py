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


class Pool(DeadlineItem):
    """Control Deadline pools."""

    _POOLS_CACHE = NOT_SET
    _SLAVES_CACHE = defaultdict(lambda: NOT_SET)

    def __init__(self, name: str):
        """Setup the cache."""
        super(Pool, self).__init__(name)

        self._slaves_cache = Pool._SLAVES_CACHE[self.name]

    @classmethod
    def _all(cls) -> List[str]:
        """Get all the pool names.
        The value is cached.
        """
        if Pool._POOLS_CACHE is NOT_SET:
            Pool._POOLS_CACHE = api.Pools.GetPoolNames()
        return Pool._POOLS_CACHE

    @classmethod
    def all(cls) -> Iterable[Slave]:
        """Get all the slaves."""
        return map(cls, cls._all())

    @property
    def _slaves(self) -> List[str]:
        """Get all of the slave names assigned to the pool.
        The value is cached.
        """
        if self._slaves_cache is NOT_SET:
            self._slaves_cache = api.Slaves.GetSlaveNamesInPool(self.name)
        return self._slaves_cache

    @property
    def slaves(self) -> Iterable[Pool]:
        """Get all the slaves assigned to the pool."""
        return map(Slave, self._slaves)

    def create(self) -> bool:
        """Create the current pool if it doesn't exist."""
        logger.info('Creating pool: %s', self.name)
        result = api.Pools.AddPool(self.name)
        logger.info(result)

        # Update cache
        if result == 'Success' and Pool._POOLS_CACHE is not NOT_SET:
            Pool._POOLS_CACHE.append(self.name)
        return result == 'Success'

    def delete(self, force: bool = False) -> bool:
        """Delete a pool."""
        logger.info('Deleting pool: %s', self.name)

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

        # Delete pool
        result = api.Pools.DeletePool(self.name)
        logger.info(result)

        # Update cache
        if result == 'Success' and Pool._POOLS_CACHE is not NOT_SET:
            Pool._POOLS_CACHE.remove(self.name)
        return result == 'Success'


class SlavePools(DeadlineList):
    """Mapping of pools for each slave."""

    def __init__(self, slave: Slave, pools: List[Union[DeadlineItem, str]]) -> None:
        super().__init__(Pool, slave, map(Pool, pools))

    @property
    def slave(self) -> Slave:
        """Map `source` to `slave`."""
        return self.source

    @property
    def pools(self) -> List[str]:
        """Map `items` to `pools`."""
        return self.items

    def trigger_add(self, pool: DeadlineItem) -> None:
        """A new pool was added."""
        super().trigger_add(pool)
        result = api.Slaves.AddPoolToSlave(str(self.slave), str(pool))
        logger.info(result)
        self.slave.info['Pools'] = ','.join(map(str, self.pools))

    def trigger_remove(self, pool: DeadlineItem) -> None:
        """A pool was removed."""
        super().trigger_remove(pool)
        result = api.Slaves.RemovePoolFromSlave(str(self.slave), str(pool))
        logger.info(result)
        self.slave.info['Pools'] = ','.join(map(str, self.pools))

    def trigger_set(self, previous: List[DeadlineItem]) -> None:
        """The pools were changed."""
        super().trigger_set(previous)
        result = api.Slaves.SetPoolsForSlave(str(self.slave), list(map(str, self.pools)))
        logger.info(result)
        self.slave.info['Pools'] = ','.join(map(str, self.pools))
