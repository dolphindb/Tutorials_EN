# Python API for DolphinDB

DolphinDB Python API supports Python 3.5 to 3.8.

Before proceeding, make sure you have DolphinDB module in your python. you can install DolphinDB using the following command:
```
$ pip install dolphindb
```
Due to implementation reasons, the Python API cannot be used together with the Linux platform Jupyter Notebook for the time being. This problem will be solved in the future.



| Method        | Explanation          |
|:------------- |:-------------|
|connect(host, port, [username, password])    | Connect a session to a DolphinDB server |
|toDF()    | Convert a DolphinDB table object to a pandas Dataframe object |
|executeAs(tableName)    | Save a table on DolphinDB server with the specified table name |
|execute()    | Used with `update` and `delete` methods |
|database(dbPath, ......)    | Create or reload a database |
|dropDatabase(dbPath)    | Delete a database |
|dropPartition(dbPath, partitionPaths)    | Delete database partitions |
|dropTable(dbPath, tableName)    | Delete a table |
|drop(colNameList)    | Delete columns from a table |
|ols(Y, X, intercept)   | Conduct ordinary least squares regression and return a dictionary of regression results |


### 1 Connect to DolphinDB

Python interacts with DolphinDB through a session. The Python application executes scripts and functions on the DolphinDB server through a session, and transfers data in both directions between the two. Among the Session class methods, the most commonly used methods are as follows:

| Method        | Explanation          |
|:------------- |:-------------|
|connect(host, port, [username, password])    | Connect a session to a DolphinDB server |
|login(username,password,enableEncryption)| Login on the server |
|run(script)   | Run the script on the DolphinDB server|
|run(functionName,args)  | Execute a remote function on DolphinDB server  |
|upload(variableObjectMap)   | Insert loacll files into DolphinDB server |
|close()  |Close the connection between two servers |

In the following example, we use teh session method to create DolphinDB connection object in Python, and connect method to establish connections to a DolphinDB server with specified domain name/IP address and port number. 
We need to start a DolphinDB server before running the following Python script.

```
import dolphindb as ddb
s = ddb.session()
s.connect("localhost",8848)
```

If you need to enter a username and password:

```
s.connect("localhost",8848, YOUR_USERNAME, YOUR_PASSWORD)
```

The default admin account username and password for DolphinDB server are "admin" and "123456", respectively. 
By default, **YOUR_USER_NAME** and **YOUR_PASS_WORD** are encrypted in transit.

### 2 Run DolphinDB server

A session object has a method **run** that can be used to execute any DolphinDB script. 
If the script returns an object in DolphinDB, method **run** will convert the object to a corresponding object in Python.

```
a=s.run("`IBM`GOOG`YHOO")
repr(a)
# output
"array(['IBM', 'GOOG', 'YHOO'], dtype='<U4')"
```

The maximum script size is now set to 65534 bytes.
### 3 Execute DolphinDB function

In addiction to running script, **run** can also be used to send commands to execute on DolphinDB server. Its parameters are the DolphinDB function to be executed and the function arguments.

The following example is about make a remote call of a DolphinDB built-in function **add**. 

There are three different methods for applying ** add()** function through **run**.

The **add()** is a built-in function with two parameters: 

Prepare the python object x and y using ** run** method 
```
s.run("x = [1,3,5];y = [2,4,6]")
```
Then, use run(script) to add these two vector.
```
a=s.run("add(x,y)")
repr(a)
# output
'array([ 3,  7, 11], dtype=int32)'
```
Prepare the python object x using ** run** method 

```
s.run("x = [1,3,5]")
```
Generate a parameter y on python:
```
import numpy as np

y=np.array([1,2,3])
```
Use partial application to fix the parameter x with **add** method.
```
result=s.run("add{x,}", y)
repr(result)
result.dtype
# output
'array([2, 5, 8])'
dtype('int64')

```
Assign values to parameter x and y on python.
```
import numpy as np
x=np.array([1.5,2.5,7])
y=np.array([8.5,7.5,3])
result=s.run("add", x, y)
repr(result)
result.dtype
# output
'array([10., 10., 10.])'dtype('float64')

```

### 4 Upload data to DolphinDB server

#### 4.1 Upload data from Python to the DolphinDB server

We can upload a Python object through function upload to the DolphinDB server, which takes a Python dictionary object as input. For this dictionary object, the key is the variable name on DolphinDB server and the value is the python object, the data object could be Numbers, Strings, List, Data Frame and so on.

* Upload a list

```Python
a = [1,2,3.0]
s.upload({'a':a})
a_new = s.run("a")
a_type = s.run("typestr(a)")
print(a_new)
print(a_type)

# output
[1. 2. 3.]
ANY VECTOR
```

we noticed that built-in lists in python will be identified as any vector after being uplpaded to DolphinDB, such as a= [1,2,3]. 
Therefore, it is recommended to use numpy.array instead of the built-in list, such as a=numpy.array([1,2,3.0],dtype=numpy.double)

* Upload a NumPy array
```Python
import numpy as np

arr = np.array([1,2,3.0],dtype=np.double)
s.upload({'arr':arr})
arr_new = s.run("arr")
arr_type = s.run("typestr(arr)")
print(arr_new)
print(arr_type)

# output
[1. 2. 3.]
FAST DOUBLE VECTOR
```
*Upload pandas DataFrame
```Python
import pandas as pd
import numpy as np

df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```
#### 4.2 Upload data With function `table`

A DolphinDB table object can be created with the `table` method of a session. 

The input of the `table` method can be a dictionary, a DataFrame, or a table name on the DolphinDB server. 

* Upload dict

For better understanding, we define a function **createDemoDict()** to return dictionary.

```Python
import numpy as np

def createDemoDict():
    return {'id': [1, 2, 2, 3],
            'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
            'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
            'price': [22, 3.5, 21, 26]}
```

After the dictionary is crated by a user-defined function, we could use **table** method to create a table on the DolphinDB server and assigns it a random table name.
```Python
import numpy as np

# save the table to DolphinDB server as table "testDict"
dt = s.table(data=createDemoDict(), tableAliasName="testDict")

# load table "testDict" on DolphinDB server 
print(s.loadTable("testDict").toDF())

# output
   id       date ticker  price
0   1 2019-02-04   AAPL   22.0
1   2 2019-02-05   AMZN    3.5
2   2 2019-02-09   AMZN   21.0
3   3 2019-02-13      A   26.0
```
Please noted that the **table** method will crate a temporary table without default table name. But loop through table method will lead to there is not enough physical memory left.


* Upload pandas DataFrame

In the example below, we define a function **createDemoDataFrame()**. 
The function creates and returns a DataFrame object from pandas. The object includes any DolphinDB data type.
```Python
import pandas as pd

def createDemoDataFrame():
    data = {'cid': np.array([1, 2, 3], dtype=np.int32),
            'cbool': np.array([True, False, np.nan], dtype=np.bool),
            'cchar': np.array([1, 2, 3], dtype=np.int8),
            'cshort': np.array([1, 2, 3], dtype=np.int16),
            'cint': np.array([1, 2, 3], dtype=np.int32),
            'clong': np.array([0, 1, 2], dtype=np.int64),
            'cdate': np.array(['2019-02-04', '2019-02-05', ''], dtype='datetime64[D]'),
            'cmonth': np.array(['2019-01', '2019-02', ''], dtype='datetime64[M]'),
            'ctime': np.array(['2019-01-01 15:00:00.706', '2019-01-01 15:30:00.706', ''], dtype='datetime64[ms]'),
            'cminute': np.array(['2019-01-01 15:25', '2019-01-01 15:30', ''], dtype='datetime64[m]'),
            'csecond': np.array(['2019-01-01 15:00:30', '2019-01-01 15:30:33', ''], dtype='datetime64[s]'),
            'cdatetime': np.array(['2019-01-01 15:00:30', '2019-01-02 15:30:33', ''], dtype='datetime64[s]'),
            'ctimestamp': np.array(['2019-01-01 15:00:00.706', '2019-01-01 15:30:00.706', ''], dtype='datetime64[ms]'),
            'cnanotime': np.array(['2019-01-01 15:00:00.80706', '2019-01-01 15:30:00.80706', ''], dtype='datetime64[ns]'),
            'cnanotimestamp': np.array(['2019-01-01 15:00:00.80706', '2019-01-01 15:30:00.80706', ''], dtype='datetime64[ns]'),
            'cfloat': np.array([2.1, 2.658956, np.NaN], dtype=np.float32),
            'cdouble': np.array([0., 47.456213, np.NaN], dtype=np.float64),
            'csymbol': np.array(['A', 'B', '']),
            'cstring': np.array(['abc', 'def', ''])}
    return pd.DataFrame(data)
