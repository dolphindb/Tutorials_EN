# Backup and Restore

**This tutorial applies to versions prior to DolphinDB 1.30.20/2.00.8.**

With DolphinDB built-in functions, users can back up and restore partitions in a database.

- [Backup and Restore](#backup-and-restore)
  - [1. Backup](#1-backup)
    - [1.1 Full Backup](#11-full-backup)
    - [1.2 Incremental Backup](#12-incremental-backup)
    - [1.3 Daily Backup](#13-daily-backup)
  - [2. Restore](#2-restore)
    - [2.1 `restore`](#21-restore)
    - [2.2 `migrate`](#22-migrate)
  - [3. Backup and Restore Management](#3-backup-and-restore-management)
    - [3.1 `getBackupList`](#31-getbackuplist)
    - [3.2 `getBackupMeta`](#32-getbackupmeta)
    - [3.3 `loadBackup`](#33-loadbackup)
  - [4. Examples](#4-examples)

## 1. Backup

DolphinDB function [backup](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/b/backup.html) backs up some or all partitions of a table and returns an integer indicating the number of partitions that are successfully backed up. Both full backup and incremental backup are supported. After backup, a metadata file named “_metaData.bin” and files named “chunkID.bin” will be created under the path “backupDir/dbName/tbName”.

**Syntax**

backup(backupDir, sqlObj, [force=false], [parallel=false])

**Parameters**

- **backupDir** is a string indicating the directory to save the backup.

- **sqlObj** is metacode indicating the data to be backed up.

- **force** is a Boolean value indicating whether to use full backup or incremental backup. The default value is false, indicating an incremental backup is performed.

- **parallel** is a Boolean value indicating whether to back up in parallel. The default value is false.



### 1.1 Full Backup

The following example shows how to back up a database.

(1) Create a DFS database with a composite domain. It uses a VALUE domain based on date and a VALUE domain based on the ID of 10 wind turbines:

```
m = "tag" + string(decimalFormat(1..523,'000'))
tableSchema = table(100:0,`wntId`insertDate join m, [INT,DATETIME] join take(FLOAT,523) )
db1 = database("",VALUE,2020.01.01..2020.12.30)
db2 = database("",VALUE,1..10)
db = database("dfs://ddb",COMPO,[db1,db2])
db.createPartitionedTable(tableSchema,"windTurbine",`insertDate`wntId)
```

(2) Write the data from 2020.01.01 to 2020.01.03 and back up the data of the first 2 days. Starting from DolphinDB server version 1.10.13/1.20.3, you can set the parameter parallel to specify whether to back up in parallel.

```
backup(backupDir="/hdd/hdd1/backup/",sqlObj=<select * from loadTable("dfs://ddb","windTurbine") where insertDate<=2020.01.02T23:59:59 >,parallel=true)

```

The result is 20, indicating 20 partitions have been backed up. Login in the server and execute tree command to obtain the following information:

```
[dolphindb@localhost backup]$ tree /hdd/hdd1/backup/ -L 3 -t
/hdd/hdd1/backup/
└── ddb
    └── windTurbine
        ├── 02ddcb20-8872-af9d-ca46-f42a42239c78
        ├── 237e6e64-d62e-13bf-0443-fa7a974f7c42
        ├── 4d04471d-fff8-2e9a-7742-a0228af21bad
        ├── 4e7e014f-1346-c4b0-264e-e9d15de494cb
        ├── 4f2aade8-97ce-bca9-934f-b0b10f0da1fe
        ├── 6256d8f2-cc53-7a87-5b43-6cce55b38933
        ├── 77a4ac82-739c-389b-994b-22f84cb11417
        ├── 8c27389b-4689-7697-d243-2b16dbca8354
        ├── 8dd539b3-f3fc-b39c-6842-039dbec1ceb1
        ├── 90a5af5f-1161-23af-ea42-877999866f44
        ├── fd6b658c-47eb-e69e-164e-601c5b51daed
        ├── _metaData
        ├── 167a9165-05ec-e093-b74a-c6121939ebf0
        ├── 3afb5932-a8fa-9e93-ff4c-120c1223dcf6
        ├── 62d47049-155d-83a7-af48-36c8969072a7
        ├── b20422a9-487d-8eb7-7143-3597a3b44796
        ├── 2ae9676f-dbe7-669a-7144-68a02572df3e
        ├── 4559d6db-bb7a-efb8-164e-3198127a7c3d
        ├── 72e15689-4bf7-44a9-b84e-16fb8e856a6d
        ├── 8652f2f0-9d60-40aa-4e44-9d77bd1309f6
        ├── dolphindb.lock
        └── e266ab82-6ef9-e289-d241-d9218be59dde

2 directories, 22 files
```

As shown above, under the backup directory 2 levels of subdirectory ddb/windTurbine with the same name as the database and table are generated, under which there are 20 partitions and 1 metadata file _metaData.

### 1.2 Incremental Backup

```
backup(backupDir="/hdd/hdd1/backup/",sqlObj=<select *  from loadTable("dfs://ddb","windTurbine") >,force=false,parallel=true)
```

The result is 10, indicating 10 partitions have been backed up. Log in the server and execute tree command to obtain the following information:

```
[dolphindb@localhost windTurbine]$ tree /hdd/hdd1/backup/ -L 3 -t
/hdd/hdd1/backup/
└── ddb
    └── windTurbine
        ├── 04eceea9-53d7-1389-4044-d31538025361
        ├── 14ff1d37-2ea7-7596-d94d-12ecfd8be197
        ├── 81f7236f-83b3-ef81-f648-3b8db67c04fa
        ├── 846aaf74-6c51-9a91-6c44-fb1e2cf93036
        ├── bcb94ce8-0e06-2fad-b946-774fcedc978d
        ├── c38cb06c-fd7f-608a-b148-b0f6a9883c5c
        ├── e5993354-cd4d-3ab0-0e4b-ea331e68a2df
        ├── _metaData
        ├── 401136d4-1fcd-408c-b84b-20c2af7b3fe8
        ├── 54076219-0904-97a2-1a4a-d076f35f76fe
        ├── b51f4f36-be16-cfad-a440-d04ac36b6791
        ├── dolphindb.lock
        ├── 02ddcb20-8872-af9d-ca46-f42a42239c78
        ├── 237e6e64-d62e-13bf-0443-fa7a974f7c42
        ├── 4d04471d-fff8-2e9a-7742-a0228af21bad
        ├── 4e7e014f-1346-c4b0-264e-e9d15de494cb
        ├── 4f2aade8-97ce-bca9-934f-b0b10f0da1fe
        ├── 6256d8f2-cc53-7a87-5b43-6cce55b38933
        ├── 77a4ac82-739c-389b-994b-22f84cb11417
        ├── 8c27389b-4689-7697-d243-2b16dbca8354
        ├── 8dd539b3-f3fc-b39c-6842-039dbec1ceb1
        ├── 90a5af5f-1161-23af-ea42-877999866f44
        ├── fd6b658c-47eb-e69e-164e-601c5b51daed
        ├── 167a9165-05ec-e093-b74a-c6121939ebf0
        ├── 3afb5932-a8fa-9e93-ff4c-120c1223dcf6
        ├── 62d47049-155d-83a7-af48-36c8969072a7
        ├── b20422a9-487d-8eb7-7143-3597a3b44796
        ├── 2ae9676f-dbe7-669a-7144-68a02572df3e
        ├── 4559d6db-bb7a-efb8-164e-3198127a7c3d
        ├── 72e15689-4bf7-44a9-b84e-16fb8e856a6d
        ├── 8652f2f0-9d60-40aa-4e44-9d77bd1309f6
        └── e266ab82-6ef9-e289-d241-d9218be59dde

2 directories, 32 files

```

There are 10 more backup files under the directory, which are the 10 partitions of 2020.01.03.

### 1.3 Daily Backup

You can set up a scheduled job for daily backup. A daily job is scheduled at 5:00 a.m. to back up data of the previous day.

```
scheduleJob(`backupJob, "backupDB", backup{"/hdd/hdd1/backup/"+(today()-1).format("yyyyMMdd"),<select * from loadTable("dfs://ddb","windTurbine") where tm between datetime(today()-1) : (today().datetime()-1) >,false,true}, 00:05m, today(), 2030.12.31, 'D');
```

## 2. Restore

There are two ways to restore the data in DolphinDB.

- By using function [restore](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/restore.html).
- By using function [migrate](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/m/migrate.html).

### 2.1 `restore`

**Syntax**

restore(backupDir, dbPath, tableName, partitionStr, [force=false], [outputTable])

**Parameters**

- **backupDir** is a string indicating the directory where the backup is kept.
- dbPath is a string indicating the path of a DFS database.
- **tableName** is a string indicating a DFS table name.
- **partition** is a string indicating the path of the partitions to be restored. It can use wildcard characters “%” and “?”. 
    - Back up a certain partition: input the relative path or “%/” + “partition name”. For example, if partition “20170810/50_100” under “dfs://compoDB” need to be restored, input ”/compoDB/20170807/0_50” or ”%/20170807/0_50” as patition path.
    - Back up all the partitions: input “%”.
- **force** is a Boolean value indicating whether to restore a full backup or incremental backup. The default value is false, indicating an incremental recovery is performed.
- **outputTable** is a DFS table with the same schema as the table to be restored. If outputTable is unspecified, partitions will be restored to the table specified by tableName; if outputTable is specified, partitions will be restored to outputTable whereas the table specified by tableName is not changed.

### 2.2 `migrate`

**Syntax**

migrate(backupDir, [backupDBPath], [backupTableName], [newDBPath=backupDBPath], [newTableName=backupTableName])

**Parameters**

- **backupDir** is a string indicating the directory to save the backup.
- **backupDBPath** is a string indicating the path of a database.
- **backupTableName** is a string indicating a backup table name.
- **newDBPath** is a string indicating the new database name. If not specified, the default value is backupDBPath.
- **newTableName** is a string indicating the new table name. If not specified, the default value is backupTableName.


The difference between `restore` and `migrate` is that you can use `migrate` to restore multiple tables in batches, whereas `restore` can only restore some or all partitions in one table at a time.

**Examples:**

Use `restore` for data backup:

The following example restores the data of January 2020 to the original table. The backup files are generated by the daily scheduled job defined in Section 1.3.

```
day=2020.01.01
for(i in 1..31){
	path="/hdd/hdd1/backup/"+temporalFormat(day, "yyyyMMdd") + "/";
	day=datetimeAdd(day,1,`d)
	if(!exists(path)) continue;
	print "restoring " + path;
	restore(backupDir=path,dbPath="dfs://ddb",tableName="windTurbine",partition="%",force=true);
}
```

Use `migrate` for data backup:

The following example restores the data of January 2020 to a new table equip in database dfs://db1. It first restores the data of 2020.01.01. Then the remaining data is restored to a temporal table and imported to table equip.

```
migrate("/hdd/hdd1/backup/20200101/","dfs://ddb","windTurbine","dfs://db1","equip")
day=2020.01.02
newTable=loadTable("dfs://db1","equip")
for(i in 2..31){
	path="/hdd/hdd1/backup/"+temporalFormat(day, "yyyyMMdd") + "/";
	day=datetimeAdd(day,1,`d)
	if(!exists(path)) continue;
	print "restoring " + path;
	t=migrate(path,"dfs://ddb","windTurbine","dfs://db1","tmp") 
	if(t['success'][0]==false){
		print t['errorMsg'][0]
		continue
	}
	newTable.append!(select * from loadTable("dfs://db1","tmp") where tm between datetime(day-1) : (day.datetime()-1) > )
	database("dfs://db1").dropTable("tmp")
}

```

## 3. Backup and Restore Management

### 3.1 `getBackupList`

Function [getBackupList](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getBackupList.html) returns a table with information (chunkID, chunkPath, cid) about a backup DFS table. Each row of the table corresponds to a backed up partition.

**Syntax**

getBackupList(backupDir, dbPath, tableName)

**Parameters**

- **backupDir** is a string indicating the directory where the backup is saved.
- **dbPath** is a string indicating the path of a DFS database.
- **tableName** is a string indicating a DFS table name.

For example, execute `getBackupList` on data backed up in Section 1.

```
getBackupList("/hdd/hdd1/backup/", "dfs://ddb", "windTurbine")
```

The result is:

|chunkID|	chunkPath|	cid|
---|---|---
|72e15689-4bf7-44a9-b84e-16fb8e856a6d|	dfs://ddb/20200101/1|	10,413
|8652f2f0-9d60-40aa-4e44-9d77bd1309f6|	dfs://ddb/20200101/2|	10,417
|4559d6db-bb7a-efb8-164e-3198127a7c3d|	dfs://ddb/20200101/3|	10,421
|2ae9676f-dbe7-669a-7144-68a02572df3e|	dfs://ddb/20200101/4|	10,425
|e266ab82-6ef9-e289-d241-d9218be59dde|	dfs://ddb/20200101/5|	10,429
|62d47049-155d-83a7-af48-36c8969072a7|	dfs://ddb/20200101/6|	10,414
|3afb5932-a8fa-9e93-ff4c-120c1223dcf6|	dfs://ddb/20200101/7|	10,418
|b20422a9-487d-8eb7-7143-3597a3b44796|	dfs://ddb/20200101/8|	10,422
|167a9165-05ec-e093-b74a-c6121939ebf0|	dfs://ddb/20200101/9|	10,426
|4d04471d-fff8-2e9a-7742-a0228af21bad|	dfs://ddb/20200101/10|	10,430
|02ddcb20-8872-af9d-ca46-f42a42239c78|	dfs://ddb/20200102/1|	10,415
|8dd539b3-f3fc-b39c-6842-039dbec1ceb1|	dfs://ddb/20200102/2|	10,419
|fd6b658c-47eb-e69e-164e-601c5b51daed|	dfs://ddb/20200102/3|	10,423
|90a5af5f-1161-23af-ea42-877999866f44|	dfs://ddb/20200102/5|	10,431
|237e6e64-d62e-13bf-0443-fa7a974f7c42|	dfs://ddb/20200102/6|	10,416
|8c27389b-4689-7697-d243-2b16dbca8354|	dfs://ddb/20200102/7|	10,420
|6256d8f2-cc53-7a87-5b43-6cce55b38933|	dfs://ddb/20200102/8|	10,424
|4e7e014f-1346-c4b0-264e-e9d15de494cb|	dfs://ddb/20200102/9|	10,428
|77a4ac82-739c-389b-994b-22f84cb11417|	dfs://ddb/20200102/10|	10,432
|54076219-0904-97a2-1a4a-d076f35f76fe|	dfs://ddb/20200103/1|	10,433
|b51f4f36-be16-cfad-a440-d04ac36b6791|	dfs://ddb/20200103/2|	10,436
|401136d4-1fcd-408c-b84b-20c2af7b3fe8|	dfs://ddb/20200103/3|	10,438
|14ff1d37-2ea7-7596-d94d-12ecfd8be197|	dfs://ddb/20200103/4|	10,439
|846aaf74-6c51-9a91-6c44-fb1e2cf93036|	dfs://ddb/20200103/5|	10,442
|c38cb06c-fd7f-608a-b148-b0f6a9883c5c|	dfs://ddb/20200103/6|	10,434
|e5993354-cd4d-3ab0-0e4b-ea331e68a2df|	dfs://ddb/20200103/7|	10,435
|04eceea9-53d7-1389-4044-d31538025361|	dfs://ddb/20200103/8|	10,437
|bcb94ce8-0e06-2fad-b946-774fcedc978d|	dfs://ddb/20200103/9|	10,440
|81f7236f-83b3-ef81-f648-3b8db67c04fa|	dfs://ddb/20200103/10|	10,441

### 3.2 `getBackupMeta`

[getBackupMeta](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getBackupMeta.html) returns a dictionary with information (schema, dfsPath, chunkID, cid) about the backup of a partition in a DFS table.

**Syntax**

getBackupMeta(backupDir, dbPath, partition, tableName)

**Parameters**

- **backupDir** is a string indicating the directory where the backup is saved.
- **dbPath** is a string indicating the path of a DFS database.
- **partition** is a string indicating the path of a partition under the database.
- **tableName** is a string indicating a DFS table name.

For example:

```
getBackupMeta("/hdd/hdd1/backup/","dfs://ddb","/20200103/10","windTurbine")
```

The result is:

```
schema->
name       typeString typeInt comment
---------- ---------- ------- -------
wntId      INT        4              
insertDate DATETIME   11             
tag001     FLOAT      15             
tag002     FLOAT      15             
tag003     FLOAT      15             
...

dfsPath->dfs://ddb/20200103/10
chunkID->81f7236f-83b3-ef81-f648-3b8db67c04fa
cid->10441
```
### 3.3 `loadBackup`

[loadBackup](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/l/loadBackup.html) loads the backup of a partition in a DFS table into memory.

**Syntax**

loadBackup(backupDir, dbPath, partition, tableName)

**Parameters**

- **backupDir** is a string indicating the directory where the backup is saved.
- **dbPath** is a string indicating the path of a DFS database.
- **partition** is a string indicating the path of a partition under the database.
- **tableName** is a string indicating a DFS table name.

For example:

```
loadBackup("/hdd/hdd1/backup/","dfs://ddb","/20200103/10","windTurbine")
```

The result is:

|wntId|insertDate|	tag001|	tags	|tag523|
|---|---|---|---|---|
|10|2020.01.03T00:00:00|	90.3187|	...|1|
|10|2020.01.03T00:00:01|	95.3273|	...|1|
|...||||
|10|2020.01.03T23:59:59|	94.6378|	...|1|


## 4. Examples

Create a DFS database dfs://compoDB with a composite domain.

```
n=1000000
ID=rand(100, n)
dates=2017.08.07..2017.08.11
date=rand(dates, n)
x=rand(10.0, n)
t=table(ID, date, x);

dbDate = database(, VALUE, 2017.08.07..2017.08.11)
dbID=database(, RANGE, 0 50 100);
db = database("dfs://compoDB", COMPO, [dbDate, dbID]);
pt = db.createPartitionedTable(t, `pt, `date`ID)
pt.append!(t);
```

Back up all partitions of table pt:

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt")>,true);
```

Back up partitions with date>2017.08.10:

```
backup("/home/DolphinDB/backup",<select * from loadTable("dfs://compoDB","pt") where date>2017.08.10>,true);
```

Obtain information on the backup partitions of table pt:

```
getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt");
```

Obtain information on the backup partition 20120810/0_50:

```
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB","/20170810/0_50","pt");
```

Load the backup data of partition 20120810/0_50 into memory:

```
loadBackup("/home/DolphinDB/backup","dfs://compoDB","/20170810/0_50","pt");
```

---

> **IMPORTANT:** 
>
> For databases created in DolphinDB 1.30.16/2.00.4 or above, the parameter *partition* of functions `getBackMeta` and `loadBackup` can be specified in the following way.

```
list=getBackupList("/home/DolphinDB/backup","dfs://compoDB","pt").chunkPath;
path=list[0][regexFind(list[0],"/20170807/0_50"):]
getBackupMeta("/home/DolphinDB/backup","dfs://compoDB", path, "pt");
loadBackup("/home/DolphinDB/backup","dfs://compoDB", path, "pt");
```

---

Restore table pt from backup:

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%",true);
```

Create table temp in dfs://compoDB with the same schema as table pt:

```
temp=db.createPartitionedTable(t, `temp, `date`ID);
```

Restore the backup of all partitions in table pt with date = 2017.08.10 to table temp:

```
restore("/home/DolphinDB/backup","dfs://compoDB","pt","%20170810%",true,temp);
```

Migrate all backup data to a new database dfs://newCompoDB and table pt:

```
migrate("/home/DolphinDB/backup","dfs://compoDB","pt","dfs://newCompoDB","pt");

```
