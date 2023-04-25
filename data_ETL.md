# DolphinDB ETL Tuning: From 4.5 Hours to 3.5 Minutes

Extract, transform, and load (ETL) is a data integration process which first extracts the data from various sources, then transforms the data according to business rules, and loads the data into a destination data warehouse. 

When utilizing traditional tech stacks like Python, MySQL, and Java as ETL tools, it's common for users to experience performance limitations as the volume of data grows, particularly when processing high-frequency trading data. In this tutorial, we will show you how to implement an ETL process and enhance its performance with SQL tuning techniques using DolphinDB. Our optimized script reduces the processing time from 4.5 hours to 3.5 minutes, with the performance improved by over 70 times.

- [DolphinDB ETL Tuning: From 4.5 Hours to 3.5 Minutes](#dolphindb-etl-tuning-from-45-hours-to-35-minutes)
  - [1. Scenario and Data Preparation](#1-scenario-and-data-preparation)
    - [1.1 Data Preparation](#11-data-preparation)
    - [1.2 Business Requirements](#12-business-requirements)
    - [1.3 Environment](#13-environment)
  - [2. ETL Process](#2-etl-process)
    - [2.1 ETL Design](#21-etl-design)
    - [2.2 Bottleneck Analysis](#22-bottleneck-analysis)
  - [3. Performance Tuning](#3-performance-tuning)
    - [3.1 Space Complexity](#31-space-complexity)
    - [3.2 Processing Speed](#32-processing-speed)
  - [4. Optimized ETL Process](#4-optimized-etl-process)
    - [4.1 Optimized Script](#41-optimized-script)
    - [4.2 Performance Analysis](#42-performance-analysis)
  - [5. Conclusion](#5-conclusion)
  - [Recommended Reading](#recommended-reading)
  - [Appendices](#appendices)

## 1. Scenario and Data Preparation

### 1.1 Data Preparation

In this tutorial, we prepare 1 year's raw trade data (up to 1.7 TB before compression) for ETL processing. Table "trade" contains tick data of around 3000 stocks with 60 million records per day.

| Field 	| Data Type 	| Description 	|
|---	|---	|---	|
| securityID 	| STRING 	| stock ID 	|
| tradingdate 	| DATE 	| trading date 	|
| tradingtime 	| TIMESTAMP 	| trading time 	|
| tradetype 	| SYMBOL 	| trade type 	|
| recid 	| INT 	| record ID 	|
| tradeprice 	| DOUBLE 	| trading price 	|
| tradevolume 	| INT 	| trading volume 	|
| buyorderid 	| INT 	| ID of the buy order 	|
| sellorderid 	| INT 	| ID of the sell order 	|
| unix 	| TIMESTAMP 	| Unix timestamp 	|

We will write the processed data to the target table. Both the source and target tables use the OLAP storage engines and adopt composite partitions that combine date-based value partition and stock-based hash partition (with 20 hash partitions). 

### 1.2 Business Requirements

To meet the requirements for quantitative analysis listed below, the ETL process is supposed to convert the field types, add symbol suffixes, add calculated fields, filter failed trades, etc.

- Convert the data type of column "tradingDate" from DATE to INT;
- Convert the data type of column "tradingTime" from TIMESTAMP to LONG type;
- Add a column of BSFlag (Buy/Sell flag);
- Add a column of tradevalue (total value traded).

### 1.3 Environment

- CPU: Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz
- Logical processors: 16
- Memory: 256 GB
- OS: 64-bit CentOS Linux 7 (Core)
- DolphinDB Server version: 2.00.6
- Deployment: high-availability cluster (with 3 controllers and 3 data nodes)

## 2. ETL Process

### 2.1 ETL Design

In DolphinDB, a general ETL design will cut the database into multiple partitions, process data within each partition, and aggregate the results to the target table. Specifically, it includes the following steps:

(1) Partition the original dataset by trading date and stock ID.

```
data = [cut1, cut2, ... , cutN]
```

(2) Clean and transform the data within each partition, and save the processed data to an in-memory object "tradingdf".

(3) Append the in-memory table "tradingdf" to a DFS table.

```
def genDataV1(date1, dateN){
    tradeSrc = loadTable("dfs://originData", "trade")
    tradeTgt = loadTable("dfs://formatData", "trade")
    for (aDate in date1..dateN){
        tradeSecurityID = (exec distinct(securityID) from tradeSrc where tradingdate = aDate).shuffle()
        for (m in tradeSecurityID){		
		    tradingdf = select  * from tradeSrc where securityID = m and tradingdate = aDate    
		    tradingdf["symbol"] = m + "SZ"        
		    //print("stock " + m + ",date is " + aDate + ",tradingdf size " + tradingdf.size())  
		    tradingdf["buysellflag"] =iif(tradingdf["sellorderid"] > tradingdf["buyorderid"],"S", "B")
		    tradingdf["tradeamount"] = tradingdf["tradevolume"] * tradingdf["tradeprice"]
		    tradingdf = tradingdf[(tradingdf["tradetype"] == "0") || (tradingdf["tradetype"] == "F")]
		    tradingdf = select symbol,tradingdate, tradingtime, recid, tradeprice, tradevolume, tradeamount, buyorderid, sellorderid, buysellflag, unix from tradingdf
		    tradingdf = select * from tradingdf order by symbol, tradingtime, recid     
		    tradingdf.replaceColumn!("tradingdate", toIntDate(::date(tradingdf.tradingDate)))            
		    tradingtime = string(exec tradingtime from tradingdf)
		    tradingdf.replaceColumn!(`tradingtime, tradingtime)
		    unix = long(exec unix from tradingdf)
		    tradingdf.replaceColumn!(`unix, unix)                                             
		    tradeTgt.append!(tradingdf)	      		
        }
	}
}
```

When using ETL tools lik Python, MySQL, Java, or middleware like Kettle, the processing is often limited due to its single-threaded nature. When the similar logic is applied to the ETL process in DolphinDB, it takes up to 4.5 hours to process trade data of 20 trading days. In the following part we will analyze the performance bottleneck and demonstrate how to optimize the script.

### 2.2 Bottleneck Analysis

The performances bottleneck of the ETL process mainly lie in:

(1) Nested loops

The code is executed in nested loops based on the stock ID and trading date. The time complexity *t* can be calculated as follows:

```
t = O(N) * O(M) * t0 = O(MN) * t0
```

- N: trading days
- M: number of stocks
- t0: execution time (in seconds) of the innermost loop

The execution time of the innermost loop is about 400 ms (i.e., 0.4 seconds), and the elapsed time for the full script is estimated to be `t ~= 20 * 0.4 * 3000 = 6.7 hours`.

(2) Repeated queries

As shown above, the transformation script repeatedly operates on the same dataset, causing higher round-trip time. However, some operations, such as data filtering and sorting, can be done within one query.

(3) Calculation on one data node

Starting from the assignment statement for "tradingdf":

`tradingdf=select * from loadTable("dfs://test", 'szl2_stock_trade_daily') where symbol = m and tradingDate = date`

The subsequent script falls short in leveraging DolphinDB's distributed and concurrent computing capabilities, as it only utilizes the resources of one data node. As a result, the performance deteriorates as the volume of data continues to increase.

## 3. Performance Tuning

The formula of execution time is referenced to optimize the performance of ETL process in DolphinDB:

```
t = S / V
```

- t: execution time.
- S: space complexity, i.e., the amount of data for an ETL job.
- V: speed of data processing, i.e., how many records can be processed per second. 

Therefore, the key to reducing execution time *t* for an ETL process lies in reducing space complexity and increasing processing speed.

### 3.1 Space Complexity

In DolphinDB, space complexity can be reduced by partition pruning, columnar storage, indexing, and so on.

- Partition pruning

For the time series data that is divided into partitions (based on the temporal column), if a filtering condition in the where clause specifies the partitioning column, then only the needed partitions are accessed.

- Columnar storage

For example, table "snapshot" contains hundreds of columns, but only a few of them are needed for an aggregate query. DolphinDB's OLAP storage engine adopts columnar storage, enabling users to access only the required columns, which greatly reduces the disk I/O.

- Indexing

An index is a data structure used to provide quick access to the table based on a search key. If a DFS table uses TSDB engine and the query statement is filtered by the specified sort columns, the corresponding block ID can be quickly queried by scanning the sparse index. Only the required blocks are accessed for the query, thus avoiding full a table scan.

### 3.2 Processing Speed

To improve the efficiency of batch processing, you can set a proper batch size and apply multithreaded and distributed computing.

- Proper batch size

DolphinDB manages historical data for batching processing on a partition basis. It is recommended to set the partition size to 100 MB – 500 MB (before compression). 

- Multithreading

DolphinDB makes extensive use of multithreading. Specifically, for a distributed SQL query, multiple threads (localExecutors configuration parameter) are applied to concurrent processing of partitioned data.

- Distributed computing

In DolphinDB, you can deploy a horizontally scalable distributed cluster with multiple servers where distributed transactions are supported. When a distributed SQL query is executed, distributed computing is performed through the Map-Reduce-Merge model. In the Map phase, nodes in the cluster are automatically scheduled to make full use of the hardware resources of the cluster.

## 4. Optimized ETL Process

Based on the performance bottleneck analysis, we optimize the code in the following aspects:

- Improve parallelism
- Reduce query times
- Adopt vectorized processing

### 4.1 Optimized Script

The script has been optimized to process market data on a daily basis. To take advantage of distributed computing and handle the daily market data of 3000 stocks (in 20 hash partitions) efficiently, the SQL query has been divided into 20 tasks. Each task has been assigned to the corresponding node within the cluster, allowing for parallel execution and optimized processing.

The optimized code is as follows:

```
def transformData(tradeDate){
    tradeSrc = loadTable("dfs://originData", "trade")
    tradeTgt = loadTable("dfs://formatData", "trade")
    data = select
        securityID + "SZ" as securityID
        ,toIntDate(tradingdate) as  tradingdate
        ,tradingtime$STRING as tradingtime
        ,recid as recid
        ,tradeprice
        ,tradevolume
        ,tradevolume * tradeprice as tradeamount        
        ,buyorderid as buyrecid
        ,sellorderid as sellrecid
        ,iif(sellorderid>  buyorderid,"S", "B") as buysellflag      
        ,unix$LONG as unix
    from tradeSrc
    where tradingdate = tradeDate and tradetype in ["0", "F"]
    tradeTgt.append!(data)
    pnodeRun(flushOLAPCache)
}
​
allDays = 2022.05.01..2022.05.20
for(aDate in allDays){
    jobId = "transform_"+ strReplace(aDate$STRING, ".", "") 
    jobDesc = "transform data"
    submitJob(jobId, jobDesc, transformData, aDate)
}
```

The script takes about 40 seconds to process one day's market data of 3000 stocks. Data of 20 trading days can be processed in concurrent jobs submitted by the function `submitJob`. By configuring *maxBatchJobWorker* =16 (generally it is set to the number of CPU cores), the optimized script takes only 210 seconds with its performance improved by 74 times.

### 4.2 Performance Analysis

The performance improvement is mainly due to:

- Distributed computing with high parallelism

The `select` statement is executed in parallel, and the parallelism depends on the number of partitions and the number of available *localExecutors* in a cluster. Specifically, for the configuration environment used in this tutorial, the 3 nodes are equipped with 15 local executors each. Based on the partitioning scheme of the source table "trade", the parallelism is 20. Compared with single-threaded processing, the execution speed on data for one trading day is increased to 18 times. Furthermore, multiple tasks can be executed in parallel through `submitJob`.

- Efficient queries

All the processing logic, including data filtering, data type conversion, and adding derived fields, can be done within one query. The data does not need to be accessed repeatedly.

- Vectorized processing

The OLAP engine adopts columnar storage, and each column is loaded into memory in the form of a vector. Therefore, vectorized processing is applied to improve the efficiency of SQL queries.

## 5. Conclusion

In this tutorial we explore the optimization of ETL process in DolphinDB using a practical example of SQL query tuning. By avoiding nested loops and adopting distributed and vectorized computing techniques, the optimized SQL query demonstrates a remarkable 74-fold increase in efficiency. Specifically, the ETL processing of market data for 3000 stocks over 20 trading days, which previously took over 4.5 hours, can now be completed in just 210 seconds. Theses features makes DolphinDB a highly efficient ETL tool for preprocessing on large data sets.

## Recommended Reading

- Partitions and performance tuning in DolphinDB: [DolphinDB Partitioned Database Tutorial](https://github.com/dolphindb/Tutorials_EN/blob/master/database.md)
- Threading Model: [Overview of Threading Model in DolphinDB](https://github.com/dolphindb/Tutorials_EN/blob/master/thread_model_SQL.md)
- TSDB Storage Engine: [Introduction to TSDB](https://github.com/dolphindb/Tutorials_EN/blob/master/tsdb_engine.md)

## Appendices

- [Data Preparation]()
- [Script Before Optimization]()
- [Optimized Script]()