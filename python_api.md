# DolphinDB Python API

DolphinDB Python API integrates Python with DolphinDB server. DolphinDB objects can be easily converted into Python objects and vise versa. DolphinDB API supports both Python 2.7 and Python 3.6 & above. 
This tutorial uses a csv file: [example.csv](data/example.csv). Note that Linux style absolute path must be provided in order for the DolphinDB server to locate the file.

### 1 Connect to DolphinDB

Python interacts with DolphinDB through a session. In the following example, we first create a session in Python, then connect the session to a DolphinDB server with specified domain name/IP address and port number. We need to start a DolphinDB server before running the following Python script.

```
import dolphindb as ddb
s = ddb.session()
s.connect("localhost",8848)
from dolphindb import *
```

If you need to enter username and password:

```
s.connect("localhost",8848, YOUR_USER_NAME, YOUR_PASS_WORD)
```

### 2 Import data

#### 2.1 Import data as an in-memory table

Users can import text files into DolphinDB with a session method **loadText**. It returns a DolphinDB table object in Python, which corresponds to an in-memory table on the DolphinDB server. The DolphinDB table object in Python has a method **toDF** to convert it to a pandas DataFrame.

This tutorial uses a csv file: [example.csv](data/example.csv). Note that Linux style absolute path must be provided in order for the DolphinDB server to locate the file.

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

Create a value-based partitioned database. As there are only 3 stock symbols in the example.csv, we use **VALUE** as partition type. The parameter **partitions** indicates the partition scheme.

```
s.database('db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
```

To create a partitioned database on DFS (distributed file system), just make the database path start with "dfs://". To run the following example we need to configure a DFS cluster. Please refer to the tutorial multi_machine_cluster_deploy.md. 

```
s.database('db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="dfs://valuedb")
```

In addition to the VALUE partition, DolphinDB also supports SEQ, HASH, RANGE and COMBO partitions.

#### 2.2.2 Create a partitioned table and append data to the table

After a database is created successfully, you can import text files into a partitioned table in the partitioned database with function **loadTextEx**. If the partitioned table does not exist, the function creates it and appends the imported data to it. Otherwise, the function appends the imported data to the partitioned table.

Parameter **dbPath** is the database path; **tableName** is the partitioned table name; **partitionColumns** is the partitioning columns; **filePath** is the absolute path of the text file; **delimiter** is the delimiter of the text file (comma by default).

In the following example, function **loadTextEx** creates a partitioned table **trade** on the server end and then appends the data from **example.csv** to the table. 

```
trade = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")
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

#### 2.3 Import data as in-memory partitioned table

We can import data as an in-memory partitioned table. Operations on an in-memory partitioned table are faster than those on a nonpartitioned in-memory table as the former utilizes parallel computing.

We can use the same function **loadTextEx** to create a in-memory partitioned database, but use an empty string for the parameter **dbPath**.

```
s.database('db', partitionType=VALUE, partitions=["GFGC","EWST","EGAS"], dbPath="")
trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

```

### 3 Load data from database

To load data from database, use function **loadTable**.

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")


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

To load only the "AMZN" partition:

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", partitions="AMZN")
print(trade.count())

# output

4941

```

To load "NFLX" and "NVDA" partitions as an in-memory partitioned table:
```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", partitions=["NFLX","NVDA"], memoryMode=True)

print(trade.count())

# output

8195


```



#### 4 SQL query and computation

DolphinDB's table class provides flexible chained methods to help users generate SQL statements.

#### 4.1 **select**

#### 4.1.1 Use list as input

We can use a list of field names in **select** method to select columns. We can also use **where** method to filter the selection.

```
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade", memoryMode=True)
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').top(5).toDF())

# output

         date    bid      ask     prc        vol
0  2007.04.25  56.80  56.8100  56.810  104463043
1  1999.09.29  80.75  80.8125  80.750   80380734
2  2006.07.26  26.17  26.1800  26.260   76996899
3  2007.04.26  62.77  62.8300  62.781   62451660
4  2005.02.03  35.74  35.7300  35.750   60580703

```

We can use the **showSQL** method to display the SQL statement.

```
print(trade.select(['date','bid','ask','prc','vol']).where('TICKER=`AMZN').where('bid!=NULL').where('ask!=NULL').where('vol>10000000').sort('vol desc').showSQL())