```


```Python
import pandas as pd

# save the table to DolphinDB server as table "testDataFrame"
dt = s.table(data=createDemoDataFrame(), tableAliasName="testDataFrame")

# load table "testDataFrame" on DolphinDB server 
print(s.loadTable("testDataFrame").toDF())

# output
   cid  cbool  cchar  cshort  ...    cfloat    cdouble csymbol cstring
0    1   True      1       1  ...  2.100000   0.000000       A     abc
1    2  False      2       2  ...  2.658956  47.456213       B     def
2    3   True      3       3  ...       NaN        NaN                
[3 rows x 19 columns]
```
###5 import data into DolphinDB server

There are 3 types of DolphinDB databases: in-memory database, local file system database and DFS (Distributed File System) database. 
DFS automatically manages data storage and replicas. DolphinDB is a distributed database system and achieves optimal performance in DFS mode. Therefore, we highly recommend to use DFS mode. Please refer to the tutorial [multi_machine_cluster_deploy](https://github.com/dolphindb/Tutorials_EN/blob/master/multi_machine_cluster_deploy.md) for details. 
For simplicity, we also use databases in the local file system in some examples. 

The examples in this case use a csv file: [example.csv](data/example.csv).

#### 5.1 Import data as an in-memory table

To import text files into DolphinDB as an in-memory table, use the `loadText` method of a session.  It returns a DolphinDB table object in Python, 
which corresponds to an in-memory table on the DolphinDB server. 
The DolphinDB table object in Python has a method `toDF` to convert it to a pandas DataFrame.


```Python
WORK_DIR = "C:/DolphinDB/Data"

# return a DolphinDB table object in Python
trade=s.loadText(WORK_DIR+"/example.csv")

# convert the imported DolphinDB table object into a pandas DataFrame
df = trade.toDF()
print(df)

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

```
The default delimiter for method `loadText` is comma ",". We can also use other delimiters instead. For example, to import a tabular text file:
```Python
t1=s.loadText(WORK_DIR+"/t1.tsv", '\t')
```
## 5.2 Import data into a partitioned database

If the data files are larger than available memory into DolphinDB, we can load data into a partitioned database.

### 5.2.1 Create a partitioned database
After we create a partitioned database, we cannot modify its partitioning scheme unless we create a value-based partitioned database.
To check if a value-based partioned database "valuedb" exists. If it exists, delete it.
```Python
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```
Now create the value-based partitioned database "valuedb" with a session method **database**. 
As "example.csv" only has data for 3 stocks, we use a VALUE partition with stock ticker as the partitioning column. 
The parameter "partitions" indicates the partition scheme.

```Python
import dolphindb.settings as keys

# 'db' indicates the database handle name on the DolphinDB server.
s.database('db', partitionType=keys.VALUE, partitions=['AMZN','NFLX', 'NVDA'], dbPath=WORK_DIR+'/valuedb')
```
To create a partitioned database in DFS, just make the database path start with "dfs://". 
Before we execute the following script, we need to configure a DFS cluster. Please refer to the tutorial [multi_machine_cluster_deploy](https://github.com/dolphindb/Tutorials_EN/blob/master/multi_machine_cluster_deploy.md).

```Python
import dolphindb.settings as keys

s.database('db', partitionType=keys.VALUE, partitions=['AMZN','NFLX', 'NVDA'], dbPath='dfs://valuedb')
#equals to s.run("db=database('dfs://valuedb', VALUE, ['AMZN','NFLX', 'NVDA'])")
```
In addition to VALUE partition, DolphinDB also supports SEQ, RANGE, LIST, COMBO, and HASH partitions.

#### 5.2.2 Create a partitioned table and append data to the table

After a partitioned database is created successfully, we can import text files to a partitioned table in the partitioned database with function `loadTextEx`. If the partitioned table does not exist, `loadTextEx` creates it and appends the imported data to it. Otherwise, the function appends the imported data to the partitioned table.

In function `loadTextEx`, parameter "dbPath" is the database path; "tableName" is the partitioned table name; "partitionColumns" is the partitioning columns; "filePath" is the absolute path of the text file; "delimiter" is the delimiter of the text file (comma by default).

In the following example, function `loadTextEx` creates a partitioned table "trade" on the DolphinDB server and then appends the data from "example.csv" to the table. 

```Python
import dolphindb.settings as keys

if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")

trade = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]

# show the number of rows in the table
print(trade.rows)
13136

# show the number of columns in the table
print(trade.cols)
6

# show the schema of the table
print(trade.schema)
     name typeString  typeInt
0  TICKER     SYMBOL       17
1    date       DATE        6
2     VOL        INT        4
3     PRC     DOUBLE       16
4     BID     DOUBLE       16
5     ASK     DOUBLE       16

```
To refer to the table:

```Python
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
```
#### 5.3 Import data as an in-memory partitioned table

#### 5.3.1 `loadTextEx`

We can import data as an in-memory partitioned table. Operations on an in-memory partitioned table are faster than those on a nonpartitioned in-memory table as the former utilizes parallel computing.

We can use function `loadTextEx` to create an in-memory partitioned database with an empty string for the parameter "dbPath".

```Python
import dolphindb.settings as keys

# "dbPath='db'" means that the system uses database handle 'db' to import data into in-memory partitioned table trade

s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX","NVDA"], dbPath="")

trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
```

#### 5.3.2 `ploadText`

Function `ploadText` loads a text file in parallel to generate an in-memory partitioned table. It runs much faster than `loadText`.

```Python
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.rows)

# output
13136
```
#### 6 Load DolphinDB database tables

#### 6.1 Load data with method `loadTable`

To load a table from a database, use function `loadTable`. Parameter "tableName" indicates the partitioned table name; "dbPath" is the database location. If "dbPath" is not specified, `loadTable` will load a DolphinDB table in memory whose name is specified in argument "tableName".

For a partitioned table: if memoryMode=True and parameter "partition" is unspecified, load all data of the table into DolphinDB server memory as a partitioned table; if memoryMode=True and parameter "partition" is specified, load only the specified partitions of the table into DolphinDB server memory as a partitioned table; if memoryMode=false, only load the metadata of the table into DolphinDB server memory.

#### 6.1.1 Load an entire table

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.toDF()

# output
TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500
5       AMZN  1997.05.23    983855   16.75000   16.62500   16.7500
...
13134   NFLX  2016.12.29   3444729  125.33000  125.31000  125.3300
13135   NFLX  2016.12.30   4455012  123.80000  123.80000  123.8300

[13136 rows x 6 columns]
```
#### 6.1.2 Load selected partitions

To load only the "AMZN" partition:

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions="AMZN")
print(trade.rows)

# output
4941
```

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions=["NFLX","NVDA"], memoryMode=True)
print(trade.rows)

# output
8195
```
#### 6.2. Load data with method `loadTableBySQL`

Method `loadTableBySQL` imports only the rows of an on-disk partitioned table that satisfy the filtering conditions in a SQL query as an in-memory partitioned table.

```Python
import os
import dolphindb.settings as keys

if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(tableName="trade", dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.rows)

# output
5286
```
6.3 Data conversion
#### 6.3.1 Data form conversion
The following shows the general mapping from DolphinDB data objects to Python data objects.

