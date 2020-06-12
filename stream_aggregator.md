# DolphinDB Tutorial: Time-Series Streaming Aggregator 

## 1. Create time-series aggregator

The streaming time-series aggregator is created by function `createTimeSeriesAggregator`. It returns an abstract table object, which is the entry point of the aggregator. Writing data to this abstract table means that data enters the aggregator for calculation.

Function `createTimeSeriesAggregator` is generally used in conjunction with function `subscribeTable`. Through function `subscribeTable`, the aggregator subscribes to a stream table. After new data enters the stream table, it will be pushed to the aggregator for calculation.

### 1.1 Syntax

createTimeSeriesAggregator(name, windowSize, step, metrics, dummyTable, outputTable, [timeColumn], [useSystemTime=false], [keyColumn], [garbageSize], [updateTime], [useWindowStartTime])

### 1.2 Parameters

- name

Type: STRING

The name of the aggregator. It is the unique identifier of the aggregator on a data node.

- useSystemTime

Type: BOOLEAN scalar

It indicates how the calculations are triggered. It is optional and the default value is false. 

If useSystemTime=true, calculations are triggered at fixed-length intervals. Fixed-length windows are determined based on the time when each record enters the aggregator (with millisecond precision) instead of the temporal column in the data. If there is at least one record in this window, a calculation is triggered immediately after the window ends. 

If useSystemTime=false, calculations are triggered when new data arrives after a window. Fixed-length windows are determined based on the temporal column specified by the parameter 'timeColumn'. Please note that the new record that triggers a calculation is not used in this calculation. 

For example, let's consider a window from 10:10:10 to 10:10:19. If useSystemTime=true, as long as there is at least one record in the window, the calculation for this window is triggered at 10:10:20 right after the window ends. If useSystemTime=false, and the first record after 10:10:19 arrives at 10:10:25, the calculation of this window is triggered at 10:10:25.

- windowSize

Type: INT

The length of the windows. 

A window includes its starting time but not its ending time. 

- step

Type: INT

It defines the length between the end time of two adjacent windows. The value of 'windowSize' must be a multiple of 'step'.

The unit of 'windowSize' and 'step' depends on the value of 'useSystemTime'. If useSystemTime=true, the unit of 'windowSize' and 'step' is millisecond; if useSystemTime=false, the unit of 'windowSize' and 'step' is the same as the unit of 'timeColumn'. 

To facilitate comparison of results, the system adjusts the starting time of the first window. For example, if the first record enters the aggregator at 2018.10.10T03:26:39.178 and step=100, the system will adjust the starting time of the first window to 2018.10.10T03:26:39.100. Please refer to Section 1.3.1 for more details. 

If the aggregator conducts calculation in groups, the windows of all groups are adjusted so that overlapping windows of all groups share the same boundaries.

- metrics

Type: METACODE

Calculation formulas. It can be one or more built-in or user-defined aggregate functions such as <[sum(volume), avg(price)]>, or expressions of aggregate functions such as as <[avg(price1)-avg(price2)]>, or aggregate functions on operations involving multiple columns such as <[std(price1-price2)]>.

To improve performance, DolphinDB optimizes selected aggregate functions in the time-series aggregator. The calculation in the current window utilizes the result from the previous window. The following table lists the optimized aggregate functions:

Name | Description
---|---
corr|correlation
covar|covariance
first|first element
last|last element
max|maximum
med|median
min|minimum
percentile|percentile
std|standard deviation
sum|sum
sum2|sum of squares
var|variance
wavg|weighted average
wsum|weighted sum

- dummyTable

Type: TABLE

The system uses the schema of 'dummyTable' to determine the data type of each column in the streaming data. The schema of 'dummyTable' must be the same as that of the stream table. Whether 'dummyTable' contains data does not matter. 

- outputTable

Type: TABLE

The output table for the calculation results. 

Before we use function `createTimeSeriesAggregator`, we need to create 'outputTable' and specify the names and data types of its columns. The aggregator inserts the results into it.  

The following rules apply to the schema of 'outputTable':

(1) The data type of the first column must be temporal. It is TIMESTAMP if useSystemTime=true. It is the same as the data type of 'timeColumn' if useSystemTime=false. 

(2) If 'keyColumn' is specified, the second column is 'keyColumn'. 

(3) The remaining columns are calculation results. 

- timeColumn

Type: STRING scalar

When useSystemTime=false, 'timeColumn' is the name of the temperal column of the stream table. 

- keyColumn

Type: STRING scalar

The name of the grouping column. It 'keyColumn' is specified, the time-series aggregator conducts calculations in groups. 

- garbageSize

Type: INT

