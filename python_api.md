# Python API for DolphinDB

The Python API supports both Python Python 2.7 or 3.6 & above.

The python API in essense encapsulates a subset of the DolphinDB script language. When a Python script is executed, it will be converted to a DolphinDB script. The DolphinDB script can then be executed on the DolphinDB server triggered by certain methods.
The execution result can either be saved to a variable on DolphinDB server, or serialized to a python client object. There are two kinds of methods provided by the Python API for this purpose. The first one does not trigger the execution of the script, but only generates the script.
The second is a method that triggers script execution. Most of functions and methods do not trigger script execution, but generate a script for later execution. The table below lists all the methods that trigger the DolphinDB script execution.

| Method        | Explanation          |
|:------------- |:-------------|
|toDF()    | Belongs to Table class; converted from DolphinDB table object to pandas Dataframe object|
|executeAs(NewTableName)    | Belongs to Table class; save the filtered table subset to variable NewTableName |
|ols(Y,X, intercept)    | Belongs to Table class; linear regression function that returns a dictionary |
|execute()    | Belongs to Table class; used with method update and delete|


This tutorial uses a csv file: [example.csv](data/example.csv).


### 1 Connect to DolphinDB

Python interacts with DolphinDB through a session. In the following example, we first create a session in Python, then connect the session to a DolphinDB server with specified domain name/IP address and port number. We need to start a DolphinDB server before running the following Python script.

```
import dolphindb as ddb
s = ddb.session()
s.connect("localhost",8848)
```

If you need to enter username and password:

```
s.connect("localhost",8848, YOUR_USERNAME, YOUR_PASSWORD)
```

The default admin account name and password for DolphinDB server are "admin" and "123456" respectively.

### 2 Import data to DolphinDB server

There are three types of DolphinDB databases: DFS(Distributed File System), local disk, and memory. DolphinDB is mainly a distributed database system and performs the best in DFS mode. Moreover, DFS automatically manages where the data should be stored and how they should be duplicated to prevent data loss.
Therefore, we highly recommend users to use DolphinDB in DFS mode. Please refer to tutorial multi_machine_cluster_deploy for details. However, in order for users to get started quickly, we use local disk for demonstration. Actually, the only difference between DFS and other types of databases is on how you name the path. All the paths of DFS databases
starts with "dfs://".

#### 2.1 Import data as an in-memory table

Users can import text files into DolphinDB with a session method called **loadText**. It returns a DolphinDB table object in Python, which corresponds to an in-memory table on the DolphinDB server. The DolphinDB table object in Python has a method **toDF** to convert it to a pandas DataFrame.

```
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

The default delimiter for function **loadText** is comma ",". You can specify other single characters as delimiters. For example, to import a tabular text file:

```
t1=s.loadText(WORK_DIR+"/t1.tsv", '\t')
```

#### 2.2 Import data into a partitioned database

To load data with function **loadText**, the data must be smaller than available memory. To work with large data files, we can load data into a partitioned database.


#### 2.2.1 Create a partitioned database

After we create a partitioned database, we cannot change its partitioning scheme. To make sure the examples below do not use pre-defined databases, check if the database "valuedb" exists. If it exists, drop the database.

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

Create a value-based partitioned database. As there are only 3 stock tickers in the example.csv, we use **VALUE** as partition type. The parameter **partitions** indicates the partition scheme.

```
# 'db' inidcates the database handle name, i.e, the database variable name on the DolphinDB server
# this is equivalent to executue 'db=database(=WORK_DIR+"/valuedb", VALUE, ["AMZN","NFLX", "NVDA"])' on DolphinDB server
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")

```

To create a partitioned database on DFS , just make the database path start with "dfs://". To run the following example, users need to configure a DFS cluster. Please refer to the tutorial multi_machine_cluster_deploy.md.

```
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
```

In addition to the VALUE partition, DolphinDB also supports SEQ, RANGE, LIST, COMBO, and HASH partitions.

#### 2.2.2 Create a partitioned table and append data to the table

After a database is created successfully, you can import text files into a partitioned table in the partitioned database with function **loadTextEx**. If the partitioned table does not exist, the function creates it and appends the imported data to it. Otherwise, the function appends the imported data to the partitioned table.

Parameter **dbPath** is the database path; **tableName** is the partitioned table name; **partitionColumns** is the partitioning columns; **filePath** is the absolute path of the text file; **delimiter** is the delimiter of the text file (comma by default).

In the following example, function **loadTextEx** creates a partitioned table **trade** on the server end and then appends the data from **example.csv** to the table. 

```

