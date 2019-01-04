# Import Data to DolphinDB

DolphinDB provides the following 3 ways to import large amounts of data from multiple data sources: 

- Import from text files
- Import from HDF5 files
- Import via ODBC interface

#### 1. DolphinDB database basic concepts and features

Data in DolphinDB are saved as tables. There are 3 types of tables based on storage location:

- In-memory table: Data are stored in data node memory. It has the fastest access speed, but the data will be lost if the data node is shut down.
- Local disk table: Data are saved on the local disk.
- Distributed Tables: Data are distributed across the disks of different nodes. 

A table can be either a partitioned table, or a regular table (nonpartitioned table).

In the traditional database system, each table in the same database can have its own partitioning scheme. In DolphinDB, a database can only use one partitioning scheme. This means that all tables in the same database must share the same partitioning scheme.

#### 2. Import from text files

DolphinDB provides the following 3 functions to import data from text files: 
- [`loadText`](http://www.dolphindb.com/cn/help/index.html?loadText.html): read a text file into memory as a table.
- [`ploadText`](https://www.dolphindb.com/help/index.html?ploadText.html): load a text file into memory in parallel as an in-memory partitioned table. Compared to `loadText`, `ploadText` is much faster but uses twice as much memory.
- [`loadTextEx`](https://www.dolphindb.com/help/index.html?loadTextEx.html): convert a text file to a table in a partitioned database, then load the table's metadata into memory.

We use file [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv) to show how to use function `loadText` and `loadTextEx`.

#### 2.1. `loadText` 

`loadText` has 3 parameters:
 - "filename" is the input file name.
 - "delimiter"(optional) is the column separator. The default value is "," for CSV files.
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
tmpTB = loadText(dataFilePath);
```

When loading a text file, the system determines the data type of each column based on a random sample of rows. This convenient feature may not always accurately determine the data types of all columns.
For example, the volume column is recognized as INT type, but we would like it to be LONG type. In this case, we need to modify the "schema" table. We can use following script:
```
nameCol = `symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
typeCol = [SYMBOL,SYMBOL,INT,DATE,DATE,INT,DOUBLE,DOUBLE,DOUBLE,DOUBLE,INT,DOUBLE,LONG]
schemaTb = table(nameCol as name,typeCol as type);
```

For a table with many columns, it could be time-consuming to write such script. To streamline the process, DolphinDB offers function [`extractTextSchema`](https://www.dolphindb.com/en/help/index.html?extractTextSchema.html) to extract table schema of a text file. We just need to modify the data types of selected columns of the "schema" table.

```
dataFilePath = "/home/data/candle_201801.csv"
schemaTb=extractTextSchema(dataFilePath)
update schemaTb set type=`LONG where name=`volume        
tt=loadText(dataFilePath,,schemaTb);
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
	t.saveText(filePath);
```

The text file is loaded by `loadText` and `ploadText` on a data node with a 4-core 8-hyperthreaded CPU.
```
timer loadText(filePath);
Time elapsed: 39728.393 ms

timer ploadText(filePath);
Time elapsed: 10685.838 ms
```

The result shows that `ploadText` is about 4 times as fast as `loadText` with this configuration.

#### 2.3. `loadTextEx`

Function `loadText` imports the entire text file into memory. There could be insufficient memory for a very large data file. To reduce memory requirement, DolphinDB provides function [`loadTextEx`](http://www.dolphindb.com/en/help/index.html?loadTextEx.html). It divides a large text file into many small parts and gradually load them into a distributed database. 

First create a distributed database:
```
db=database("dfs://dataImportCSVDB",VALUE,2018.01.01..2018.01.31);
```

Then import the text file into table "cycle" in the distributed database:
```
loadTextEx(db, "cycle", "tradingDay", dataFilePath);
```

To access data, we first load the metadata of the partitioned table into memory with function `loadTable`. 
```
tb = database("dfs://dataImportCSVDB").loadTable("cycle");
```
Subsequently, as a query is executed, the system will load the necessary data into memory.

#### 3. Import data via HDF5 files

HDF5 is a highly efficient binary file format and is widely used. DolphinDB supports importing data via HDF5 files.

DolphinDB uses [HDF5 plugin](https://github.com/dolphindb/DolphinDBPlugin/blob/master/hdf5/README.md) to import HDF5 files. The plugin has the following methods:

- hdf5::ls - List all Group and Dataset objects in an HDF5 file.

- hdf5::lsTable - List all Dataset objects in an HDF5 file.

- hdf5::hdf5DS - Return the metadata of a Dataset in an HDF5 file.

- hdf5::loadHdf5 - Import an HDF5 file as an in-memory table.

- hdf5::loadHdf5Ex - Import an HDF5 file as a partitioned table.

- hdf5::extractHdf5Schema - Extract table schema from an HDF5 file.

Download [HDF5 plugin](http://www.dolphindb.com/downloads/HDF5_V0.7.zip), then deploy the plugin to a node's plugins directory. Use the following script to load the plugin:
```
loadPlugin("plugins/hdf5/PluginHdf5.txt")
```

The plugin method should follow the namespace. For example, to use the loadHdf5 method we can write `hdf5::loadHdf5`. Another way is:
```
use hdf5
loadHdf5(filePath,tableName)
```

Importing HDF5 files is similar to importing text files. For example, to import file candle_201801.h5 that contains a Dataset candle_201801, we can use the following script:
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
tmpTB = hdf5::loadHdf5(dataFilePath,datasetName)
```
To specify the data type of a column, use `hdf5::extractHdf5Schema`.
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
schema=hdf5::extractHdf5Schema(dataFilePath,datasetName)
update schema set type=`LONG where name=`volume        
tt=hdf5::loadHdf5(dataFilePath,datasetName,schema)
```

To load an HDF5 file larger than available memory, use `hdf5::loadHdf5Ex`.

First create a distributed table:
```
dataFilePath = "/home/data/candle_201801.h5"
datasetName = "candle_201801"
dfsPath = "dfs://dataImportHDF5DB"
db=database(dfsPath,VALUE,2018.01.01..2018.01.31)  
```
Then import the HDF5 file:
```
hdf5::loadHdf5Ex(db, "cycle", "tradingDay", dataFilePath,datasetName)
```

#### 4. Import data via ODBC interface

DolphinDB supports ODBC interface to connect to third-party databases, and directly reads tables from the source database into a DolphinDB in-memory table.

DolphinDB provides [ODBC plugin](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md) for connecting to third-party data sources, which can be easily accessed from ODBC-supported databases and migrate data to DolphinDB.

The ODBC plugin provides the following 4 methods to manipulate data from third-party data sources:

- odbc::connect - open a connection

- odbc::close - close a connection

- odbc::query - execute a SQL statement and return DolphinDB in-memory table

- odbc::execute - execute a SQL statement in a third-party database and return nothing

Bfore using ODBC plugin, we need to install the ODBC driver. Please refer to [ODBC plugin tutorial](https://github.com/dolphindb/DolphinDBPlugin/blob/master/odbc/README.md).

As an example, use ODBC plugin to connect to the following MS SQL Server:
- Server: 172.18.0.15
- Default Port: 1433
- Account Name: sa
- Password: 123456
- Database Name: SZ_TAQ

First, download ODBC plugin and extract all the files in the plugins/odbc directory to the plugins/odbc directory of DolphinDB server. Use the following script for the plugin initialization:
```
loadPlugin("plugins/odbc/odbc.cfg")
conn=odbc::connect("Driver=ODBC Driver 17 for SQL Server;Server=172.18.0.15;Database=SZ_TAQ;Uid=sa;Pwd=123456;")
```
Next, create a distributed database. Use the table structure on SQL Server as the template for the corresponding DolphinDB table. 
```
tb = odbc::query(conn,"select top 1 * from candle_201801")
db=database("dfs://dataImportODBC",VALUE,2018.01.01..2018.01.31)
db.createPartitionedTable(tb, "cycle", "tradingDay")
```
Lastly, import data from SQL Server and save as a DolphinDB partitioned table:
```
tb = database("dfs://dataImportODBC").loadTable("cycle")
data = odbc::query(conn,"select * from candle_201801")
tb.append!(data);
```
Importing data through ODBC is also a userful tool for data synchronization.

#### 5. Example

The following example imports CSV files of daily stocks data of about 100GB in 10 years. The data are stored in annual directories. For the year 2008:
```
2008
    ---- 000001.csv
    ---- 000002.csv
    ---- 000003.csv
    ---- 000004.csv
    ---- ...
```

Each CSV file has the same structure:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/csvfile.PNG?raw=true)

#### 5.1. Partition Planning

First, we should plan how to partition the data. We need to determine the partitioning columns and the granularity of the partitions.

Columns that are frequently used in **where**, **group by** or **context by** clauses are good candidates for partitioning columns. As queries on stocks data often involve trading days and stock symbols, we recommend to use "tradingDay" column and "symbol" column to form a composite (COMPO) partition. 

For optimal performance, each partition should have roughly the same size, and the size of each partition should be between 100MB and 1GB before compression. For details please refer to [DolphinDB Partitioned Database Tutorial](https://github.com/dolphindb/Tutorials_EN/blob/master/database.md) section 4.

We can use a range partition on the trading date (each year is a range), and a range partition on stock symbols (100 ranges) in the composite partition. In total we have 10\*100=1000 partitions, and each partition has about 100MB data. 

Use the following script to create the partition scheme for "tradingDay" column. It creates empty partitions for future data up to 2030.
```
yearRange =date(2008.01M + 12*0..22)
```
Use the following script to create the partition scheme for "symbol" column. As each symbol has the same amount of data, we go through all annual directories to get a list of stock symbols, then use `cutPoint` function to divide them into 100 intervals. Considering that new stock symbols may be larger than the current maximum stock symbol, we add a stock symbol of 999999 as the maximum stock symbol.
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

Create a partitioned database with a composite (COMPO) partition and a table "stockData" with the following script:

```
columns=`symbol`exchange`cycle`tradingDay`date`time`open`high`low`close`volume`turnover`unixTime
types =  [SYMBOL,SYMBOL,INT,DATE,DATE,TIME,DOUBLE,DOUBLE,DOUBLE,DOUBLE,LONG,DOUBLE,LONG]

dbDate=database("", RANGE, yearRange)
dbID=database("", RANGE, symRanges)
db = database(dbPath, COMPO, [dbDate, dbID])

pt=db.createPartitionedTable(table(1000000:0,columns,types), `stockData, `tradingDay`symbol);
```

#### 5.2. Import data

We import data by going through the directories to read and write all CSV files to the distributed table dfs://SAMPLE_TRDDB. 

First, the data format of a column in a CSV file might be different from that in DolphinDB. For example, milliseconds in timestamps might be saved as integers in a CSV file. To convert them to milliseconds in timestamps in DolphinDB, we can use the temporal conversion function `datetimeParse` together with the formatting function `format`:
```
datetimeParse(format(time,"000000000"),"HHmmssSSS")
```
It takes a long time to use a single-thread loop operation to import 100GB data. To fully utilize the cluster resources, we can divide the importing task into multiple subtasks to be executed on all nodes in parallel. Each subtask imports a year's data. This process is implemented in the following two steps:

First, define a function to import all data files in an annual directory:
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
Next, the function defined above is used with [`submitJob`](https://www.dolphindb.com/help/submitJob.html) function and [`rpc`](https://www.dolphindb.com/help/rpc.html) function to submit the tasks to each node in the cluster to execute:
```
nodesAlias="NODE" + string(1..4)
years= files(rootDir)[`filename]

index = 0;
for(year in years){	
	yearPath = rootDir + "/" + year
	des = "loadCsv_" + year
	rpc(nodesAlias[index%nodesAlias.size()],submitJob,des,des,loadCsvFromYearPath,yearPath,dbPath,`stockData)
	index=index+1
}
```

During the data importing process, we can monitor the status of the tasks with `pnodeRun(getRecentJobs)`.

In DolphinDB, partitions are the smallest units to store data and writing access to a partition is exclusive. We should avoid writing to the same partition from multiple tasks at the same time. In the example above, each task writes a different year's data, so it is impossible to write to the same partition by multiple tasks at the same time.

The script for this example can be downloaded from the Appendix.

#### 6. Appendix

CSV file [ [click to download] ](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv)

HDF5 file [ [click to download] ](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.h5)

Script for examples [ [click to download] ](https://github.com/dolphindb/Tutorials_CN/blob/master/data/demoScript.txt)