As the subscribed data continues to accumulate in the aggregator, a machenism is needed to clear data in the memory that is no longer needed. When the number of rows of historical data in the memory exceeds 'garbageSize', the system will clear the historical data that is not needed for the current calculation. 'garbageSize' has a default value of 50,000. 

If 'keyColumn' is specified, memory cleanup is performed independently within each group. When the number of rows of historical data in memory of a group exceeds 'garbageSize', the historical data that is not needed in the current calculation in this group will be cleared.

- updateTime

Type: INT

If 'updateTime' is not specified, calculation for a window will not occur before the ending time of the window. If we want to conduct a calculation for the current window before it ends, we can specify 'updateTime'. The unit of 'updateTime' is the same as the unit of 'step', and 'step' must be a multiple of 'updateTime'. To specify 'updateTime', 'useSystemTime' must be set to false. 

If 'updateTime' is specified, multiple calculations may happen within the current window. These calculations are triggered with the following rules:

(1) Divide the current window into 'windowSize'/'updateTime' small windows. Each small window has a length of 'updateTime'. When a new record arrives after a small window finishes, if there is at least one record in the current window that is not used in a calculation (excluding the new record), a calculation is triggered. Please note that this calculation does not use the new record. 

(2) If max(2\*updateTime, 2 seconds) after a record arrives at the aggregator, it still has not been used in a calculation, a calculation is triggered. This calculation includes all data in the current window at the time.

If 'keyColumn' is specified, these rules apply within each group. 

Please note that the timestamp of each calculation result within the current window is the current window starting time or starting time + 'windowSize' (depending on parameter 'useWindowStartTime') instead of a timestamp inside the current window.

If 'updateTime' is specified, 'outputTable' must be a keyed table (created with function `keyedTable`). If 'keyColumn' is not specified, the primary key of the output table is 'timeColumn'; if 'keyColumn' is specified, the primary keys of the output table are 'timeColumn' and 'keyColumn'. If the output table is an ordinary in-memory table or a stream table, each calculation will add a record, which will produce a large number of results with the same timestamp. The output table cannot be a keyed stream table either, as the records of a keyed stream table cannot be updated.

For details, please refer to the example in section 1.3.6.

- useWindowStartTime

Type: INT

Indicates whether the first column in 'outputTable' is the starting time of the windows. The default value is false, which means that the first column in 'outputTable' is the starting time of the windows + 'windowSize'.

### 1.3 More about parameters and examples

#### 1.3.1 step

The system adjusts the starting time of the first window with a value 'alignmentSize' based on the precision of 'timeColumn' and the value of the parameter 'step'. 

If the precision of 'timeColumn' is second, such as DATETIME or SECOND:

step | alignmentSize
---|---
0~2 |2
3~5 |5
6~10|10
11~15|15
16~20|20
21~30|30
31~60|60

If the precision of 'timeColumn' is millisecond, such as TIMESTAMP or TIME:

step | alignmentSize
---|---
0~2 |2
3~5 |5
6~10 |10
11~20 |20
21~25 |25
26~50|50
51~100|100
101~200|200
201~250|250
251~500|500
501~1000|1000

DolphinDB stores temporal data as integers. For example, 13:30:10 is stored as 13\*60\*60+30\*60+10=48610. The system adjusts the starting time of the first window to be the last value before the time of the first record that is divisible by 'alignmentSize'.

If the time of the first record is x with data type of TIMESTAMP, then the starting time of the first window is adjusted to be timestamp(x/alignmentSize\*alignmentSize), where / produces only the integer part after division. For example, if the time of the first record is 2018.10.08T01:01:01.365 and step=60000, then alignmentSize=60000, and the starting time of the first window is timestamp(2018.10.08T01:01:01.365/60000*60000)=2018.10.08T01:01:00.000.

The following example explains in detail how the boundaries of windows are set and how the aggregator conducts calculations. We first create the stream table "trades" with 2 columns: time and volume. Then we create a time-series aggregator "streamAggr1" to calculate sum(volume) for the past 6 milliseconds every 3 millisecond. 

```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
outputTable = table(10000:0, `time`sumVolume, [TIMESTAMP, INT])
tradesAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <[sum(volume)]>, trades, outputTable, `time)
subscribeTable(, "trades", "append_tradesAggregator", 0, append!{tradesAggregator}, true)   
```

Insert 10 records into the stream table "trades":
```
def writeData(t, n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    volumev = take(1, n)
    insert into t values(timev, volumev)
}
writeData(trades, 10)

