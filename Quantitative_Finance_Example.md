# Quantitative Finance Examples with DolphinDB

It is recommended to write DolphinDB script in DolphinDB GUI. Please download [DolphinDB GUI](https://www.dolphindb.com/downloads.html) and refer to the DolphinDB GUI Tutorial if necessary. 

## 1. Storage Structure of DolphinDB

DolphinDB uses the embedded distributed file system to implement database storage and transactions. Data in DolphinDB is organized and managed in partitions. The metadata of the partitions (such as the version chain, size, location, etc. of each partition) is stored in controller nodes, whereas the partitions are stored in data nodes. Each partition can have multiple replicas and they may be stored on multiple servers. DolphinDB guarantees strong consistency and data integrity through the transaction mechanism and the two-phase commit protocol. For external users, these mechanisms are completely transparent. 

DolphinDB is a columnar database and each column of a partition is stored as a file. The compression algorithm uses the LZ4 method which can achieve a lossless compression ratio of 20% or lower for high frequency data. 

The smallest unit of data loaded into memory is a column of a partition. A partitioning column in DolphinDB is similar to an index in other databases. If the partitioning column is included in at least one of the filtering conditions of a query, the SQL engine can quickly locate the relevant partitions without scanning the entire table.

For optimal performance, data should be distributed evenly across partitions. For that purpose DolphinDB offers 5 partition schemes: VALUE, RANGE, HASH, LIST and COMPO (up to 3 levels). For high frequency data, a COMPO paritition scheme with VALUE partition on date and RANGE or HASH partition on security ticker is the most frequently used partition scheme. The following example creates a distributed database. 
```
login(`admin, `123456)
db1 = database("", VALUE, 2020.01.01..2020.12.31)
db2 = database("", HASH,[SYMBOL,3])
db = database("dfs://futures",COMPO, [db1,db2])
colNames=`instrument`tradingday`calendarday`time`lastp`volume`openinterest`turnover`ask1`asksz1`bid1`bidsz1
colTypes=[SYMBOL,DATE,DATE,TIME,DOUBLE,INT,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,INT]
t=table(1:0,colNames,colTypes)
db.createPartitionedTable(t,`tick,`tradingday`instrument)
```
Please note that authorization is required to create or access distributed databases and tables. The default username and password are "admin" and "123456" respectively in this tutorial. In all following examples we will skip the login step. 

After the data is written to the database, the directory and data files of the database are as follows:
```
[dolphindb@localhost futures]$ tree
.
├── 20200101
│   ├── Key0
│   │   ├── chunk.dict
│   │   └── tick
│   │       ├── ask1.col
│   │       ├── asksz1.col
│   │       ├── bid1.col
│   │       ├── bidsz1.col
│   │       ├── calendarday.col
│   │       ├── instrument.col
│   │       ├── lastp.col
│   │       ├── openinterest.col
│   │       ├── time.col
│   │       ├── tradingday.col
│   │       ├── turnover.col
│   │       └── volume.col
│   ├── Key1
│   │   ├── chunk.dict
│   │   └── tick
│   │       ├── ask1.col
│   │       ├── asksz1.col
│   │       ├── bid1.col
│   │       ├── bidsz1.col
│   │       ├── calendarday.col
│   │       ├── instrument.col
│   │       ├── lastp.col
│   │       ├── openinterest.col
│   │       ├── time.col
│   │       ├── tradingday.col
│   │       ├── turnover.col
│   │       └── volume.col
│   └── Key2
│       ├── chunk.dict
│       └── tick
│           ├── ask1.col
│           ├── asksz1.col
│           ├── bid1.col
│           ├── bidsz1.col
│           ├── calendarday.col
│           ├── instrument.col
│           ├── lastp.col
│           ├── openinterest.col
│           ├── time.col
│           ├── tradingday.col
│           ├── turnover.col
│           └── volume.col
├── 20200102
│   ├── Key0
...
├── dolphindb.lock
├── domain
└── tick.tbl