# output
select date,bid,ask,prc,vol from Tff260d29 where TICKER=`AMZN and bid!=NULL and ask!=NULL and vol>10000000 order by vol desc

```

#### 4.1.2 Use string as input

We can also pass a list of field names as a string to **select** method and conditions as string to **where** method.

```
trade.select("ticker, date, vol").where("bid!=NULL, ask!=NULL, vol>50000000").toDF()

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

#### 4.2 **top**

Get the top records in a table. 

```
trade.top(5).toDF()



# output
      TICKER        date       VOL        PRC        BID       ASK
0       AMZN  1997.05.16   6029815   23.50000   23.50000   23.6250
1       AMZN  1997.05.17   1232226   20.75000   20.50000   21.0000
2       AMZN  1997.05.20    512070   20.50000   20.50000   20.6250
3       AMZN  1997.05.21    456357   19.62500   19.62500   19.7500
4       AMZN  1997.05.22   1577414   17.12500   17.12500   17.2500

```

#### 4.3 **selectAsVector**

Export a single column as a vector. 

```
print(t.where('TICKER=`AMZN').where('date>2016.12.15').sort('date').selectAsVector('prc'))

#output
[757.77002 766.      771.21997 770.59998 766.34003 760.59003 771.40002
 772.13    765.15002 749.87   ]
```


#### 4.4 **groupby**

Method **groupby** must be followed by an aggregate function such as **count**, **sum**, **avg**, **std**, **agg** or **agg2**. **agg2** is for DolphinDB functions with 2 arguments.

```
print(trade.select('ticker').groupby(['ticker']).count().sort(bys=['ticker desc']).toDF())

# output
  ticker  count_ticker
0   NVDA          4516
1   NFLX          3679
2   AMZN          4941

```

Group by column "sym" and calculate the sum of columns "vol" and "prc":

```
print(trade.select(['vol','prc']).groupby(['ticker']).sum().toDF())

# output

   ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   NFLX  14928048887  421568.81674
2   NVDA  46879603806  127139.51092
```


**groupby** with **having**:

```
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

#### 4.5 **contextby**

**contextby** is similar to **groupby** except that **groupby** returns a scalar for each group but **contextby** returns a vector for each group. The vector size is the same as the number of rows in the group. 

```
df= s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade").select(["vol","prc"]).contextby('ticker').sum().top(10).toDF()
print(df)

# output
  ticker      sum_vol       sum_prc
0   AMZN  33706396492  772503.81377
1   AMZN  33706396492  772503.81377
2   AMZN  33706396492  772503.81377
3   AMZN  33706396492  772503.81377
4   AMZN  33706396492  772503.81377
5   AMZN  33706396492  772503.81377
6   AMZN  33706396492  772503.81377
7   AMZN  33706396492  772503.81377
8   AMZN  33706396492  772503.81377
9   AMZN  33706396492  772503.81377

```

#### 4.6 Regression

Method **ols** conducts regression analysis. The result is a dictionary with ANOVA, RegressionStat and Coefficient.

```
trade = s.loadTable(dbPath=WORK_DIR + "/valuedb", tableName="trade", memoryMode=True)
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

#### 4.7 **run**

A session object has a method **run** that can be used to execute any DolphinDB script. If the script returns an object in DolphinDB, method **run** converts the object to a corresponding object in Python.  

```
# Load table
trade = s.loadTable(dbPath=WORK_DIR+"/valuedb", tableName="trade")

# query the table and returns a pandas DataFrame
t = s.run("select bid, ask, prc from trade where bid!=NULL, ask!=NULL, vol>1000")
print(t)
```



#### 4.8 Table join

Use method **merge** for inner, left, and outer join; method **merge_asof** for "asof" join.

#### 4.8.1 **merge**

Specify joining columns with parameter **on** if joining column names are identical in both tables; use parameters **left_on** and **right_on** when joining column names are different. Parameter "how" indicates table join type.


Inner join with a partitioned table

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
t1 = s.table(data={'TICKER': ['AMZN', 'AMZN', 'AMZN'], 'date': ['2015.12.31', '2015.12.30', '2015.12.29'], 'open': [695, 685, 674]})
print(trade.merge(t1,on=["TICKER","date"]).select("*").toDF())

# outuput
  TICKER        date      VOL        PRC        BID        ASK  open
0   AMZN  2015.12.29  5734996  693.96997  693.96997  694.20001   674
1   AMZN  2015.12.30  3519303  689.07001  689.07001  689.09998   685
2   AMZN  2015.12.31  3749860  675.89001  675.85999  675.94000   695
```

