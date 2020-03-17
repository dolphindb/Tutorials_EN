# DolphinDB tutorial: Importing text files

DolphinDB provides the following 4 functions to import text files into memory or database:

- [`loadText`](https://www.dolphindb.com/help/loadText.html): Import a text file as an in-memory table.
- [`ploadText`](https://www.dolphindb.com/help/ploadText.html): Import a text file in parallel as a partitioned in-memory tables. It is faster than function `loadText`.
- [`loadTextEx`](https://www.dolphindb.com/help/loadTextEx.html): Import a text file into a database either on disk or in memory.
- [`textChunkDS`](https://www.dolphindb.com/help/textChunkDS.html): Divide a text file into multiple data sources, then use function [`mr`](https://www.dolphindb.com/help/mr.html) for fast and flexible data processing.

Importing text files in DolphinDB is very flexible and is also very fast. Compared with popular systems such as Clickhouse, MemSQL, Druid or Pandas, DolphinDB is faster up to an order of magnitude with single-threaded importing and is even faster with multi-threaded parallel importing.

This tutorial covers the folowing topics:

- [1. Automatic identification of schema](#1-automatic-identification-of-schema)
- [2. Specify schema](#2-specify-schema)
    - [2.1 Get text file schema](#21-get-text-file-schema)
    - [2.2 Specify column names and types](#22-specify-column-names-and-types)
    - [2.3 Specify the format of temporal types](#23-specify-the-format-of-temporal-types)
    - [2.4 Import selected columns](#24-import selected columns)
    - [2.5 Skip lines](#25-skip lines)
- [3. Import data in parallel](#3-import data in parallel)
    - [3.1 Import a single file in parallel](#31-import-a-single-file-in-parallel)
    - [3.2 Import multiple files in parallel](#32-import-multiple-files-in-parallel)
- [4. Data preprocessing before importing text files](#4-data-preprocessing-before-importing-text-files)
- [5. Custom data import with Map-Reduce](#5-custom-data-import-with-map-reduce)
- [6. Other considerations](#6-other-considerations)
    - [6.1 Encoding of strings](#61-encoding-of-strings)
    - [6.2 Parsing Numeric Types](#62-parsing-numeric-types)
    - [6.3 Automatically remove double quotation marks](#63-automatically-remove-double-quotation-marks)
- [Appendix](#appendix)

## 1. Automatic identification of schema

In most other systems, users need to specify column names and data types when importing text files. For the convenience of users, DolphinDB can automatically identify the schema when importing text files.

If none of the columns in the first line of the file starts with a number, the system considers the first line to be the file header with column names. DolphinDB will take a small number of rows as a sample and automatically infer the data type of each column. As only a subset of data are used to infer data types, the data types of some columns may be incorrectly identified. For most text files, however, users don't need to manually specify column names and their data types when importing these files.

> Please note: DolphinDB supports automatic identification of most [data types provided by DolphinDB](https://www.dolphindb.com/help/DataType.html), but currently does not support automatic identification of UUID and IPADDR types. They will be supported in a later version.

The following example shows how to use function [`loadText`](https://www.dolphindb.com/help/loadText.html) to import a text file as an in-memory table. About the text file used in the examples, please refer to [Appendix](#Appendix).

```
dataFilePath = "/home/data/candle_201801.csv"
tmpTB = loadText(filename=dataFilePath)
select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

Call function [`schema`](https://www.dolphindb.com/help/schema.html) to view the table schema (column name, data type and other information):

```
tmpTB.schema().colDefs;

name       typeString typeInt comment
---------- ---------- ------- -------
symbol     SYMBOL     17
exchange   SYMBOL     17
cycle      INT        4
tradingDay DATE       6
date       DATE       6
time       INT        4
open       DOUBLE     16
high       DOUBLE     16
low        DOUBLE     16
close      DOUBLE     16
volume     INT        4
turnover   DOUBLE     16
unixTime   LONG       5
```

## 2. Specify schema

All 4 text file loading functions covered in this tutorial support parameter 'schema', which specifies a table that may contain the following 4 columns:

Column name | Meaning
--- | ---
name | a string indicating the column name
type | a string indicating the data type of the column
format | a string indicating the format of a date or time column
col | an integer indicating the index of the column to be imported. The values in this column must be in ascending order.

The columns 'name' and 'type' are required and must be the first two columns. The columns 'format' and 'col' are optional.

For example, we can assign the following table to parameter 'schema':

name | type
--- | ---
timestamp | SECOND
ID | INT
qty | INT
price | DOUBLE

### 2.1 Get text file schema

Function [`extractTextSchema`](https://www.dolphindb.com/help/extractTextSchema.html) is used to obtain the schema of a text file.

For example, to get the schema of the sample file in this tutorial:

```
dataFilePath = "/home/data/candle_201801.csv"
schemaTB = extractTextSchema(dataFilePath)
schemaTB;

name       type
---------- ------
symbol     SYMBOL
exchange   SYMBOL
cycle      INT
tradingDay DATE
date       DATE
time       INT
open       DOUBLE
high       DOUBLE
low        DOUBLE
close      DOUBLE
volume     INT
turnover   DOUBLE
unixTime   LONG
```

### 2.2 Specify column names and types

If the columns names or data types automatically inferred by the system are not expected, we can specify the column names and data types by modifying the schema table generated by function `extractTextSchema` or creating the schema table directly.

For example, if the column 'volume' is automatically recognized as INT, and the required type is LONG, we need to specify the data type of column 'volume' as LONG in the schema table. 
```
dataFilePath = "/home/data/candle_201801.csv"
schemaTB = extractTextSchema(dataFilePath)
update schemaTB set type="LONG" where name="volume";
```

Use function `loadText` to import a text file and import the data into the database according to the field data type specified by schemaTB.
```
tmpTB = loadText(filename = dataFilePath, schema = schemaTB);
```

We can use the same method to modify column names.

> Please note that if automatically inferred date or time related data types do not meet expectations, please refer to [section 2.3](#23-specify-the-format-of-temporal-types).

### 2.3 Specify the format of temporal types

For temporal data, if the automatically inferred data types do not meet expectations, we need to specify not only the data type, but also the format (represented by a string) in column 'format' of the schema table, such as "MM/dd/yyyy". For more details please refer to [Parsing and Format of Temporal Variables](https://www.dolphindb.com/help/ParsingAndFormatOfTemporalVariab.html).

Execute the following script in DolphinDB to generate the data file for this example.
```
dataFilePath = "/home/data/timeData.csv"
t = table(["20190623 14:54:57", "20190623 15:54:23", "20190623 16:30:25"] as time, `AAPL`MS`IBM as sym, 2200 5400 8670 as qty, 54.78 59.64 65.23 as price)
saveText(t, dataFilePath);
```

Before loading the file, use function `extractTextSchema` to get the schema of the data file:

```
schemaTB = extractTextSchema(dataFilePath)
schemaTB;

name  type
----- ------
time  SECOND
sym   SYMBOL
qty   INT
price DOUBLE
```

The automatically inferred data type of column 'time' is SECOND while the expected data type is DATETIME. If the file is loaded without specifying parameter 'schema', column 'time' will be empty. In order to load the file correctly, we need to specify the data type of column 'time' as DATETIME and the format of the column as "yyyyMMdd HH:mm:ss".

```
update schemaTB set type="DATETIME" where name="time"
schemaTB[`format]=["yyyyMMdd HH:mm:ss",,,]
tmpTB = loadText(dataFilePath,,schemaTB)
tmpTB;

time                sym  qty  price
------------------- ---- ---- -----
2019.06.23T14:54:57 AAPL 2200 54.78
2019.06.23T15:54:23 MS   5400 59.64
2019.06.23T16:30:25 IBM  8670 65.23
```
### 2.4 Import selected columns

We can import some columns instead of all columns from a text file by modifying the schema table.  

In the following example, we only import 7 columns: symbol, date, open, high, close, volume and turnover from a text file.

First, get the text file schema:

```
dataFilePath = "/home/data/candle_201801.csv"
schemaTB = extractTextSchema(dataFilePath);
```

Use function `rowNo` to generate indices of the columns in the text file and assign them to column 'col' in the schema table. Modify the schema table so that only the rows indicating the 7 columns to be imported remain. 

```
update schemaTB set col = rowNo(name)
schemaTB = select * from schemaTB where name in `symbol`date`open`high`close`volume`turnover;
```

Please note：
> 1. Column indices start from 0. In the example above, the column index for the first column 'symbol' is 0.
> 2. The order of the columns cannot be changed when loading text files. To adjust the order of the columns, use function [`reorderColumns!`](https://www.dolphindb.com/help/reorderColumns.html) after loading the text file.

Finally, use function `loadText` and specify parameter 'schema' to import the selected columns from the text file.

```
tmpTB = loadText(filename=dataFilePath, schema=schemaTB);
```

Only the selected columns are imported:
```
select top 5 * from tmpTB

symbol date       open   high  close volume turnover
------ ---------- ------ ----- ----- ------ ----------
000001 2018.01.02 9.31E7 13.35 13.35 13     2.003635E6
000001 2018.01.02 9.32E7 13.37 13.33 13     867181
000001 2018.01.02 9.33E7 13.32 13.32 13     903894
000001 2018.01.02 9.34E7 13.35 13.35 13     1.012E6
000001 2018.01.02 9.35E7 13.35 13.35 13     1.601939E6
```

### 2.5 Skip lines

We can skip a number of lines in the beginning of a text file (could be file description) by specifying parameter 'skipRows'. All 4 text file loading functions covered in this tutorial support parameter 'skipRows'. The maximum value allowed for parameter 'skipRows' is 1024. 

```
dataFilePath = "/home/data/candle_201801.csv"
tmpTB = loadText(filename=dataFilePath)
select count(*) from tmpTB;

count
-----
5040

select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

Now set skipRows=1000 in function `loadText` to skip the first 1000 lines of the text file when importing the file:

```
tmpTB = loadText(filename=dataFilePath, skipRows=1000)
select count(*) from tmpTB;

count
-----
4041

select top 5 * from tmpTB;

col0   col1 col2 col3       col4       col5      col6  col7  col8  col9  col10  col11      col12
------ ---- ---- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE 1    2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE 1    2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE 1    2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE 1    2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE 1    2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

> Note: As shown in the example above, if we skip the first n rows and the first row is file header, file header will be skipped as the first of the n rows.

In the example above, as the file header is skipped in importing, the column names in the imported table are the default column names: col0, col1, col2, and so on. To retain the original column names and skip the first n rows, we can get the schema of the text file with function `extractTextSchema`, and then specify parameter 'schema' when importing:

```
schema=extractTextSchema(dataFilePath)
tmpTB=loadText(filename=dataFilePath,schema=schema,skipRows=1000)
select count(*) from tmpTB;

count
-----
4041

select top 5 * from tmpTB;

symbol exchange cycle tradingDay date       time      open  high  low   close volume turnover   unixTime
------ -------- ----- ---------- ---------- --------- ----- ----- ----- ----- ------ ---------- -------------
000001 SZSE     1     2018.01.08 2018.01.08 101000000 13.13 13.14 13.12 13.14 646912 8.48962E6  1515377400000
000001 SZSE     1     2018.01.08 2018.01.08 101100000 13.13 13.14 13.13 13.14 453647 5.958462E6 1515377460000
000001 SZSE     1     2018.01.08 2018.01.08 101200000 13.13 13.14 13.12 13.13 700853 9.200605E6 1515377520000
000001 SZSE     1     2018.01.08 2018.01.08 101300000 13.13 13.14 13.12 13.12 738920 9.697166E6 1515377580000
000001 SZSE     1     2018.01.08 2018.01.08 101400000 13.13 13.14 13.12 13.13 469800 6.168286E6 1515377640000
```

## 3. Import data in parallel

### 3.1 Import a single file in parallel

Function [`ploadText`](https://www.dolphindb.com/help/ploadText.html) loads a text file into memory in a multi-threaded manner. The syntax of the syntax of `ploadText` is the same as [`loadText`](https://www.dolphindb.com/help/loadText.html). The difference is that function `ploadText` loads a large file more quickly and generates a partitioned in-memory table. It makes full use of multi-core CPUs to load a file in parallel. The degree of parallelism depends on the number of CPU cores and the specification of parameter 'localExecutors'.

The following compares the performance of functions `loadText` and `ploadText`.

First generate a text file of about 4GB:

```txt
filePath="/home/data/testFile.csv"
appendRows=100000000
t=table(rand(100,appendRows) as int,take(string('A'..'Z'),appendRows) as symbol,take(2010.01.01..2018.12.30,appendRows) as date,rand(float(100),appendRows) as float,00:00:00.000 + rand(86400000,appendRows) as time)
t.saveText(filePath);
```

Load the file with `loadText` and `ploadText` respectively. A 6-core 12-thread CPU is used for this test.

```txt
timer loadText(filePath);
Time elapsed: 12629.492 ms

timer ploadText(filePath);
Time elapsed: 2669.702 ms
```

The results show that with the configuration of this test, the performance of `ploadText` is about 4.5 times as fast as that of `loadText`.

### 3.2 Import multiple files in parallel

In big data applications, data import is often about the batch import of dozens or even hundreds of large files instead of importing one or two files. For optimal performance, we should import a large number of files in parallel. 

Function [`loadTextEx`](https://www.dolphindb.com/help/loadTextEx.html) imports a text file into a specified database, either on disk or in memory. As the partitioned tables in DolphinDB support concurrent reading and writing, they support multi-threaded data import. 

When we use function `loadTextEx` to import a text file into a distributed database, the system imports data into memory first, and then writes the data to the database on disk. These two steps are completed by the same function to ensure optimal performance.

The following example shows how to batch write multiple files on disk to a DolphinDB partitioned database. First, execute the following script in DolphinDB to generate 100 files. These files have about 10 million records and have a total size of about 778MB.

```
n=100000
dataFilePath="/home/data/multi/multiImport_"+string(1..100)+".csv"
for (i in 0..99){
    trades=table(sort(take(100*i+1..100,n)) as id,rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5)
    trades.saveText(dataFilePath[i])
};
```

Create a partitioned database and a table in the database:

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,1..10000)
tb=db.createPartitionedTable(trades,`tb,`id);
```

Function [`cut`](https://www.dolphindb.com/help/cut.html) can group elements in a vector. The following script calls function `cut` to group the file paths to be imported, and then calls function [`submitJob`](https://www.dolphindb.com/help/submitJob.html) to assign write jobs to each thread.

```
def writeData(db,file){
   loop(loadTextEx{db,`tb,`id,},file)
}
parallelLevel=10
for(x in dataFilePath.cut(100/parallelLevel)){
    submitJob("loadData"+parallelLevel,"loadData",writeData{db,x})
};
```

> Please note: In DolphinDB, multiple threads are not allowed to write to the same partition of a database at the same time. In the example above, each text file has a different value of the partitioning column (column 'id'), so we don't need to worry that multiple threads may write to the same partition at the same time. When designing concurrent reads and writes of partitioned tables in DolphinDB, please make sure that only one thread writes to the same partition at the same time.

Use function [`getRecentJobs`](https://www.dolphindb.com/help/getRecentJobs.html) to get the status of the last n batch jobs on the local node. The following script calculates the time consumed to import batch files in parallel. The result shows it took about 1.59 seconds with a 6-core 12-threaded CPU.

```
select max(endTime) - min(startTime) from getRecentJobs() where jobId like "loadData"+string(parallelLevel)+"%";

max_endTime_sub
---------------
1590
```

The following script shows it took 8.65 seconds to sequentially import 100 files into the database with a single thread.

```
timer writeData(db, dataFilePath);
Time elapsed: 8647.645 ms
```

With the configuration of this test, the speed of importing 10 threads in parallel is about 5.5 times that of single thread import.

The number of records in the table:

```
select count(*) from loadTable("dfs://DolphinDBdatabase", `tb);

count
------
10000000
```

## 4. Data preprocessing before importing text files

Before importing text files, if we need to preprocess the data, such as changing data types or filling NULL values, we can specify parameter 'transform' when calling function [`loadTextEx`](https://www.dolphindb.com/help/loadTextEx.html). The parameter 'transform' accepts a function that accepts only one parameter. Both the input and the output of the function is an unpartitioned in-memory table. Only function `loadTextEx` supports parameter 'transform'.

### 4.1 Specify the data types of temporal columns

#### 4.1.1 Convert integers into specified temporal types

A column representing time in a text file may be of type INT or LONG. We often need to save this type of data as a temporal type in the database. We can make convert the data type of columns while loading the text file with parameter 'transform' of function `loadTextEx`. 

First, create a partitioned database and a table in the database.

```
login(`admin,`123456)
dataFilePath="/home/data/candle_201801.csv"
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="TIME" where name="time"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date);
```

The user-defined function `i2t` preprocesses the data.
```
def i2t(mutable t){
    return t.replaceColumn!(`time,time(t.time/10))
}
```

> Please note: When processing data in a user-defined function, please try to use in-place modifications (functions that finish with !) if possible for optimal performance.

Call function `loadTextEx` and assign function `i2t` to parameter 'transform'. The system executes function `i2t` with the imported data, and then saves the result to the database.

```
tmpTB=loadTextEx(dbHandle=db, tableName=`tb1, partitionColumns=`date, filename=dataFilePath, transform=i2t);
```

Column 'time' is stored as data type TIME instead of INT in the text file:
```
select top 5 * from loadTable(dbPath,`tb1);

symbol exchange cycle tradingDay date       time               open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- ------------------ ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01.02 2018.01.02 02:35:10.000000000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:20.000000000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:30.000000000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:40.000000000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01.02 2018.01.02 02:35:50.000000000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

#### 4.1.2 Data type conversion between temporal types 

We may need to load a DATE type column in a text file as MONTH type to the database. We can use the same methodology as in section 4.1.1. 

```
login(`admin,`123456)
dbPath="dfs://DolphinDBdatabase"
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
schemaTB=extractTextSchema(dataFilePath)
update schemaTB set type="MONTH" where name="tradingDay"
tb=table(1:0,schemaTB.name,schemaTB.type)
tb=db.createPartitionedTable(tb,`tb1,`date)
def d2m(mutable t){
    return t.replaceColumn!(`tradingDay,month(t.tradingDay))
}
tmpTB=loadTextEx(dbHandle=db,tableName=`tb1,partitionColumns=`date,filename=dataFilePath,transform=d2m);
```

Column 'tradingDay' is stored as MONTH in the database instead of as DATE in the text file:
```
select top 5 * from loadTable(dbPath,`tb1);

symbol exchange cycle tradingDay date       time     open  high  low   close volume  turnover   unixTime
------ -------- ----- ---------- ---------- -------- ----- ----- ----- ----- ------- ---------- -------------
000001 SZSE     1     2018.01M   2018.01.02 93100000 13.35 13.39 13.35 13.38 2003635 2.678558E7 1514856660000
000001 SZSE     1     2018.01M   2018.01.02 93200000 13.37 13.38 13.33 13.33 867181  1.158757E7 1514856720000
000001 SZSE     1     2018.01M   2018.01.02 93300000 13.32 13.35 13.32 13.35 903894  1.204971E7 1514856780000
000001 SZSE     1     2018.01M   2018.01.02 93400000 13.35 13.38 13.35 13.35 1012000 1.352286E7 1514856840000
000001 SZSE     1     2018.01M   2018.01.02 93500000 13.35 13.37 13.35 13.37 1601939 2.140652E7 1514856900000
```

### 4.2 Fill Null values

As parameter 'transform' only takes a function with one parameter, to assign a DolphinDB built-in function with multiple parameters to 'transform', we can use [Partial Application](https://www.dolphindb.com/help/PartialApplication.html) to convert the function into a function with only one parameter. The following example assigns function [nullFill!](https://www.dolphindb.com/help/nullFill1.html) to parameter 'transform' to fill the Null values in the text file with 0. 

```
db=database(dbPath,VALUE,2018.01.02..2018.01.30)
tb=db.createPartitionedTable(tb,`tb1,`date)
tmpTB=loadTextEx(dbHandle=db,tableName=`pt,partitionColumns=`date,filename=dataFilePath,transform=nullFill!{,0});
```

## 5. Custom data import with Map-Reduce

DolphinDB supports the use of Map-Reduce in custom data import. We can divide a text file into multiple parts and import all or some of the parts into DolphinDB with Map-Reduce.

We can use function [`textChunkDS`](https://www.dolphindb.com/help/textChunkDS.html) to divide a text file into multiple data sources with each data source meaning a part of the text file, and then use function [`mr`](https://www.dolphindb.com/help/mr.html) to write the data sources to the database. Function `mr` can also process data before saving data to database.

### 5.1 Save stocks and futures data in two separate tables

Execute the following script in DolphinDB to generate a text file that includes both stocks data and futures data. The size of the file is about 1GB. 
```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`stock`futures,n) as type, rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,take(2000.01.01..2000.06.30,n) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4,rand(10000,n) as qty5,rand(10000,n) as qty6)
trades.saveText(dataFilePath);
```

Create a partitioned databases and tables to store stocks data and futures data, respectively:
```
login(`admin,`123456)
dbPath1="dfs://stocksDatabase"
dbPath2="dfs://futuresDatabase"
db1=database(dbPath1,VALUE,`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
db2=database(dbPath2,VALUE,2000.01.01..2000.06.30)
tb1=db1.createPartitionedTable(trades,`stock,`sym)
tb2=db2.createPartitionedTable(trades,`futures,`date);
```

Define a function to divide data into stocks data and futures data, and to save the data to corresponding databases.
```
def divideImport(tb, mutable stockTB, mutable futuresTB)
{
	tdata1=select * from tb where type="stock"
	tdata2=select * from tb where type="futures"
	append!(stockTB, tdata1)
	append!(futuresTB, tdata2)
}
```

Use function `textChunkDS` to divide the text file into multiple parts. In this example the size of each part is 300MB. The file is divided into 4 parts.
```
ds=textChunkDS(dataFilePath,300)
ds;

(DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment, DataSource<readTableFromFileSegment)
```

Call function `mr` and specify the result of function `textChunkDS` as the data source to import the file into the database. As the map function (specified by parameter 'mapFunc') only accepts a table as the input, here we use [Partial Application](https://www.dolphindb.com/help/PartialApplication.html) to convert function `divideImport` into a function that only takes a table as the input.

```
mr(ds=ds, mapFunc=divideImport{,tb1,tb2}, parallel=false);
```

> Please note that in this example, different data sources generated by function `textChunkDS` may contain data for the same partition. As DolphinDB does not allow multiple threads to write to the same partition at the same time, we need to set parallel=false in function `mr`, otherwise an exception will be thrown.

The stocks table contains only stocks data and the futures table contains only futures data.

stocks table:

```
select top 5 * from loadTable("dfs://DolphinDBTickDatabase", `stock);

type  sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 qty6
----- ---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ----
stock AMZN 2000.02.14 11.224234 112.26763  1160.926836 11661.418403 11902.403305 11636.093467 4    53   450  2072 9116 12
stock AMZN 2000.03.29 10.119057 111.132165 1031.171855 10655.048121 12682.656303 11182.317321 6    21   651  2078 7971 6207
stock AMZN 2000.06.16 11.61637  101.943971 1019.122963 10768.996906 11091.395164 11239.242307 0    91   857  3129 3829 811
stock AMZN 2000.02.20 11.69517  114.607763 1005.724332 10548.273754 12548.185724 12750.524002 1    39   270  4216 8607 6578
stock AMZN 2000.02.23 11.534805 106.040664 1085.913295 11461.783565 12496.932604 12995.461331 4    35   488  4042 6500 4826
```

futures table:

```
select top 5 * from loadTable("dfs://DolphinDBFuturesDatabase", `futures);

type    sym  date       price1    price2     price3      price4       price5       price6       qty1 qty2 qty3 qty4 qty5 ...
------- ---- ---------- --------- ---------- ----------- ------------ ------------ ------------ ---- ---- ---- ---- ---- ---
futures MSFT 2000.01.01 11.894442 106.494131 1000.600933 10927.639217 10648.298313 11680.875797 9    10   241  524  8325 ...
futures S    2000.01.01 10.13728  115.907379 1140.10161  11222.057315 10909.352983 13535.931446 3    69   461  4560 2583 ...
futures GM   2000.01.01 10.339581 112.602729 1097.198543 10938.208083 10761.688725 11121.888288 1    1    714  6701 9203 ...
futures IBM  2000.01.01 10.45422  112.229537 1087.366764 10356.28124  11829.206165 11724.680443 0    47   741  7794 5529 ...
futures TSLA 2000.01.01 11.901426 106.127109 1144.022732 10465.529256 12831.721586 10621.111858 4    43   136  9858 8487 ...
```

### 5.2 Quickly load data from the beginning and the end of large files

We can use function `textChunkDS` to divide a large file into multiple small data sources (chunks), then load the first and the last one. Execute the following script in DolphinDB to generate the data file:

```
n=10000000
dataFilePath="/home/data/chunkText.csv"
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym,sort(take(2000.01.01..2000.06.30,n)) as date,10.0+rand(2.0,n) as price1,100.0+rand(20.0,n) as price2,1000.0+rand(200.0,n) as price3,10000.0+rand(2000.0,n) as price4,10000.0+rand(3000.0,n) as price5,10000.0+rand(4000.0,n) as price6,rand(10,n) as qty1,rand(100,n) as qty2,rand(1000,n) as qty3,rand(10000,n) as qty4, rand(10000,n) as qty5, rand(1000,n) as qty6)
trades.saveText(dataFilePath);
```
Then use function `textChunkDS` to divide the text file into multiple parts. In this example the size of each part is 10MB.
```
ds=textChunkDS(dataFilePath, 10);
```

Call function `mr` to load the first chunk and the last chunk:
```
head_tail_tb = mr(ds=[ds.head(), ds.tail()], mapFunc=x->x, finalFunc=unionAll{,false});
```

View the number of records in table 'head_tail_tb':
```
select count(*) from head_tail_tb;

count
------
192262
```

## 6. Other considerations

### 6.1 Encoding of strings

As strings in DolphinDB are encoded in UTF-8, if a text file with string columns is not UTF-8 encoded, the string columns must be changed to UTF-8 encoding after importing. DolphinDB provides functions [`convertEncode`](https://www.dolphindb.com/help/convertEncode.html), [`fromUTF8`](https://www.dolphindb.com/help/fromUTF8.html) and [`toUTF8`](https://www.dolphindb.com/help/toUTF8.html) to convert encoding of strings.

For example, use function `convertEncode` to convert the encoding of column 'exchange' in the tmpTB table:

```
dataFilePath="/home/data/candle_201801.csv"
tmpTB=loadText(filename=dataFilePath, skipRows=0)
tmpTB.replaceColumn!(`exchange, convertEncode(tmpTB.exchange,"gbk","utf-8"));
```

### 6.2 Parsing Numeric Types

This section explains the automatic identification of numeric data types (CHAR, SHORT, INT, LONG, FLOAT and DOUBLE). The system can automatically recognize the following formats of numeric data:

-Numeric values, such as 123
-Numeric values with thousands separators, such as 100,000
-Numeric values with decimal point (floating point number), such as 1.231
-Scientific notation, such as 1.23E5

If a column is specified as a numeric type, the system ignores letters or other symbols before and after numeric values when importing. If there are no numbers in an entry, it will be loaded as a NULL value. Please see the following example for more details.

First, execute the following script to create a text file.

```
dataFilePath="/home/data/test.csv"
id=1..3
prices1=["2131","$2,131", "N/A"]
prices2=["213.1","$213.1", "N95C21t/2"]
price3 = [2.658E2, 2.658E3, 2.658E1]
total=["2.658E7","-2.658e7","2.658e-7"]
tt=table(id as id, prices1 as price1, prices2 as price2, price3 as price3, total as total)
saveText(tt,dataFilePath);
```

In the text file, both column 'price1' and column 'price2' contain numbers and characters. If we load the text file without specifying parameter 'schema', the system will identify these 2 columns as SYMBOL types:

```
tmpTB=loadText(dataFilePath)
tmpTB;

id price1 price2 total
-- ------ ------ --------
1  2131   213.1  2.658E7
2  $2,131 $213.1 -2.658E7
3  N/A    N/A    2.658E-7

tmpTB.schema().colDefs;

name   typeString typeInt comment
------ ---------- ------- -------
id     INT        4
price1 SYMBOL     17
price2 SYMBOL     17
total  DOUBLE     16
```

If column 'price1' is specified as INT type and column 'price2' is specified as DOUBLE type, the system will ignore characters and symbols before and after the number when importing. If there are no numbers, an entry is recognized as a Null value.

```
schemaTB=table(`id`price1`price2`total as name, `INT`INT`DOUBLE`DOUBLE as type) 
tmpTB=loadText(dataFilePath,,schemaTB)
tmpTB;

id price1 price2 total
-- ------ ------ --------
1  2131   213.1  2.658E7
2  2131   213.1  -2.658E7
3                2.658E-7
```

### 6.3 Automatically remove double quotation marks

In CSV files, double quotation marks are sometimes used in numeric columns with special characters (such as delimiters). In DolphinDB, the system automatically strips double quotation marks in these columns.

In the text file of the following example, column 'num' contains numeric values with thousands separators.

```
dataFilePath="/home/data/testSym.csv"
tt=table(1..3 as id,  ["\"500\"","\"3,500\"","\"9,000,000\""] as num)
saveText(tt,dataFilePath);
```

We can see that the system automatically strips the double quotation marks when importing the text file.  

```
tmpTB=loadText(dataFilePath)
tmpTB;

id num
-- -------
1  500
2  3500
3  9000000
```


Appendix
-

The text file used in the examples in this tutorial: [candle_201801.csv](https://github.com/dolphindb/Tutorials_CN/blob/master/data/candle_201801.csv).