if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
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

# shows how many rows in the table
print(trade.rows)
13136

# shows how many columns in the table
print(trade.cols)
6

# shows the schema of the table
print(trade.schema)
     name typeString  typeInt
0  TICKER     SYMBOL       17
1    date       DATE        6
2     VOL        INT        4
3     PRC     DOUBLE       16
4     BID     DOUBLE       16
5     ASK     DOUBLE       16

```

To refer to the table later:

```
 trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")

```



#### 2.3 Import data as in-memory partitioned table

#### 2.3.1 loadTextEx
We can import data as an in-memory partitioned table. Operations on an in-memory partitioned table are faster than those on a nonpartitioned in-memory table as the former utilizes parallel computing.

We can use the same function **loadTextEx** to create a in-memory partitioned database, but use an empty string for the parameter **dbPath**.

```

s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="")

# "dbPath='db'" means that the system uses database handle 'db' to import data into in-memory partitioned table trade
trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")


```


#### 2.3.2 ploadText

If we use function **ploadText** to load a text file, it loads the data in parallel and runs much faster but consumes more memory.It also generates an in-memory partitioned table.

```
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.rows)

# output

13136

````

#### 2.4 Upload data from Python to the DolphinDB server

#### 2.4.1 Through a python dictionary
We can upload a Python object through function **upload** to the DolphinDB server, which takes a Python dictionary object as input. For this dictionary object, the key is the variable name on DolphinDB server and the value is the Python object.
This is equivalent to executing **t1=table(1 2 3 4 3 as id, 7.8, 4.6, 5.1, 9.6, 0.1 as value,5, 4, 3, 2, 1 as x)** on the DolphinDB server.

```
df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```

#### 2.4.2 Through table function.

DolphinDB table object in Python serves as a bridge between a DolphinDB table and a pandas DataFrame. A DolphinDB table object can be created by the **table** method of a session.

The input of the **table** method can be a dictionary, a DataFrame, or a table name on the DolphinDB server. It creates a table on the DolphinDB server and assigns it a random table name.

```
dt = s.table(data={'id': [1, 2, 2, 3],
                   'ticker': ['APPL', 'AMNZ', 'AMNZ', 'A'],
                   'price': [22, 3.5, 21, 26]})
print(dt.toDF())

# output
   id  price   sym
0   1   22.0  APPL
1   2    3.5  AMNZ
2   2   21.0  AMNZ
3   3   26.0     A

# save the table to DolphinDB server variable "test"
dt = s.table(data={'id': [1, 2, 2, 3],
                   'ticker': ['APPL', 'AMNZ', 'AMNZ', 'A'],
                   'price': [22, 3.5, 21, 26]}).executeAs("test")

# load table "test" on DolphinDB server(just uploaded from Python)
print(s.loadTable("test").toDF())

# output
   id  price   sym
0   1   22.0  APPL
1   2    3.5  AMNZ
2   2   21.0  AMNZ
3   3   26.0     A

```

The following statements generate SQL queries and then send them to the DolphinDB server.  The example below selects column **price** and calculates the average price for each **id** less than 3.

```
# average price for each id
dt = s.table(data={'id': [1, 2, 2, 3],
                   'ticker': ['APPL', 'AMNZ', 'AMNZ', 'A'],
                   'price': [22, 3.5, 21, 26]})

print(dt['price'][dt.id < 3].groupby('id').avg().toDF())

# output
   id  avg_price
0   1       22.0
1   2       12.25

print(dt['price'][(dt.price > 10) & (dt.id < 3)].groupby('id').avg().toDF())

# output
   id  avg_price
0   1       22.0
1   2       21.0

print(  dt['price'][(dt.price > 10) & (dt.id < 3)].groupby('id').avg().showSQL())

# output
select avg(price) from T699daec5 where ((price > 10) and (id < 3)) group by id

```


