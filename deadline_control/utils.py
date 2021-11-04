"""
Main:
    'AuthenticationModeEnabled', 'Balancer', 'EnableAuthentication', 'Groups', 'JobReports', 'Jobs',
    'LimitGroups', 'MappedPaths', 'MaximumPriority', 'Plugins', 'Pools', 'Pulse', 'Repository',
    'SetAuthenticationCredentials', 'Slaves', 'SlavesRenderingJob', 'TaskReports', 'Tasks', 'Users'

Slaves:
    'AddGroupToSlave', 'AddPoolToSlave', 'DeleteSlave', 'GetSlaveHistoryEntries', 'GetSlaveInfo',
    'GetSlaveInfoSettings', 'GetSlaveInfos', 'GetSlaveNames', 'GetSlaveNamesInGroup', 'GetSlaveNamesInPool',
    'GetSlaveReports', 'GetSlaveReportsContents', 'GetSlaveSettings', 'GetSlavesInfoSettings',
    'GetSlavesSettings', 'RemoveGroupFromSlave', 'RemovePoolFromSlave', 'SaveSlaveInfo', 'SaveSlaveSettings',
    'SetGroupsForSlave', 'SetPoolsForSlave'

Pools:
    'AddPool', 'AddPools', 'DeletePool', 'DeletePools', 'GetPoolNames', 'PurgePools'

Groups:
    'AddGroup', 'AddGroups', 'DeleteGroup', 'DeleteGroups', 'GetGroupNames', 'PurgeGroups'

LimitGroups:
    'DeleteLimitGroup', 'GetLimitGroup', 'GetLimitGroupNames', 'GetLimitGroups',
    'ResetLimitGroup', 'SaveLimitGroup', 'SetLimitGroup'
"""

from DeadlineConnect import DeadlineCon

JOB_STAT = {
    0: 'queued',
    1: 'active',
    2: 'suspended',
    3: 'completed',
    4: 'failed',
    6: 'pending',
}

api = DeadlineCon('localhost', 8081)
