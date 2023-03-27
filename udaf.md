# User-Defined Aggregate Functions

DolphinDB provides extensible support through user-defined functions (UDFs) and user-defined aggregate functions (UDAFs), both of which can be created with the DolphinDB scripting language.

In this tutorial, we will discuss:

> \- how to define a UDAF in DolphinDB;
>
> \- defining a UDAF with MapReduce for distributed computing
>
> \- defining a UDAF with cumulative grouping logic

## 1. Defining a UDAF with `defg`

Use the `defg` keyword to define an aggregate function. 

This example shows how geometric mean is calculated in DolphinDB. To prevent data overflow, the logarithmic method is used.

```
defg geometricMean(x){
    return x.log().avg().exp()
}

> geometricMean(2 4 8);
4
```

Similar to the built-in aggregate functions, UDAFs can be called directly and can also be used in SQL queries.

The following example shows how the aggregate function `geometricMean` is applied to grouped records from an in-memory table.

```
t = table(1 1 1 2 2 2 as id, 2.0 4.0 8.0 1.0 3.0 9.0 as value)
select geometricMean(value) as gval from t group by id
```

## 2. Defining a UDAF with MapReduce Implementation

Things get more complicated when a SQL query applies a UDAF to grouped records in a DFS table:

- If the *group by* columns are partitioning columns, the system only needs to execute the query in each partition and merge the intermediate results to get the final result.
- If the *group by* columns don’t match the partitioning columns, the MapReduce model is implemented. 

Let’s see how the `geometricMean` function that we defined earlier is executed in the second scenario with the MapReduce implementation:

(1) the map phase - the system calculates the logarithmic mean and the number of non-null values in each partition;

(2) the reduce phase - calculates the weighted average of the logarithmic means of all partitions. Apply the exponential function `exp` to the weighted average to transform it to the geometric mean.

```
// standard UDAF declaration
defg geometricMean(x){
    return x.log().avg().exp()
}

// in a distributed model
def logAvg(x) : log(x).avg()

defg geometricMeanReduce(logAvgs, counts) : wavg(logAvgs, counts).exp()

mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce}
```

Use the `mapr` keyword to define the MapReduce implementation of a UDAF. Next to the `mapr` keyword is the signature of the UDAF. The functions are wrapped in curly braces `{}`. Inside the braces, the functions to the left of `->`  are executed in the map phase, and the function to its right is executed in the reduce phase. 

In this example, there are two map functions, `logAvg` and `count`, which are separated by a comma. Note that the parameters of the map functions must be defined in the UDAF signature.

> To use this UDAF in a distributed DolphinDB database, paste the above code to the initialization script *dolphindb.dos* and reboot the server.

In the next example, we apply the UDAF `geometricMean` to a partitioned in-memory table. The in-memory table is partitioned on dates while the SQL query groups data by stock symbols, which would trigger the implementation of MapReduce.

```
t = table(2020.09.01 + 0 0 1 1 3 3 as date, take(`IBM`MSFT, 6) as sym, 1.0 2.0 3.0 4.0 9.0 8.0 as value)
db = database("", RANGE, [2020.09.01, 2020.09.03, 2020.09.10])
stock = db.createPartitionedTable(t, "stock", "date").append!(t)
select geometricMean(value) as gval from stock group by sym

sym  gval
---- ----
IBM  3
MSFT 4
```

The following rules about MapReduce could be concluded from this example:

- The map functions are applied to each and every partition of the queried table. Therefore, for a table with *n* partitions, each map function will be called *n* times. In this example, the “stock“ table is divided into two partitions by dates, so the map functions `logAvg(x)` and `count(x)` each get called twice. 
- The results of the map functions are passed as arguments to the reduce function. The number of map functions is equal to the number of arguments of the reduce function. Each argument of the reduce function is a vector whose length is equal to the number of partitions. 

## 3. Defining a UDAF with Cumulative Grouping Logic

Cumulative grouping (“cgroup by”) is often used to calculate cumulative metrics of data grouped by time. The system first calculates the metric of the first group, then the metric of the first two groups, then the first three groups, and so on. However, if the computing engine follows exactly this logic, the calculation would be very inefficient.  

One way to improve this is to calculate a few metrics in each group first and perform running aggregation over the results. This logic is similar to MapReduce. The difference is that, with MapReduce, a single aggregation is performed, whereas with cumulative grouping, running aggregations are performed over each group.

Sticking with the geometric mean example, the following script calculates the geometric mean with cumulative grouping logic by a) defining a new UDF `geometricMeanRunning` and b) extending the `mapr` statement. 

The following `mapr` statement contains the implementations of MapReduce and cumulative grouping (`copy,copy -> geometricMeanRunning`), which are separated by a semicolon. Since the map phases in both MapReduce and cumulative grouping are identical, we can use the `copy` function to pass the map phase output of MapReduce directly to the reduce function of cumulative grouping, i.e., `geometricMeanRunning`. 

```
def geometricMeanRunning(logAvgs, counts) : cumwavg(logAvgs, counts).exp()

defg geometricMeanReduce(logAvgs, counts) : wavg(logAvgs, counts).exp()

mapr geometricMean(x){logAvg(x), count(x) -> geometricMeanReduce; copy, copy->geometricMeanRunning}
```

> To use the UDAF `geometricMean` with cumulative grouping in a distributed system, update *dolphindb.dos* with the script above and reboot the server.

```
t = table(2020.09.01 + 0 0 1 1 3 3 as date, take(`IBM`MSFT, 6) as sym, 1.0 2.0 3.0 4.0 9.0 8.0 as value)
select geometricMean(value) as gval from t cgroup by date order by date

date       gval
---------- -----------------
2020.09.01 1.414213562373095
2020.09.02 2.213363839400643
2020.09.04 3.464101615137754
```

## 4. Example of a More Complex UDAF

This section introduces the implementation of a more complex UDAF for t-statistics calculation, `tval`. The following script shows the definition of `tval`.

```
defg tval(x, w){
	wavgX = wavg(x, w)
	wavgX2 = wavg(x*x, w)
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

def wsum2(x,w): wsum(x*x, w)

defg tvalReduce(wsumX, wsumX2, w){
	wavgX = wsumX.sum()\w.sum()
	wavgX2 = wsumX2.sum\w.sum()
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

def tvalRunning(wsumX, wsumX2, w){
	wavgX = wsumX\w
	wavgX2 = wsumX2\w
	return wavgX/sqrt(wavgX2 - wavgX.square())
}

mapr tval(x, w){wsum(x, w), wsum2(x, w), contextSum(w, x)->tvalReduce; cumsum, cumsum, cumsum->tvalRunning}
```

The map phase of MapReduce involves three parts of calculation: the weighted sum of x [wsum(x,w)](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/w/wsum.html), the weighted sum of squares of x `wsum2(x,w)`, and the sum of weights [contextSum(w,x)](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/c/contextSum.html) (instead of [sum(w)](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/sum.html), considering that the data may contain null values). 

The reduce function `tvalReduce` of MapReduce takes the outputs of the three map functions as arguments and returns the final result. For cumulative grouping, we transform the output of each map function in MapReduce to cumulative sums and pass them to the reduce function `tvalRunning` for running aggregation. 