#### 3 Load DolphinDB database tables


#### 3.1 loadTable

To load data from database, we use function **loadTable**. Parameter tableName **indicates** the partitioned table name in the database specified by argument **dbPath** that shows the database location. When "dbPath" is not specified,
**loadTable** will try to find the variable on DolphinDB server that points to a DolphinDB table using argument **tableName**.

#### 3.1.1 Load entire table

```
# this is equivalent to executing 'trade = loadTable(WORK_DIR+"/valuedb", "trade")' on DolphinDB server
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

#### 3.1.2 Load selected partitions

To load only the "AMZN" partition:

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions="AMZN")
print(trade.rows)

# output

4941

```

#### 3.1.3 load as in-memory table

When memoryNode is set to True,we load "NFLX" and "NVDA" partitions as an in-memory partitioned table:

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", partitions=["NFLX","NVDA"], memoryMode=True)
print(trade.rows)
# output

8195

```


#### 3.2. loadTableBySQL

We provide another flexible function **loadTableBySQL** to allow users to import partial data from a on-disk partitioned table into a in-memory partitioned table through a SQL query.

```
import os
if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(tableName="trade", dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.rows)

# output

5286

```


#### 4 Manipulate Databases and Tables

#### 4.1 Database operations

#### 4.1.1 Creating a database

As introduced in early sections, we can use session function database to create a partitioned database.

```
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```


#### 4.1.2 Drop a database

To drop a database, i.e., remove all data in the database and its physical path, we use function: dropDatabase(dbPath). The following statement will drop a database if it exists (databaseExists(dbPath)) on disk.

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```

#### 4.1.3 Drop a DFS database partition

We use session function dropPartition to drop a DFS database partition. Note that only DFS database is supported.

**Drop partitions**

When the partition(s) is(are) dropped, all associated tables' data on those partitions are also dropped.

```
if s.existsDatabase("dfs://valuedb"):
    s.dropDatabase("dfs://valuedb")
s.database('db', partitionType=ddb.VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
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

**Drop partitions for a table**

```
s.dropPartition(dbPath=WORK_DIR+"/valuedb", partitionPaths=["/AMZN", "/NFLX"], tableName="trade")

```


#### 4.2 Table operations

#### 4.2.1 Load a database table

This has been introduced in section 3.1


#### 4.2.2 Append data to a table

**Append a table to a partitioned table on disk**

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
c1 = trade.rows
print(c1)

#output
13136

# take the top 10 results from the table "trade" and assign it to variable "top10" on the DolphinDB server
top10 = trade.top(10).executeAs("top10")

trade.append(top10)

# table has to be reloaded in order to see the appended records
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
c1 = trade.rows
print (c1)


# output
13146
```

**Append a table to an in-memory table**

```
trade=s.loadText(WORK_DIR+"/example.csv")
top10 = trade.top(10).executeAs("top10")
t1=trade.append(top10)

print(t1.rows)

# output
13146

```


#### 4.3 Update data from a table

Note that function **update** must be followed by function **execute** in order to update the table. Note that inMem has to be set to True in order to make update to the partitioned table
as on-disk partitioned table does not support update.

```
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


#### 4.4 Delete data from a table

Note that function **delete** must be followed by function **execute** in order to delete the data from the table

```
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade.delete().where('date<2013.01.01').execute()
print(trade.rows)

# output

3024

```

#### 4.5 Drop table columns

```
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

#### 4.6 Drop a table


```
s.dropTable(WORK_DIR + "/valuedb", "trade")
trade = s.loadTable(tableName="trade", dbPath=WORK_DIR + "/valuedb", memoryMode=True)

// since table is dropped, it will throw exception.
Exception: ('Server Exception', 'table file does not exist: C:/Tutorials_EN/data/valuedb/trade.tbl')

```



#### 5 SQL query

DolphinDB's table class provides flexible chained methods to help users generate SQL statements.

#### 5.1 **select**