|DolphinDB|Python |Example for DolphinDB|Example for Python|
|-------------|----------|-------------|----------|
|scalar|Numbers, Strings, Numpy.datetime64|please refer chapter 6.3.2| refer chapter 6.3.2|
|vector|Numpy.array|1..2|[1 2 3]|
|pair|Lists|1:5|[1,5]|
|matrix|Lists|1..6$2:3|[array([[1, 3, 5],[2, 4, 6]], dtype=int32), None, None]|
|set|Sets|set(3 5 4 6)|{3,4,5,6}|
|dictionary|Dictionaries||dict(['IBM','MS','ORCL'], 170.5 56.2 49.5)|
{'MS': 56.2, 'IBM': 170.5, 'ORCL': 49.5}|
|table|pandas.DataFame|see[chapter 6.1](#61-`loadtable`)|see[chapter 6.1](#61-`loadtable`)|

#### 6.3.2 Data type conversion
The dolphinDB data objects can be automatically converted into corresponding Python data objects by using the method `toDF`. Also note that:

- CHAR are converted into int64. To convert integer into character, use chr().
- Temporal data types are converted into datetime64. For example, 2012.06M is converted into 2012-06-01; 13:30m is converted into 1970-01-01 13:30:00.

|DolphinDB Data Type|Python Data Type | DolphinDB data object|Python data object|
|-------------|----------|-------------|-----------| 
|BOOL|bool|[true,00b]|[True, nan]| 
|CHAR|int64|[12c,00c]|[12, nan]|
|SHORT|int64|[12,00h]|[12, nan]| 
|INT|int64|[12,00i]|[12, nan]| 
|LONG|int64|[12l,00l]|[12, nan]| 
|DOUBLE|float64|[3.5,00F]|[3.5,nan]| 
|FLOAT|float64|[3.5,00f]|[3.5, nan]| 
|SYMBOL|object|symbol(["AAPL",NULL])|["AAPL",""]| 
|STRING|object|["AAPL",string()]|["AAPL", ""]|
|DATE|datetime64|[2012.6.12,date()]|[2012-06-12, NaT]| 
|MONTH|datetime64|[2012.06M, month()]|[2012-06-01, NaT]| 
|TIME|datetime64|[13:10:10.008,time()]|[1970-01-01 13:10:10.008, NaT]|
|MINUTE|datetime64|[13:30,minute()]|[1970-01-01 13:30:00, NaT]| 
|SECOND|datetime64|[13:30:10,second()]|[1970-01-01 13:30:10, NaT]| 
|DATETIME|datetime64|[2012.06.13 13:30:10,datetime()]|[2012-06-13 13:30:10,NaT]|
|TIMESTAMP|datetime64|[2012.06.13 13:30:10.008,timestamp()]|[2012-06-13 13:30:10.008,NaT]|
|NANOTIME|datetime64|[13:30:10.008007006, nanotime()]|[1970-01-01 13:30:10.008007006,NaT]|
|NANOTIMESTAMP|datetime64|[2012.06.13 13:30:10.008007006,nanotimestamp()]|[2012-06-13 13:30:10.008007006,NaT]|

#### 6.4 Null values
`toDF` is a method to execute the equivalent SQL query on the DolphinDB server, and return the results as DataFrames in pandas.
Python API provides special Null corresponding to DolphinDB data types. For any null values in logical temporal or integral are treated as NaN, NaT, and for STRING type NULL, the default value is empty string.

### 7. Append data into DolphinDB table

we will introduce how to upload and save the retrieve data to the DolphinDB table through the Python API.

There are 3 types of DolphinDB tables: 
- In-memory table: Data is stored only in memory, user can access data at super-fast-speed.
- table in the local file system : Data can be store in local file, any user can access data files directly. 
- Distributed table: Data can be partitioned to multiple nodes and data retrieval in DFS is fast. 

#### 7.1 Append data to a in-memory table
DolphinDB provides several ways to store data into in-memory table:
- The method `insert into` can be used to store data
- The method `tableInsert` can be used to store multiple rows in a table.

In this tutorial, we'll cover three ways of storing data. The data table used in the following example has 4 columns, which are INT, DATE, STRINR, and DOUBLE types. The column names are id, date, ticker, and price.

Execute the following script in Python.

```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# generated a in-memory table:
script = """t = table(1:0,`id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
share t as tglobal"""
s.run(script)
```
A DolphinDB memory table can be created with the `run` method.

Before, we use `table` function to create a DolphinDB table object in Python, and specify the capacity and initial size of the table, column names and data types.
Since In-memory tables are session isolated, they are only visible to current session. In-memory table can be shared between sessions by using the method `share` .

#### 7.1.1 Add data With `INSERT INTO` function

We can save a single piece of data in the following way:

```Python
import numpy as np

script = "insert into tglobal values(%s, date(%s), %s, %s);tglobal"% (1, np.datetime64("2019-01-01").astype(np.int64), '`AAPL', 5.6)
s.run(script)
```
*Please note**,DolphinDB's memory table can not perform the data type conversion automatically,
Therefore we need to call the time conversion function for time type data when we append data to the memory table.
Just make sure the inserted data type is consistent with the data type in the memory table schema, and then append data. 

In the above example, we convert the time type of numpy into a 64-bit integer, and call the `date` function in the insert statement to convert the integer data of the time column into the corresponding type on the server.

We can also use the `INSERT INTO` to insert multiple rows at once, as follows:
```Python
import numpy as np
import random

rowNum = 5
ids = np.arange(1, rowNum+1, 1, dtype=np.int32)
dates = np.array(pd.date_range('4/1/2019', periods=rowNum), dtype='datetime64[D]')
tickers = np.repeat("AA", rowNum)
prices = np.arange(1, 0.6*(rowNum+1), 0.6, dtype=np.float64)
s.upload({'ids':ids, "dates":dates, "tickers":tickers, "prices":prices})
script = "insert into tglobal values(ids,dates,tickers,prices);"
s.run(script)
```

In the above example, using `date_range()` function to generate the time column containing only with date,  which is consistent with the date type of DolphinDB, so the data is inserted directly through the insert statement without any data type conversion. If the time data type is datetime64, you need to append data to the memory table like this:

```Python
script = "insert into tglobal values(ids,date(dates),tickers,prices);" 
s.run(script)
```
#### 7.1.2 Append multiple rows by `tableInsert` 


```Python
args = [ids, dates, tickers, prices]
s.run("tableInsert{tglobal}", args)
s.run("tglobal")
```
#### 7.1.3 Append a table with `tableInsert` 

we can add a table to the in-memory table by using `tableInsert` function, but treat the  time column carefully. 

- a table without time column

we can upload a DataFrame to the server and append it to in-memory table by using partial application.

```Python
import pandas as pd

#generate a in-memory table
script = """t = table(1:0,`id`ticker`price, [INT,STRING,DOUBLE])
share t as tdglobal"""
s.run(script)

# generate a DataFrame
tb=pd.DataFrame({'id': [1, 2, 2, 3],
                 'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
                 'price': [22, 3.5, 21, 26]})
s.run("tableInsert{tdglobal}",tb)
```

- a table with time column 

The temporal data type datetime64 in Python need to be converted into DolphinDB temporal data type.

```Python
import pandas as pd
tb=pd.DataFrame(createDemoDict())
s.upload({'tb':tb})
s.run("tableInsert(tglobal,(select id, date(date) as date, ticker, price from tb))")
```

we could also use the method `append!` to store data into memory table. The method `append!` return extra information about the schema of a table. Therefore, it is generally not recommended to save data through the `append!` function.


- a table without time column

```Python
import pandas as pd

# generate a in-memory table
script = """t = table(1:0,`id`ticker`price, [INT,STRING,DOUBLE])
share t as tdglobal"""
s.run(script)

# generate the appended DataFrame
tb=pd.DataFrame({'id': [1, 2, 2, 3],
                 'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
                 'price': [22, 3.5, 21, 26]})
s.run("append!{tdglobal}",tb)
```

- a table with time column 

```Python
import pandas as pd
tb=pd.DataFrame(createDemoDict())
s.upload({'tb':tb})
s.run("append!(tglobal, (select id, date(date) as date, ticker, price from tb))")
```

#### 7.2 Append data to a table in the local file system 

A table in the local file system can be created by executing the following script. 
We can use function `database` to create a database, and then use `saveTable` to save an in-memory table on disk.
```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# generate a table in local file system
dbPath="/home/user/dbtest/testPython"
tableName='dt'
script = """t = table(100:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE]); 
db = database('{db}'); 
saveTable(db, t, `{tb}); 
share t as tDiskGlobal;""".format(db=dbPath,tb=tableName)
s.run(script)
```
Use `tableInsert` is one of most common way for adding data to a table in the local file system.
In this case, we use `tableInsert` to insert data into shared memory table tDiskGlobal, and then call function `saveTable` to save table to disk.

Please note that， `tableInsert` is a function to add data into memory. The table could be loaded into disk with function `savaTable`.


```Python
import numpy as np
import random

rowNum = 5
ids = np.arange(1, rowNum+1, 1, dtype=np.int32)
dates = np.array(pd.date_range('4/1/2019', periods=rowNum), dtype='datetime64[D]')
tickers = np.repeat("AA", rowNum)
prices = np.arange(1, 0.6*(rowNum+1), 0.6, dtype=np.float64)
args = [ids, dates, tickers, prices]
s.run("tableInsert{tDiskGlobal}", args)
s.run("saveTable(db,tDiskGlobal,`{tb});".format(tb=tableName))
```

The table in the local file system also supports method `tableInsert` and method `append!`. But method `saveTable` must be followed by appending data into local files system table. 

#### 7.3 Append data into disrtibuted table



The distributed table is available only if enableDFS=1 in cluster node


Use `createPartitionedTable` to create a distributed table 

```Python
import dolphindb as ddb