#### 4.8.2 **merge_asof**
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

#### 5 Append, update and delete

#### 5.1 Append data to a table

Data can be appended to a table with function **append**.

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade", inMem=True)
c1 = trade.count()
print (c1)

 take the top 10 results from the table "trade" and assign it to variable "top10" on the server end
top10 = trade.top(10).executeAs("top10")

append table "top10" to table "trade"
c2 = trade.append(top10).count()
print (c2)
```


#### 5.2 Update data from a table

Note that function **update** must be followed by function **execute** in order to update the table

```
trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade", inMem=True)
trade = trade.update(["VOL"],["999999"]).where("TICKER=`AMZN").where(["date=2015.12.16"]).execute()
t1=trade.where("ticker=`AMZN").where("VOL=999999")
print(t1.toDF())


# output

  TICKER        date     VOL        PRC        BID        ASK
0   AMZN  2015.12.16  999999  675.77002  675.76001  675.83002

```

#### 5.3 Delete data from a table

Note that function **delete** must be followed by function **execute** in order to delete the data from the table

```
trade.delete().where('date<2013.01.01').execute()
print(trade.count())

# output

3024

```

#### 5.4 Drop table columns

```
trade = s.table(dbPath=WORK_DIR + "/valuedb", data="trade", inMem=True)
t1=trade.drop(['ask', 'bid'])
print(t1.top(5))

  TICKER        date      VOL     PRC
0   AMZN  1997.05.15  6029815  23.500
1   AMZN  1997.05.16  1232226  20.750
2   AMZN  1997.05.19   512070  20.500
3   AMZN  1997.05.20   456357  19.625
4   AMZN  1997.05.21  1577414  17.125

```

#### 5.5 Drop a table

After a table is dropped, it can be no longer used. 

```
s.dropTable(WORK_DIR + "/valuedb", "trade")
trade = s.table(dbPath=WORK_DIR + "/valuedb", data="trade", inMem=True)

Exception: ('Server Exception', 'table file does not exist: C:/Tutorials_EN/data/valuedb/trade.tbl')

```


#### 6. Upload data from Python to the DolphinDB server

We can upload a Python object through function **upload** to the DolphinDB server, which takes a Python dictionary object as input. For this dictionary object, the key is the variable name on DolphinDB server and the value is the Python object. This is equivalent to executing **t1=table(1 2 3 4 3 as id, 7.8, 4.6, 5.1, 9.6, 0.1 as value,5, 4, 3, 2, 1 as x)** on the DolphinDB server.

```
df = pd.DataFrame({'id': np.int32([1, 2, 3, 4, 3]), 'value':  np.double([7.8, 4.6, 5.1, 9.6, 0.1]), 'x': np.int32([5, 4, 3, 2, 1])})
s.upload({'t1': df})
print(s.run("t1.value.avg()"))

# output
5.44
```


#### 7 Table object

DolphinDB table object in Python serves as a bridge between a DolphinDB table and a pandas DataFrame. A DolphinDB table object can be created by the **table** method of a session. The input of the **table** method can be a dictionary, a DataFrame, or a table name on the DolphinDB server. It creates a table on the DolphinDB server and assigns it a random table name. The DolphinDB table object in Python has a method **toDF** to convert it to a pandas DataFrame.

```
dt = s.table(data={'id': [1, 2, 2, 3],
                   'sym': ['APPL', 'AMNZ', 'AMNZ', 'A'],
                   'price': [22, 3.5, 21, 26]})
print(dt.toDF())

# output
   id  price   sym
0   1   22.0  APPL
1   2    3.5  AMNZ
2   2   21.0  AMNZ
3   3   26.0     A

```

It generates a SQL query and sends it to the DolphinDB server. A table object is returned. The example below selects column **price** and calculates the average price for each **id**.

```
# average price for each id

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

#### 4 Load data into a partitioned database

To load data with function **loadText**, the data must be smaller than available memory. To work with large data files, a better way is to load data into a partitioned database.