select * from trades;
```
time	|volume
---|---
2018.10.08T01:01:01.002	|1
2018.10.08T01:01:01.003	|1
2018.10.08T01:01:01.004	|1
2018.10.08T01:01:01.005	|1
2018.10.08T01:01:01.006	|1
2018.10.08T01:01:01.007	|1
2018.10.08T01:01:01.008	|1
2018.10.08T01:01:01.009	|1
2018.10.08T01:01:01.010	|1
2018.10.08T01:01:01.011	|1

```
select * from outputTable;
```
time|sumVolume
---|---
2018.10.08T01:01:01.003	|1
2018.10.08T01:01:01.006	|4
2018.10.08T01:01:01.009	|6

Now we describe how the 3 calculations were conducted in details. For simplicity, in this paragraph regarding the "time" column we ignore the part of 2018.10.08T01:01:01 and only use the milliseconds part. As the first record's time is 002 and step=3, the beginning time of the first window is adjusted to be 000. As step=3, the first window ends at 002 and only contains the record of 002. The calculation is triggered by the record of 003 and the result is 1. The second window is from 000 to 005 with 4 records. The calculation is triggered by the record of 006 and the result is 4. The third window is from 003 to 008 with 6 records. The calculation is triggered by the record of 009 and the result is 6. Although the fourth window is from 006 to 011 with 6 records, there is no record after 011 so the calculation for this window is not triggered. 

To execute the script above again, we need to unsubscribe from the stream table and delete both the stream table and the aggregator with the following script:
```
unsubscribeTable(, "trades", "append_tradesAggregator")
undef(`trades, SHARED)
dropAggregator("streamAggr1")
```

#### 1.3.2 metrics

The time-series aggregator supports a wide variety of calculation formulas.

- One or more aggregate functions
```
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <sum(ask)>, quotes, outputTable, `time)
```

- Operations with aggregate function results
```
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <max(ask)-min(ask)>, quotes, outputTable, `time)
```

- Aggregate functions on operations with columns
```
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <max(ask-bid)>, quotes, outputTable, `time)
```

- Output multiple results
```
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <[max((ask-bid)/(ask+bid)*2), min((ask-bid)/(ask+bid)*2)]>, quotes, outputTable, `time)
```

- Aggregate functions with multiple parameters
```
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <corr(ask,bid)>, quotes, outputTable, `time)

tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <percentile(ask-bid,99)/sum(ask)>, quotes, outputTable, `time)
```

- User-defined function
```
def spread(x,y){
	return abs(x-y)/(x+y)*2
}
tsAggregator = createTimeSeriesAggregator("streamAggr1", 6, 3, <spread(ask, bid)>, quotes, outputTable, `time)
```

Note: Nested aggregate function calls are not supported, such as sum(spread(ofr,bid)).

#### 1.3.3 dummyTable

```
share streamTable(1000:0, `time`volume, [TIMESTAMP, INT]) as trades
modelTable = table(1000:0, `time`volume, [TIMESTAMP, INT])
outputTable = table(10000:0, `time`sumVolume, [TIMESTAMP, INT])
tradesAggregator = createTimeSeriesAggregator("streamAggr1", 5, 5, <[sum(volume)]>, modelTable, outputTable, `time)
subscribeTable(, "trades", "append_tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(t,n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    volumev = take(1, n)
    insert into t values(timev, volumev)
}

writeData(trades, 6)

sleep(1)
select * from outputTable
```

#### 1.3.4 outputTable

Aggregation results can be output to an in-memory table or a stream table. Records in an in-memory table can be updated or deleted. Records in a stream table cannot be modified or deleted, but can be published as the data source of another aggregator. 

In the following example, the aggregator "electricityAggregator1" subscribes to the stream table "electricity" and conducts moving average calculations. The results are output to a stream table "outputTable1". The aggregation engine "electricityAggregator2" subscribes to "outputTable1" and conducts moving max calculations. 

```
share streamTable(1000:0,`time`voltage`current,[TIMESTAMP,DOUBLE,DOUBLE]) as electricity

share streamTable(10000:0,`time`avgVoltage`avgCurrent,[TIMESTAMP,DOUBLE,DOUBLE]) as outputTable1 

electricityAggregator1 = createTimeSeriesAggregator("electricityAggregator1", 10, 10, <[avg(voltage), avg(current)]>, electricity, outputTable1, `time, , , 2000)
subscribeTable(, "electricity", "avgElectricity", 0, append!{electricityAggregator1}, true)

