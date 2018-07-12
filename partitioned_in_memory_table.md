
# How to load a large dataset as a partitioned in-memory table


DolphinDB offers the following 4 ways to load a large dataset as a partitioned in-memory table. For each approach, we will give an example in the section of “Examples”.

**1. Use ploadText to import a text file as an in-memory table with sequential partition**

When we would like to import a text file smaller than the memory, we can use this approach. The sequential partition table, however, cannot be used to execute within-partition sorting tasks.

**2. Use loadTextEx to import a text file as an in-memory table with specified partition scheme**

This use case is for the following situations:
* Within-partition sorting
* Optimal performance of “group by” operations. When the grouping column and the partitioning column are identical, the performance is optimal.

For this use case, please use empty string ("") for the parameter of tableName of function loadTextEx and the directory parameter in the definition of the database.

**3. Create a partitioned table in a partitioned database on disk, and use loadTable to import the entire table or selected partitions into memory**

This use case is for the following situations:
 * When we work with a text file that is larger than the memory of the server, and only a subset of the data are needed each time.
 * Use the same data set repeatedly. It is much faster to load a DolphinDB database table than to import a text file.

There are 2 ways to create a partitioned table in a partitioned database on disk:
 * Use function loadTextEx
 *	Use function createPartitionedTable and append!

To load a partitioned table as an in-memory partitioned table, remember to make the optional parameter of memoryMode in function loadTable to be 1. Otherwise only the meta data of the table are loaded.

**4. Use loadTable to load meta data of a partitioned table, then use loadTableBySQL with a meta code object representing a SQL query to import selected columns and/or rows into memory.**

This use case is suitable for the same situations as in 3. Compared with 3, this approach is more flexible. We can select columns or use where conditions to select rows.


#### Syntax of relevant functions

* ploadText(fileName, [delimiter], [schema])
* loadTextEx(dbHandle, tableName, partitionColumns, filename, [delimiter=','], [schema])
* database(directory, [partitionType], [partitionScheme], [locations])
* loadTable(database, tableName, [partitions], [memoryMode=false])
* loadTableBySQL(meta code representing a SQL query)
* sortBy!(table, sortColumns, [sortDirections])
* update!(table, colNames, newValues, [filter])
* drop!(table, colNames)
* erase!(table, filter)
* rename!(table, ColName, newColName)


#### Examples about loading datasets

please run the examples in the order that are presented, as some examples may need definitions given before them.
```
// generate data:
n=10000000
workDir = "C:/DolphinDB/Data"
if(!exists(workDir)) mkdir(workDir)
trades=table(rand(`IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S,n) as sym, 2000.01.01+rand(365,n) as date, 10.0+rand(2.0,n) as price1, 100.0+rand(20.0,n) as price2, 1000.0+rand(200.0,n) as price3, 10000.0+rand(2000.0,n) as price4, 10000.0+rand(3000.0,n) as price5, 10000.0+rand(4000.0,n) as price6, rand(10,n) as qty1, rand(100,n) as qty2, rand(1000,n) as qty3, rand(10000,n) as qty4, rand(10000,n) as qty5, rand(10000,n) as qty6)
trades.saveText(workDir + "/trades.txt")

// (1) ploadText:

trades = ploadText(workDir + "/trades.txt")

// (2) loadTextEx:

db = database("", VALUE, `IBM`MSFT`GM`C`FB`GOOG`V`F`XOM`AMZN`TSLA`PG`S)
trades = db.loadTextEx("", `sym, workDir + "/trades.txt")

// group by operations have the best performance when the grouping column is the same as the partitioning column.
select std(qty1) from trades group by sym

// the following sorting operations are within-partition sorting. They cannot be meaningfully executed on a table with a sequential partition in (1)

trades.sortBy!(`qty1)
trades.sortBy!(`date`qty1, false true)
trades.sortBy!(<qty1 * price1>, false)

// (3) loadTable:

// use loadTextEx to create a partitioned table in a partitioned database on disk:
db = database(workDir+"/tradeDB", RANGE, ["A","G","M","S","ZZZZ"])
db.loadTextEx(`trades, `sym, workDir + "/trades.txt")

// when we need to load a subset of partitions of the table into memory:
db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades, ["A", "M"], 1)   // load the partitions ["A","G"] and ["M","S"]

// (4) loadTableBySQL:

db = database(workDir+"/tradeDB")
trades=loadTable(db, `trades)
sample=loadTableBySQL(<select * from trades where date between 2000.03.01 : 2000.05.01>)
sample=loadTableBySQL(<select sym, date, price1, qty1 from trades where date between 2000.03.01 : 2000.05.01>)

dates = 2000.01.16 2000.02.14 2000.08.01
st = sql(<select sym, date, price1, qty1>, trades, expr(<date>, in, dates))
sample = loadTableBySQL(st)

colNames =`sym`date`qty2`price2
st= sql(sqlCol(colNames), trades)
sample = loadTableBySQL(st)
```

#### Examples about data manipulation with in-memory tables

The following operations can be conducted on any in-memory partitioned tables. If you work with in-memory tables from (3) or (4), make sure your table has all the necessary columns for the
examples below.

```
trades = ploadText(workDir + "/trades.txt")

/** add new columns to an in-memory table in 3 ways: sql, function, and assignment */
//1 use sql update
update trades set logPrice1= log(price1), newQty1= double(qty1)

//2 use update! function
trades.update!(`logPrice1`newQty1, <[log(price1), double(qty1)]>)

//3 use assignment statement
trades[`logPrice1`newQty1] = <[log(price1), double(qty1)]>

/** update existing columns in 3 ways: sql, function, and assignment */
//1 use sql update statement
update trades set qty1 = qty1 + 10
update trades set qty1 = qty1 + 10 where sym = `IBM

//2 use update! function
trades.update!(`qty1, <qty1+10>)
trades.update!(`qty1, <qty1+10>, <sym=`IBM>)

//3 use assginment statement
trades[`qty1] = <qty1 + 10>
trades[`qty1, <sym=`IBM>] = <qty1+10>

/** delete rows from table using sql and function */
//1 use sql delete statement to delete rows
delete from trades where qty3 <20

//2 use erase! function
trades.erase!(< qty3 <30 >)

/** drop columns using function */
trades.drop!("qty1")

/** rename columns */
trades.rename!("qty2", "qty2New")


// For more details please check relevant functions in the online manual.
```