s = ddb.session()
s.connect(host, port, "admin", "123456")

# Create a distributed table 
dbPath="dfs://testPython"
tableName='t1'
script = """
dbPath='{db}'
if(existsDatabase(dbPath))
	dropDatabase(dbPath)
db = database(dbPath, VALUE, 0..100)
t1 = table(10000:0,`id`cbool`cchar`cshort`cint`clong`cdate`cmonth`ctime`cminute`csecond`cdatetime`ctimestamp`cnanotime`cnanotimestamp`cfloat`cdouble`csymbol`cstring,[INT,BOOL,CHAR,SHORT,INT,LONG,DATE,MONTH,TIME,MINUTE,SECOND,DATETIME,TIMESTAMP,NANOTIME,NANOTIMESTAMP,FLOAT,DOUBLE,SYMBOL,STRING])
insert into t1 values (0,true,'a',122h,21,22l,2012.06.12,2012.06M,13:10:10.008,13:30m,13:30:10,2012.06.13 13:30:10,2012.06.13 13:30:10.008,13:30:10.008007006,2012.06.13 13:30:10.008007006,2.1f,2.1,'','')
t = db.createPartitionedTable(t1, `{tb}, `id)
t.append!(t1)""".format(db=dbPath,tb=tableName)
s.run(script)
```

Different from in-memory table and local disk table, distributed table provides time type conversion when adding tables, so there is no need to do date type conversions again.

```Python
tb = createDemoDataFrame()
s.run("tableInsert{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName), tb)
```

you can also use the method `append!`  to store data into disrtibuted table, which can append a table to another table. The `append!` method will cost extra time to return the information of the schema of a table.
Therefore, we will not recommend to use append! to add data to a DFS table.

```Python
tb = createDemoDataFrame()
s.run("append!{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName),tb)
```

### 8 Databases and Tables 
#### 8.1 Database and Table operations
In addition to the common methods listed in Section 1, the `Session` class also provides some methods equivalent to DolphinDB's built-in functions for operating databases and tables, as follows:
* Database

| Method      | Explanation          |
|:------------- |:-------------|
|database|create a database|
|dropDatabase(dbPath)|delete a database|
|dropPartition(dbPath, partitionPaths)|Delete data from one or multiple partitions from a database|
|existsDatabase|Check if a database exists under the specified folder.|

* Tables and Partitions

| Method      | Explanation      |
|:------------- |:-------------|
|dropTable(dbPath, tableName)|Delete the specified table on database|
|existsTable|Check if the specified table exists in the specified database.|
|loadTable| load data from database|
|table|create a table|

Once we have a table object in python, we could operate this object by using the `table` type method of a session.

|Method      | Explanation          |
|:------------- |:-------------|
|append|add data into the table|
|drop(colNameList)|delete a specified column|
|executeAs(tableName)|Save a table on DolphinDB server with the specified table name|
|execute()|Used with update and delete methods|
|toDF()|Convert a DolphinDB table object to a pandas Dataframe object|

For more methods provided by the `Session` and `Table`, please see files session.py and table.py.

Python API, is a server that can use to retrieve and send data to using code. The python code is converted into a DolphinDB script and executed on the DolphinDB server.

For example, we can create a data table in the following ways:

1. Use method ` table` from `Session` class:
```Python
tdata = {'id': [1, 2, 2, 3],
         'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
         'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'],
         'price': [22, 3.5, 21, 26]}
s.table(data=tdata).executeAs('tb')
```
2. Use method `upload` from `Session` calss:
```Python
tdata = pd.DataFrame({'id': [1, 2, 2, 3], 
                      'date': np.array(['2019-02-04', '2019-02-05', '2019-02-09', '2019-02-13'], dtype='datetime64[D]'),
                      'ticker': ['AAPL', 'AMZN', 'AMZN', 'A'], 
                      'price': [22, 3.5, 21, 26]})
s.upload({'tb': tdata})
```
3. Use method `run` from `Session` calss:

```Python
s.run("tb=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)")
```

These above three methods are similar as using `table` function from DolphinDB to create a new table named `tb`:
```
tb=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)
```
Next, we will use various methods provided by the `Session` in the Python environment to create a distributed database and table, and then append data to the table.

```Python
import dolphindb as ddb
import dolphindb.settings as keys
import numpy as np
s = ddb.session()
s.connect(HOST, PORT, "admin", "123456")
dbPath="dfs://testDB"
tableName='tb'
if s.existsDatabase(dbPath):
    s.dropDatabase(dbPath)
s.database('db', keys.VALUE, ["AAPL", "AMZN", "A"], dbPath)
tdata=s.table(data=createDemoDict()).executeAs("testDict")
s.run("db.createPartitionedTable(testDict, `{tb}, `ticker)".format(tb=tableName))
tb=s.loadTable(tableName, dbPath)
tb.append(tdata)
tb.toDF()

# output
    id       date ticker  price
 0   3 2019-02-13      A   26.0
 1   1 2019-02-04   AAPL   22.0
 2   2 2019-02-05   AMZN    3.5
 3   2 2019-02-09   AMZN   21.0
```
Similarly, we can also directly call the `run` method in python to create a database and table, and then call DolphinDB’s built-in function `append!` to append to table. 
However, remote function `append!` will cost a extra step to return the table structure. Therefore, we recommend adding data through `tableInsert` function.

```Python
import dolphindb as ddb
import numpy as np