#### 5.1.1 Use list as input

We can use a list of field names in **select** method to select columns.

```
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

We can use the **showSQL** method to display the SQL statement.

```
print(trade.select(['ticker','date','bid','ask','prc','vol']).showSQL())

# output
select ticker,date,bid,ask,prc,vol from Tff260d29

```

#### 5.1.2 Use string as input

We can also pass a list of field names as a string to **select** method and conditions as string to **where** method.

```
trade.select("ticker, date, vol").toDF()

# output
     ticker        date       vol
0       AMZN  1997.05.15   6029815
1       AMZN  1997.05.16   1232226
2       AMZN  1997.05.19    512070
3       AMZN  1997.05.20    456357
4       AMZN  1997.05.21   1577414
...

```


#### 5.2 **top**

Get the top records in a table.

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)
trade.top(5).toDF()

# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```

#### 5.3 **where**

We can also use **where** method to filter the selection.

#### 5.3.1 Use chaining method

We can use chaining method to apply multiple where conditions.

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb", memoryMode=True)

# use chaining where conidtions and save filtered result to DolphinDB server variable "t1" through function "executeAs"
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

We can use the **showSQL** method to display the SQL statement.

```
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc

```

#### 5.3.2 Use string as input

We can also pass a list of field names as a string to **select** method and conditions as string to **where** method.

```
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


#### 5.4 **groupby**

Method **groupby** must be followed by an aggregate function such as **count**, **sum**, **avg**, **std**, **agg** or **agg2**. **agg2** is for DolphinDB functions with 2 arguments.

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select('ticker').groupby(['ticker']).count().sort(bys=['ticker desc']).toDF())

# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```

Group by column "ticker" and calculate the sum of columns "vol" and "prc":

```
trade = s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb")
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```


**groupby** with **having**:

```
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

#### 5.5 **contextby**

**contextby** is similar to **groupby** except that **groupby** returns a scalar for each group but **contextby** returns a vector for each group. The vector size is the same as the number of rows in the group.

#### 5.5.1 contextby + top

```
df= s.loadTable( tableName="trade",dbPath=WORK_DIR+"/valuedb").contextby('ticker').top(5).toDF()
print(df)

  TICKER        date      VOL     PRC     BID     ASK
0   AMZN  1997.05.15  6029815  23.500  23.500  23.625
1   AMZN  1997.05.16  1232226  20.750  20.500  21.000
2   AMZN  1997.05.19   512070  20.500  20.500  20.625
3   AMZN  1997.05.20   456357  19.625  19.625  19.750
4   AMZN  1997.05.21  1577414  17.125  17.125  17.250

```

#### 5.5.2 contextby + having

```
df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").contextby('ticker').having(" sum(VOL)>40000000000").toDF()
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


#### 5.5.3 contextby multiple columns and calculated columns

**Vector functions**

```
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, cumsum(VOL)").contextBy("TICKER,month(date)").toDF()
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

**Aggregated functions**

```
df= s.loadTable(tableName="trade",dbPath=WORK_DIR+"/valuedb").select("TICKER, month(date) as month, sum(VOL").contextBy("TICKER,month(date)").toDF()
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



#### 5.6 Table join

We use method **merge** for inner, left, and outer join; method **merge_asof** for "asof" join; method **merge_window** for "window join".

#### 5.6.1 **merge**

Specify joining columns with parameter **on** if joining column names are identical in both tables; use parameters **left_on** and **right_on** when joining column names are different. Parameter "how" indicates table join type.


**Inner join**

Inner join is the default value for function merge when the optional parameter "how" is not set.

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})

# Below is the same as print(trade.merge(t1,how="inner",on=["TICKER","date"]).select("*").toDF())
print(trade.merge(t1,on=["TICKER","date"]).select("*").toDF())

# outuput
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

We have to specify arguments "left_on" and "right_on" when left joining columns and right joining columns are using different names

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
t1 = s.table(data={'TICKER1': ['AMZN', 'AMZN', 'AMZN'], 'date1': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,left_on=["TICKER","date"], right_on=["TICKER1","date1"]).select("*").toDF())