#### 4.1 Create a partitioned database

First, check if the database exists. If it exists, drop the database.

```
if s.existsDatabase(WORK_DIR+"/valuedb"):
    s.dropDatabase(WORK_DIR+"/valuedb")
```


Then, create a value-based partitioned database. Since there are only 3 stock symbols in the example.csv, we use **VALUE** as partition type. The parameter **partitions** indicates the partition scheme.

```
s.database('db', partitionType=VALUE, partitions=["GFGC","EWST", "EGAS"], dbPath="C:/Tutorials_EN/data/valuedb")
```

The only difference between creating a partitioned database on DFS (distributed file system) and creating a local database is the different database path. All DFS database paths start with "dfs://"

```
s.database('db',partitionType=VALUE, partitions=["GFGC","EWST", "EGAS"], dbPath="dfs://valuedb")
```

In addition to the VALUE partition, other partitions supported by DolphinDB include: SEQ, HASH, RANGE and COMBO.

#### 4.2 Create a partitioned table and append data to the table

After the database is created successfully, you can import the text file into the partitioned database with function **loadTextEx**. If the partitioned table does not exist, the function creates a partition table (with the given table name) in the database and appends the data to the partitioned table. Otherwise, the function loads the input data directly into the partitioned table.

Parameter **dbPath** is the database path; **tableName** is the partitioned table name; **partitionColumns** indicates the partitioning columns; **filePath** is the absolute path of the text file; **delimiter** is the separator of the file (comma by default).

In the following example, function **loadTextEx** creates a partitioned table **trade** on the server end and then appends the data from **example.csv** to the table. 

```
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
```

To refer to the table later:

```
 trade = s.table(dbPath=WORK_DIR+"/valuedb", data="trade")
```


#### 4.3 In-memory partitioned table

To utilize distributed computing on the partitioned database, we can import data directly into an in-memory partitioned table.

#### 4.3.1 loadTextEx

We can use the same function loadTextEx, which differs from the disk-based partitioned table in that the dbPath is an empty string.


```
# create a in-memory partitioned database **db**. note that dbPath must be empty
s.database('db',partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath="")

# **dbPath** specifies here the database handle **db** on the server end instead of a real database path since we just create a in-memory database **db**

trade=s.loadTextEx(dbPath="db", partitionColumns=["TICKER"], tableName='trade', filePath=WORK_DIR + "/example.csv")
print(trade.toDF())

# output
     TICKER        date       VOL       PRC       BID       ASK
0       AMZN  1997.05.15   6029815   23.5000   23.5000   23.6250
1       AMZN  1997.05.16   1232226   20.7500   20.5000   21.0000
2       AMZN  1997.05.19    512070   20.5000   20.5000   20.6250
3       AMZN  1997.05.20    456357   19.6250   19.6250   19.7500
4       AMZN  1997.05.21   1577414   17.1250   17.1250   17.2500
...

13134   NVDA  2016.12.29  54384676  111.4300  111.2600  111.4200
13135   NVDA  2016.12.30  30323259  106.7400  106.7300  106.7500

[13136 rows x 6 columns]
```

#### 4.3.2 loadTableBySQL

Import partial data from a on-disk partitioned table into a in-memory partitioned table through function s.loadTableBySQL

```
if s.existsDatabase(WORK_DIR+"/valuedb"  or os.path.exists(WORK_DIR+"/valuedb")):
    s.dropDatabase(WORK_DIR+"/valuedb")
s.database(dbName='db', partitionType=VALUE, partitions=["AMZN","NFLX", "NVDA"], dbPath=WORK_DIR+"/valuedb")
t = s.loadTextEx("db",  tableName='trade',partitionColumns=["TICKER"], filePath=WORK_DIR + "/example.csv")

trade = s.loadTableBySQL(dbPath=WORK_DIR+"/valuedb", sql="select * from trade where date>2010.01.01")
print(trade.count())

# output 

5286

```


#### 4.3.3 ploadText: loadText in parallel mode

If we use function **ploadText** to load a text file, it actually generates an in-memory partitioned table. Compared to the non-partitioned table, it will be much faster, but it also consumes twice as much memory.

```
trade=s.ploadText(WORK_DIR+"/example.csv")
print(trade.count())

# output

13136

````

