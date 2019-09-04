# Hybrid Paradigm Programming for DolphinDB

To develop big data applications, in addition to a distributed database that can store huge volumes of data and a distributed computing framework capable of making efficient use of multi-cores and multi-nodes, we also need a programming language that is organically integrated with the distributed database and the distributed computing framework. DolphinDB drew inspiration from popular programming languages such as SQL and Python. It provides a highly expressive programming language that offers high performance and enables rapid development.

In this tutorial, we will explain how to program in hybrid paradigm in DolphinDB.

## 1. Vector Programming

Vector programming is the most basic programming paradigm in DolphinDB. Most of the functions in DolphinDB can use vectors as input parameters. There are 2 types of functions depending on the data form of the result: an aggregate function returns a scalar; a vector function returns a vector of the same length as input vectors.

Vector programming has 3 main advantages: (1) concise script; (2) significant reduction in the cost of interpreting the scripting language; (3) can optimize numerous algorithms. As time-series data can be represented with a vector, time-series analysis is particularly suitable for vector programming.

The following example sums two huge vectors. Imperative programming with 'for' statements takes more than 100 times longer to execute than vector programming.

``` txt
n = 10000000
a = rand(1.0, n)
b = rand(1.0, n)

//'for' statement in imperative programming:
c = array(DOUBLE, n)
for(i in 0 : n)
    c[i] = a[i] + b[i]

//vector programming:
c = a + b
```

Vector programming is essentially batch processing of homogeneous data. With it, the instructions can be optimized with vectorization in compiling, and numerous algorithms can be optimized. For instance, to calculate moving average with n rows of data and a window size of k, the runtime complexity is O(nk) without batch computing. When we move to a new window, however, only one data point changes. To get the new average, we only need to adjust for this data point. Therefore, the runtime complexity of batch computing is O(n).

DolphinDB has optimized most of the moving window fuctions with runtime in the order of O(n). These functions include: `mmax`, `mmin`, `mimax`, `mimin`, `mavg`, `msum`, `mcount`, `mstd`, `mvar`, `mrank`, `mcorr`, `mcovar`, `mbeta` and `mmed`. The following example shows that optimized `mavg` function significantly improves the performance of moving average calculation.

``` TXT
n = 10000000
a = rand(1.0, n)
window = 60
//compute each window respectively with `avg` function:
timer moving(avg, a, window)

Time elapsed: 4039.23 ms

//batch computing with `mavg` function:
timer mavg(a, window)

Time elapsed: 12.968 ms
```
Vector programming also has its limitations. First, not all operations can be conducted with vectorized computing. In machine learning and statistical analysis, there are numerious occasions where we can only process data through iteration sentence by sentence instead of vectorization. To improve system performance in these situations, DolphinDB is developing just-in-time (JIT) compilation, which dynamically compiles script to machine code.

Second, languages like MATLAB and R usually load an entire vector into a contiguous memory block. Sometimes large segments of contiguous memory may not be found due to the memory fragmentation problem. DolphinDB introduces big array to handle this problem. Big array can represent a vector with segmented memory blocks. Whether the system uses big array is dynamically determined and transparent to users. Usually, compared with contiguous memory, the performance loss is 1%~5% for scanning a big array and 20%~30% for random access. DolphinDB sacrifices acceptable performance for improved system availability in return.

## 2. SQL Programming

SQL statements in DolphinDB support the standard SQL features and offer extensions for time-series data analysis.

### 2.1 Integration of SQL and Programming Languages

In DolphinDB, the scripting language is fully integrated with SQL statements. 

* SQL query can be assigned directly to a variable or as a function parameter.
* SQL query statements can quote variables or functions. If a SQL query involves a distributed table, the variables and functions in the SQL query can be automatically serialized to the corresponding nodes.
* SQL statements can be dynamically generated script.
* Database table is a data form. Other data forms include scalar, vector, matrix, set, and dictionary. Database table can be transformed into other data forms.

``` TXT
//generate a table of employee wages
emp_wage = table(take(1..10, 100) as id, take(2017.10M + 1..10, 100).sort() as month, take(5000 5500 6000 6500, 100) as wage)

//compute the average wage for each employee. The employee list is stored in the array 'empIds'.
empIds = 3 4 6 7 9
select avg(wage) from emp_wage where id in empIds group by id
id avg_wage
-- --------
3  5500
4  6000
6  6000
7  5500
9  5500

//display average wage and corresponding employee's name. Get employee name from the dictionary 'empName'.
empName = dict(1..10, `Alice`Bob`Jerry`Jessica`Mike`Tim`Henry`Anna`Kevin`Jones)
select empName[first(id)] as name, avg(wage) from emp_wage where id in empIds group by id
id name    avg_wage
-- ------- --------
3  Jerry   5500
4  Jessica 6000
6  Tim     6000
7  Henry   5500
9  Kevin   5500
```