# outuput
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

**Left join**

To use left join, set parameter "how" to value "left"

```
print(trade.merge(t1,how="left", on=["TICKER","date"]).select("*").toDF())
        TICKER        date       VOL       PRC       BID       ASK  open
0       AMZN  1997.05.15   6029815   23.5000   23.5000   23.6250   NaN
1       AMZN  1997.05.16   1232226   20.7500   20.5000   21.0000   NaN
2       AMZN  1997.05.19    512070   20.5000   20.5000   20.6250   NaN
3       AMZN  1997.05.20    456357   19.6250   19.6250   19.7500   NaN
...
13142   NVDA  2016.12.27  29857132  117.3200  117.3100  117.3200   NaN
13143   NVDA  2016.12.28  57384116  109.2500  109.2500  109.2900   NaN
13144   NVDA  2016.12.29  54384676  111.4300  111.2600  111.4200   NaN
13145   NVDA  2016.12.30  30323259  106.7400  106.7300  106.7500   NaN

```

**Outer join (Full join)**

To use outer join, set parameter "how" to value "outer". Partitioned table can only be outer jointed with partitioned table. In-memory table can only be outer joined with in-memory table.

```
print(trade.merge(t1,how="outer", on=["TICKER","date"]).select("*").toDF())

t2 = s.table(data={'TICKER': ['NFLX', 'NFLX', 'NFLX'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [892, 185, 1000]})
print(t1.merge(t2,how="left", lefton=["TICKER","date"]).select("*").toDF())

  TICKER        date   open T615123b5_TICKER T615123b5_date  T615123b5_open
0   AMZN  2015.12.31  695.0                                             NaN
1   AMZN  2015.12.30  685.0                                             NaN
2   AMZN  2015.12.29  674.0                                             NaN
3                       NaN             NFLX     2015.12.29          1000.0
4                       NaN             NFLX     2015.12.30           185.0
5                       NaN             NFLX     2015.12.31           892.0

```



#### 5.6.2 **merge_asof**
Method **merge_asof** corresponds to DolphinDB asof join(aj). The joining column of method **merge_asof** must be integer or temporal data type. If there is only 1 joining column, the asof join function assumes the right table is sorted on the joining column. 
If there are multiple joining columns, the asof join function assumes the right table is sorted on the last joining column within each group defined by the other joining columns. In the example below, although there are no values for 1997 in table t1, 
the joined table uses the last lastest available data points from 1993.12.31. 

```
from datetime import datetime
dates = [Date.from_date(x) for x in [datetime(1993,12,31), datetime(2015,12,30), datetime(2015,12,29)]]
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': dates, 'open': [695, 685, 674]})

print(trade.merge_asof(t1,on=["date"]).select(["date","prc","open"]).top(5).toDF())

         date     prc  open
0  1997.05.16  23.500   23
1  1997.05.17  20.750   23
2  1997.05.20  20.500   23
3  1997.05.21  19.625   23
4  1997.05.22  17.125   23


```


#### 5.6.3 **merge_window**

**merge_window** as "window join" is a generalization of "asof" join. For each row in leftTable, window join applies aggregate functions on a window of rows in rightTable.If window defined by parameters: leftBound and rightBound,
for each row in leftTable with the value of the last column in matchCols equal to t, find the rows in rightTable with matching values of the other columns in matchCols and the value of the last column in matchCols between (t+w1) and (t+w2),
then apply aggFunctions to the selected rows in rightTable.The only difference between window join and prevailing window join is that if rightTable doesn't contain a matching value for w1 (the left boundary of window),
prevailing window join will fill it with the last value before w1 (with all the matching columns except the last one are matched), and apply the aggregate functions.