s = ddb.session()
s.connect(HOST, PORT, "admin", "123456")
dbPath="dfs://testDB"
tableName='tb'
testDict=pd.DataFrame(createDemoDict())
script="""
dbPath='{db}'
if(existsDatabase(dbPath))
    dropDatabase(dbPath)
db=database(dbPath, VALUE, ["AAPL", "AMZN", "A"])
testDictSchema=table(5:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
db.createPartitionedTable(testDictSchema, `{tb}, `ticker)""".format(db=dbPath,tb=tableName)
s.run(script)
# s.run("append!{{loadTable({db}, `{tb})}}".format(db=dbPath,tb=tableName),testDict)
s.run("tableInsert{{loadTable('{db}', `{tb})}}".format(db=dbPath,tb=tableName),testDict)
s.run("select * from loadTable('{db}', `{tb})".format(db=dbPath,tb=tableName))
```
```
login("admin","123456")
dbPath="dfs://testDB"
tableName=`tb
if(existsDatabase(dbPath))
    dropDatabase(dbPath)
db=database(dbPath, VALUE, ["AAPL", "AMZN", "A"])
testDictSchema=table(5:0, `id`date`ticker`price, [INT,DATE,STRING,DOUBLE])
tb=db.createPartitionedTable(testDictSchem, tableName, `ticker)
testDict=table([1, 2, 2, 3] as id, [2019.02.04,2019.02.05,2019.02.09,2019.02.13] as date, ['AAPL','AMZN','AMZN','A'] as ticker, [22, 3.5, 21, 26] as price)
tb.append!(testDict)
```
#### 8.2 Database Operations
#### 8.2.1 Create databases 
Use method `database` to create a new distributed database.

```Python
import dolphindb.settings as keys
s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```
#### 8.2.2 Drop database 
Use method `dropdatabase` to drop an existing database.

```Python
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```
#### 8.2.3 Drop partitions
Use method `dropPartition` to delete one or more selected partitions.


```Python
import dolphindb.settings as keys

if s.existsDatabase("dfs://valuedb"):
    s.dropDatabase("dfs://valuedb")
s.database('db', partitionType=keys.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
trade=s.loadTextEx(dbPath="dfs://valuedb", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.rows)

# output
13136

s.dropPartition("dfs://valuedb", partitionPaths=["/AMZN", "/NFLX"])
trade = s.loadTable(tableName="trade", dbPath="dfs://valuedb")
print(trade.rows)
# output
4516

print(trade.select("distinct TICKER").toDF())

  distinct_TICKER
0            NVDA
```

#### 8.3 table operations

#### 8.3.1 upload the table from database

For more details please see [chapter 6]()

#### 8.3.2 Add data into database
We could use method `append` to append to database.
The following example appends to a partition table on the disk. To use the appended table, we need to reload it into memory.
```py
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.rows)
# output
13136
# take the top 10 rows of table "trade" on the DolphinDB server
t = trade.top(10).executeAs("top10")

trade.append(t)
# table "trade" needs to be reloaded in order to see the appended records
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print (trade.rows)
# output
13146
```
The following example appends to an in-memory table.
```py
trade=s.loadText(WORK_DIR+"/example.csv")
t = trade.top(10).executeAs("top10")
t1=trade.append(t)
print(t1.rows)
# output
13146
```
For more details, please see chapter 7.

#### 8.3.3 update data from a table
Note that function update must be followed by function execute in order to update the table.

```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade = trade.update(["VOL"],["999999"]).where("TICKER=`AMZN").where(["date=2015.12.16"]).execute()
t1=trade.where("ticker=`AMZN").where("VOL=999999")
print(t1.toDF())
# output
  TICKER        date     VOL        PRC        BID        ASK
0      AMZN  1997.05.15  999999   23.50000   23.50000   23.62500
1      AMZN  1997.05.16  999999   20.75000   20.50000   21.00000
2      AMZN  1997.05.19  999999   20.50000   20.50000   20.62500
3      AMZN  1997.05.20  999999   19.62500   19.62500   19.75000
4      AMZN  1997.05.21  999999   17.12500   17.12500   17.25000
...
4948   AMZN  1997.05.27  999999   19.00000   19.00000   19.12500
4949   AMZN  1997.05.28  999999   18.37500   18.37500   18.62500
4950   AMZN  1997.05.29  999999   18.06250   18.00000   18.12500

[4951 rows x 6 columns]
```
#### 8.3.4 Delete data from a table
Note that function `delete` must be followed by function `execute` in order to delete the data from the table

```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade.delete().where('date<2013.01.01').execute()
print(trade.rows)

# output
3024
```
#### 8.3.5 Drop table columns
```Python
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR + "/valuedb", memoryMode=True)
t1=trade.drop(['ask', 'bid'])
print(t1.top(5).toDF())
  TICKER        date      VOL     PRC
0   AMZN  1997.05.15  6029815  23.500
1   AMZN  1997.05.16  1232226  20.750
2   AMZN  1997.05.19   512070  20.500
3   AMZN  1997.05.20   456357  19.625
4   AMZN  1997.05.21  1577414  17.125
```
#### 8.3.6 Drop a table
```Python
s.dropTable(WORK_DIR + "/valuedb", "trade")
```
### 9 SQLquery
DolphinDB provides flexible chained methods to help users generate SQL statements.
#### 9.1 `select`

#### 9.1.1 Use list as input
We can use a list of field names in **select** method to select columns
```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)
print(trade.select(['ticker','date','bid','ask','prc','vol']).toDF())
# output
  TICKER        date      VOL     PRC     BID     ASK
0   AMZN  1997.05.15  6029815  23.500  23.500  23.625
1   AMZN  1997.05.16  1232226  20.750  20.500  21.000
2   AMZN  1997.05.19   512070  20.500  20.500  20.625
3   AMZN  1997.05.20   456357  19.625  19.625  19.750
4   AMZN  1997.05.21  1577414  17.125  17.125  17.250
...
```
We can use the `showSQL` method to display the SQL statement.
```Python
print(trade.select(['ticker','date','bid','ask','prc','vol']).where("date=2012.09.06").where("vol<10000000").showSQL())
# output
select ticker,date,bid,ask,prc,vol from T64afd5a6 where date=2012.09.06 and vol<10000000
```

#### 9.1.2 Use string as input
We can also pass a list of field names as a string to **select** method and conditions as string to **where** method.
```Python
print(trade.select("ticker,date,bid,ask,prc,vol").where("date=2012.09.06").where("vol<10000000").toDF())
# output
  ticker       date        bid     ask     prc      vol
0   AMZN 2012-09-06  251.42999  251.56  251.38  5657816
1   NFLX 2012-09-06   56.65000   56.66   56.65  5368963
...
```
#### 9.2 `top`

Get the top records in a table.

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
trade.top(5).toDF()
# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```
#### 9.3 `where`

We can use where method to filter the selection.

#### 9.3.1 Filter with multiple conditions
```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)
# use chaining WHERE conditions and save result to DolphinDB server variable "t1" through function "executeAs"
t1=trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("t1")
print(t1.toDF())
# output
         date    bid      ask     prc        vol
0  2007.04.25  56.80  56.8100  56.810  104463043
1  1999.09.29  80.75  80.8125  80.750   80380734
2  2006.07.26  26.17  26.1800  26.260   76996899
3  2007.04.26  62.77  62.8300  62.781   62451660
4  2005.02.03  35.74  35.7300  35.750   60580703
...
print(t1.rows)
765
```
```Python
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc
```
#### 9.3.2 Use string as input

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select("ticker, date, vol").where("bid!=NULL, ask!=NULL, vol>50000000").toDF())
# output
   ticker        date        vol
0    AMZN  1999.09.29   80380734
1    AMZN  2000.06.23   52221978
2    AMZN  2001.11.26   51543686
3    AMZN  2002.01.22   57235489
4    AMZN  2005.02.03   60580703
...
38   NVDA  2016.11.11   54384267
39   NVDA  2016.12.28   57384116
40   NVDA  2016.12.29   54384676
```

#### 9.4 `groupby`
Method `groupby` must be followed by an aggregate function such as `count`, `sum`, or `agg2`.  `agg2` is for DolphinDB functions with 2 arguments.

```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(*)').groupby(['ticker']).sort(bys=['ticker desc']).toDF())
# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```
Group by column "sym" and calculate the sum of columns "vol" and "prc".