In the examples above, SQL queries quote a vector and a dictionary directly. By integrating the programming language and SQL queries, the system uses hash tables to solve a problem that would have required subqueries and table joins. It makes the script more concise and easier to understand. More importantly, it improves the performance.

DolphinDB introduces a SQL keyword 'exec'. Compared with 'select', the result returned by 'exec' can be a matrix, vector or scalar. The following example uses 'exec' and 'pivot by' to return a matrix.

```TXT
exec first(wage) from emp_wage pivot by month, id

         1    2    3    4    5    6    7    8    9    10
         ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
2017.11M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2017.12M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.01M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.02M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.03M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.04M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.05M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.06M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
2018.07M|5000 5500 6000 6500 5000 5500 6000 6500 5000 5500
2018.08M|6000 6500 5000 5500 6000 6500 5000 5500 6000 6500
```

### 2.2 Support for Panel Data

Some calculations with panel data return the same number of rows as the input data, such as converting stock prices into stock returns and calculating moving window statistics. For these tasks SQL server and PostGreSQL use window functions. DolphinDB offers 'context by' clause in SQL statements. Compared with window functions, 'context by' clause has the following advantages:

* Can be used with not only 'select' statements but also 'update' statements.
* Window functions can only group existing fields, while 'context by' can also group calculated fields.
* Window functions can only use a limited number of functions, whereas 'context by' clause has no limits on what functions can be used. Besides, 'context by' can use arbitrary expressions, such as a combination of multiple functions.
* 'context by' can be used with 'having' clause to filter rows within each group.

In the following example, we use 'context by' to calculate daily stock returns and ranks. 

```TXT
//calculate daily stock returns assuming data for each stock are already ordered.
update trades set ret = ratios(price) - 1.0 context by sym

//calculate the daily rank（in descending order of stock return）of each stock within each day.
select date, symbol,  ret, rank(ret, false) + 1 as rank from trades where isValid(ret) context by date

//select top 10 stocks each day
select date, symbol, ret from trades where isValid(ret) context by date having rank(ret, false) < 10
```