```
t= s.loadText(filename=WORK_DIR+"/example.csv")
wjt = t.merge_window(t, -10, -5, aggFunctions='sum(VOL)', on=["TICKER","date"]).toDF()
print(wjt)

   TICKER        date       VOL        PRC        BID       ASK     sum_VOL
0       AMZN  1997.05.15   6029815   23.50000   23.50000   23.6250         NaN
1       AMZN  1997.05.16   1232226   20.75000   20.50000   21.0000         NaN
2       AMZN  1997.05.19    512070   20.50000   20.50000   20.6250         NaN
3       AMZN  1997.05.20    456357   19.62500   19.62500   19.7500   6029815.0
4       AMZN  1997.05.21   1577414   17.12500   17.12500   17.2500   7262041.0
5       AMZN  1997.05.22    983855   16.75000   16.62500   16.7500   7262041.0
6       AMZN  1997.05.23   1330026   18.00000   18.00000   18.1250   7262041.0
7       AMZN  1997.05.27    726192   19.00000   19.00000   19.1250   4761922.0
8       AMZN  1997.05.28    382132   18.37500   18.37500   18.6250   6091948.0
9       AMZN  1997.05.29    289970   18.06250   18.00000   18.1250   4859722.0
...

```

Perform windows join on two DFS tables

```
trade = s.loadTable(tableName="trade", dbPath="dfs://EQY")
nbbo = s.loadTable(tableName="nbbo", dbPath="dfs://EQY")

trade.merge_window(nbbo,leftBound=-100000000, rightBound=0,aggFunctions="[avg(Offer_Price) as Offer_Price, avg(Bid_Price) as Bid_Price]",left_on=["Symbol","Time"], prevailing=True).select("sum(Trade_Volume*abs(Trade_Price-(Bid_Price+Offer_Price)/2)/sum(Trade_Volume*Trade_Price))*10000 as cost").groupby("symbol").executeAs("TC2")
print(s.loadTable(tableName="TC2").where("symbol in `GS`TSLA`AAPL").toDF())

  symbol       cost
0   AAPL   0.547702
1     GS   1.081448
2   TSLA  17.893567

```

#### 5.7 executeAs

For almost all the examples above, when applying filtering, we do not save the filtering results on the server. Sometimes, we need to work on a subset of table. In order to do so, we need to use a very import
function "executeAs(NewTableName)", which is equivalent to saving a table or the subset of the data table to a new table(NewTableName) on DolphinDB server.


```
trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').executeAs("amznData")

# Above is the same as executing  "amznData = select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc" on DolphinDB server

```

To refer the new generated table "amznData" on DolphinDB server:

```
t1=s.loadTable(tableName="amznData")

```


#### 6 Computing

#### 6.1 Regression

Method **ols** conducts regression analysis. The result is a dictionary with ANOVA, RegressionStat and Coefficient.

```
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
0.6053065019659698
```

#### 6.2 **run**

A session object has a method **run** that can be used to execute any DolphinDB script. If the script returns an object in DolphinDB, method **run** converts the object to a corresponding object in Python.  

```
# Load table
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")

# query the table and returns a pandas DataFrame
t = s.run("select bid, ask, prc from trade where bid!=NULL, ask!=NULL, vol>1000")
print(t)
```

#### 7 Comprehensive examples


#### 7.1 Build a momentum strategy
In this section we give an example of conducting a backtest on a stock momentum strategy. The momentum strategy is one of the best-known quantitative long short equity strategies. It has been studied in numerous academic and sell-side publications since Jegadeesh and Titman (1993). Investors in the momentum strategy believe among individual stocks, past winners will outperform past losers.
The most commonly used momentum factor is stocks' past 12 months returns skipping the most recent month. In academic publications, the momentum strategy is usually rebalanced once a month and the holding period is also one month. In this example, we rebalance roughly 1/21 of our portfolio everyday and hold the new tranche for 21 days. For simplicity, transaction costs are not considered.

**Build server session**

```
import dolphindb as ddb
s=ddb.session()
s.connect("localhost",8921, "admin", "123456")