```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```
`groupby` with `having`:


```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('count(ask)').groupby(['vol']).having('count(ask)>1').toDF())
# output

       vol  count_ask
0   579392          2
1  3683504          2
2  5732076          2
3  6299736          2
4  6438038          2
5  6946976          2
6  8160197          2
7  8924303          2
...

```

#### 9.5 `contextby`
`contextby` is similar to `groupby` except that `groupby` returns a scalar for each group but `contextby` returns a vector for each group. The vector size is the same as the number of rows in the group.

```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").contextby('ticker').top(3).toDF()
print(df)
  TICKER       date      VOL      PRC      BID      ASK
0   AMZN 1997-05-15  6029815  23.5000  23.5000  23.6250
1   AMZN 1997-05-16  1232226  20.7500  20.5000  21.0000
2   AMZN 1997-05-19   512070  20.5000  20.5000  20.6250
3   NFLX 2002-05-23  7507079  16.7500  16.7500  16.8500
4   NFLX 2002-05-24   797783  16.9400  16.9400  16.9500
5   NFLX 2002-05-28   474866  16.2000  16.2000  16.3700
6   NVDA 1999-01-22  5702636  19.6875  19.6250  19.6875
7   NVDA 1999-01-25  1074571  21.7500  21.7500  21.8750
8   NVDA 1999-01-26   719199  20.0625  20.0625  20.1250

```
```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, cumsum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

    TICKER     month  cumsum_VOL
0       AMZN  1997.05M     6029815
1       AMZN  1997.05M     7262041
2       AMZN  1997.05M     7774111
3       AMZN  1997.05M     8230468
4       AMZN  1997.05M     9807882
...
13133   NVDA  2016.12M   367356016
13134   NVDA  2016.12M   421740692
13135   NVDA  2016.12M   452063951
```

```Python
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, sum(VOL)").contextby("TICKER,month(date)").toDF()
print(df)

 TICKER     month    sum_VOL
0       AMZN  1997.05M   13736587
1       AMZN  1997.05M   13736587
2       AMZN  1997.05M   13736587
3       AMZN  1997.05M   13736587
4       AMZN  1997.05M   13736587
5       AMZN  1997.05M   13736587
...
13133   NVDA  2016.12M  452063951
13134   NVDA  2016.12M  452063951
13135   NVDA  2016.12M  452063951
```

```Python
df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").contextby('ticker').having("sum(VOL)>40000000000").toDF()
print(df)

     TICKER        date       VOL       PRC       BID       ASK
0      NVDA  1999.01.22   5702636   19.6875   19.6250   19.6875
1      NVDA  1999.01.25   1074571   21.7500   21.7500   21.8750
2      NVDA  1999.01.26    719199   20.0625   20.0625   20.1250
3      NVDA  1999.01.27    510637   20.0000   19.8750   20.0000
4      NVDA  1999.01.28    476094   19.9375   19.8750   20.0000
5      NVDA  1999.01.29    509718   19.0000   19.0000   19.3125
...
4512   NVDA  2016.12.27  29857132  117.3200  117.3100  117.3200
4513   NVDA  2016.12.28  57384116  109.2500  109.2500  109.2900
4514   NVDA  2016.12.29  54384676  111.4300  111.2600  111.4200
4515   NVDA  2016.12.30  30323259  106.7400  106.7300  106.7500
```

#### 9.6 Table join
Use method `merge` for inner, left, and outer join; method `merge_asof` for "asof" join; method `merge_window` for “window” join.

#### 9.6.1 `merge`
Specify joining columns with parameter on if joining column names are identical in both tables; use parameters left_on and right_on when joining column names are different. Parameter "how" indicates table join type.


```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': np.array(['2015-12-31', '2015-12-30', '2015-12-29'], dtype='datetime64[D]'), 'open': [695, 685, 674]})
print(trade.merge(t1,on=["TICKER","date"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```
```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER1': ['AMZN', 'AMZN', 'AMZN'], 'date1': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
#use parameters left_on and right_on when joining column names are different
print(trade.merge(t1,left_on=["TICKER","date"], right_on=["TICKER1","date1"]).toDF())

# output
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```
Set the parameter to “left” when using method merge for left join. 

```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,how="left", on=["TICKER","date"]).where('TICKER=`AMZN').where('2015.12.23<=date<=2015.12.31').toDF())

# output
  TICKER       date      VOL        PRC        BID        ASK   open
0   AMZN 2015-12-23  2722922  663.70001  663.48999  663.71002    NaN
1   AMZN 2015-12-24  1092980  662.78998  662.56000  662.79999    NaN
2   AMZN 2015-12-28  3783555  675.20001  675.00000  675.21002    NaN
3   AMZN 2015-12-29  5734996  693.96997  693.96997  694.20001  674.0
4   AMZN 2015-12-30  3519303  689.07001  689.07001  689.09998  685.0
5   AMZN 2015-12-31  3749860  675.89001  675.85999  675.94000  695.0
```
Set the parameter to “outer” when using method merge for outer join.

The partition table can only be linked with the partition table, and the memory table can only be linked with the memory table.

```Python
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'open': [674, 685, 942]})
t2 = s.table(data={'TICKER': ['AMZN', 'NFLX', 'NFLX'], 'date': ['2015.12.29', '2015.12.30', '2015.12.31'], 'close': [690, 936, 951]})
print(t1.merge(t2, how="outer", on=["TICKER","date"]).toDF())

# output
  TICKER        date   open TMP_TBL_ec03c3d2_TICKER TMP_TBL_ec03c3d2_date  \
0   AMZN  2015.12.29  674.0                    AMZN            2015.12.29   
1   AMZN  2015.12.30  685.0                                                 
2   NFLX  2015.12.31  942.0                    NFLX            2015.12.31   
3                       NaN                    NFLX            2015.12.30   

   close  
0  690.0  
1    NaN  
2  951.0  
3  936.0  
```
#### 9.6.2 `merge_asof`
Method `merge_asof` corresponds to DolphinDB asof join(aj). The asof join function is used in non-synchronous join. It is similar to the left join function with the following differences:
- Assume the last matching column is "time". For a row in the left table with time=t, among the rows in the right table that match all other matching columns, if there is not a record with time=t, select the last row before time=t.
- If there is only 1 joining column, the asof join function assumes the right table is sorted on the joining column. If there are multiple joining columns, the asof join function assumes the right table is sorted on the last joining column within each group defined by the other joining columns. The right table does not need to be sorted by the other joining columns. If these conditions are not met, unexpected results may be returned. The left table does not need to be sorted.

In the following examples, we use [trades.csv](data/trades.csv) and [quotes.csv](data/quotes.csv), which contain the AAPL and FB downloaded from the NYSE website on October 24, 2016 Daily transaction and quotation data. 

```Python
import dolphindb.settings as keys

WORK_DIR = "C:/DolphinDB/Data"
if s.existsDatabase(WORK_DIR+"/tickDB"):
    s.dropDatabase(WORK_DIR+"/tickDB")
s.database('db', partitionType=keys.VALUE, partitions=["AAPL","FB"], dbPath=WORK_DIR+"/tickDB")
trades = s.loadTextEx("db",  tableName='trades',partitionColumns=["Symbol"], filePath=WORK_DIR + "/trades.csv")
quotes = s.loadTextEx("db",  tableName='quotes',partitionColumns=["Symbol"], filePath=WORK_DIR + "/quotes.csv")

print(trades.top(5).toDF())

# output
                        Time  Exchange  Symbol  Trade_Volume  Trade_Price
0 1970-01-01 08:00:00.022239        75    AAPL           300        27.00
1 1970-01-01 08:00:00.022287        75    AAPL           500        27.25
2 1970-01-01 08:00:00.022317        75    AAPL           335        27.26
3 1970-01-01 08:00:00.022341        75    AAPL           100        27.27
4 1970-01-01 08:00:00.022368        75    AAPL            31        27.40

