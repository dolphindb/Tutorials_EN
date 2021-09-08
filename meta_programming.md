# DolphinDB Tutorial: Metaprogramming

Metaprogramming is a programming technique in which computer programs are treated as data. It means that a program can read, generate, analyze or transform other programs, or even modify itself while running. 

DolphinDB supports metaprogramming for dynamic expression generation and delayed evaluation. With metaprogramming, users can generate SQL statements and evaluate them dynamically.

## 1. How to use metaprogramming 

Use the following 2 ways for metaprogramming in DolphinDB. 

(1) Use <>. 

```
a = <1 + 2 * 3>
typestr(a);
CODE

eval(a);
7
```

In the example above, "a" is metacode and its data type is "CODE". Function `eval` executes metacode. 

(2) Use metaprogramming functions including `expr`, `parseExpr`, `partial`, `sqlCol`, `sqlColAlias`, `sql`, `eval` and `makeCall`. 

- [`expr`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/e/expr.html) generates metacode from objects, operators, or other metacode.

```
a=6
expr(a,+,1);

< 6 + 1 >
```

- [`parseExpr`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/p/parseExpr.html) converts string into metacode, which can be executed by function `eval`.

```
t=table(1 2 3 4 as id, 5 6 7 8 as value, `IBM`MSFT`IBM`GOOG as name)
parseExpr("select * from t where name='IBM'").eval();

id value name
-- ----- ----
1  5     IBM
3  7     IBM
```

- [`partial`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/p/partital.html) creates a partial application. It sets some of the arguments of a function to fixed values to create a new function with less arguments. 

```
partial(add,1)(2);
3

def f(a,b):a pow b
g=partial(f, 2)
g(3);
8
```

- [`sqlCol`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/sqlCol.html) generates metacode for selecting one or multiple columns with or without calculations; [`sqlColAlias`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/sqlColAlias.html) uses metacode and an optional alias name to define a column; [`sql`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/sql.html) creates a SQL statement dynamically.

```
symbol = take(`GE,6) join take(`MSFT,6) join take(`F,6)
date=take(take(2017.01.03,2) join take(2017.01.04,4), 18)
price=31.82 31.69 31.92 31.8  31.75 31.76 63.12 62.58 63.12 62.77 61.86 62.3 12.46 12.59 13.24 13.41 13.36 13.17
volume=2300 3500 3700 2100 1200 4600 1800 3800 6400 4200 2300 6800 4200 5600 8900 2300 6300 9600
t1 = table(symbol, date, price, volume);

x=5000
whereConditions = [<symbol=`MSFT>,<volume>x>]
havingCondition = <sum(volume)>200>;

sql(sqlCol("*"), t1);
< select * from t1 >

sql(sqlCol("*"), t1, whereConditions);
< select * from t1 where symbol == "MSFT",volume > x >

sql(select=sqlColAlias(<avg(price)>), from=t1, where=whereConditions, groupBy=sqlCol(`date));
< select avg(price) as avg_price from t1 where symbol == "MSFT",volume > x group by date >

sql(select=sqlColAlias(<avg(price)>), from=t1, groupBy=[sqlCol(`date),sqlCol(`symbol)]);
< select avg(price) as avg_price from t1 group by date,symbol >

sql(select=(sqlCol(`symbol),sqlCol(`date),sqlColAlias(<cumsum(volume)>, `cumVol)), from=t1, groupBy=sqlCol(`date`symbol), groupFlag=0);
< select symbol,date,cumsum(volume) as cumVol from t1 context by date,symbol >

sql(select=(sqlCol(`symbol),sqlCol(`date),sqlColAlias(<cumsum(volume)>, `cumVol)), from=t1, where=whereConditions, groupBy=sqlCol(`date), groupFlag=0);
< select symbol,date,cumsum(volume) as cumVol from t1 where symbol == "MSFT",volume > x context by date >

sql(select=(sqlCol(`symbol),sqlCol(`date),sqlColAlias(<cumsum(volume)>, `cumVol)), from=t1, where=whereConditions, groupBy=sqlCol(`date), groupFlag=0, csort=sqlCol(`volume), ascSort=0);
< select symbol,date,cumsum(volume) as cumVol from t1 where symbol == "MSFT",volume > x context by date csort volume desc >