```

**Step 1:** Load the data file, clean the data by applying some filters on the data, and construct the momentum signal (past 12 months return skipping the most recent month) for each firm. Undefine table USstocks to release the large amount of memory it occupies.

Note that "executeAs" must be used in order to save the intermediate filtering results on DolphinDB server, otherwise the filtering will not be triggered.
Data set "US" contains US stock price data from 1990 to 2016.

```
US = s.loadTable(dbPath="dfs://US", tableName="US")
def loadPriceData(inData):
    s.loadTable(inData).select("PERMNO, date, abs(PRC) as PRC, VOL, RET, SHROUT*abs(PRC) as MV").where("weekday(date) between 1:5, isValid(PRC), isValid(VOL)").sort(bys=["PERMNO","date"]).executeAs("USstocks")
    s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, cumprod(1+RET) as cumretIndex").contextby("PERMNO").executeAs("USstocks")
    return s.loadTable("USstocks").select("PERMNO, date, PRC, VOL, RET, MV, move(cumretIndex,21)/move(cumretIndex,252)-1 as signal").contextby("PERMNO").executeAs("priceData")

# US.tableName() corresponds to the variable on DolphinDB server that points to table "US"
priceData = loadPriceData(US.tableName())

```

**Step 2:** Generate the portfolios for the momentum strategy.

```
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
holdingDays=21
groups=10
ports=formPortfolio(startDate=startDate,endDate=endDate,tradables=tradables,holdingDays=holdingDays,groups=groups,WtScheme=2)
dailyRtn=priceData.select("date, PERMNO, RET as dailyRet").where("date between "+startDate+":"+endDate).executeAs("dailyRtn")

```

**Step 3:** Calculate the profit/loss for each stock in our portfolio in each of the subsequent holding period days. Close the position for a stock at the end of the holding period.

```
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

```
portPnl = stockPnL.select("pnl").groupby("date").sum().executeAs("portPnl")
portPnl = portPnl.sort(bys=["date"])
print(portPnl.toDF())

      date   sum_pnl
0     1996.01.03 -0.001723
1     1996.01.04 -0.002033
2     1996.01.05 -0.000283
3     1996.01.08  0.000076
4     1996.01.09 -0.007517
5     1996.01.10  0.000964
...
5283  2016.12.27  0.005143
5284  2016.12.28 -0.001795
5285  2016.12.29  0.006746
5286  2016.12.30 -0.009754

```

#### 7.2 Distributed multiple linear regression

Table function ols is for calculating linear regression on DolphinDB table columns. A complicated multiple linear regression calculation  below could be completed with just one line of code.
Note that when both columns are integers, we use ratio operator "\", which happens to be the escape character in python, so we have to pass "VOL\\SHROUT" to function select as blow.

```
result = s.loadTable(tableName="US",dbPath="dfs://US").select("select VOL\\SHROUT as turnover, abs(RET) as absRet, (ASK-BID)/(BID+ASK)*2 as spread, log(SHROUT*(BID+ASK)/2) as logMV").where("VOL>0").ols("turnover", ["absRet","logMV", "spread"], True)
print(result["ANOVA"])

   Breakdown        DF            SS            MS            F  Significance
0  Regression         3  2.814908e+09  9.383025e+08  30884.26453           0.0
1    Residual  46701483  1.418849e+12  3.038125e+04          NaN           NaN
2       Total  46701486  1.421674e+12           NaN          NaN           NaN

```

#### 7.3 A time series decay factor calculation

The example below shows how to generate a decay factor with Python API.

```
def alpha98(t):
    t1 = s.table(data=t)
    # add two calcualted columns through function update
    t1.contextby(["date"]).update(cols=["rank_open","rank_adv15"], vals=["rank(open)","rank(adv15)"]).execute()
    # add two more calculated columns
    t1.contextby(["PERMNO"]).update(["decay7", "decay8"], ["mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7)","mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8)"]).execute()
    # return the final results with three columns: PERMNO, date, and A98
    return t1.select("PERMNO, date, rank(decay7)-rank(decay8) as A98").contextby(["date"]).executeAs("alpha98")

US = s.loadTable(tableName="US", dbPath="dfs://US").select("PERMNO, date, PRC as vwap, PRC+rand(1.0, PRC.size()) as open, mavg(VOL, 5) as adv5, mavg(VOL,15) as adv15").where("2007.01.01<=date<=2016.12.31").contextby("PERMNO").executeAs("US")
result=alpha98(US.tableName()).where('date>2007.03.12').executeAs("result")
print(result.top(100).toDF())

```