print(quotes.where("second(Time)>=09:29:59").top(5).toDF())

# output
                         Time  Exchange  Symbol  Bid_Price  Bid_Size  Offer_Price  Offer_Size
0  1970-01-01 09:30:00.005868        90    AAPL      26.89         1        27.10           6
1  1970-01-01 09:30:00.011058        90    AAPL      26.89        11        27.10           6
2  1970-01-01 09:30:00.031523        90    AAPL      26.89        13        27.10           6
3  1970-01-01 09:30:00.284623        80    AAPL      26.89         8        26.98           8
4  1970-01-01 09:30:00.454066        80    AAPL      26.89         8        26.98           1

print(trades.merge_asof(quotes,on=["Symbol","Time"]).select(["Symbol","Time","Trade_Volume","Trade_Price","Bid_Price", "Bid_Size","Offer_Price", "Offer_Size"]).top(5).toDF())

# output
  Symbol                        Time          Trade_Volume  Trade_Price  Bid_Price  Bid_Size  \
0   AAPL  1970-01-01 08:00:00.022239                   300        27.00       26.9         1   
1   AAPL  1970-01-01 08:00:00.022287                   500        27.25       26.9         1   
2   AAPL  1970-01-01 08:00:00.022317                   335        27.26       26.9         1   
3   AAPL  1970-01-01 08:00:00.022341                   100        27.27       26.9         1   
4   AAPL  1970-01-01 08:00:00.022368                    31        27.40       26.9         1   

   Offer_Price  Offer_Size  
0       27.49           10  
1       27.49           10  
2       27.49           10  
3       27.49           10  
4       27.49           10  
[5 rows x 8 columns]
```
```Python
print(trades.merge_asof(quotes, on=["Symbol","Time"]).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").toDF())

# output
  Symbol       cost
0   AAPL   6.486813
1     FB  35.751041
```
#### 9.6.3 `merge_window`
Method `merge_window` corresponds to DolphinDB window join(wj). Window join is a generalization of asof join. 
The parameters leftBound and rightBound indicate the left bound and the right bound (both are inclusive) of the window relative to the records in the left table, for each row in leftTable with the value of the last column in matchCols equal to t, find the rows in rightTable with the value of the last column in matchCols between (t+w1) and (t+w2) conditional on all other columns in matchCols are matched, then apply aggFunctions to the selected rows in rightTable.

the only difference between window join and prevailing window join is that if the right table doesn't have a matching value for t+w1 (the left boundary of window), prevailing window join will include the last value before t+w1 in the window. We should set the parameter prevailing to True when using prevailing window join.
```Python
print(trades.merge_window(quotes, -5000000000, 0, aggFunctions=["avg(Bid_Price)","avg(Offer_Price)"], on=["Symbol","Time"]).where("Time>=07:59:59").top(10).toDF())

# output
                        Time  Exchange Symbol  Trade_Volume \
0 1970-01-01 08:00:00.022239        75   AAPL           300
1 1970-01-01 08:00:00.022287        75   AAPL           500
2 1970-01-01 08:00:00.022317        75   AAPL           335
3 1970-01-01 08:00:00.022341        75   AAPL           100
4 1970-01-01 08:00:00.022368        75   AAPL            31
5 1970-01-01 08:00:02.668076        68   AAPL          2434
6 1970-01-01 08:02:20.116025        68   AAPL            66
7 1970-01-01 08:06:31.149930        75   AAPL           100
8 1970-01-01 08:06:32.826399        75   AAPL           100
9 1970-01-01 08:06:33.168833        75   AAPL            74

   avg_Bid_Price  avg_Offer_Price
0          26.90            27.49
1          26.90            27.49
2          26.90            27.49
3          26.90            27.49
4          26.90            27.49
5          26.75            27.36
6            NaN              NaN
7            NaN              NaN
8            NaN              NaN
9            NaN              NaN

[10 rows x 6 columns]
```
Window join use the row of **symbol** at **time** to calculate the transaction cost.


```Python
trades.merge_window(quotes,-1000000000, 0, aggFunctions="[wavg(Offer_Price, Offer_Size) as Offer_Price, wavg(Bid_Price, Bid_Size) as Bid_Price]", on=["Symbol","Time"], prevailing=True).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2))/sum(Trade_Volume*Trade_Price)*10000 as cost").groupby("Symbol").executeAs("tradingCost")
print(s.loadTable(tableName="tradingCost").toDF())
# output
  Symbol       cost
0   AAPL   6.367864
1     FB  35.751041
```

#### 9.7 `executeAs`

`executeAs` can help to save the result as a table object in DolphinDB.


```Python
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")
trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("AMZN")
```
Use the generated table: 


```Python
t1=s.loadTable(tableName="AMZN")
```

#### 9.8 Regression
Method **ols** conducts regression analysis. The result is a dictionary with ANOVA, RegressionStat and Coefficient.


```Python
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR + "/valuedb", memoryMode=True)
z=trade.select(['bid','ask','prc']).ols('PRC', ['BID', 'ASK'])

print(z["ANOVA"])

# output
    Breakdown     DF            SS            MS             F  Significance
0  Regression      2  2.689281e+08  1.344640e+08  1.214740e+10           0.0
1    Residual  13133  1.453740e+02  1.106937e-02           NaN           NaN
2       Total  13135  2.689282e+08           NaN           NaN           NaN

print(z["RegressionStat"])

# output
         item    statistics
0            R2      0.999999
1    AdjustedR2      0.999999
2      StdError      0.105211
3  Observations  13136.000000


print(z["Coefficient"])

# output
      factor      beta  stdError      tstat    pvalue
0  intercept  0.003710  0.001155   3.213150  0.001316
1        BID  0.605307  0.010517  57.552527  0.000000
2        ASK  0.394712  0.010515  37.537919  0.000000

print(z["Coefficient"].beta[1])

# output
0.6053065014691369
```
The following example conducts regression on a partitioned database. Note that the ratio operator between 2 integer columns in DolphinDB is "\", which happens to be the escape character in Python, so we need to use "VOL\\SHROUT" in function `select`.


```Python
result = s.loadTable(tableName="US",dbPath="dfs://US").select("select VOL\\SHROUT as turnover, abs(RET) as absRet, (ASK-BID)/(BID+ASK)*2 as spread, log(SHROUT*(BID+ASK)/2) as logMV").where("VOL>0").ols("turnover", ["absRet","logMV", "spread"], True)
print(result["ANOVA"])

   Breakdown        DF            SS            MS            F  Significance
0  Regression         3  2.814908e+09  9.383025e+08  30884.26453           0.0
1    Residual  46701483  1.418849e+12  3.038125e+04          NaN           NaN
2       Total  46701486  1.421674e+12           NaN          NaN           NaN
```



#### 10 More Examples

#### 10.1 Stock momentum strategy

In this section we give an example of a backtest on a stock momentum strategy. 
The momentum strategy is one of the best-known quantitative long short equity strategies. It has been studied in numerous academic and sell-side publications since Jegadeesh and Titman (1993). Investors in the momentum strategy believe among individual stocks, past winners will outperform past losers. 

The most commonly used momentum factor is stocks' past 12 months returns skipping the most recent month. In academic research, the momentum strategy is usually re-balanced once a month and the holding period is also one month. 

In this example, we rebalance 1/5 of our portfolio positions every day and hold the new tranche for 5 days. For simplicity, transaction costs are not considered.

**Create server session**
```Python
import dolphindb as ddb
s=ddb.session()
s.connect("localhost",8921, "admin", "123456")
```

**Step 1:** Load data, clean the data, and construct the momentum signal (past 12 months return skipping the most recent month) for each firm. Undefine the table "USstocks" to release the large amount of memory it occupies. Note that `executeAs` must be used to save the intermediate results on DolphinDB server. Dataset "US" contains US stock price data from 1990 to 2016.


```Python
US = s.loadTable(dbPath="dfs://US", tableName="US")
def loadPriceData(inData):
    s.loadTable(inData).select("PERMNO, date, abs(PRC) as PRC, VOL, RET, SHROUT*abs(PRC) as MV").where("weekday(date) between 1:5, isValid(PRC), isValid(VOL)").sort(bys=["PERMNO","date"]).executeAs("USstocks")
    s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, cumprod(1+RET) as cumretIndex").contextby("PERMNO").executeAs("USstocks")
    return s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, move(cumretIndex,21)/move(cumretIndex,252)-1 as signal").contextby("PERMNO").executeAs("priceData")