sql(select=(sqlCol(`symbol),sqlCol(`date),sqlColAlias(<cumsum(volume)>, `cumVol)), from=t1, where=whereConditions, groupBy=sqlCol(`date), groupFlag=0, having=havingCondition);
< select symbol,date,cumsum(volume) as cumVol from t1 where symbol == "MSFT",volume > x context by date having sum(volume) > 200 >

sql(select=sqlCol("*"), from=t1, where=whereConditions, orderBy=sqlCol(`date), ascOrder=0);
< select * from t1 where symbol == "MSFT",volume > x order by date desc >

sql(select=sqlCol("*"), from=t1, limit=1);
< select top 1 * from t1 >

sql(select=sqlCol("*"), from=t1, groupBy=sqlCol(`symbol), groupFlag=0, limit=1);
< select top 1 * from t1 context by symbol >
```

- [`eval`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/e/eval.html) executes metacode. 

```
a = <1 + 2 * 3>
eval(a);
7

sql(sqlColAlias(<avg(vol)>,"avg_vol"),t1,,sqlCol(["sym","date"])).eval();
sym  date       avg_vol
---- ---------- -------
F    2017.01.03 4900   
F    2017.01.04 6775   
GE   2017.01.03 2900   
GE   2017.01.04 2900   
MSFT 2017.01.03 8300   
MSFT 2017.01.04 4925   
```

- [`makeCall`](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/m/makeCall.html) calls a function with the specified parameters to generate metacode.

The following metacode outputs column 'date' as string in the format of "dd/MM/yyyy":
```
sql([sqlColAlias(makeCall(temporalFormat,sqlCol(`date),"dd/MM/yyyy"),"date"),sqlCol(`sym),sqlCol(`PRC),sqlCol(`vol)],t1)
< select temporalFormat(date, "dd/MM/yyyy") as date,sym,PRC,vol from t1 >
```

## 2. Applications of metaprogramming

### 2.1 Update in-memory tables

We can use either SQL statements or metaprogramming to conduct update or delete operations on in-memory tables. 

Create a partitioned in-memory table:

```
n=1000000
sym=rand(`IBM`MSFT`GOOG`FB`IBM`MSFT,n)
date=rand(2018.01.02 2018.01.02 2018.01.02 2018.01.03 2018.01.03 2018.01.03,n)
price=rand(1000.0,n)
qty=rand(10000,n)
trades=table(sym,date,price,qty)
```

#### 2.1.1 Update 

```
trades[`qty,<sym=`IBM>]=<qty+100>
```
Equivalent to:
```
update trades set qty=qty+100 where sym=`IBM
```

#### 2.1.2 Add a column

```
trades[`volume]=<price*qty>
```

#### 2.1.3 Delete records

```
trades.erase!(<qty=0>)
```
Equivalent to:
```
delete from trades where qty=0
```

#### 2.1.4 Dynamically generate filtering conditions and update tables

```
ind1=rand(100,10)
ind2=rand(100,10)
ind3=rand(100,10)
ind4=rand(100,10)
ind5=rand(100,10)
ind6=rand(100,10)
ind7=rand(100,10)
ind8=rand(100,10)
ind9=rand(100,10)
ind10=rand(100,10)
indNum=1..10
t=table(ind1,ind2,ind3,ind4,ind5,ind6,ind7,ind8,ind9,ind10,indNum)

update t set ind1=1 where indNum=1
update t set ind2=1 where indNum=2
update t set ind3=1 where indNum=3
update t set ind4=1 where indNum=4
update t set ind5=1 where indNum=5
update t set ind6=1 where indNum=6
update t set ind7=1 where indNum=7
update t set ind8=1 where indNum=8
update t set ind9=1 where indNum=9
update t set ind10=1 where indNum=10
```

A large number of lines of code are needed if there are many columns in a table. It can be simplified with metaprogramming:

```
for(i in 1..10){
	t["ind"+i,<indNum=i>]=1
}
```

### 2.2 Use metaprogramming in DolphinDB built-in functions

The parameters of some DolphinDB built-in functions need to use metaprogramming. 

#### 2.2.1 Window join

Use metaprogramming to specify metrics to be calculated. 
```
t = table(take(`ibm, 3) as sym, 10:01:01 10:01:04 10:01:07 as time, 100 101 105 as price)
q = table(take(`ibm, 8) as sym, 10:01:01+ 0..7 as time, 101 103 103 104 104 107 108 107 as ask, 98 99 102 103 103 104 106 106 as bid)
wj(t, q, -2:1, <[max(ask), min(bid), avg((bid+ask)*0.5) as avg_mid]>, `time)

sym time     price max_ask min_bid avg_mid
--- -------- ----- ------- ------- -------
ibm 10:01:01 100   103     98      100.25
ibm 10:01:04 101   104     99      102.625
ibm 10:01:07 105   108     103     105.625

```

#### 2.2.2 Streaming engine

DolphinDB provides multiple streaming engines. To use the streaming engines, we need to specify functions or expressions and the parameters with metaprogramming. 

```
share streamTable(1000:0, `time`sym`qty, [DATETIME, SYMBOL, INT]) as trades
output1 = table(10000:0, `time`sym`sumQty, [DATETIME, SYMBOL, INT])
agg1 = createTimeSeriesEngine(name="engine1", windowSize=60, step=60, metrics=<[sum(qty)]>, dummyTable=trades, outputTable=output1, timeColumn=`time, useSystemTime=false, keyColumn=`sym, garbageSize=50, useWindowStartTime=false)
subscribeTable(tableName="trades", actionName="tableName", offset=0, handler=append!{agg1}, msgAsTable=true)

insert into trades values(2018.10.08T01:01:01,`A,10)
insert into trades values(2018.10.08T01:01:02,`B,26)
insert into trades values(2018.10.08T01:01:10,`B,14)
insert into trades values(2018.10.08T01:01:12,`A,28)
insert into trades values(2018.10.08T01:02:10,`A,15)
insert into trades values(2018.10.08T01:02:12,`B,9)
insert into trades values(2018.10.08T01:02:30,`A,10)
insert into trades values(2018.10.08T01:04:02,`A,29)
insert into trades values(2018.10.08T01:04:04,`B,32)
insert into trades values(2018.10.08T01:04:05,`B,23)

select * from output1

time                sym sumQty
------------------- --- ------
2018.10.08T01:02:00 A   38    
2018.10.08T01:03:00 A   25    
2018.10.08T01:02:00 B   40    
2018.10.08T01:03:00 B   9  
```

### 2.3 Customized reports

The following example defines a function to generate a report. The user only needs to enter the table object, the column names and the corresponding formats. 

```
def generateReport(tbl, colNames, colFormat, filter){
	colCount = colNames.size()
	colDefs = array(ANY, colCount)
	for(i in 0:colCount){
		if(colFormat[i] == "") 
			colDefs[i] = sqlCol(colNames[i])
		else
			colDefs[i] = sqlCol(colNames[i], format{,colFormat[i]})
	}
	return sql(colDefs, tbl, filter).eval()
}
```

Create sample data:

```
n=31
date=2020.09.30+1..n
sym=take(`A,n) join take(`B,n)
t=table(take(date,2*n) as date, sym, 100+rand(1.0,2*n) as price, rand(1000..10000,2*n) as volume)
select * from t where date=2020.10.16 and sym=`B;

date       sym price               volume
---------- --- ------------------- ------
2020.10.16 B   100.324969965266063 6657
```

```
generateReport(t,`date`sym`price`volume,["MM/dd/yyyy","","###.00","#,###"],<date=2020.10.16 and sym=`B >);

date       sym price  volume
---------- --- ------ ------
10/16/2020 B   100.32 6,657
```

The script above is equivalent to the following script:

```
select format(date,"MM/dd/yyyy") as date, sym, format(price,"###.00") as price, format(volume,"#,###") as volume from t where date=2020.10.16 and sym=`B
```


### 2.4 Execute a large number of similar queries and combine results

Sometimes we may need to execute a large number of similar queries on the same table and then combine the results. We can use metaprogramming to simplify these queries. 

The first row of the data used in this example:

mt       |vn       |bc |cc  |stt |vt |gn |bk   |sc |vas |pm |dls        |dt         |ts     |val   |vol  
-------- |-------- |-- |--- |--- |-- |-- |---- |-- |--- |-- |---------- |---------- |------ |----- |-----
52354955 |50982208 |25 |814 |11  |2  |1  |4194 |0  |0   |0  |2020.02.05 |2020.02.05 |153234 |5.374 |18600                  

We may need to execute thousands of queries with a day's observations. For simplicity, we use the following 4 queries:

```sql
select * from t where vn=50982208,bc=25,cc=814,stt=11,vt=2, dls=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=50982208,bc=25,cc=814,stt=12,vt=2, dls=2020.02.05, mt<52355979 order by mt desc limit 1
select * from t where vn=51180116,bc=25,cc=814,stt=12,vt=2, dls=2020.02.05, mt<52354979 order by mt desc limit 1
select * from t where vn=41774759,bc=1180,cc=333,stt=3,vt=116, dsl=2020.02.05, mt<52355979 order by mt desc limit 1
```

All of the where conditions in these queries have the same filtering columns and ordering columns. Some of the where conditions share the same filter value. All of the queries only output the first row after sorting. We can create a function `bundleQuery` with metaprogramming:

```
def bundleQuery(tbl, dt, dtColName, mt, mtColName, filterColValues, filterColNames){
	cnt = filterColValues[0].size()
	filterColCnt =filterColValues.size()
	orderByCol = sqlCol(mtColName)
	selCol = sqlCol("*")
	filters = array(ANY, filterColCnt + 2)
	filters[filterColCnt] = expr(sqlCol(dtColName), ==, dt)
	filters[filterColCnt+1] = expr(sqlCol(mtColName), <, mt)
	
	queries = array(ANY, cnt)
	for(i in 0:cnt)	{
		for(j in 0:filterColCnt){
			filters[j] = expr(sqlCol(filterColNames[j]), ==, filterColValues[j][i])
		}
		queries.append!(sql(select=selCol, from=tbl, where=filters, orderBy=orderByCol, ascOrder=false, limit=1))
	}
	return loop(eval, queries).unionAll(false)
}
```

The parameters of function `bundleQuery` are:

- tbl is the input table
- dt is the filter value for date
- dtColName is the column name for date
- mt is the filter value for mt
- mtColName is the column name for mt
- filterColValues is a tuple indicating the filter values in other where conditions. Each element of the tuple is a vector indicating the filter values of a where condition in each query. 
- filterColNames is the column names used in other where conditions.

We can rewrite the aforementioned 4 lines of SQL statements with the following script:

```
dt = 2020.02.05 
dtColName = "dls" 
mt = 52355979 
mtColName = "mt"
colNames = `vn`bc`cc`stt`vt
colValues = [50982208 50982208 51180116 41774759, 25 25 25 1180, 814 814 814 333, 11 12 12 3, 2 2 2 116]

bundleQuery(t, dt, dtColName, mt, mtColName, colValues, colNames)
```

We can execute the following query to add `bundleQuery` as a function view. With this, we can call `bundleQuery` directly either after restarting or on the other nodes of the cluster. 

```
//please login as admin first
addFunctionView(bundleQuery)
```


