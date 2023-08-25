# Data Migration: From SQL Server to DolphinDB

This tutorial introduces two methods for migrating from SQL Server to DolphinDB with a database example. Additionally, it compares the differences in performance and application between the two methods.

- [Data Migration: From SQL Server to DolphinDB](#data-migration-from-sql-server-to-dolphindb)
  - [Migration Methods](#migration-methods)
  - [Business Requirements](#business-requirements)
  - [Migration Steps](#migration-steps)
    - [Migrate With ODBC Plugin](#migrate-with-odbc-plugin)
    - [Migrate with DataX](#migrate-with-datax)
  - [Performance Comparison](#performance-comparison)

## Migration Methods

DolphinDB provides two migration tools:

- ODBC Plugin:

The Microsoft Open Database Connectivity (ODBC) interface is a C programming language interface that makes it possible for applications to access data from a variety of database management systems (DBMS). You can use the ODBC plugin to migrate data from SQL Server to DolphinDB.

See [DolphinDB ODBC Plugin](https://github.com/dolphindb/DolphinDBPlugin/blob/release200/odbc/README.md) for detailed instructions on the methods.

- DataX:

DataX is a platform for offline data synchronization between various heterogeneous data sources. As a data synchronization framework, DataX abstracts the synchronization of different data sources as a Reader plugin for reading data from the data source and a Writer plugin for writing data to the target end. It implements efficient data synchronization between various heterogeneous data sources.

DolphinDB provides open-source drivers based on DataXReader and DataXWriter. Combined with the reader plugin of DataX, DolphinDBWriter can synchronize data from different sources to DolphinDB. Users can include the DataX driver package in their Java projects and develop data migration software from SQL Server data sources to DolphinDB.

| Method 	| Data Write Performance 	| High Availability 	|
|---	|---	|---	|
| ODBC Plugin 	| high 	| supported 	|
| DataX Driver 	| medium 	| not supported 	|

## Business Requirements

DolphinDB provides various data migration methods to fully or incrementally synchronize massive data from multiple data sources.

We have tick data of 10 years stored in SQL Server:

|TradeDate| OrigTime| SendTime| RecvTime| LocalTime| ChannelNo| MDStreamID| ApplSeqNum| SecurityID| SecurityIDSource |Price |OrderQty| TransactTime| Side| OrderType| ConfirmID| Contactor| ContactInfo |ExpirationDays| ExpirationType|
| ------- | ------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | ---------|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3090000|	2013|	11|	1	|300104	|102|	2.74|	911100|	2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3130000|	2023|	11|	1|	159919|	102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL	|0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	2	|159919|	102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2	|0.0|	NULL|	NULL	|0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	3	|159919|	102	|3.002|	100|	2019-01-02 09:15:00.000|	1	|2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	4	|159919	|102	|3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL	|0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	5	|159919	|102|	3.002|	100	|2019-01-02 09:15:00.000|	1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2023|	11|	6|	159919|	102	|3.002|	100|	2019-01-02 09:15:00.000	|1|	2|	0.0	|NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	2|	002785|	102|	10.52|	664400|	2019-01-02 09:15:00.000|	1	|2|	0.0|	NULL|	NULL|	0	|0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	3|	200613|	102|	5.12|	4400	|2019-01-02 09:15:00.000|	2|	2|	0.0|	NULL|	NULL|	0|	0|
|2019-01-02|	09:15:00.0000000|	09:15:00.0730000|	09:15:00.3030000|	09:15:00.3140000|	2013|	11|	4|	002785|	102	|10.52|	255500|	2019-01-02 09:15:00.000|	1|	2|	0.0|	NULL|	NULL|	0	|0|

To facilitate the integration with data from other sources, the table schema is modified as shown below:

| SQL Server Column Name 	| Description 	| Data Type 	| DolphinDB Column Name 	| Description 	| Data Type 	|
|---	|---	|---	|---	|---	|---	|
| tradedate 	| trade date 	| date 	|  	|  	|  	|
| OrigTime 	| record creation time 	| time(7) 	|  	|  	|  	|
| SendTime 	| record send time 	| time(7) 	|  	|  	|  	|
| Recvtime 	| record receive time 	| time(7) 	|  	|  	|  	|
| LocalTime 	| local time 	| time(7) 	| LocalTime 	| local time 	| TIME 	|
| ChannelNo 	| channel number 	| int 	| ChannelNo 	| channel number 	| INT 	|
| MDStreamID 	| identifier of the price stream 	| int 	| MDStreamID 	| identifier of the price stream 	| INT 	|
| ApplSeqNum 	| application sequence number 	| bigint 	| ApplSeqNum 	| application sequence number 	| LONG 	|
| SecurityID 	| security ID 	| varchar(255) 	| SecurityID 	| security ID 	| SYMBOL 	|
| SecurityIDSource 	| security ID source 	| int 	| SecurityIDSource 	| security ID source 	| INT 	|
| Price 	| order price 	| float 	| Price 	| order price 	| DOUBLE 	|
| OrderQty 	| order quantity 	| int 	| OrderQty 	| order quantity 	| INT 	|
| TransactTime 	| order time 	| datetime 	| TransactTime 	| order time 	| TIMESTAMP 	|
| Side 	| buy or sell order 	| varchar(255) 	| Side 	| buy or sell order 	| SYMBOL 	|
| OrderType 	| order type 	| varchar(255) 	| OrderType 	| order type 	| SYMBOL 	|
| ConfirmID 	| confirm ID 	| varchar(255) 	|  	|  	|  	|
| Contactor 	| contactor 	| varchar(255) 	|  	|  	|  	|
| ContactInfo 	| contact information 	| varchar(255) 	|  	|  	|  	|
| ExpirationDays 	| expiration days 	| int 	|  	|  	|  	|
| ExpirationType 	| expiration type 	| varchar(255) 	|  	|  	|  	|
|  	|  	|  	| BizIndex 	| business index 	| LONG 	|
|  	|  	|  	| DataStatus 	| data status 	| INT 	|
|  	|  	|  	| SeqNo 	| sequence number 	| LONG 	|
|  	|  	|  	| Market 	| market 	| SYMBOL 	|


This example uses:

- DolphinDB: DolphinDB_Linux64_V2.00.8.6
- SQL Server: Microsoft SQL Server 2017 (RTM-CU31) (KB5016884) - 14.0.3456.2 (X64)


## Migration Steps

### Migrate With ODBC Plugin

#### Install ODBC Driver

In this example, the operating system where DolphinDB server is deployed is ubuntu22.04.

(1) Run the following commands in Terminal to install the freeTDS library, the unixODBC library, and the SQL Server ODBC driver.

```
# install freeTDS
apt install -y freetds

# install unixODBC library
apt-get install unixodbc unixodbc-dev

# install SQL Server ODBC driver
apt-get install tdsodbc
```

(2) Add the IP and port of SQL Server in */etc/freetds/freetds.conf*:

```
[sqlserver]
host = 127.0.0.1
port = 1433
```

(3) Configure */etc/odbcinst.ini*:

```
[SQLServer]
Description = ODBC for SQLServer
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
FileUsage = 1
```

For CentOS, follow the steps below:

(1) Run the following commands in the terminal to install the freeTDS library and the unixODBC library.

```
# install freeTDS
yum install -y freetds

# install unixODBC library
yum install unixODBC-devel
```

(2) Add the IP and port of SQL Server in */etc/freetds.conf*.

(3) Configure */etc/odbcinst.ini*:

```
[SQLServer]
Description = ODBC for SQLServer
Driver = /usr/lib64/libtdsodbc.so.0.0.0
Setup = /usr/lib64/libtdsodbc.so.0.0.0
FileUsage = 1
```

#### Synchronize Data

(1) Run the following command to load the ODBC plugin:

```
loadPlugin("/home/Linux64_V2.00.8/server/plugins/odbc/PluginODBC.txt")
```

(2) Establish a connection to SQL Server:

```
conn =odbc::connect("Driver={SQLServer};Servername=sqlserver;Uid=sa;Pwd=DolphinDB;database=historyData;;");
```

(3) Synchronize data:

```
def transform(mutable msg){
	msg.replaceColumn!(`LocalTime,time(temporalParse(msg.LocalTime,"HH:mm:ss.nnnnnn")))
    msg.replaceColumn!(`Price,double(msg.Price))
	msg[`SeqNo]=int(NULL)
	msg[`DataStatus]=int(NULL)
	msg[`BizIndex]=long(NULL)
	msg[`Market]="SZ"
	msg.reorderColumns!(`ChannelNo`ApplSeqNum`MDStreamID`SecurityID`SecurityIDSource`Price`OrderQty`Side`TransactTime`OrderType`LocalTime`SeqNo`Market`DataStatus`BizIndex)
    return msg
}

def synsData(conn,dbName,tbName){
    odbc::query(conn,"select ChannelNo,ApplSeqNum,MDStreamID,SecurityID,SecurityIDSource,Price,OrderQty,Side,TransactTime,OrderType,LocalTime from data",loadTable(dbName,tbName),100000,transform)
}

submitJob("synsData","synsData",synsData,conn,dbName,tbName)
```

As the output shows, the elapsed time is around 122 seconds.

```
startTime                      endTime
2022.11.28 11:51:18.092        2022.11.28 11:53:20.198
```

Incremental synchronization can be performed with DolphinDB built-in function scheduleJob. For example, set a daily scheduled job to synchronize data of the previous day at 00:05:

```
def synchronize(){
	login(`admin,`123456)
    conn =odbc::connect("Driver={SQLServer};Servername=sqlserver;Uid=sa;Pwd=DolphinDB;database=historyData;;")
    sqlStatement = "select ChannelNo,ApplSeqNum,MDStreamID,SecurityID,SecurityIDSource,Price,OrderQty,Side,TransactTime,OrderType,LocalTime from data where TradeDate ='" + string(date(now())-1) + "';"
    odbc::query(conn,sqlStatement,loadTable("dfs://TSDB_Entrust",`entrust),100000,transform)
}
scheduleJob(jobId=`test, jobDesc="test",jobFunc=synchronize,scheduleTime=00:05m,startDate=2022.11.11, endDate=2023.01.01, frequency='D')
```

Note: To avoid parsing failure of the scheduled job, add `preloadModules=plugins::odbc` to the configuration file before startup.

### Migrate with DataX

#### Deploy DataX

Download [DataX](https://datax-opensource.oss-cn-hangzhou.aliyuncs.com/202210/datax.tar.gz) and extract it to a custom directory.

#### Deploy DataX-DolphinDBWriter Plugin

Copy all the contents of the *./dist/dolphindbwriter* directory from the [DataX-Writer project](https://github.com/dolphindb/datax-writer) to the *DataX/plugin/writer* directory.

#### Synchronize Data

(1) The configuration file synchronization.json is placed in the data/job directory:

```
{
    "core": {
        "transport": {
            "channel": {
                "speed": {
                    "byte": 5242880
                }
            }
        }
    },
    "job": {
        "setting": {
            "speed": {
                "byte":10485760
            }
        },
        "content": [
            {
                "reader": {
                    "name": "sqlserverreader",
                    "parameter": {
                        "username": "sa",
                        "password": "DolphinDB123",
                        "column": [
                            "ChannelNo","ApplSeqNum","MDStreamID","SecurityID","SecurityIDSource","Price","OrderQty","Side","TransactTime","OrderType","LocalTime"
                        ],
                        "connection": [
                            {
                                "table": [
                                    "data"
                                ],
                                "jdbcUrl": [
                                    "jdbc:sqlserver://127.0.0.1:1433;databasename=historyData"
                                ]
                            }
                        ]
                    }
                },
                "writer": {
                    "name": "dolphindbwriter",
                    "parameter": {
                        "userId": "admin",
                        "pwd": "123456",
                        "host": "127.0.0.1",
                        "port": 8888,
                        "dbPath": "dfs://TSDB_Entrust",
                        "tableName": "entrust",
                        "batchSize": 100000,
                        "saveFunctionDef": "def customTableInsert(dbName, tbName, mutable data) {data.replaceColumn!(`LocalTime,time(temporalParse(data.LocalTime,\"HH:mm:ss.nnnnnn\")));data.replaceColumn!(`Price,double(data.Price));data[`SeqNo]=int(NULL);data[`DataStatus]=int(NULL);data[`BizIndex]=long(NULL);data[`Market]=`SZ;data.reorderColumns!(`ChannelNo`ApplSeqNum`MDStreamID`SecurityID`SecurityIDSource`Price`OrderQty`Side`TransactTime`OrderType`LocalTime`SeqNo`Market`DataStatus`BizIndex);pt = loadTable(dbName,tbName);pt.append!(data)}",
                        "saveFunctionName" : "customTableInsert",
                        "table": [
                            {
                                "type": "DT_INT",
                                "name": "ChannelNo"
                            },
                            {
                                "type": "DT_LONG",
                                "name": "ApplSeqNum"
                            },
                            {
                                "type": "DT_INT",
                                "name": "MDStreamID"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "SecurityID"
                            },
                            {
                                "type": "DT_INT",
                                "name": "SecurityIDSource"
                            },
                            {
                                "type": "DT_DOUBLE",
                                "name": "Price"
                            },
                            {
                                "type": "DT_INT",
                                "name": "OrderQty"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "Side"
                            },
                            {
                                "type": "DT_TIMESTAMP",
                                "name": "TransactTime"
                            },
                            {
                                "type": "DT_SYMBOL",
                                "name": "OrderType"
                            },
                            {
                                "type": "DT_STRING",
                                "name": "LocalTime"
                            }
                        ]

                    }
                }
            }
        ]
    }
}
```

(2) Run the following command in the Linux terminal to execute the synchronization task:

```
cd ./DataX/bin/
python DataX.py ../job/synchronization.json
```

The log is displayed as follows:

```
Start Time               : 2022-11-28 17:58:52
End Time                 : 2022-11-28 18:02:24
Elapsed Time             :                212s
Average Flow             :            3.62MB/s
Write Speed              :          78779rec/s
Total Read Records       :            16622527
Total Failed Attempts    :                   0
```

Similarly, you can add the “where” condition to the “reader” part of *synchronization.json* to incrementally synchronize the selected data. For example, specify a “where” filter on the trading date as shown below, and then every time when the synchronization task is executed, only the data filtered in the where condition (i.e., data of the previous day) is synchronized.

```
"reader": {
                    "name": "sqlserverreader",
                    "parameter": {
                        "username": "sa",
                        "password": "DolphinDB123",
                        "column": [
                            "ChannelNo","ApplSeqNum","MDStreamID","SecurityID","SecurityIDSource","Price","OrderQty","Side","TransactTime","OrderType","LocalTime"
                        ],
                        "connection": [
                            {
                                "table": [
                                    "data"
                                ],
                                "jdbcUrl": [
                                    "jdbc:sqlserver://127.0.0.1:1433;databasename=historyData"
                                ]
                            }
                        ]
                        "where":"TradeDate=(select CONVERT ( varchar ( 12) , dateadd(d,-1,getdate()), 102))"
                    }
                }
```

## Performance Comparison

The table shows the time consumed by data migration:

| ODBC plugin 	| DataX 	|
|---	|---	|
| 122s 	| 212s 	|

We can see that the ODBC plugin demonstrates better performance than DataX. This performance advantage becomes evident when there is a larger amount of data (especially with more tables involved). Both methods support full or incremental synchronization, but the ODBC plugin is fully integrated with DolphinDB, while DataX requires deployment and JSON configurations for migration. Additionally, if the migrated data does not require further processing, migration with DataX requires configuring a JSON file for each table, whereas the ODBC plugin only needs modification on the table names.
