# Tiered Storage

- [Tiered Storage](#tiered-storage)
  - [1. Introduction](#1-introduction)
  - [2. Configuring Tiered Storage](#2-configuring-tiered-storage)
    - [2.1 Specifying Configuration Parameters](#21-specifying-configuration-parameters)
    - [2.2 Setting Data Retention Period](#22-setting-data-retention-period)
    - [2.3 Triggering Data Migration](#23-triggering-data-migration)
  - [3. Tiered Storage Architecture](#3-tiered-storage-architecture)
    - [3.1 Auto-Migration Trigger](#31-auto-migration-trigger)
    - [3.2 Data Migration Process](#32-data-migration-process)
    - [3.3 Access to Migrated Data](#33-access-to-migrated-data)
  - [4. Conclusion](#4-conclusion)


## 1. Introduction

Tiered storage is a storage architecture that uses multiple tiers of storage with different speeds and capacities. 

Old data that is infrequently accessed ("cold data") can consume a lot of resources on high-performance storage media like SSDs. With tiered storage, cold data can be automatically moved from fast disks (e.g., SSDs) to slower, less expensive disks (e.g., HDDs) or object storage services, allowing frequently accessed ("hot") data to reside on high-speed storage tiers.  

This tutorial describes how to configure and use tiered storage in DolphinDB.

## 2. Configuring Tiered Storage

### 2.1 Specifying Configuration Parameters

Before implementing tiered storage, the required configuration parameters must be specified. 

1. **Cold data storage**

```
coldVolumes=file:/{your_local_path},s3://{your_bucket_name}/{s3_path_prefix}
```

*coldVolumes* specifies the volumes to store the cold data. Multiple (local or S3) directories can be specified with a comma delimiter. A local path starts with the identifier "file://"; An S3 path is in the format of "s3://{BucketName}/{s3path}" where "s3path" must be specified.

For example:

```
coldVolumes=file://home/mypath/hdd/<ALIAS>,s3://bucket1/data/<ALIAS>
```

**Note:** To prevent data from being overwritten by other nodes, specify a unique storage path for each data node. The storage path can be defined using a macro in the format: `/home/mypath/hdd/<ALIAS>`, where`<ALIAS>` is the alias of each data node. This action ensures that the system saves data for each node to a directory named after the node's alias.

**2. Amazon S3**

If an S3 path is specified for *coldVolumes*, load the DolphinDB AWS plugin and configure the related parameters (`s3AccessKeyId`, `s3SecretAccessKey`, `s3Region`) accordingly.

```
pluginDir=plugins //specify the directory for plugins. The AWS S3 plugin must be saved under the plugins directory.
preloadModules=plugins::awss3 //the AWS S3 plugin will be automatically loaded on server startup
s3AccessKeyId={your_access_key_id}
s3SecretAccessKey={your_access_screet_key}
s3Region={your_s3_region}
```

For more information on configurations, see [user manual - Tiered Storage](https://dolphindb.com/help200/DatabaseandDistributedComputing/Database/TieredStorage.html).

For more information on the DolphinDB AWS S3 plugin, see [plugin README](https://github.com/dolphindb/DolphinDBPlugin/blob/release200/aws/README_EN.md).

### 2.2 Setting Data Retention Period 

Use the *hoursToColdVolume* parameter of the [setRetentionPolicy](https://dolphindb.com/help200/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) function to specify the data retention period.

For example, cold data storage volumes have been specified as:

```
coldVolumes=file://home/dolphindb/tiered_store/<ALIAS>
```

The range of data that will be migrated to cold storage depends on the time values in the data. This requires the database to adopt time-based partitioning as one of its partitioning schemes. 

In this example, we create a VALUE partitioned DFS database using the time column, then append the data for the past 15 days to the database:

```
db = database("dfs://db1", VALUE, (date(now()) - 14)..date(now())) //create a database VALUE partitioned on dates
data = table((date(now()) - 14)..date(now()) as cdate, 1..15 as val) //create a table with a column containing dates of the last 15 days
tbl = db.createPartitionedTable(data, "table1", `cdate)
tbl.append!(data)
```

Call [setRetentionPolicy](https://dolphindb.com/help200/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) to specify:

Migrate data which has been kept for over 5 days (120 hours) to the cold volumes, and delete data which has been kept for over 30 days (720 hours). As the database has only one partitioning scheme on date values, the parameter *retentionDimension* (indicating the level of the time-based partitions) is 0.

```
setRetentionPolicy(dbHandle=db, retentionHours=720, retentionDimension=0, hoursToColdVolume=120)
```

### 2.3 Triggering Data Migration

Once the retention policies are set, DolphinDB will perform migration checks every 1 hour in the background. In this example, we use the [moveHotDataToColdVolume](https://dolphindb.com/help200/FunctionsandCommands/CommandsReferences/m/moveHotDataToColdVolume.html) function to manually trigger a migration.

```
pnodeRun(moveHotDataToColdVolume) //initiate data migration on each data node
```

As a result, DolphinDB starts the tasks to migrate data in the range of [current day - 15 days, current day - 5 days). Call [getRecoveryTaskStatus](https://dolphindb.com/help200/FunctionsandCommands/FunctionReferences/g/getRecoveryTaskStatus.html) to view the status of the migration tasks.

```
rpc(getControllerAlias(), getRecoveryTaskStatus) //the result shows the tasks have been created
```

Sample output (some columns are omitted):

| **TaskId**                           | **TaskType**  | **ChunkPath**   | **Source** | **Dest** | **Status** |
| :----------------------------------- | :------------ | :-------------- | :--------- | :------- | :--------- |
| 2059a13f-00d7-1c9e-a644-7a23ca7bbdc2 | LoadRebalance | /db1/20230209/4 | NODE0      | NODE0    | Finish     |
| …                                    | …             | …               | …          | …        | …          |

**Note:**

1. If multiple paths are specified for `coldVolumes`, the data will be transferred randomly to one of the specified directories.
2. If `coldVolumes` is a local path, the migration is conducted locally by copying files directly.
3. If `coldVolumes` is an AWS S3 path, data will be uploaded using the AWS S3 plugin in a multi-threaded manner. Migration to S3 may be slower than to a local path.
4. During migration, partitions involved will temporarily become unavailable for reads/writes. 

After migration completes, migrated partitions become read-only. You can query data in these partitions using `select` statements, but cannot `update`, `delete`, or `append!` the data.

```
select * from tbl where cdate = date(now()) - 10 //query migrated data with the select statement
update tbl set val = 0 where cdate = date(now()) - 10 //an error will be reported after executing the update statement 
```

Note that executing drop operations (e.g. `dropTable`, `dropPartition`, `dropDatabase`) will remove the corresponding data in the object storage service.

To check permissions for partitions, call `getClusterChunksStatus`: 

```
rpc(getControllerAlias(), getClusterChunksStatus)
```

Sample output (some columns are omitted):

| **chunkId**                          | **file**        | **permission**                                               |
| :----------------------------------- | :-------------- | :----------------------------------------------------------- |
| ef23ce84-f455-06b7-6842-c85e46acdaac | /db1/20230216/4 | READ_ONLY *(indicating that this partition has been migrated)* |
| 260ab856-f796-4a87-3d4b-993632fb09d9 | /db1/20230223/4 | READ_WRITE *(indicating that this partition has not been migrated)* |

## 3. Tiered Storage Architecture

### 3.1 Auto-Migration Trigger

Once retention policies ([setRetentionPolicy](https://dolphindb.com/help200/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html)) have been defined, a background worker checks for data pending migration every hour based on each time-based partition. The worker searches in the time range *[current time - hoursToColdVolume - 10 days, current time minus hoursToColdVolume)*. 

If there is data that needs to be migrated, migration tasks are created.   Once the migration starts, the system does not usually migrate all partitions of all databases simultaneously. Instead, migration occurs database by database, with only a portion of a single database's data migrated each hour. This strategy reduces system pressure and maximizes data availability.

For example, databases "dfs://db1" and "dfs://db2" both partition data by time. The *hoursToColdVolume* parameter is set to 120h, meaning data will be retained for 5 days:

- At 17:00 on February 20, 2023, the system may migrate all db1 partitions in the range [2023.02.05, 2023.02.15).
- At 18:00 on February 20, 2023, the system may migrate all db2 partitions in [2023.02.05, 2023.02.15).
- If the system has been performing checks and handling migration tasks throughout the day, it will complete migrating partitions in [2023.02.05 to 2023.02.15) in both databases by the end of February 20, 2023.

### 3.2 Data Migration Process

DolphinDB’s tiered storage leverages its data recovery mechanism to migrate partition replicas on each node to slower storage media - either local disks or AWS S3. The data migration process is as follows:

1. A user defines the *hoursToColdVolume* parameter (data retention time) via the [setRetentionPolicy](https://www.dolphindb.cn/cn/help/FunctionsandCommands/CommandsReferences/s/setRetentionPolicy.html) function. 
2. A background worker identifies data eligible for migration based on partitions and creates corresponding recovery tasks.  
3. The system executes tasks by uploading or copying data files to AWS S3 or local directories.
4. The partition metadata and paths are updated, and migrated partition permissions are changed to `READ_ONLY`.

### 3.3 Access to Migrated Data 

When you query data stored in S3 using a SQL "select" statement, the system uses methods of the DolphinDB S3 plugin to perform the necessary operations, such as reading data and file lengths, and listing all files in a directory. Aside from these S3-specific operations, the data access process works the same as usual. 

However, since accessing S3 over a network is much slower than reading from a local disk, and because data saved to S3 remains static, DolphinDB caches some S3 file metadata (such as file length) as well as the data itself. As a result, if the cached data matches a query, it can be returned directly from the cache instead of retrieving it from S3 over the network.

## 4. Conclusion 

DolphinDB’s tiered storage feature allows cold data to be migrated regularly to slower disks or cloud storage. Users can access migrated data by using SQL "select" statements.