A paper [101 Formulaic Alphas](http://www.followingthetrend.com/?mdocs-file=3424) introduced 101 quant factors used by WorldQuant, one of Wall Street's top quantitative hedge funds. A quant hedge fund calculated these factors with C#. One of the most complicated factor (No.98) needs hundreds of lines of code in C# and takes about 30 minutes to calculate with data for 3,000 stocks in 10 years. In contrast, the same calcuation in DolphinDB only needs 4 lines of code and takes only 2 seconds, an almost 3 orders of magnitude improvement in performance.

```TXT
//Implementation of No.98 alpha factor. 'stock' is the input table.
def alpha98(stock){
    t = select code, valueDate, adv5, adv15, open, vwap from stock order by valueDate
    update t set rank_open = rank(open), rank_adv15 = rank(adv15) context by valueDate
    update t set decay7 = mavg(mcorr(vwap, msum(adv5, 26), 5), 1..7), decay8 = mavg(mrank(9 - mimin(mcorr(rank_open, rank_adv15, 21), 9), true, 7), 1..8) context by code
    return select code, valueDate, rank(decay7)-rank(decay8) as A98 from t context by valueDate
}
```

### 2.3 Support for Time Series Data

DolphinDB uses columnar data storage and vector programming, which are very friendly for time-series data analysis.

* DolphinDB supports temporal data types with various precisions up to nanosecond. High-frequency data can be conveniently converted into low-frequency data such as second-level, minute-level and hour-level with SQL statements. It can also be converted into data for intervals with specified length with function `bar` and SQL clause 'group by'.

* DolphinDB offers convenient time-series functions, such as lead, lag, moving window, cumulative window and so on. More importantly, these functions are all optimized with performance 1 to 2 orders of magnitude better than other systems.

* DolphinDB designs 2 ways of nonsynchronous table joins: asof join and window join.

The following example calculates the average salary of a group of people for 3 months before a certain point in time with function `wj`. For more details about function `wj`, please refer to [User Manual, Chapter 8](http://www.dolphindb.com/help/)

```TXT
p = table(1 2 3 as id, 2018.06M 2018.07M 2018.07M as month)
s = table(1 2 1 2 1 2 as id, 2018.04M + 0 0 1 1 2 2 as month, 4500 5000 6000 5000 6000 4500 as wage)
select * from wj(p, s, -3:-1,<avg(wage)>,`id`month)

id month    avg_wage
-- -------- -----------
1  2018.06M 5250
2  2018.07M 4833.333333
3  2018.07M

```

A typical application of window join in quant finance is to calculate transaction costs with a 'trades' table and a 'quotes' table.

```TXT
//table 'trades'
sym  date       time         price  qty
---- ---------- ------------ ------ ---
IBM  2018.06.01 10:01:01.005 143.19 100
MSFT 2018.06.01 10:01:04.006 107.94 200
...

//table 'quotes'
sym  date       time         bid    ask    bidSize askSize
---- ---------- ------------ ------ ------ ------- -------
IBM  2018.06.01 10:01:01.006 143.18 143.21 400     200
MSFT 2018.06.01 10:01:04.010 107.92 107.97 800     100
...

dateRange = 2018.05.01 : 2018.08.01

//select the last quote before each transaction with asof join, and use the average of bid and ask as the benchmark for transaction costs.
select sum(abs(price - (bid+ask)/2.0)*qty)/sum(price*qty) as cost from aj(trades, quotes, `date`sym`time) where date between dataRange group by sym

//select all the quotes in the 10 ms before each transaction with window join, and calculate the average mid price as the benchmark for transaction costs.
select sum(abs(price - mid)*qty)/sum(price*qty) as cost from pwj(trades, quotes, -10:0, <avg((bid + ask)/2.0) as mid>,`date`sym`time) where date between dataRange group by sym
```

### 2.4 Other Extensions of SQL

DolphinDB offers many other SQL extensions. For examples:

* User-defined functions can be used in SQL on the local node or distributed environment without compiling, packaging or deploying.
* As shown in 5.4, SQL is fully integrated with the distributed computing framework in DolphinDB, making in-database analytics more convenient and efficient.
* DolphinDB supports composite column, which can output multiple return values of complex analysis functions into one row of a table.

When using composite columns in SQL statements, the function must output a key-value pair or an array. Otherwise you can convert the result into one of these two types with a user-defined function. For details please refer to [User Manual](http://www.dolphindb.com/help/).

```TXT
factor1=3.2 1.2 5.9 6.9 11.1 9.6 1.4 7.3 2.0 0.1 6.1 2.9 6.3 8.4 5.6
factor2=1.7 1.3 4.2 6.8 9.2 1.3 1.4 7.8 7.9 9.9 9.3 4.6 7.8 2.4 8.7
t=table(take(1 2 3, 15).sort() as id, 1..15 as y, factor1, factor2)

//run `ols` for each id: y = alpha + beta1 * factor1 + beta2 * factor2, and output parameters alpha, beta1 and beta2.
select ols(y, [factor1,factor2], true, 0) as `alpha`beta1`beta2 from t group by id

id alpha     beta1     beta2
-- --------- --------- ---------
1  1.063991  -0.258685 0.732795
2  6.886877  -0.148325 0.303584
3  11.833867 0.272352  -0.065526

//output R2 with a user-defined function.
def myols(y,x){
    r=ols(y,x,true,2)
    return r.Coefficient.beta join r.RegressionStat.statistics[0]
}
select myols(y,[factor1,factor2]) as `alpha`beta1`beta2`R2 from t group by id

id alpha     beta1     beta2     R2
-- --------- --------- --------- --------
1  1.063991  -0.258685 0.732795  0.946056
2  6.886877  -0.148325 0.303584  0.992413
3  11.833867 0.272352  -0.065526 0.144837
```

## 3. Imperative Programming

Like most scripting languages (e.g. Python, JavaScript) and various strongly-typed, compiled languages (e.g. C++, C, Java), DolphinDB supports imperative programming, which means script can be executed sentence by sentence. DolphinDB currently supports 18 types of statements, including the most commonly used assignment statements, branch statements (e.g. 'if..else') and loop statements (e.g. 'for', 'do..while'). For more details, please refer to [User Manual, Chapter 5](http://www.dolphindb.com/help/).

DolphinDB supports single and multiple assignment:
```txt
x = 1 2 3
y = 4 5
y += 2
x, y = y, x //swap the value of x and y
x, y =1 2 3, 4 5
```

DolphinDB supports loop statements, including 'for' loop and 'do..while' loop. The iterator of a 'for' loop can be a range (not including the upper bound), an array, a matrix or a table.

```txt
//loop from 1 to 100 to compute the cumulative sum:

s = 0
for(x in 1:101) s += x
print s
```

```txt
//loop over an array to compute the sum of all the elements in the array:

s = 0;
for(x in 1 3 5 9 15) s += x
print s
```

``` txt
//loop over a matrix to compute the average of each column and then print them:

m = matrix(1 2 3, 4 5 6, 7 8 9)
for(c in m) print c.max()
```

```txt
//loop over a table "product" to compute the sales of each product:

t= table(["TV set", "Phone", "PC"] as productId, 1200 600 800 as price, 10 20 7 as qty)
for(row in t) print row.productId + ": " + row.price * row.qty
```

DolphinDB supports branch statement 'if..else' as in other programming languages.

```txt
if(condition){
    <true statements>
}
else{
     <false statements>
}
```

With large amounts of data, control statements (e.g. 'for', 'if..else') are very inefficient. We recommend using vector programming, functional programming and SQL programmming to process large amounts of data. 

## 4. Functional Programming

DolphinDB supports functional programming including: (1) pure function; (2) user defined function (udf); (3) lambda function; (4) higher order function; (5) partial application; (6) closure. For more details, please refer to [User Manual, Chapter 7](http://www.dolphindb.com/help/).

### 4.1 User Defined Function & Lambda Function

 A user-defined function can be created with or without function name (usually lamdba function). DolphinDB is different from Python in that only function parameters and local variables can be referred inside a function. This greatly improves the software quality with slight reduction in the flexibility of syntactic sugar.

```TXT
//define a function to return weekdays
def getWorkDays(dates){
    return dates[def(x):weekday(x) between 1:5]
}

getWorkDays(2018.07.01 2018.08.01 2018.09.01 2018.10.01)

[2018.08.01, 2018.10.01]
```

In the example above, we defined a lambda function getWorkDays(). The function accepts an array of dates and returns weekdays.

### 4.2 Higher Order Function

In this section we focus on higher-order functions and partial applications. A higher-order function accepts another function as a parameter. In DolphinDB, higher-order functions are mainly used as template functions. Usually the first parameter is another function. For example, object A has m elements and object B has n elements. To calculate pairwise correlation of the elements in A and B, we need to use function `corr` on all possible pairs of elements in A and elements in B, and arrange the results in an m*n matrix. In DolphinDB, the aforementioned steps can be simplified with a high-order function `cross`: cross(corr, A, B). DolphinDB provides many such template functions including `all`, `any`, `each`, `loop`, `eachLeft`, `eachRight`, `eachPre`, `eachPost`, `accumulate`, `reduce`, `groupby`, `contextby`, `pivot`, `cross`, `moving`, `rolling`, etc.

In the following example, we use 3 higher-order functions to calculate the pairwise correlation with tick-level stock data.

```TXT
//simulate 100 million data points

n=10000000
syms = rand(`FB`GOOG`MSFT`AMZN`IBM, n)
time = 09:30:00.000 + rand(21600000, n)
price = 500.0 + rand(500.0, n)

//generate a pivot table with `pivot` function
priceMatrix = pivot(avg, price, time.minute(), syms)

//generate stock return per minute for each stock (each column of the matrix) with functions `each` and `ratios`
retMatrix = each(ratios, priceMatrix) - 1

//compute pairwise correlation with funtions `cross` and `corr`
corrMatrix = cross(corr, retMatrix, retMatrix)

     AMZN      FB        GOOG      IBM       MSFT
     --------- --------- --------- --------- ---------
AMZN|1         0.015181  -0.056245 0.005822  0.084104
FB  |0.015181  1         -0.028113 0.034159  -0.117279
GOOG|-0.056245 -0.028113 1         -0.039278 -0.025165
IBM |0.005822  0.034159  -0.039278 1         -0.049922
MSFT|0.084104  -0.117279 -0.025165 -0.049922 1
```

### 4.3 Partial Application

Partial application fixes part or all of the parameters of a function to produce a new function with fewer parameters. In DolphinDB, function calls use () and partial applications use {}. For example, the `ratios` function is a partial application with the higher order function `eachPre`: `eachPre{ratio}`.

The following 2 lines of script are equivalent:
``` TXT
`retMatrix = each(ratios, priceMatrix) - 1`
retMatrix = each(eachPre{ratio}, priceMatrix) - 1
```

Partial applications are often used with higher order functions. Higher order functions usually have certain requirements for parameters, and partial applications can ensure that the parameters meet these requirements. For example, to calculate the correlation between vector a and each column in a matrix m, we can use the higher order function `each`. However, if we use function `corr`, vector a and matrix m as the parameters of `each`, the system would try to calculate the correlation between each element of vector a and each column of matrix m, which will throw an exception. We can use partial application to form a new function corr{a}, and then use it as a parameter for the higher order function `each` together with matrix m. We can also use 'for' statement for this problem, but the script is lengthy and the execution takes longer time.

```TXT
a = 12 14 18
m = matrix(5 6 7, 1 3 2, 8 7 11)

//calculate correlation with `each` and partial applications
each(corr{a}, m)

//calculate with 'for' statement
cols = m.columns()
c = array(DOUBLE, cols)
for(i in 0:cols)
    c[i] = corr(a, m[i])
```

Partial application can also be used to keep a function in a state. Usually the result of a function is completely determined by the input parameters. Occasionally, however, we would like a function to be in a state. For example, in streaming, we define a message handler to accept a new message and return a result. For the message handler to return the average of a column for all the messages received, we can use partial application.

```TXT
def cumavg(mutable stat, newNum){
    stat[0] = (stat[0] * stat[1] + newNum)/(stat[1] + 1)
    stat[1] += 1
    return stat[0]
}

msgHandler = cumavg{0.0 0.0}
each(msgHandler, 1 2 3 4 5)

[1,1.5,2,2.5,3]
```

## 5. RPC Programming

Remote Procedure Call (RPC) is one of the most commonly used functionalities in distributed systems. In DolphinDB, the implementation of the distributed file system, distributed database and distributed computing framework all utilize the built-in RPC system.

* Can not only execute functions registered on a remote machine, but also serialize a local user-defined function to a remote node for execution. User privileges on remote machines are equivalent to those on local machines.
* Parameters of a function can be either regular parameters such as scalar, vector, matrix, set, dictionary and table, or functions including user-defined functions.
* Can use both exclusive connections between two nodes and shared connections between data nodes in a cluster.

### 5.1 Remote call with `remoteRun`

We can use `xdb` to create a connection to a remote node. The remote node can be any node running DolphinDB and doesn't need to be in the current cluster. After the connection is created, we can use `remoteRun` to execute a function that is registered on the remote node or a locally defined function on the remote node.

```TXT
h = xdb("localhost", 8081)
//run on the remote node
remoteRun(h, "sum(1 3 5 7)");
16

//the script above can be simplified as
h("sum(1 3 5 7)");
16

//at the remote node, run a function registered on the remote node
h("sum", 1 3 5 7);
16

//run a user-defined function on the remote node
def mysum(x) : reduce(+, x)
h(mysum, 1 3 5 7);
16

//create a shared table 'sales' on the remote node (localhost:8081)
h("share table(2018.07.02 2018.07.02 2018.07.03 as date, 1 2 3 as qty, 10 15 7 as price) as sales")
//when we execute a user-defined function on a remote node, its dependent functions will be automatically serialized to the remote node.
defg salesSum(tableName, d): select mysum(price*qty) from objByName(tableName) where date=d
h(salesSum, "sales", 2018.07.02);
40
```

### 5.2 Remote call with `rpc`

Another way of remote procedure call is function `rpc`. Its parameters are the remote node alias, the function to be executed and the function parameters. Both the calling node and the remote node must be located in the same cluster. Otherwise, we need to use function `remoteRun`. Function `rpc` doesn't need a new connection. Instead, it reuses existing network connections. This way it saves network resources and the time to create new connections, especially when the cluster has many users. Please note that `rpc` can only execute one function on a remote node. To execute script with `rpc`, the script must be wrapped in a user-defined function. 

```TXT
//'sales' is a shared table on a remote node 'nodeB'
rpc("nodeB", salesSum, "sales",2018.07.02);
40

//when using `rpc`, we recommend using partial application to increase readability of the script
rpc("nodeB", salesSum{"sales", 2018.07.02});
40

//create a user on the controller node 'master'
rpc("master", createUser{"jerry", "123456"})

//`rpc` can also call a built-in function or a user-defined function to run on a remote node
rpc("nodeB", reduce{+, 1 2 3 4 5});
15
```
The most powerful feature of built-in remote call funcions (`remoteRun` and `rpc`) is that we can send a local function that calls local user-defined functions to run on a remote node on the fly without compilation or deployment. The system automatically serializes the function definition and the definitions of all dependent functions together with necessary local data to remote nodes. In other systems we can only remote call functions without any user-defined dependent functions.

### 5.3 Indirect remote call with other functions

DolphinDB provides numerous functions for indirect remote procedure calls. For examples, linear regression on distributed database uses `rpc` and `olsEx`; function `pnodeRun` calls a function on multiple remote nodes in parallel and then merges the returned results. `pnodeRun` is a quite useful tool in cluster management. 

```TXT
//return the most recent 10 running or completed batch jobs on each node
pnodeRun(getRecentJobs{10})

//return the most recent 10 SQL queries on 'nodeA' and 'nodeB'
pnodeRun(getCompletedQueries{10}, `nodeA`nodeB)

//clear caches on all data nodes
pnodeRun(clearAllCache)
```

### 5.4 Distributed computing

DolphinDB provides function `mr` for distributed computing and `imr` for iterative distributed computing based on MapReduce. Users only need specify a distributed data source and functions such as map function, reduce function, final function and terminate function.

In the example below, we illustrate distributed median calculation and distributed linear regression.

```TXT
n=10000000
x1 = pow(rand(1.0,n), 2)
x2 = norm(3.0:1.0, n)
y = 0.5 + 3 * x1 - 0.5*x2 + norm(0.0:1.0, n)
t=table(rand(10, n) as id, y, x1, x2)

login(`admin,"123456")
db = database("dfs://testdb", VALUE, 0..9)
db.createPartitionedTable(t, "sample", "id").append!(t)

```
Construct a function 'myOLSEx' to conduct a distributed linear regression with user-defined map function `myOLSMap`, built-in reduce function `add`, user-defined final function `myOLSFinal`, and built-in function `mr`. 

```TXT
//define a map function 'myOLSMap'
def myOLSMap(table, yColName, xColNames){
    x = matrix(take(1.0, table.rows()), table[xColNames])
    xt = x.transpose()
    return xt.dot(x), xt.dot(table[yColName])
}

//define a final function 'myOLSFinal'
def myOLSFinal(result){
    xtx = result[0]
    xty = result[1]
    return xtx.inv().dot(xty)[0]
}

def myOLSEx(ds, yColName, xColNames){
  return mr(ds, myOLSMap{, yColName, xColNames}, +, myOLSFinal)
}

//calculate the linear regression coefficients on distributed data source with function 'myOLSEx'
sample = loadTable("dfs://testdb", "sample")
myOLSEx(sqlDS(<select * from sample>), `y, `x1`x2);
[0.4991, 3.0001, -0.4996]

//get the same result by running the built-in function `ols` on unpartitioned data
ols(y, [x1,x2],true);
[0.4991, 3.0001, -0.4996]
```

The following example calculates the approximate median value based on a distributed data source. The data is scattered on multiple nodes. First, for each data source, divide the data into buckets and use the map function to count the number of data points in each bucket. Then use the reduce function to calculate the number of data points in each bucket across all data sources. Locate the bucket that contains the median. In the next iteration, the chosen bucket is divided into multiple buckets and the bucket with the median value is located. The iterations is finished when the size of the chosen bucket is no more than the specified precision.

```TXT
def medMap(data, range, colName): bucketCount(data[colName], double(range), 1024, true)

def medFinal(range, result){
    x= result.cumsum()
    index = x.asof(x[1025]/2.0)
    ranges = range[1] - range[0]
    if(index == -1)
        return (range[0] - ranges*32):range[1]
    else if(index == 1024)
        return range[0]:(range[1] + ranges*32)
    else{
        interval = ranges / 1024.0
        startValue = range[0] + (index - 1) * interval
        return startValue : (startValue + interval)
    }
}

def medEx(ds, colName, range, precision){
    termFunc = def(prev, cur): cur[1] - cur[0] <= precision
    return imr(ds, range, medMap{,,colName}, +, medFinal, termFunc).avg()
}

sample = loadTable("dfs://testdb", "sample")
medEx(sqlDS(<select y from sample>), `y, 0.0 : 1.0, 0.001);
-0.052973

//calculate the median of unpartitioned data with a built-in function `med`
med(y);
-0.052947
```

## 6. Metaprogramming

Metaprogramming is a programming technique in which computer programs are treated as data. It means that a program can read, generate, analyze or transform other programs, or even modify itself while running. 

Metaprogramming usually serves 2 purposes: code generation and delayed execution. 

We can use metaprogramming to dynamically create script including function calls and SQL statements. Quite often job details are not known when the script is written. For example, in customized reporting, a complete SQL statement is determined only after the customer selects the table, columns and formats. Dynamic expressions are generated with a pair of '<>' or with built-in functions including  `objByName`, `sqlCol`, `sqlColAlias`, `sql`, `expr`, `eval`, `partial` and `makeCall`.

Delayed execution usually invloves the following scenarios: (1) to provide a callback function; (2) for system optimization; (3) when implementation of script is at a later stage than description stage.

```TXT
//generate dynamic expression with a pair of '<>'
a = <1 + 2 * 3>
a.typestr();
CODE

a.eval();
7

//generate dynamic expression with a built-in function
a = expr(1, +, 2, *, 3)
a.typestr();
CODE

a.eval();
7
```

The following example generates a customized report with metaprogramming. 

```TXT
//Generate a SQL expression dynamicly to execute based on the given table, columns and formats. 
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

//generate a table with 100 rows of simulated data
t = table(1..100 as id, (1..100 + 2018.01.01) as date, rand(100.0, 100) as price, rand(10000, 100) as qty)

//generate filter conditions with metaprogramming for a customized report
generateReport(t, ["id","date","price","qty"], ["000","MM/dd/yyyy", "00.00", "#,###"], < id<5 or id>95 >);

id  date       price qty
--- ---------- ----- -----
001 01/02/2018 50.27 2,886
002 01/03/2018 30.85 1,331
003 01/04/2018 17.89 18
004 01/05/2018 51.00 6,439
096 04/07/2018 57.73 8,339
097 04/08/2018 47.16 2,425
098 04/09/2018 27.90 4,621
099 04/10/2018 31.55 7,644
100 04/11/2018 46.63 8,383
```

Some DolphinDB built-in functions need to use metaprogramming for their parameters. For example, for window join function (`wj`), we need to specify one or more aggregate functions for the right table and the parameters for these functions. As description and execution of the task occur on different stages, we need to use metaprogramming to specify the aggregate functions and their parameters for delayed evaluation. 

```TXT
t = table(take(`ibm, 3) as sym, 10:01:01 10:01:04 10:01:07 as time, 100 101 105 as price)
q = table(take(`ibm, 8) as sym, 10:01:01+ 0..7 as time, 101 103 103 104 104 107 108 107 as ask, 98 99 102 103 103 104 106 106 as bid)
wj(t, q, -2 : 1, < [max(ask), min(bid), avg((bid+ask)*0.5) as avg_mid]>, `time);

sym time     price max_ask min_bid avg_mid
--- -------- ----- ------- ------- -------
ibm 10:01:01 100   103     98      100.25
ibm 10:01:04 101   104     99      102.625
ibm 10:01:07 105   108     103     105.625
```

We may also need metaprogramming to update in-memory partitioned tables without using SQL statements. 

```TXT
//create an in-memory partitioned database with 'date' as the partitioning column
db = database("", VALUE, 2018.01.02 2018.01.03)

date = 2018.01.02 2018.01.02 2018.01.02 2018.01.03 2018.01.03 2018.01.03
t = table(`IBM`MSFT`GOOG`FB`IBM`MSFT as sym, date, 101 103 103 104 104 107 as price, 0 99 102 103 103 104 as qty)
trades = db.createPartitionedTable(t, "trades", "date").append!(t)

//delete the records with qty=0, and sort by volume in ascending order in each partition
trades.erase!(<qty=0>).sortBy!(<price*qty>)

//add a new column 'logPrice'
trades[`logPrice]=<log(price)>

//update column 'qty' for IBM
trades[`qty, <sym=`IBM>]=<qty+100>
```

## 7. Summary

DolpinDB is specifically designed to process huge volumes of data by integrating the distributed database and the distributed computing framework. DolphinDB supports various programming paradigms, such as SQL programming, functional programming and metaprogramming. As a result, DolphinDB's scripting language is high expressive and enables rapid development.