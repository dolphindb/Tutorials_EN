# Data Migration and Rebalancing

With the increasing demands on database capacity and computing performance, DolphinDB offers data rebalancing to ensure that chunk replicas can be evenly distributed across a cluster as much as possible after cluster scaling. In this tutorial, we summarize common scenarios and methods for data rebalancing.

The code examples in this tutorial can be executed with server version 1.30.17/2.00.5 or higher.

- [1. Background](#1-background)
- [2. Environment and Data Preparation](#2-environment-and-data-preparation)
  - [2.1 Hardware Environment](#21-hardware-environment)
  - [2.2 Cluster Configuration](#22-cluster-configuration)
  - [2.3 Data Simulation](#23-data-simulation)
  - [2.4 Notes](#24-notes)
- [3. Functions](#3-functions)
  - [3.1 Functions for Data Rebalancing](#31-functions-for-data-rebalancing)
  - [3.2 Balancing Algorithm](#32-balancing-algorithm)
- [4. Rebalancing After Cluster Scale-out/in](#4-rebalancing-after-cluster-scale-outin)
  - [4.1 Cluster Scale-out](#41-cluster-scale-out)
  - [4.2 Migration Performance](#42-migration-performance)
  - [4.3 Cluster Scale-in](#43-cluster-scale-in)
- [5. Rebalancing After Node Scale-up/down](#5-rebalancing-after-node-scale-updown)
  - [5.1 Node Scale-up](#51-node-scale-up)
  - [5.2 Migration Performance](#52-migration-performance)
  - [5.3 Node Scale-down](#53-node-scale-down)
- [6. Conclusion](#6-conclusion)
- [Appendix](#appendix)

## 1. Background

A DolphinDB cluster can be scaled by adding nodes and disks for improved storage and computing capabilities. However, data will not be automatically moved to the newly-added nodes or disks. The uneven distribution of replicas across a cluster can significantly affect I/O performance, node load, and data access latency. Failure to achieve a balanced data distribution can lead to several issues:

- Tasks broken down from a distributed query job cannot be allocated to the newly-added nodes, resulting in the underutilization of computing resources.

- The old disks may experience excessive IO pressure, while the newly added disks cannot be fully utilized.
- If data writes or updates only operate on the old nodes/disks, the old disks can be fully occupied, leading to various problems.

To avoid such problems, it's necessary to perform data rebalancing after cluster scaling. In the following sections, we will focus on the methods for cluster scaling and data rebalancing.

## 2. Environment and Data Preparation

### 2.1 Hardware Environment

We set up three servers P1, P2, and P3 with the same hardware configurations:

| **CPU**                                    | **Cores** | **Memory** | **OS**                   | **Disk** |
| ------------------------------------------ | --------- | ---------- | ------------------------ | -------- |
| Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz | 64        | 512 GB     | CentOS Linux release 7.9 | SSD      |


### 2.2 Cluster Configuration

DolphinDB server version: 2.00.9

A two-replica cluster is established based on two servers P1 and P2, where a controller, an agent and a data node are deployed on P1 and an agent and a data node are deployed on P2. See Appendix 1 for configurations for these nodes. 

| **Server** | **IP**         | **Port** | **Node Alias** | **Node Type** |
| ---------- | -------------- | -------- | -------------- | ------------- |
| P1         | 192.168.100.4X | 8110     | ctl1           | controller    |
| P1         | 192.168.100.4X | 8111     | P1-agent       | agent         |
| P1         | 192.168.100.4X | 8112     | P1-dn1         | data node     |
| P2         | 192.168.100.4X | 8111     | P2-agent       | agent         |
| P2         | 192.168.100.4X | 8112     | P2-dn1         | data node     |

For the specific configuration parameters, see [Configuration](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/index.html). Unless otherwise specified, the code used in this tutorial is executed on a data node of the cluster.

### 2.3 Data Simulation

We use the script below to simulate Level 1 data of 2000 stocks and write the data into DolphinDB databases "dfs://Level1" and "dfs://Level1_TSDB" separately:

```
model = table(1:0, `SecurityID`DateTime`PreClosePx`OpenPx`HighPx`LowPx`LastPx`Volume`Amount`BidPrice1`BidPrice2`BidPrice3`BidPrice4`BidPrice5`BidOrderQty1`BidOrderQty2`BidOrderQty3`BidOrderQty4`BidOrderQty5`OfferPrice1`OfferPrice2`OfferPrice3`OfferPrice4`OfferPrice5`OfferQty1`OfferQty2`OfferQty3`OfferQty4`OfferQty5, [SYMBOL, DATETIME, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, LONG, LONG, LONG, LONG, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, LONG, LONG, LONG, LONG, LONG])

// OLAP engine
dbDate = database("", VALUE, 2020.06.01..2020.06.07)
dbSecurityID = database("", HASH, [SYMBOL, 10])
db = database("dfs://Level1", COMPO, [dbDate, dbSecurityID])
createPartitionedTable(db, model, `Snapshot, `DateTime`SecurityID)

// TSDB engine
dbDate = database("", VALUE, 2020.06.01..2020.06.07)
dbSymbol = database("", HASH, [SYMBOL, 10])
db = database("dfs://Level1_TSDB", COMPO, [dbDate, dbSymbol], engine="TSDB")
createPartitionedTable(db, model, `Snapshot, `DateTime`SecurityID, sortColumns=`SecurityID`DateTime)

def mockHalfDayData(Date, StartTime) {
    t_SecurityID = table(format(600001..602000, "000000") + ".SH" as SecurityID)
    t_DateTime = table(concatDateTime(Date, StartTime + 1..2400 * 3) as DateTime)
    t = cj(t_SecurityID, t_DateTime)
    size = t.size()
    return  table(t.SecurityID as SecurityID, t.DateTime as DateTime, rand(100.0, size) as PreClosePx, rand(100.0, size) as OpenPx, rand(100.0, size) as HighPx, rand(100.0, size) as LowPx, rand(100.0, size) as LastPx, rand(10000, size) as Volume, rand(100000.0, size) as Amount, rand(100.0, size) as BidPrice1, rand(100.0, size) as BidPrice2, rand(100.0, size) as BidPrice3, rand(100.0, size) as BidPrice4, rand(100.0, size) as BidPrice5, rand(100000, size) as BidOrderQty1, rand(100000, size) as BidOrderQty2, rand(100000, size) as BidOrderQty3, rand(100000, size) as BidOrderQty4, rand(100000, size) as BidOrderQty5, rand(100.0, size) as OfferPrice1, rand(100.0, size) as OfferPrice2, rand(100.0, size) as OfferPrice3, rand(100.0, size) as OfferPrice4, rand(100.0, size) as OfferPrice5, rand(100000, size) as OfferQty1, rand(100000, size) as OfferQty2, rand(100000, size) as OfferQty3, rand(100000, size) as OfferQty4, rand(100000, size) as OfferQty5)
}

def mockData(DateVector, StartTimeVector) {
    for(Date in DateVector) {
        for(StartTime in StartTimeVector) {
            data = mockHalfDayData(Date, StartTime)
 
            // append data to the OLAP database
            loadTable("dfs://Level1", "Snapshot").append!(data)
  
            // append data to the TSDB database
            loadTable("dfs://Level1_TSDB", "Snapshot").append!(data)
        }   
    }
}

mockData(2020.06.01..2020.06.10, 09:30:00 13:00:00)
```

In the above script, we simulate data of 10 days from 2020.06.01 to 2020.06.10. The OLAP and the TSDB databases adopt the same partitioning scheme that combines date-based value partitions and 10 symbol-based hash partitions. The chunk granularity is set at table level.

The number of partitions on each data node is shown below:

```
select count(*) from pnodeRun(getAllChunks) where dfsPath like "/Level1%" group by site, type
```

| site   | type | count |
| ------ | ---- | ----- |
| P1-dn1 | 0    | 4     |
| P1-dn1 | 1    | 200   |
| P2-dn1 | 0    | 4     |
| P2-dn1 | 1    | 200   |

The field "type" indicates the chunk type: 

- **0: file chunk**. It contains metadata files *domain* (each corresponds to a database) and *.tbl* (each corresponds to a table) that stores the schema information.
- **1: tablet chunk**. It is where the data is stored. 

Since a two-replica cluster is configured, the replicas are distributed on P1 and P2 separately as resources allow. A total of 408 replicas is as expected.

### 2.4 Notes

The following are common cases that may occur during data balancing:

- Data migration and rebalancing tasks can be resource-intensive, and partitions that are being written, modified, or deleted may fail to migrate due to partition locks. 
- For time-consuming calculation jobs, exceptions may be thrown when the cache points to the old partition path.

Therefore, it is recommended to perform data migration and rebalancing operations when there are no write or query tasks being executed to avoid potential failures.

## 3. Functions

### 3.1 Functions for Data Rebalancing

DolphinDB has offered built-in functions for data rebalancing in different scaling scenarios. These functions must be executed on the controller by an administrator.

- [rebalanceChunksAmongDataNodes](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/rebalanceChunksAmongDataNodes.html): rebalances data among data nodes within a cluster.
- [rebalanceChunksWithinDataNode](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/rebalanceChunksWithinDataNode.html): rebalances data among volumes within a data node.
- [restoreDislocatedTablet](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/restoreDislocatedTablet.html): moves all tables under the same partition to one node.
- [moveReplicas](https://www.dolphindb.com/help/FunctionsandCommands/CommandsReferences/m/moveReplicas.html): moves replicas of one or multiple chunks from the source node to the destination node.
- [moveChunksAcrossVolume](https://www.dolphindb.com/help200/FunctionsandCommands/CommandsReferences/m/moveChunksAcrossVolume.html): moves the chunks from the source volume to the destination volume on the same node.

### 3.2 Balancing Algorithm

The balancing algorithm in DolphinDB is based on the assumptions that:

- All the partitions are stored on the old disks;
- All new disks are used to store new partitions;
- All partitions are of the same size.

However, the real-world situations may not match the conditions that were previously assumed. For example, the disks may store data other than DolphinDB databases, or the partition sizes may be unequal. These differences can lead to unexpected rebalancing results. Additionally, after data rebalancing, changes may occur in the disk space, partition size, etc. across the old and new disks. Performing rebalancing multiple times can help optimize the rebalancing effect to some extent.

## 4. Rebalancing After Cluster Scale-out/in

This chapter introduces data migration and balancing during cluster scaling via node addition or removal.

### 4.1 Cluster Scale-out

We add a server P3 (with an agent and a controller deployed) to the cluster.

| **Server** | **IP**         | **Port** | **Node Alias** | **Node Type** |
| ---------- | -------------- | -------- | -------------- | ------------- |
| P3         | 192.168.100.4X | 8111     | P3-agent       | agent         |
| P3         | 192.168.100.4X | 8112     | P3-dn1         | data node     |

First, execute the following command:

```
rpc(getControllerAlias(), rebalanceChunksAmongDataNodes{ false })
```

The results show that a total of 114 partitions are estimated to be migrated from P1-dn1 and P2-dn1 to P3-dn1.



Then execute the following command for data rebalancing:

```
rpc(getControllerAlias(), rebalanceChunksAmongDataNodes{ true })
```

Check the rebalancing progress and job parallelism:

```
rpc(getControllerAlias(), getRecoveryTaskStatus)
rpc(getControllerAlias(), getConfigure{ `dfsRebalanceConcurrency })
pnodeRun(getRecoveryWorkerNum)
```

As shown above, the values returned for DeleteSource are all “true”, indicating the data is migrated from the source node to the target node with the original data deleted during data rebalancing.

The number of tasks with the "In-Progress" Status reflects the job parallelism initiated by the controller. The parallelism is configured via the *dfsRebalanceConcurrency* parameter, which defaults to twice the number of data nodes. The parameter *recoveryWorkers* indicates the number of workers that can be used to recover chunks concurrently during node recovery, and its default value is 1.

The tasks marked with "Finished" Status are deemed completed. Once all tasks are completed, execute the following command to view the number of partitions on each data node.

```
select count(*) from pnodeRun(getAllChunks) group by site
```

| **site** | **count** |
| -------- | --------- |
| P1-dn1   | 196       |
| P2-dn1   | 98        |
| P3-dn1   | 114       |

### 4.2 Migration Performance

Execute the following command to calculate the time spent on data rebalancing:

```
select max(FinishTime - StartTime) as maxDiffTime from rpc(getControllerAlias(), getRecoveryTaskStatus)
```

It returns 89 seconds. The 114 partitions take up about 17 GB. The migration speed is about 200 MB/s when the data is migrated among nodes.

| **Scenario**          | **Cross Servers** | **Network**         | **Hard Disk** | **Initiation Parallelism** | **Execution Parallism** | **Migration Speed (MB/s)** |
| --------------------- | ----------------- | ------------------- | ------------- | -------------------------- | ----------------------- | -------------------------- |
| Migration Among Nodes | √                 | 10 Gigabit Ethernet | SSD           | 6                          | 6                       | 200                        |

### 4.3 Cluster Scale-in

To scale in the cluster (e.g., by removing the server P3 added in Section 4.2), we need to first migrate the replicas on the data node P3-dn1 to other data nodes in the cluster.

Define a function `moveChunks` that takes a source node alias as the input by encapsulating function `moveReplicas`. This function migrates all partitions on the source node to other nodes.

```
def moveChunks(srcNode) {
    chunks = exec chunkId from pnodeRun(getAllChunks) where site = srcNode
    allNodes = pnodeRun(getNodeAlias).node
    for(chunk in chunks) {
        destNode = allNodes[at(not allNodes in (exec site from pnodeRun(getAllChunks) where chunkId = chunk))].rand(1)[0]
        print("From " + srcNode + ", to " + destNode + ", moving " + chunk)
        rpc(getControllerAlias(), moveReplicas, srcNode, destNode, chunk)
    }
}

srcNode = "P3-dn1"
moveChunks(srcNode)
```

Then check the progress of migration:

```
rpc(getControllerAlias(), getRecoveryTaskStatus)
```

After all migration tasks are completed, you can check the partition distribution on each data node:

```
select count(*) from pnodeRun(getAllChunks) group by site
```

| **site** | **count** |
| -------- | --------- |
| P1-dn1   | 204       |
| P2-dn1   | 204       |

Since there is no data stored on the node P3-dn1, you can then remove the node.

## 5. Rebalancing After Node Scale-up/down

This chapter introduces data migration and balancing during node scaling via disk addition or removal.

### 5.1 Node Scale-up

To add a hard disk ssd1 to each data node, the configuration parameter *volumes* is modified from

```
volumes=/ssd/ssd0/chunkData
```

to 

```
volumes=/ssd/ssd0/chunkData,/ssd/ssd1/chunkData
```

Rebalance the data distribution across the disks on P1-dn1:

```
rpc(getControllerAlias(), rebalanceChunksWithinDataNode{ "P1-dn1", false })
rpc(getControllerAlias(), rebalanceChunksWithinDataNode{ "P1-dn1", true })
```

Check the migration progress:

```
rpc(getControllerAlias(), getRecoveryTaskStatus)
```

Similarly, rebalance the data distribution across the disks on P2-dn1:

```
rpc(getControllerAlias(), rebalanceChunksWithinDataNode{ "P2-dn1", false })
rpc(getControllerAlias(), rebalanceChunksWithinDataNode{ "P2-dn1", true })
```

Check the migration progress:

```
rpc(getControllerAlias(), getRecoveryTaskStatus)
```

As shown above, the rebalance operation migrates 189 partitions. The field DeleteSource always returns “false” because the data is migrated within a data node.

After all migration tasks are completed, you can check the partition distribution on all data nodes:

```
def getDiskNo(path) {
    size = path.size()
    result = array(STRING, 0, size)
    for(i in 0 : size) { append!(result, concat(split(path[i], "/")[0:5], "/")) }
    return result
}

select count(*) from pnodeRun(getAllChunks) group by site, getDiskNo(path) as disk
```

| **site** | **disk**            | **count** |
| -------- | ------------------- | --------- |
| P1-dn1   | /ssd/ssd0/chunkData | 108       |
| P1-dn1   | /ssd/ssd1/chunkData | 96        |
| P2-dn1   | /ssd/ssd0/chunkData | 111       |
| P2-dn1   | /ssd/ssd1/chunkData | 93        |

### 5.2 Migration Performance

Execute the following command to calculate the time spent on data rebalancing:

```
select max(FinishTime - StartTime) as maxDiffTime from rpc(getControllerAlias(), getRecoveryTaskStatus)
```

It returns 56 seconds. The 96 partitions take up about 14 GB. The migration speed is about 250 MB/s while the data is being rebalanced among volumes within a node.

| **Scenario**           | **Cross Servers** | **Network**         | **Hard Disk** | **Initiation Parallelism** | **Execution Parallism** | **Migration Speed (MB/s)** |
| ---------------------- | ----------------- | ------------------- | ------------- | -------------------------- | ----------------------- | -------------------------- |
| Migration Across Disks | ×                 | 10 Gigabit Ethernet | SSD           | 4                          | 4                       | 250                        |

### 5.3 Node Scale-down

To scale down the cluster (e.g., by removing the disk ssd1 added in Section 5.2), we need to first migrate the partitions from the newly-added disk to other disks.

Migrate the data stored on disk ssd1 of data node P1-dn1 and P2-dn1 to disk ssd0:

```
srcPath = "/ssd/ssd1/chunkData/CHUNKS"
destPath = "/ssd/ssd0/chunkData/CHUNKS"

node = "P1-dn1"
chunkIds = exec chunkId from pnodeRun(getAllChunks) where site = node, path like (srcPath + "%")
rpc(node, moveChunksAcrossVolume{ srcPath, destPath, chunkIds, isDelSrc=true })

node = "P2-dn1"
chunkIds = exec chunkId from pnodeRun(getAllChunks) where site = node, path like (srcPath + "%")
rpc(node, moveChunksAcrossVolume{ srcPath, destPath, chunkIds, isDelSrc=true })
```

Check the partition distribution on all volumes and data nodes:

```
select count(*) from pnodeRun(getAllChunks) group by site, getDiskNo(path) as disk
```

| site   | disk                | count |
| ------ | ------------------- | ----- |
| P1-dn1 | /ssd/ssd0/chunkData | 204   |
| P2-dn1 | /ssd/ssd0/chunkData | 204   |

Now all the data on ssd1 is migrated to ssd0, and the disk ssd1 can be removed.

## 6. Conclusion

In this tutorial, we explore the process of scaling nodes and disks in production environments using DolphinDB. Through simulating and implementing solutions for these scenarios, we demonstrate DolphinDB's robust data migration and balancing capabilities. Our focus is on optimizing resource usage after cluster scaling, thereby providing a powerful and convenient solution for this common production issue.

## Appendix

[data_move_rebalance](https://github.com/dolphindb/Tutorials_CN/blob/master/script/data_move_rebalance)

