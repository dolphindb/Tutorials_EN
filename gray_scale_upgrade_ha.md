# Grayscale Upgrade for High-availability Clusters

- [Grayscale Upgrade for High-availability Clusters](#grayscale-upgrade-for-high-availability-clusters)
  - [1. Introduction](#1-introduction)
  - [2. Compatibility](#2-compatibility)
  - [3. Procedure](#3-procedure)
    - [3.1 Preparation for Upgrade](#31-preparation-for-upgrade)
    - [3.2 Node Upgrade](#32-node-upgrade)
    - [3.3 Verification](#33-verification)


## 1. Introduction

This tutorial introduces how to grayscale upgrade (partial update) a high-availability (HA) cluster.

For a regular upgrade, all nodes must be shut down before you upgrade a cluster. A cluster is upgraded after all nodes are updated to the new version, and during the upgrade, all services and operations are interrupted.

In a grayscale upgrade, a cluster is upgraded on a node-by-node basis with uninterrupted service. After a node is upgraded and returns to service, another node is upgraded, and so on until all nodes are upgraded. During a grayscale upgrade, the system remains online. This requires that the cluster must be deployed for high availability.

## 2. Compatibility

Grayscale upgrades requires in-memory data formats, including transmission protocols, serialization protocols, etc., to be fully compatible between the new and the old versions.

Therefore, before a major upgrade, it is recommended to contact our technical support for a risk assessment.

## 3. Procedure

In the following example, the cluster of version 2.00.7.4 is upgraded to version 2.00.8.12.

`controller.cfg`

```
mode=controller
localSite=10.10.11.2:8920:HActl44
dfsHAMode=Raft
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dataSync=1
workerNum=4
localExecutors=3
maxConnections=512
maxMemSize=8
lanCluster=0
dfsRecoveryWaitTime=30000
```

`cluster.nodes`

```sh
localSite,mode
10.10.11.1:8920:HActl43,controller
10.10.11.2:8920:HActl44,controller
10.10.11.3:8920:HActl45,controller
10.10.11.1:8921:agent43,agent
10.10.11.2:8921:agent44,agent
10.10.11.3:8921:agent45,agent
10.10.11.1:8922:node43,datanode
10.10.11.2:8922:node44,datanode
10.10.11.3:8922:node45,datanode
```

`pnodeRun(version)`

```sh
	node	value
0	node43	2.00.7.4 2022.12.08
1	node44	2.00.7.4 2022.12.08
2	node45	2.00.7.4 2022.12.08
```

Suppose you have a database "dfs://stock" with a DFS table "stock" in DolphinDB (which can be created with the following script).

```python
db = database("dfs://stock",VALUE,2023.01.01..2023.01.10,,'TSDB')
tmp = table(1:0,[`time,`name,`id],[TIMESTAMP,SYMBOL,INT])
pt = db.createPartitionedTable(tmp,`stock,`time,,`name,ALL)
```

We use Python API to write data to the DFS table in a highly available manner during the upgrade.

```python
import dolphindb as ddb
import pandas as pd
import datetime
import time
import random
s = ddb.session()
sites = ["192.168.100.43:8922","192.168.100.44:8922","192.168.100.45:8922"]
s.connect(host="192.168.100.43",port=8922,userid="admin",password="123456", highAvailability=True, highAvailabilitySites=sites)
appender = ddb.tableAppender(dbPath="dfs://stock",tableName='stock',ddbSession=s,action="fitColumnType")
x = ['Apple','Microsoft','Meta','Google','Amazon']
i = 1
while i<=10000000:
    now = datetime.datetime.now()
    name = random.sample(x,1)
    data = pd.DataFrame({'time':now,'name':name,'id':i})
    appender.append(data)
    print(i)
    i = i+1
    time.sleep(1)
```

### 3.1 Preparation for Upgrade

Step 1: Execute the following script to check the status of all chunks. If all copies are in COMPLETE status, the NULL value will be returned. To continue with the subsequent steps, ensure that the chunks should not be in RECOVERING status.

```sql
select * from rpc(getControllerAlias(), getClusterChunksStatus) where state != "COMPLETE" 
```

Step 2: Execute the following script to get the directory where the metadata files are stored.

```
pnodeRun(getConfig{`chunkMetaDir})
```

```sh
	node	value
0	node44	/home/zjchen/HA/server/clusterDemo/data/node44/storage
1	node45	/home/zjchen/HA/server/clusterDemo/data/node45/storage
2	node43	/home/zjchen/HA/server/clusterDemo/data/node43/storage
```

```sh
rpc(getControllerAlias(),getConfig{`dfsMetaDir})
```

```
string('/home/zjchen/HA/server/clusterDemo/data/HActl44/dfsMeta')
```

### 3.2 Node Upgrade

Step 1: Shut down all nodes on the 10.10.11.1 server, including controller, agent, and data nodes.

```sh
cd /home/zjchen/HA/server/clusterDemo/
sh stopAllNodes.sh
```

Step 2: Back up metadata.

- Back up the metadata on controller.

```sh
cd /home/zjchen/HA/server/clusterDemo/data/node43/storage/
cp -r CHUNK_METADATA/ CHUNK_METADATA_BAK/
```

- Back up metadata on data nodes.

```sh
cd /home/zjchen/HA/server/clusterDemo/data/HActl44/
cp -r dfsMeta/ dfsMeta_bak/
```

Step 3: Upgrade.

```sh
cd /home/zjchen/HA/server/clusterDemo/
sh upgrade.sh
```

Expected results:

```sh
DolphinDB package uploaded successfully!  UpLoadSuccess
DolphinDB package unzipped successfully!  UnzipSuccess
DolphinDB upgraded successfully!  UpgradeSuccess
```

Step 4: Restart controller, agents, and data nodes, and check the "time" and "id" columns of the DFS table "stock". If the latest timestamp of "time" column is the current time, and the "id" column stores consecutive positive integers, the write is not interrupted during the upgrade; otherwise, it is affected by the outage.

Perform the operations in section 3.1 and 3.2 for machine 10.10.11.2 and 10.10.11.3.

**Note**: Make sure that the chunks are not in RECOVERING status before upgrading the nodes of another machine.

### 3.3 Verification

Execute the following command to verify that all nodes are successfully upgraded.

`pnodeRun(version)`

```sh
	node	value
0	node44	2.00.8.12 2023.01.10
1	node45	2.00.8.12 2023.01.10
2	node43	2.00.8.12 2023.01.10
```