priceData = loadPriceData(US.tableName())
# US.tableName() returns the name of the table on the DolphinDB server that corresponds to the table object "US" in Python. 
```

**Step 2:** Generate the portfolios for the momentum strategy.
```Python
def genTradeTables(inData):
    return s.loadTable(inData).select(["date", "PERMNO", "MV", "signal"]).where("PRC>5, MV>100000, VOL>0, isValid(signal)").sort(bys=["date"]).executeAs("tradables")


def formPortfolio(startDate, endDate, tradables, holdingDays, groups, WtScheme):
    holdingDays = str(holdingDays)
    groups=str(groups)
    ports = tradables.select("date, PERMNO, MV, rank(signal,,"+groups+") as rank, count(PERMNO) as symCount, 0.0 as wt").where("date between "+startDate+":"+endDate).contextby("date").having("count(PERMNO)>=100").executeAs("ports")
    if WtScheme == 1:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-1.0/count(PERMNO)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["1.0/count(PERMNO)/"+holdingDays]).execute()
    elif WtScheme == 2:
        ports.where("rank=0").contextby("date").update(cols=["wt"], vals=["-MV/sum(MV)/"+holdingDays]).execute()
        ports.where("rank="+groups+"-1").contextby("date").update(cols=["wt"], vals=["MV/sum(MV)/"+holdingDays]).execute()
    else:
        raise Exception("Invalid WtScheme. valid values:1 or 2")
    return ports.select("PERMNO, date as tranche, wt").where("wt!=0").sort(bys=["PERMNO","date"]).executeAs("ports")

tradables=genTradeTables(priceData.tableName())
startDate="1996.01.01"
endDate="2017.01.01"
holdingDays=5
groups=10
ports=formPortfolio(startDate=startDate,endDate=endDate,tradables=tradables,holdingDays=holdingDays,groups=groups,WtScheme=2)
dailyRtn=priceData.select("date, PERMNO, RET as dailyRet").where("date between "+startDate+":"+endDate).executeAs("dailyRtn")
```

**Step 3:** Calculate the profit/loss for each stock in the portfolio in each of the days in the holding period. Close the positions at the end of the holding period.

```Python
def calcStockPnL(ports, dailyRtn, holdingDays, endDate):
    s.table(data={'age': list(range(1,holdingDays+1))}).executeAs("ages")
    ports.select("tranche").sort("tranche").executeAs("dates")
    s.run("dates = sort distinct dates.tranche")
    s.run("dictDateIndex=dict(dates,1..dates.size())")
    s.run("dictIndexDate=dict(1..dates.size(), dates)")
    ports.merge_cross(s.table(data="ages")).select("dictIndexDate[dictDateIndex[tranche]+age] as date, PERMNO, tranche, age, take(0.0,age.size()) as ret, wt as expr, take(0.0,age.size()) as pnl").where("isValid(dictIndexDate[dictDateIndex[tranche]+age]), dictIndexDate[dictDateIndex[tranche]+age]<=min(lastDays[PERMNO], "+endDate+")").executeAs("pos")
    t1= s.loadTable("pos")
    t1.merge(dailyRtn, on=["date","PERMNO"], merge_for_update=True).update(["ret"],["dailyRet"]).execute()
    t1.contextby(["PERMNO","tranche"]).update(["expr"], ["expr*cumprod(1+ret)"]).execute()
    t1.update(["pnl"],["expr*ret/(1+ret)"]).execute()
    return t1

lastDaysTable = priceData.select("max(date) as date").groupby("PERMNO").executeAs("lastDaysTable")
s.run("lastDays=dict(lastDaysTable.PERMNO,lastDaysTable.date)")
# undefine priceData to release memory
s.undef(priceData.tableName(), 'VAR')
stockPnL = calcStockPnL(ports=ports, dailyRtn=dailyRtn, holdingDays=holdingDays, endDate=endDate)
```

**Step 4:** Calculate portfolio profit/loss

```Python
portPnl = stockPnL.select("pnl").groupby("date").sum().sort(bys=["date"]).executeAs("portPnl")

print(portPnl.toDF())
```
Python Streaming API
---
## 1 Python streaming API
### 1.1 Specify the subscriber port number
Use function `enableStreaming` in Python API to enable streaming data functionality.
Use function subscribe in Python API to subscribe to stream tables in DolphinDB.
```Python
s.enableStreaming(port)
```
 - Port is the subscriber port number for incoming data, and each session has its own unique port.
In the following example, we create a session in Python, and enable the streaming data functionality with specified port number 8000:
```Python
import dolphindb as ddb
import numpy as np
s = ddb.session()
s.enableStreaming(8000)
```

### 1.2 Call function subscribe
Use function subscribe in Python API to subscribe to stream tables in DolphinDB.
Syntax of function subscribe:
```Python
s.subscribe(host, port, handler, tableName, actionName="", offset=-1, resub=False, filter=None)
```
host is the IP address of the publisher node.
port is the port number of the publisher node.
handler is a user-defined function to process the subscribed data.
tableName is a string indicating the name of the publishing stream table.
actionName is a string indicating the name of the subscription task.
offset is an integer indicating the position of the first message where the subscription begins. A message is a row of the stream table. Offset is relative to the first row of the stream table when it is created. If offset is unspecified, or -1, or above the number of rows of the stream table, the subscription starts with the next new message. If some rows were cleared from memory due to cache size limit, they are still considered in determining where the subscription starts.
resub is a Boolean value indicating whether to resubscribe after network disconnection.
filter is a vector indicating filtering condition. Only the rows with values of the filtering column in the vector specified by the parameter 'filter' are published to the subscriber.

Please noted that: Specify parameter maxPubConnections for the publisher.
Refer [streaming](https://github.com/dolphindb/Tutorials_EN/blob/master/streaming_tutorial.mdabout streaming) for more information.

Example: Create a shared stream table 'trades' in DolphinDB and insert data into the table.


```
share streamTable(10000:0,`time`sym`price`id, [TIMESTAMP,SYMBOL,DOUBLE,INT]) as trades
setStreamTableFilterColumn(trades, `sym)
insert into trades values(take(now(), 10), take(`000905`600001`300201`000908`600002, 10), rand(1000,10)/10.0, 1..10)
```
Subscribe to table 'trades' in Python, set the filter to display only symbol 000905:
```Python
def handler(lst):         
    print(lst)

s.subscribe("192.168.1.103",8921,handler,"trades","action",0,False,np.array(['000905']))

# output
[numpy.datetime64('2020-09-24T12:05:53.029'), '000905', 48.3, 1]
[numpy.datetime64('2020-09-24T12:05:53.029'), '000905', 75.4, 6]
```

### 1.3 get subscription topic name
All subscription topics can be obtained through the `getSubscriptionTopics` function. The topic is composed of host/port/tableName/actionName, and all topics in each session are different from each other.
Use to get the all list of subscription topic names. The subscription topic name is a combination of the information about IP address, port number, tableName and actionName, each are separated by “/”.
```Python
s.getSubscriptionTopics()
# output
['192.168.1.103/8921/trades/action']
```

### 1.4 Unsubscribe
Use `unsubscribe` to unsubscribe.
Syntax of `unsubscribe`:
```Python
s.unsubscribe(host,port,tableName,actionName="")
```
Unsubscribe in the example:
```Python
s.unsubscribe("192.168.1.103", 8921,"trades","action")
```