```
Each level of the partition corresponds to a level of subdirectories. For example, the subdirectories 20200101, 20200102 ...... are the VALUE partitions and Key0, Key1 and Key2 are the HASH partitions. Each column in the table is stored as a .col file, such as ask1.col, bid1.col, etc.

## 2. Database Design for market data

For optimal performance, data should be distributed evenly across partitions and the size of raw data (before compression) of each partition should be around 100MB. As the smallest unit of data loaded into memory is a column of a partition, if the partition size is too large, a query may load too much unrelevant data into memory. If the partition size is too small, a query may need to work with too many small data files and drag down performance. 

>- Do all partitions have to be exactly 100MB for optimal performance? No. It should be fine as long as the partition size is not too small (smaller than 10MB) or too large (larger than 1G). If there are a lot of columns in a table and only a small subset of them are used in most queries, the partitions can be made larger than 100MB. 

High frequency data can usually be partitioned with a COMPO scheme on date and security ticker:
(1) For date, in most cases we can use VALUE partition.   
(2) For security ticker, we can use RANGE or HASH partitions. In most developed markets, liquid securities tend to have consistently more quotes and trades than illiquid securities. For these markets we can use the data of one day or a few days as a sample to specify multiple security ticker ranges (with function `cutPoints`) so that each range has similar number of records. For details please refer to the example in section 3.  

Market data include end of day data, level 1, level 2 or level 3 high frequency data, etc. As the data of different categories are of different orders of magnitude, we should use different partitioning arrangements for these data. 

## 3. Import Historical Data

You may have a large number of high frequency data files. For example, quite often the quotes or trades data in each day is saved as a CSV file. If all the high frequency data files are stored in the same directory, we can use the following script to create a partitioned database in DolphinDB and load the data files into the database. Suppose for a typical day the quotes data is about 8GB and trades data is about 2GB, we can create a partitioned database with a COMPO partition. The first level of partition is a VALUE partition on date and the second level is a RANGE partition with 50 partitions on stock symbols.

It is critically important to choose an appropriate partitioning arrangement to ensure optimal performance for queries. For more details please refer to [DolphinDB Partitioned Database Tutorial](database.md). 

```
DATA_DIR="/hdd/HFdata/"
t=loadText(DATA_DIR + "EQY_US_ALL_NBBO_20161024.csv")
t1=select count(*) as ct from t group by Symbol order by Symbol
partitions = cutPoints(exec Symbol from t1, 50, exec ct from t1)
partitions[size(partitions)-1]=`ZZZZZ

dbDate = database("", VALUE, 2020.01.01..2025.12.31)
dbSymbol = database("", RANGE, partitions)
db = database("dfs://HF", COMPO, [dbDate, dbSymbol])

//Please change dataDir to your directory
dataDir="/hdd/hdd1/data/HFTextFiles/"

def importTxtFiles(dataDir, db){
    dataFiles = exec filename from files(dataDir) where isDir=false
    for(f in dataFiles){
        loadTextEx(dbHandle=db, tableName=`quotes, partitionColumns=`Date`Symbol, filename=dataDir+f)
    }
}
importTxtFiles(dataDir, db);
```
Please note that here we didn't specify the schema of the database table as DolphinDB can automatically determine the schema based on a random sample of the data file. We recommend that you load a day's data and then check if the automatically determined schema is correct. If not, then you can retrieve the schema with function `extractTextSchema`, revise the schema with SQL update statement and then specify the parameter 'schema' in function `loadTextEx'. 


## 4. Working with Historical Data 

### 4.1 SQL Queries

