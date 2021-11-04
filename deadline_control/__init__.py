from .slaves import Slave
from .pools import Pool
from .groups import Group
from .base import DeadlineItem, DeadlineList


# Fix for Deadline\DeadlineUtility.py using basestring
import builtins
builtins.basestring = str


if __name__ == '__main__':
    slave = Slave('BZWORKG108-GPU0')
    group = Group('rose')
    #slave.pools.append('test2')
    #print(slave.pools[0].exists)
    #print(list(Group.all()))

    # slave.groups = ['rose']
    #print(Group('rose').slaves, 'slaves')
    #Group('rose').slaves.index(DeadlineItem('BZWORKG108-gpu1'))
