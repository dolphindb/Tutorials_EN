# Adding Columns and Calculated Metrics Dynamically

The industrial internet of things (IIoT) data and financial market data features high frequency, multiple dimensions, sheer volume, and no updates once generated.

In the IIoT, when amassing data, we often increase the dimensions of data for further analysis. In financial sector, more risk indicators are required for real-time risk monitoring. To deal with such requirements, DolphinDB supports to add columns and calculated metrics dynamically for both scenarios in stream processing.

The stream processing in DolphinDB involves stream tables, streaming engines,  DFS tables. If the dimension for data analysis increases, the columns and metrics of these tables must be added with the following order:
1. DFS table
2. stream table
3. streaming engine

This tutorial uses specific examples of the IIoT to expound how to add columns and calculated metrics to DFS tables, stream tables, and streaming engines in stream processing.

## 1. Adding Columns to a DFS Table

DolphinDB provides function [addColumn](https://docs.dolphindb.cn/en/help200/FunctionsandCommands/CommandsReferences/a/addColumn.html) to add columns to a table (of any type). 

For example, you can add columns for a DFS table as follows:

* Create a DFS database and the DFS table "pt" to save stream data.

```
if(existsDatabase("dfs://iotDemo")){
	dropDatabase("dfs://iotDemo")
	}
db=database("dfs://iotDemo",RANGE,`A`F`M`T`Z)
pt = db.createPartitionedTable(table(1000:0,`time`equipmentId`voltage`current,[TIMESTAMP,SYMBOL,INT,DOUBLE]), `pt, `equipmentId)
```

Add two columns for the DFS table "pt". Note that the table should be updated by function [loadTable](https://docs.dolphindb.cn/en/help200/FunctionsandCommands/FunctionReferences/l/loadTable.html) after adding a new column into the DFS table.

```
addColumn(pt,`temperature`humidity,[DOUBLE,DOUBLE])
pt=loadTable("dfs://iotDemo","pt")
```

## 2. Adding Columns for a Stream Table

IIoT data and real-time market data are often ingested into stream tables (created by ``streamTable``) first. If the number of dimensions increases, the schema of the stream table needs to be adjusted correspondingly.

In the following examples, a stream table with two dimensions is created to record real-time voltage and current.

```
streamTb=streamTable(1000:0,`time`equipmentId`voltage`current,[TIMESTAMP,SYMBOL,INT,DOUBLE])
```

Add two new columns for the stream table: temperature and humidity.

```
addColumn(streamTb,`temperature`humidity,[DOUBLE,DOUBLE])
```

The table is updated immediately after the new columns are added.

## 3. Adding Calculated Metrics for a Streaming Engine

You can specify the calculated metrics with metacode when defining the streaming engine. DolphinDB provides function [addMetrics](https://docs.dolphindb.cn/en/help200/FunctionsandCommands/CommandsReferences/a/addMetrics.html) to add calculated metrics.

In the following example, we define a streaming engine to calculate the average voltage and average current for each device every 50ms.

```
// Define a time-series engine and subscribe to the stream table
streamTb=streamTable(1000:0,`time`equipmentId`voltage`current,[TIMESTAMP,SYMBOL,INT,DOUBLE])
share streamTb as sharedStreamTb
outTb=table(1000:0,`time`equipmentId`avgVoltage`avgCurrent,[TIMESTAMP,SYMBOL,INT,DOUBLE])
streamEngine = createTimeSeriesEngine(name="agg1", windowSize=100, step=50, metrics=<[avg(voltage),avg(current)]>, dummyTable=sharedStreamTb, outputTable=outTb, timeColumn=`time, useSystemTime=false, keyColumn=`equipmentId, garbageSize=2000)
subscribeTable(, "sharedStreamTb", "streamTable", 0, append!{streamEngine}, true)

// Insert data into a stream table
n=10
time=temporalAdd(2019.01.20 12:30:10.000,rand(300,n),"ms")
equipmentId=rand(`A`F`M`T`Z,n)
voltage=rand(250,n)
current=rand(16.0,n)
insert into sharedStreamTb values(time, equipmentId, voltage, current)

// check the stream table
select * from sharedStreamTb
```

|time                       |equipmentId    |voltage    |current   |
|---                        |---            |---        |---       |
|2019.01.20T12:30:10.160    |A    |79    |1.9056|
|2019.01.20T12:30:10.021    |T    |65    |11.6551|
|2019.01.20T12:30:10.244    |M    |113   |12.2897|
|2019.01.20T12:30:10.053    |A    |133   |1.2491|
|2019.01.20T12:30:10.175    |A    |186   |7.5363|
|2019.01.20T12:30:10.260    |M    |118   |10.4733|
|2019.01.20T12:30:10.003    |M    |172   |1.1165|
|2019.01.20T12:30:10.101    |M    |170   |10.5922|
|2019.01.20T12:30:10.260    |T    |95    |15.5515|
|2019.01.20T12:30:10.249    |Z    |90    |15.2511|


```
// check the output table
select * from outTb
```

|time                   |equipmentId|avgVoltage|avgCurrent   |
|----                   |-----------|----------|-------------|
|2019.01.20T12:30:10.050	|T	|65	|11.6551|
|2019.01.20T12:30:10.100	|T	|65	|11.6551|
|2019.01.20T12:30:10.250	|M	|113|12.2897|

Add two new calculated metrics to the time-series engine, which takes the lastest voltage and current every 50ms. When there is no incoming data, the value of the new metrics in the output table is empty.

```
newMetricsSchema=table(1:0,`lastvoltage`lastCurrent,[INT,DOUBLE])
addMetrics(aggregator,<[last(voltage), last(current)]>,newMetricsSchema)

// check the output table
select * from outTb
```

|time                   |equipmentId|avgVoltage|avgCurrent   |lastVoltage|lastCurrent|
|----                   |-----------|----------|-------------|---|---|
|2019.01.20T12:30:10.050	|T	|65	|11.6551|
|2019.01.20T12:30:10.100	|T	|65	|11.6551|
|2019.01.20T12:30:10.250	|M	|113|12.2897|

Insert new data.

```
n=10
timev=temporalAdd(2019.01.20 12:30:10.000,rand(300,n),"ms")
equipmentIdv=rand(`A`F`M`T`Z,n)
voltagev=rand(220..250,n)
eletricityv=rand(16.0,n)
insert into sharedStreamTb values(time, equipmentId, voltage, current)
select * from outTb
```

|time                   |equipmentId|avgVoltage|avgCurrent   |lastVoltage|lastCurrent|
|----                   |-----------|----------|-------------|---|---|
|2019.01.20T12:30:10.050	|T	|65	|11.6551|
|2019.01.20T12:30:10.100	|T	|65	|11.6551|
|2019.01.20T12:30:10.250	|M	|113|12.2897|
|2019.01.20T12:30:10.200|F          |235       |9.182104     |234|14.896723|
|2019.01.20T12:30:10.150|T          |243       |10.816871    |236|7.026039|
|2019.01.20T12:30:10.200|Z          |225       |5.893952     |225|2.098874|