Load the metadata of table 'quotes' and 'trades' into memory:
```
db = database("dfs://HF")
quotes = loadTable(db, `quotes);
trades = loadTable(db, `trades);
```
Calculate the average bid-ask spread of a stock every minute in a day and plot the result:
```
avgSpread = select max((Offer_Price-Bid_Price)/(Offer_Price+Bid_Price)*2) as avgSpread from quotes where Date=2016.10.24, Symbol=`AAPL, Time between 09:30:00.000000000 : 15:59:59.999999999, Offer_Price>=Bid_Price group by minute(Time) as minute
plot(avgSpread.avgSpread, avgSpread.minute, "Average bid-ask spread per minute")
```

### 4.2 'context by' Clause for Panel Data

The 'context by' clause is an extension of standard SQL by DolphinDB that significantly simplifies panel data operations. 

'context by' is similar to 'group by' as both conducts calculations within each group. Their differences are:
- For each group, 'group by' returns one row whereas 'context by' returns the same number of rows as the group. 
- 'group by' can only be used with aggregate functions whereas 'context by' can be used with aggregate functions, moving window functions or cumulative functions. 

Calculate the maximum trading volume for selected stocks and days in the previous 20 transactions:
```
t = select Symbol, Date, Time, mmax(Trade_Volume, 20) as volume_mavg20 from trades where Date=2016.10.24, Symbol in `AAPL`NFLX context by Symbol
```
Calculate the maximum trading volume up to the current moment for selected stocks and days:
```
t = select Symbol, Date, Time, cummax(Trade_Volume) as volume_cummax from trades where Date=2016.10.24, Symbol in `AAPL`NFLX context by Symbol, Date
```
Calculate the maximum trading volume for selected stocks and days and assign the result to each row in the input:
```
t = select Symbol, Date, Time, max(Trade_Volume) as volume_dailyMax from trades where Date=2016.10.24, Symbol in `AAPL`NFLX context by Symbol, Date
```

Nested moving window functions:
```
t=select Symbol, Date, Time, mcorr(mavg(Bid_Size,100), mavg(Offer_Size,100), 60) from quotes where Date=2016.10.24, Symbol=`AAPL, Time between 09:30:00.000000000 : 15:59:59.999999999 context by Symbol order by Symbol, Date, Time
```

### 4.3 'pivot by' Clause

The 'pivot by' clause is an extension of standard SQL by DolphinDB to generate a pivot table. It can be used together with an aggregate function. 
```
select sum(Trade_Volume) as Volume from trades where Date=2016.10.24, Symbol in `DAL`AAL`UAL`LUV`JBLU, Time between 09:30:00.000000000 : 15:59:59.999999999 pivot by minute(Time) as minute, Symbol
```
The result is:
```
minute	AAL     DAL     JBLU    LUV     UAL
------  ------- ------  ------- ------  ------
09:30m	214,978	77,439	152,927	88,763	5,001
09:31m	20,950	42,583	19,134	15,255	52,307
09:32m	68,403	71,521	23,395	25,780	28,131
09:33m	27,260	62,254	8,807	29,488	20,510
09:34m	37,784	32,374	22,429	43,823	12,411
09:35m	12,704	19,616	7,254	28,472	32,387
09:36m	22,285	40,953	64,316	25,013	20,959
09:37m	21,865	25,745	22,111	19,484	10,913
09:38m	47,561	42,527	16,508	19,974	32,019
09:39m	30,173	36,081	20,173	46,281	20,150
......
```


### 4.4 Map-Reduce

To calculate OHLC bars for a day:
```
minuteBar = select first(Trade_Price) as open, max(Trade_Price) as high, min(Trade_Price) as low, last(Trade_Price) as last, sum(Trade_Volume) as volume from trades where Date=2016.10.24 group by Symbol, Date, minute(Time) as minute;
```

To calculate OHLC bars for a month and save the results to the database, we can use the map-reduce function `mr`. 
```
model=select top 1 Symbol, Date, minute(Time) as minute, open, high, low, last, Trade_Volume as volume from trades where Date=2016.10.24, Symbol=`XOM
if(existsTable("dfs://HF", "minuteBar"))
	db.dropTable("minuteBar")
db.createPartitionedTable(model, "minuteBar", `Date`Symbol)

def saveMinuteBar(t){
	minuteBar=select first(Trade_Price) as open, max(Trade_Price) as high, min(Trade_Price) as low, last(Trade_Price) as last, sum(Trade_Volume) as volume from t where Time between 09:30:00.000000000 : 15:59:59.999999999 group by Symbol, Date, minute(Time) as minute
	loadTable("dfs://HF", "minuteBar").append!(minuteBar)
	return minuteBar.size()
}

ds = sqlDS(<select Symbol, Date, Time, Trade_Price, Trade_Volume from trades where Date between 2016.10.01 : 2016.10.31>)
mr(ds,saveMinuteBar,+)
```

### 4.5 asof join and window join

Asof join (function `aj`) and window join (function `wj`) are frequently used to calculate trading costs. Trades and quotes are usually saved in different tables. For each stock, asof join gets the last quote before (and up to) each trade and window join conducts calculations on a specified window of quotes relative to each trade. Function `aj` is faster than the asof join function in pandas by about 200 times. 

In the following example, we calculate 2 measures of trading cost (in basis points) with asof join and window join, respectively. For window join, the average quote in the 100 milliseconds before each trade is used instead of the last quote for asof join. 
```
TC1 = select sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost from aj(trades, quotes, `Symbol`Time) where Time between 09:30:00.000000000 : 15:59:59.999999999 group by Symbol

TC2 = select sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost from pwj(trades, quotes, -100000000:0,<[avg(Offer_Price) as Offer_Price, avg(Bid_Price) as Bid_Price]>,`Symbol`Time) where Time between 09:30:00.000000000 : 15:59:59.999999999 group by Symbol
```

