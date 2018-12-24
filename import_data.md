# Import Data to DolphinDB

When enterprises use big data analytics platforms, the first step is to migrate large amounts of data from multiple data sources to big data platforms. DolphinDB provides the following 3 ways to import data:

- Import from CSV files
- Import from HDF5 files
- Import via ODBC interface

#### 1. DolphinDB database basic concepts and features

Data in DolphinDB are saved as structured tables. There are 3 types of tables based on storage location:

- In-memory table: Data are only stored in the memory of a data node. The access speed is the fastest, but it does not exist if the data node is shut down.
- Local disk table: Data are saved on the local disk. Even if the node is closed, it can be easily loaded from the disk to the memory through a DolphinDB script.
- Distributed Tables: Data is distributed across different nodes. 

A table can be either a partitioned table, or a regular table (nonpartitioned table).

In the traditional database system, each table in the same database can have its own partitioning scheme. In DolphinDB, a database can only use one partitioning scheme. This means that all tables in the same database must use the same partitioning scheme.

#### 2. Import from CSV files

Data transfer through CSV files is a general data migration method, which is simple and easy to operate. DolphinDB provides 3 functions for this purpose: `loadText`(http://www.dolphindb.com/cn/help/index.html?loadText.html)，
`ploadText`(https://www.dolphindb.com/help/index.html?ploadText.html)，
`loadTextEx`(https://www.dolphindb.com/help/index.html?loadTextEx.html). 

- `loadText`: read a text file into memory as a DolphinDB table.
- `ploadText`: load a text file into memory in parallel as an in-memory partitioned table. Compared to `loadText`, `ploadText` is much faster but uses twice as much memory.
- `loadTextEx`: convert a text file to a distributed table in a DolphinDB database, then load the table's metadata into memory.

We use file [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv) to show how to use function `loadText` and `loadTextEx`.

#### 2.1. `loadText` 

`loadText` has 3 parameters:
 - "filename" is the input file name.
 - "delimiter"(optional) is the column separator. The default value is "," for csv files.
 - "schema"(optional) is a table that specifies the data type of each column of the imported table. For example:

name|type
---|---
timestamp|SECOND
ID|INT
qty|INT
price|DOUBLE

The simplest way to import data:

```
dataFilePath = "/home/data/candle_201801.csv"
tmpTB = loadText(dataFilePath)
```

When loading a text file, the system determines the data type of each column based on a random sample of rows. This convenient feature may not always accurately determine the data types of all columns.
For example, the volume column is recognized as INT type, but we would like it to be LONG type. In this case, we need to modify the "schema" table. We can use following script:
```
nameCol = `symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
typeCol = [SYMBOL,SYMBOL,INT,DATE,DATE,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,LONG]
schemaTb = table(nameCol as name,typeCol as type)
```

For a table with many columns, it could be time-consuming to write such script. To streamline the process, DolphinDB offers function `extractTextSchema`(https://www.dolphindb.com/cn/help/index.html?extractTextSchema.html) to extract table schema of a text file. We just need to modify the data type of a few columns of the schema table.

```
dataFilePath = "/home/data/candle_201801.csv"
schemaTb=extractTextSchema(dataFilePath)
update schemaTb set type=`LONG where name=`volume        
tt=loadText(dataFilePath,,schemaTb)
```
#### 2.2. `ploadText`

Function `ploadText` can quickly load large files. It is designed to utilize multiple CPU cores to load files in parallel. The degree of parallelism depends on the number of CPU cores in the server and configuration parameter "localExecutors" of the nodes.

First, we generate a 4GB CSV file with the script below:
```
	filePath = "/home/data/testFile.csv"
	appendRows = 100000000
	dateRange = 2010.01.01..2018.12.30
	ints = rand(100, appendRows)
	symbols = take(string('A'..'Z'), appendRows)
	dates = take(dateRange, appendRows)
	floats = rand(float(100), appendRows)
	times = 00:00:00.000 + rand(86400000, appendRows)
	t = table(ints as int, symbols as symbol, dates as date, floats as float, times as time)
	t.saveText(filePath)
```

The file is loaded by `loadText` and `ploadText` on a data node with a 4-core 8-hyperthreaded CPU.
```
timer loadText(filePath);
//Time elapsed: 39728.393 ms
timer ploadText(filePath);
//Time elapsed: 10685.838 ms
```

The result shows that `ploadText` is about 4 times as fast as `loadText`.

#### 2.3. `loadTextEx`

Function `loadText` imports the entire text file into memory. With a very large data file, server memory may become a bottleneck. For this, DolphinDB provides function `loadTextEx`(http://www.dolphindb.com/cn/help/index.html?loadTextEx.html). As it loads a partition into memory, it saves the partition to disk. In this way it greatly reduces memory requirements. 

First create a distributed table:
```
dataFilePath = "/home/data/candle_201801.csv"
tb = loadText(dataFilePath)
db=database("dfs://dataImportCSVDB",VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "tradingDay")
```

Then import the file into the distributed table:

```
loadTextEx(db, "cycle", "tradingDay", dataFilePath)
```

In data analysis, we first load the metadata of a partitioned table into memory with function `loadTable`. When a query is executed, DolphinDB will load the data into memory as needed.
```
tb = database("dfs://dataImportCSVDB").loadTable("cycle")
```
#### 3. Import data via HDF5 files

HDF5 is a more efficient binary data file format than CSV and is widely used in data analysis. DolphinDB supports importing data via HDF5 files.

DolphinDB uses [HDF5 plugin](https://github.com/dolphindb/DolphinDBPlugin/blob/master/hdf5/README.md) to import HDF5 files，the plugin provides the following files:

- hdf5::ls : List all Group and Dataset objects in an HDF5 file.

- hdf5::lsTable ：List all Dataset objects in an HDF5 file.

- hdf5::hdf5DS ：Return the metadata of the Dataset in an HDF5 file.

- hdf5::loadHdf5 ：Import an HDF5 file as an in-memory table.

- hdf5::loadHdf5Ex ：Import an HDF5 file as a partitioned table.

- hdf5::extractHdf5Schema ：Extract the table structure from an HDF5 file.

When calling the plugin method, we need to provide the namespace in front of the method. For example: `hdf5::loadHdf5`. To avoid using namespace, we can use the `use` keyword:
```
use hdf5
loadHdf5(filePath,tableName);
```

To use DolphinDB plugin, we first need to download HDF5 plugin (http://www.dolphindb.com/downloads/HDF5_V0.7.zip), then deploy the plugin to the node's plugins directory. Finally, use the following script to load the plugin:
```
loadPlugin("plugins/hdf5/PluginHdf5.txt")
```

Importing HDF5 files is similar to importing CSV files. For example, to import file candle_201801.h5 that contains a Dataset candle_201801, we can use the following script:
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
tmpTB = hdf5::loadHdf5(dataFilePath,datasetName)
```
To specify data types before importing, use `hdf5::extractHdf5Schema`.
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
schema=hdf5::extractHdf5Schema(dataFilePath,datasetName)
update schema set type=`LONG where name=`volume        
tt=hdf5::loadHdf5(dataFilePath,datasetName,schema)
```

If an HDFS5 file is very large relative to the server memory, we can use method `hdf5::loadHdf5Ex`.

First create a distributed table:
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
dfsPath = "dfs://dataImportHDF5DB"
tb = hdf5::loadHdf5(dataFilePath,datasetName)
db=database(dfsPath,VALUE,2018.01.01..2018.01.31)  
db.createPartitionedTable(tb, "cycle", "tradingDay")
```

Then import the HDF5 file with method `hdf5::loadHdf5Ex`:
```
hdf5::loadHdf5Ex(db, "cycle", "tradingDay", dataFilePath,datasetName)
```

#### 4. Import data via ODBC interface

DolphinDB supports ODBC interface to connect to third-party databases, and directly reads tables from the source database into a DolphinDB in-memory table.

DolphinDB provides [ODBC plugin] (https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md) for connecting to third-party data sources, which can be easily accessed from ODBC-supported databases and migrate data to DolphinDB.

The ODBC plugin provides the following 4 methods to manipulate data from third-party data sources:

- odbc::connect : open the connection.

- odbc::close : close the connection.

- odbc::query : execute a SQL statement and return DolphinDB in-memory table.

- odbc::execute : execute a SQL statement in a third-party database and return nothing.

Note that before using the ODBC plugin, you need to install the ODBC driver for the system. Please refer to the ODBC plugin tutorial (https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md).

As an example, we use ODBC plugin to onnect to the following MS SQL Server:
- Server：172.18.0.15
- Default Port：1433
- Account Name：sa
- Password：123456
- Database Name： SZ_TAQ

Table candle_201801 stores data for January 2018.

First, download the plugin and extract all the files in the plugins/odbc directory to the plugins/odbc directory of DolphinDB server. Use the following script for the plugin initialization:
```
// load plugin
loadPlugin("plugins/odbc/odbc.cfg")

// connect to SQL Server
conn=odbc::connect("Driver=ODBC Driver 17 for SQL Server;Server=172.18.0.15;Database=SZ_TAQ;Uid=sa;Pwd=123456;")
```

Next, create a distributed database:
```
// get the table structure from SQL Server as a template for the corresponding DolphinDB table
tb = odbc::query(conn,"select top 1 * from candle_201801")
db=database("dfs://dataImportODBC",VALUE,2018.01.01..2018.01.31)
db.createPartitionedTable(tb, "cycle", "tradingDay")
```
Lastly, import data from SQL Server and save as a DolphinDB partitioned table:
```
data = odbc::query(conn,"select * from candle_201801")
tb = database("dfs://dataImportODBC").loadTable("cycle")
tb.append!(data);
```
Importing data through ODBC is also a userful tool for data synchronization.

#### 5. Import financial data

The following example imports CSV files of daily K-line data for stocks in 10 years. The data are about 100GB and are stored in annual directories:
```
2008
    ---- 000001.csv
    ---- 000002.csv
    ---- 000003.csv
    ---- 000004.csv
    ---- ...
2009
...
2017
```

Each CSV file has the same structure:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/csvfile.PNG?raw=true)

#### 5.1. Partition Planning

Before importing data, we should plan how to partition the data. We need to determine the partitioning columns and the granularity of the partitions.

Columns that are commonly used in WHERE, GROUP BY, or CONTEXT BY are good candidates as partitioning columns. As most of the queries on financial data involve trading days and stock symbols, we can use `tradingDay` and `symbol` to form a COMPO partition. 

The time span of the data is 2008-2017, and we can use a value partition based on the year of the data. To leave room for new data, we can set the time span to 2008-2030.

```
yearRange =date(2008.01M + 12*0..22)
```

Since there are thousands of stock symbols, if we adopt a value partition on the stock symbols, we would have a large number of small partitions, each of which is only a few megabytes in size. When a distributed system executes a query, it divides the query into multiple subtasks and distributes them to different partitions. Too many partitions may result in too many tasks each of which may take extremely short time to execute. The system may take more time managing tasks than executing tasks. This is obviously suboptimal. 

Here we divide all stock symbols into 100 intervals. Each interval represents a partition. The size of each partition is about 100M. Considering that new stock symbols may be larger than the current maximum stock symbol, we add a stock symbol of 999999.

Use the following script to get the partition ranges of stock symbols:
```
// Traverse all the annual catalogs, to reorganize the stock code list, and divide into 100 intervals by cutPoint
symbols = array(SYMBOL, 0, 100)
yearDirs = files(rootDir)[`filename]
for(yearDir in yearDirs){
	path = rootDir + "/" + yearDir
	symbols.append!(files(path)[`filename].upper().strReplace(".CSV",""))
}
// Increase the expansion scope:：
symbols = symbols.distinct().sort!().append!("999999");
// Divided into 100 parts
symRanges = symbols.cutPoints(100)
```

Create a database and a partitioned table with a composite (COMPO) partition with the following script:

```
columns=`symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
types =  [SYMBOL,SYMBOL,INT,DATE,DATE,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,DOUBLE,LONG]

dbDate=database("", RANGE, yearRange)
dbID=database("", RANGE, symRanges)
db = database(dbPath, COMPO, [dbDate, dbID])

pt=db.createPartitionedTable(table(1000000:0,columns,types), tableName, `tradingDay`symbol)
```

Please do not write to the same partition from multiple tasks at the same time. In the example above, each task writes a year's data, so it is impossible to write to the same partition by multiple tasks.

#### 5.2. Import data
The main idea of the data import is very simple, i.e., to read and write all the CSV files one by one to the distributed database table `dfs://SAMPLE_TRDDB` through the circular directory tree, but there are still many potential problems that might be encountered during the data import process.

First, the data format of a column in the CSV file might be different from that in DolphinDB. For example, if a column in a CSV file is saved in a format such as "9390100000" indicating millisecond level time, it will be recognized as an integer. To convert it to millisecond level time, we need to use the temporal conversion function `datetimeParse` together with the formatting function `format`:

```
datetimeParse(format(time,"000000000"),"HHmmssSSS")
```
We need to import a large number of small files of about 5MB. A single-threaded loop operation takes a long time to finish. In order to fully utilize the cluster resources, we can divide the import task into multiple subtasks. Each subtask imports a year's data. The task queues sent to the nodes are executed in parallel. This process is implemented in the following two steps:

First, define a function to import all the files in the specified annual directory:
```
def loadCsvFromYearPath(path, dbPath, tableName){
	symbols = files(path)[`filename]
	for(sym in symbols){
		filePath = path + "/" + sym
		t=loadText(filePath)
		database(dbPath).loadTable(tableName).append!(select symbol, exchange,cycle, tradingDay,date,datetimeParse(format(time,"000000000"),"HHmmssSSS"),open,high,low,close,volume,turnover,unixTime from t )			
	}
}
```
Next, the function defined above is used with `submitJob`(https://www.dolphindb.com/help/submitJob.html) function and `rpc`(https://www.dolphindb.com/help/rpc.html) function. The tasks are submited to each node in the cluster to execute:
```
nodesAlias="NODE" + string(1..4)
years= files(rootDir)[`filename]

index = 0;
for(year in years){	
	yearPath = rootDir + "/" + year
	des = "loadCsv_" + year
	rpc(nodesAlias[index%nodesAlias.size()],submitJob,des,des,loadCsvFromYearPath,yearPath,dbPath,tableName)
	index=index+1
}
```

During the data import process, we can monitor the task status with `pnodeRun(getRecentJobs)`.

The script for this case can be downloaded from the Appendix.

#### 6. Appendix

CSV file [[click to download]] (https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv)

HDF5 file [Click to download] (https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.h5)

Complete script in examples [Click to download] (https://github.com/dolphindb/Tutorials_CN/blob/master/data/demoScript.txt)