outputTable2 =table(10000:0, `time`maxVoltage`maxCurrent, [TIMESTAMP,DOUBLE,DOUBLE])
electricityAggregator2 = createTimeSeriesAggregator("electricityAggregator2", 100, 100, <[max(avgVoltage), max(avgCurrent)]>, outputTable1, outputTable2, `time, , , 2000)
subscribeTable(, "outputTable1", "maxElectricity", 0, append!{electricityAggregator2}, true);
```
Insert 500 records into the stream table "electricity":
```
def writeData(t, n){
        timev = 2018.10.08T01:01:01.000 + timestamp(1..n)
        voltage = 1..n * 0.1
        current = 1..n * 0.05
        insert into t values(timev, voltage, current)
}
writeData(electricity, 500);
```

The final results:
```
select * from outputTable2;
```
time	|maxVoltage	|maxCurrent
---|---|---
2018.10.08T01:01:01.100	|8.45	|4.225
2018.10.08T01:01:01.200	|18.45	|9.225
2018.10.08T01:01:01.300	|28.45	|14.225
2018.10.08T01:01:01.400	|38.45	|19.225
2018.10.08T01:01:01.500	|48.45	|24.225

To execute the script above again, we need to unsubscribe from the stream tables and delete both the stream tables and the aggregators with the following script:
```
unsubscribeTable(, "electricity", "avgElectricity")
undef(`electricity, SHARED)
unsubscribeTable(, "outputTable1", "maxElectricity")
undef(`outputTable1, SHARED)
dropAggregator("electricityAggregator1")
dropAggregator("electricityAggregator2")
```

#### 1.3.5 keyColumn

The following example conducts calculations within each 'sym' group. 
```
share streamTable(1000:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as trades
outputTable = table(10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
tradesAggregator = createTimeSeriesAggregator("streamAggr1", 3, 3, <[sum(volume)]>, trades, outputTable, `time, false,`sym, 50)
subscribeTable(, "trades", "append_tradesAggregator", 0, append!{tradesAggregator}, true)    

def writeData(t, n){
    timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
    symv =take(`A`B, n)
    volumev = take(1, n)
    insert into t values(timev, symv, volumev)
}

writeData(trades, 6)

select * from trades order by sym;
```
time|sym|volume
---|---|---
2018.10.08T01:01:01.002	|A	|1
2018.10.08T01:01:01.004	|A	|1
2018.10.08T01:01:01.006	|A	|1
2018.10.08T01:01:01.003	|B	|1
2018.10.08T01:01:01.005	|B	|1
2018.10.08T01:01:01.007	|B	|1

The final results:
```
select * from outputTable;
```
time	|sym|	sumVolume
---|---|---
2018.10.08T01:01:01.003	|A|	1
2018.10.08T01:01:01.006	|A|	1
2018.10.08T01:01:01.006	|B|	2

The starting time of the first window is adjusted to be 000. As windowSize=3 and step=3, the windows are [000,003), [003,006), [006,009), etc. 
(1) The record of group A at 004 triggers the calculation of [000,003) for group A. 
(2) The record of group A at 006 triggers the calculation of [003,006) for group A. 
(3) The record of group B at 007 triggers the calculation of [003,006) for group B.

If 'keyColumn' is specified, 'timeColumn' values must be increasing within each group and does not have to be increasing across groups. If 'keyColumn' is not specified, 'timeColumn' values must be increasing. Otherwise unexpected results may occur. 

#### 1.3.6 updateTime

The following 2 examples illustrate the role of 'updateTime'. 

First, create a stream table "trades" and insert 10 records:
```
share streamTable(1000:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as trades
insert into trades values(2018.10.08T01:01:01.785,`A,10)
insert into trades values(2018.10.08T01:01:02.125,`B,26)
insert into trades values(2018.10.08T01:01:10.263,`B,14)
insert into trades values(2018.10.08T01:01:12.457,`A,28)
insert into trades values(2018.10.08T01:02:10.789,`A,15)
insert into trades values(2018.10.08T01:02:12.005,`B,9)
insert into trades values(2018.10.08T01:02:30.021,`A,10)
insert into trades values(2018.10.08T01:04:02.236,`A,29)
insert into trades values(2018.10.08T01:04:04.412,`B,32)
insert into trades values(2018.10.08T01:04:05.152,`B,23);
```

- Do not specify 'updateTime':
```
output1 = table(10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
agg1 = createTimeSeriesAggregator("agg1",60000, 60000, <[sum(volume)]>, trades, output1, `time, false,`sym, 50,,false)
subscribeTable(, "trades", "agg1",  0, append!{agg1}, true)

sleep(10)

select * from output1;
```

time                    |sym| sumVolume
----------------------- |---| ------
2018.10.08T01:02:00.000 |A   |38    
2018.10.08T01:03:00.000 |A   |25    
2018.10.08T01:02:00.000 |B   |40   
2018.10.08T01:03:00.000 |B   |9   

- Set updateTime=1000:
```
output2 = keyedTable(`time`sym,10000:0, `time`sym`sumVolume, [TIMESTAMP, SYMBOL, INT])
agg2 = createTimeSeriesAggregator("agg2",60000, 60000, <[sum(volume)]>, trades, output2, `time, false,`sym, 50, 1000,false)
subscribeTable(, "trades", "agg2",  0, append!{agg2}, true)

sleep(2010)

select * from output2;
```

time                    |sym| sumVolume
----------------------- |---| ------
2018.10.08T01:02:00.000 |A   |38    
2018.10.08T01:03:00.000 |A   |25    
2018.10.08T01:02:00.000 |B   |40   
2018.10.08T01:03:00.000 |B   |9   
2018.10.08T01:05:00.000 |B   |55   
2018.10.08T01:05:00.000 |A   |29         

Next, we will explain the calculations triggered in the last window from 01:04:00.000 to 01:05:00.000. For simplicity, regarding the "time" column we ignore the part of "2018.10.08T" and only use the "hour:minute:second.millisecond" part. 

(1) At 01:04:04.236, 2000 milliseconds after the first record of group A arrived, a group A calculation is triggered. The result (01:05:00.000, `A, 29) is written to the output table. 

(2) The record of group B at 01:04:05.152 is the first record after the small window of [01:04:04.000, 01:04:05.000) that contains the group B record at 01:04:04.412. It triggers a group B calculation. The result (01:05:00.000,"B",32) is written to the output table. 

(3) 2000 milliseconds later, at 01:04:07.152, as the B group record at 1:04:05.152 has not been used in a calculation, a group B calculation is triggered. The result is (01:05:00.000,"B",55). As the output table's keys are columns 'time' and 'sym', the record of (01:05:00.000,"B",32) in the output table is updated and becomes (01:05:00.000,"B",55). 

## 2. Filtering the streaming data source

When using function `subscribeTable`, we can use parameter 'handle' to filter the subscribed streaming data.

In the following example, voltage and current data is uploaded to a stream table in real time. Records with voltage<=122 or current=NULL need to be filtered out before entering the aggregator. 

```
share streamTable(1000:0, `time`voltage`current, [TIMESTAMP, DOUBLE, DOUBLE]) as electricity
outputTable = table(10000:0, `time`avgVoltage`avgCurrent, [TIMESTAMP, DOUBLE, DOUBLE])

def append_after_filtering(inputTable, msg){
	t = select * from msg where voltage>122, isValid(current)
	if(size(t)>0){
		insert into inputTable values(t.time,t.voltage,t.current)		
	}
}
electricityAggregator = createTimeSeriesAggregator("electricityAggregator", 6, 3, <[avg(voltage), avg(current)]>, electricity, outputTable, `time, , , 2000)
subscribeTable(, "electricity", "avgElectricity", 0, append_after_filtering{electricityAggregator}, true)

def writeData(t, n){
        timev = 2018.10.08T01:01:01.001 + timestamp(1..n)
        voltage = 120+1..n * 1.0
        current = take([1,NULL,2]*0.1, n)
        insert into t values(timev, voltage, current);
}
writeData(electricity, 10);
```

Records in the stream table:
```
select * from electricity;
```
time	|voltage	|current
---|---|---
2018.10.08T01:01:01.002	|121	|0.1
2018.10.08T01:01:01.003	|122	|
2018.10.08T01:01:01.004	|123	|0.2
2018.10.08T01:01:01.005	|124	|0.1
2018.10.08T01:01:01.006	|125	|
2018.10.08T01:01:01.007	|126	|0.2
2018.10.08T01:01:01.008	|127	|0.1
2018.10.08T01:01:01.009	|128	|
2018.10.08T01:01:01.010	|129	|0.2
2018.10.08T01:01:01.011	|130	|0.1

The aggregation results:
```
select * from outputTable;
```
time	|avgVoltage |avgCurrent
---|-----|---
2018.10.08T01:01:01.006	|123.5 |0.15
2018.10.08T01:01:01.009	|125  |0.15

As the records with voltage<=122 or electric=NULL have been filtered, the first window [000,003) has no records and therefore no calculation is triggered for this window. 

## 3. Aggregator-related functions

- To get a list of existing aggregators, use function [`getAggregatorStat`](http://www.dolphindb.com/help/getAggregatorStat.html)

- To get the handle of an aggregator, use function [`getAggregator`](http://www.dolphindb.com/help/getAggregator.html)

- To delete an aggregator, use function [`dropAggregator`](http://www.dolphindb.com/help/dropAggregator.html)

