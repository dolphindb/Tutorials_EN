# High Frequency Data Analysis: Working with Pivoting

For high frequency data in financial markets, each record typically holds the information of a stock at a specific timestamp. We often need to rearrange a column (or the calculation results involving multiple columns) into a matrix or table with the timestamps as row labels and security IDs as column labels. This operation (referred to as "pivoting") can be achieved with the SQL `pivot by` keyword or the `pivot` function in DolphinDB. The result can be used in vector operations for optimal performance.

## 1. Calculating Pairwise Correlations of Stock Returns

In pairs trading and hedging, we often need to calculate the pairwise correlations of multiple securities. Traditional databases are not able to perform such complex calculations. Using statistical software would require data migration between systems, which can be very time-consuming with a large amount of data. In DolphinDB, pairwise correlation can be calculated with the help of SQL `pivot by` clause.

First, load the “quotes” table with the US stock data.

```
quotes = loadTable("dfs://TAQ", "quotes")
```

Select the 500 stocks with the largest numbers of quotes on 08/04/2009: 

```
dateValue=2009.08.04
num=500
syms = (exec count(*) from quotes where date = dateValue, time between 09:30:00 : 15:59:59, 0<bid, bid<ofr, ofr<bid*1.1 group by Symbol order by count desc).Symbol[0:num]
```

Use the [pivot by](https://dolphindb.com/help/SQLStatements/pivotBy.html) clause together with the aggregate function avg to downsample the raw data into minute level data. The `exec` keyword generates a matrix with stock IDs as column labels and minutes as row labels.

```
priceMatrix = exec avg(bid + ofr)/2.0 as price from quotes where date = dateValue, Symbol in syms, 0<bid, bid<ofr, ofr<bid*1.1, time between 09:30:00 : 15:59:59 pivot by time.minute() as minute, Symbol
```

Convert the price matrix to a stock return matrix:

```
retMatrix = ratios(priceMatrix)-1
```

Use the function `corrMatrix` to calculate the pairwise correlations: 

```
corrMAT = corrMatrix(retMatrix)
```

The above scripts select nearly 190 million records on 08/04/2009 from the 269.3 billion records of the “quotes“ table to calculate the pairwise correlations of the returns of 500 stocks. It only takes 2629.85 milliseconds to complete the computation.  

We can run the following queries on the corrMAT matrix: 

(1) For each stock, select the 10 stocks with the highest correlation:

```
mostCorrelated = select * from table(corrMAT.columnNames() as sym, corrMAT).unpivot(`sym, syms).rename!(`sym`corrSym`corr) context by sym having rank(corr,false) between 1:10
```

(2) Select the 10 stocks with the highest correlation with “SPY”:

```
select * from mostCorrelated where sym='SPY' order by corr desc
```

## 2. IOPV Calculation

When backtesting index arbitrage strategies, we need to calculate the IOPV (Indicative Optimized Portfolio Value) of an index or an ETF.

For simplicity, we assume an ETF has 2 constituents, AAPL and FB. The weights of the constituents are saved in the “weights“ dictionary. Nanosecond timestamps are used in this example.

Simulate data for the ETF:

```
Symbol=take(`AAPL, 6) join take(`FB, 5)
Time=2019.02.27T09:45:01.000000000+[146, 278, 412, 445, 496, 789, 212, 556, 598, 712, 989]
Price=173.27 173.26 173.24 173.25 173.26 173.27 161.51 161.50 161.49 161.50 161.51
quotes=table(Symbol, Time, Price)
weights=dict(`AAPL`FB, 0.6 0.4)
ETF = select Symbol, Time, Price*weights[Symbol] as weightedPrice from quotes
select last(weightedPrice) from ETF pivot by Time, Symbol;
```

The above script creates the table ETF and rearranges it into a new table with the `pivot by` clause:

```
Time                          AAPL    FB
----------------------------- ------- ------
2019.02.27T09:45:01.000000146 103.962
2019.02.27T09:45:01.000000212         64.604
2019.02.27T09:45:01.000000278 103.956
2019.02.27T09:45:01.000000412 103.944
2019.02.27T09:45:01.000000445 103.95
2019.02.27T09:45:01.000000496 103.956
2019.02.27T09:45:01.000000556         64.6
2019.02.27T09:45:01.000000598         64.596
2019.02.27T09:45:01.000000712         64.6
2019.02.27T09:45:01.000000789 103.962
2019.02.27T09:45:01.000000989         64.604
```

A traditional statistical system would calculate the IOPV of an index at each timestamp as follows:

- Rearrange three columns (timestamps, symbols, and prices) in the "quotes" table to generate a new table.
- Forward fill the NULLs in the new table.
- Sum up the weighted price of the constituents at each row.

Since the U.S. market uses nanosecond timestamps, it is very rare that different stocks have records with the same timestamp. Moreover, an index is usually composed of a large number of constituents (e.g., the S&P 500). If the time period for backtesting is very long involving hundreds of millions of or even billions of rows, using a traditional statistical system will generate an intermediate table that is much larger than the original table. This may cause memory shortage and slow down the performance.

The steps described above can be completed in DolphinDB with just one SQL statement with `pivot by`. Not only is much less script needed, but also the performance is significantly improved. No intermediate tables are generated, thus avoiding out of memory issues.

```
select rowSum(ffill(last(weightedPrice))) from ETF pivot by Time, Symbol;
```

Output:

```
Time                          rowSum
----------------------------- -------
2019.02.27T09:45:01.000000146 103.962
2019.02.27T09:45:01.000000212 168.566
2019.02.27T09:45:01.000000278 168.56
2019.02.27T09:45:01.000000412 168.548
2019.02.27T09:45:01.000000445 168.554
2019.02.27T09:45:01.000000496 168.56
2019.02.27T09:45:01.000000556 168.556
2019.02.27T09:45:01.000000598 168.552
2019.02.27T09:45:01.000000712 168.556
2019.02.27T09:45:01.000000789 168.562
2019.02.27T09:45:01.000000989 168.566
```

