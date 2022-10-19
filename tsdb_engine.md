# Introduction to DolphinDB TSDB Storage Engine

This tutorial introduces the TSDB storage engine that was released in DolphinDB 2.0.

- [Introduction to DolphinDB TSDB Storage Engine](#introduction-to-dolphindb-tsdb-storage-engine)
  - [1. Application Scenarios: OLAP vs TSDB](#1-application-scenarios-olap-vs-tsdb)
    - [Examples](#examples)
  - [2. How the TSDB Engine Works](#2-how-the-tsdb-engine-works)
    - [2.1 Redo Log](#21-redo-log)
    - [2.2 Cache Engine](#22-cache-engine)
    - [2.3 Sort Columns](#23-sort-columns)
    - [2.4 Level Files](#24-level-files)
  - [3. Usage Tips](#3-usage-tips)

## 1. Application Scenarios: OLAP vs TSDB

Before DolphinDB version 2.0, the OLAP engine was the only storage engine. Each column in a partition of a table is saved as a file. Data is stored in the order as it is written, which makes writing highly efficient.

The OLAP engine has the following major limitations:

(1) There's no index within a partition, which means (the selected columns of) an entire partition must be loaded even for queries involving only 1 record;

(2) Deduplication cannot be conducted during writing;

(3) It is not suitable for tables with more than a few hundred columns.

(4) To modify a single record, an entire partition must be rewritten.

The TSDB storage engine can overcome the aforementioned limitations of the OLAP engine. It is developed based on the Log-Structured Merge-Tree (LSM Tree). The data in each partition is stored in level files. The data in each level file is sorted and has block indexing.

The TSDB engine has the following advantages over the OLAP engine:

(1) Queries with partitioning columns and within-partition sort columns in filtering conditions have extremely high performance;

(2) Data can be sorted and duplicate data can be purged as data is written to the database.

(3) Suitable for storing tables with hundreds or thousands of columns (up to 32,767 columns). It also supports data types such as array vector or BLOB;

(4) If only the last record is kept for duplicate records (set *keepDuplicates*=LAST for function `createPartitionedTable`), to update a record, only the level file that this record belongs to needs to be rewritten instead of an entire partition. 

The TSDB engine has the following disadvantages compared with the OLAP engine:

(1) Lower write throughput as data needs to be sorted in the cache engine and the level files might be merged and compacted;

(2) Lower performance when reading data from an entire partition or columns in an entire partition.

### Examples

The following example illustrates the types of queries that are suitable for the OLAP and TSDB engines respectively. Table *t* uses a COMPO partition based on stock ticker and trading date. The following is sample data from table *t*:

| StockID | Timestamp           | Bid   |
| :------ | :------------------ | :---- |
| AAA     | 2021.08.05T09:30:00 | 12.53 |
| BBB     | 2021.08.05T09:30:00 | 21.36 |
| AAA     | 2021.08.05T09:31:00 | 12.54 |
| CCC     | 2021.08.05T09:31:00 | 31.49 |
| …       | …                   | …     |

Create a database with OLAP storage engine:

```
dbTime = database("", VALUE, 2021.08.01..2021.09.01)
dbStockID = database("", HASH, [SYMBOL, 100])

db = database(directory="dfs://stock",partitionType=COMPO,partitionScheme=[dbTime,dbStockId],engine="OLAP")

schema = table(1:0, `Timestamp`StockID`bid, [TIMESTAMP, SYMBOL, DOUBLE])
stocks = db.createPartitionedTable(table=schema, tableName=`stocks, partitionColumns=`Timestamp`StockID) 
```

Create a database with TSDB storage engine:

```
dbTime = database("", VALUE, 2021.08.01..2021.09.01)
dbStockID = database("", HASH, [SYMBOL, 100])

db = database(directory="dfs://stock",partitionType=COMPO,partitionScheme=[dbTime,dbStockId],engine="TSDB")

schema = table(1:0, `Timestamp`StockID`bid, [TIMESTAMP, SYMBOL, DOUBLE])
stocks = db.createPartitionedTable(table=schema, tableName=`stocks, partitionColumns=`Timestamp`StockID, sortColumns=`StockID`Timestamp)
```

Note: Please specify the parameter *engine* as “TSDB” when creating a database with function `database`, and then specify *sortColumns* as columns “StockID” and “Timestamp” in function `createPartitionedTable`.


The OLAP engine is a better choice for queries like the following:

```
select avg(Bid) from t where date(Timestamp)=2021.08.05 group by StockID
```

The TSDB engine is a better choice for queries like the following:

```
select * from t where StockID='AAA', Timestamp > 2021.08.05T09:30:00, Timestamp < 2021.08.05T09:35:00
```

For databases created with the OLAP engine, there is no index inside each partition. The smallest unit of data to load from a database is a column in a partition. Therefore, to query a single record, the entire partition containing this record must be loaded, and the query usually takes over 100 milliseconds. In comparison, as the TSDB engine has indices inside each partition, retrieving a small amount of records doesn't require loading the entire partition and it may take only a few milliseconds. Moreover, the performance of the TSDB engine for massive data aggregation and analysis is generally only marginally slower than the OLAP engine.


## 2. How the TSDB Engine Works

Next, we explain how the TSDB engine works in details based on the example in the previous section.

### 2.1 Redo Log

After data is loaded into memory, it is first persisted to the redo log (also known as Write-Ahead Log or WAL). Even if there is a crash when data is written to the database, you can still recover the data from the redo log when you reboot the server.

### 2.2 Cache Engine

After it is confirmed that data is persisted to the redo log, data is written to the cache engine in memory. As the data is written to the cache engine, it is first appended without sorting. This is called an “unsorted write buffer”. After the unsorted write buffer reaches a threshold, it is sorted by StockID and becomes a “sorted write buffer”. The sorted write buffer is read-only, and it can be compressed in memory. After multiple sorted write buffers are created and their total size reaches a threshold (specified by the configuration parameter *TSDBCacheEngineSize*), data in all the sorted write buffers is sorted by Timestamp and written to data files on disk (“level files”).

The two stage design (from “unsorted write buffer” to “sorted write buffer”) of the TSDB's cache engine is different from the cache engine (also called “MemTable”) of most of other database systems that are based on LSMT. This is to balance the performance of reads and writes.

Please note that if there's new data coming in while the cache engine is being flushed to disk, extra memory will be allocated to store the incoming data. Therefore, the TSDB cache engine may occupy up to twice the size of *TSDBCacheEngineSize*.

### 2.3 Sort Columns

In the TSDB engine, columns that are used to sort data within each level file, such as StockID and Timestamp in the above example, are called “sort columns” (which are specified by the parameter *sortColumns* of function `createPartitionedTable`). A common practice is to specify a temporal column as the last column of sort columns, and column(s) that SQL *where* conditions may frequently involve as the other sort columns. The unique combinations of the values of the sort columns (except the last sort column) are called sort keys. Records with the same sort key are sorted by the temporal column and stored in blocks (the size of which is 16 KB by default). When a query is executed, relevant blocks are first located based on the sort key and the specified time range, and then loaded to memory for decompression, which considerably improves the query efficiency.

### 2.4 Level Files

Data in each level file is sorted by StockID and Timestamp. Data with the same StockID is contiguously stored on disk and is split into multiple data blocks. The starting location of each data block is maintained as an index entry. Subsequent writes are stored in other level files, and so forth.

There can be at most 4 levels of level files. Level 0 files are generated as the data is written from the cache engine to disk, and higher level files are merged from lower-level files. The maximum size of a level 0 file is 32MB. If more than 32MB is written from the cache engine to a partition, multiple level 0 files are created. When the number of level 0 files exceeds 10 or the total size of level 0 files is larger than a threshold (256 MB), all level 0 files are merged, sorted based on StockID and Timestamp, and then compressed to form a level 1 file. The same logic applies to the merge/compact from level 1 files to level 2 files. In this way, the number of level files can be kept at a relatively low number so that query performance does not suffer from a large number of level files.


## 3. Usage Tips

**Data deduplication**

The parameter *keepDuplicates* of function `createPartitionedTable` specifies how to deal with records with duplicate *sortColumns* values (data with the same value of `StockID` and `Timestamp` in the above example).

The parameter can be set to the following values:

- ALL: keep all records (the default value)
- LAST: only keep the last record
- FIRST: only keep the first record

**Limit the number of sort keys**

To ensure optimal performance, it is recommended that the number of sort keys within each partition does not exceed 1000. If the number of sort keys is too large but there are only a few records with the same sort key, there might be too many blocks. This may affect query performance. You can specify sortKeyMappingFunction for function createPartitionedTable to reduce the dimensionality of sort keys. It, however, may affect the write performance. Therefore, when creating a table, please carefully specify the sort columns to avoid an excessive number of sort keys.


**Configure cache engine size**

Use the configuration parameter *TSDBCacheEngineSize* to set the cache engine size (in GB). The default value is 1. It's recommended to be no smaller than 1 GB.

**Configure TSDB block size**

Use the configuration parameter *TSDBMaxBlockSize* to set the TSDB block size (in bytes). The default value is 16,384. Setting a smaller size may speed up certain queries, but it may decrease the compression ratio.

**Trigger level file compaction**

A large number of level files may slow down query performance. For partitions that will no longer be written to, you can use command `triggerTSDBCompaction` to force merge the level 0 files. It can improve not only query performance but also the compression ratio.
