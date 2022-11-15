# High Frequency Data Analysis: Converting High-frequency Signals to Discrete Buy/Sell Signals

In high-frequency trading, we generate high-frequency signals from trade and quote tick data and analyze these signals to identify trading opportunities. This tutorial demonstrates how to convert high-frequency signals into discrete buy/sell/hold signals. Essentially, the problem is to convert an array of floating-point values into an array of only 3 integers: +1 (buy), 0 (hold) and -1 (sell).

The conversion rules can be quite simple. For example,

- +1 if signal > t1 
- -1 if signal < t2 
- 0 otherwise  

Such conversion rules can be easily implemented in DolphinDB with the function `iif`:

```
iif(signal > t1, 1, iif(signal <t2, -1, 0))
```

However, to avoid too frequent reversals of trading direction, we usually adopt a more complex set of rules: if a signal is above the *t1* threshold, it’s a buy signal (+1) and the subsequent signals remain buy signals until one falls below the *t10* threshold. Similarly, if a signal is below the *t2* threshold, it is a sell signal (-1) and the subsequent signals remain sell signals until a signal exceeds the *t20* threshold. The relationship between the thresholds is as follows:

```
t1 > t10 > t20 > t2
```

With the above rules, the value of a trade signal is determined not only by the value of the current signal but also by the state of the previous signal. This is a typical example of path dependence, which is commonly considered unsuitable or difficult to be handled by vector operations and thus very slow in scripting languages including DolphinDB.

In some cases, however, a path dependence problem can be solved with vector operations. The problem above is one such example. The next section describes how to solve it with vector operations.

First, find out the signals that fall in the ranges of a determined state:

- if signal > t1, state=1 
- if signal < t2, state=-1 
- if t20<= signal <= t10, state=0 

The states of the signals in the ranges of [t2,t20] and [t10,t1] are determined by the states of the signals preceding these ranges. 

The DolphinDB script for implementing the above rules:

```
direction = (iif(signal>t1, 1, iif(signal<t2, -1, iif(signal between t20:t10, 0, NULL)))).ffill().nullFill(0)
```

Let’s run a simple test:

```
t1= 10
t10 = 6
t20 = -6
t2 = -10
signal = 20.12 8.78 4.39 -20.68 -8.49 -6.98 0.7 2.08 8.97 12.41
direction = (iif(signal>t1, 1, iif(signal<t2, -1, iif(signal between t20:t10, 0, NULL)))).ffill().nullFill(0)
```

 The script would be like this if we use pandas:

```python
t1=60
t10=50
t20=30
t2=20
signal=pd.Series([20.12,8.78,4.39,-20.68,-8.49,-6.98,0.7,2.08,8.97,12.41])
start=time.time()
direction1=(signal.apply(lambda signal: 1 if signal > t1 else(-1 if signal<t2 else(0 if t20 < signal < t10 else np.nan)))).ffill().fillna(0)
```

The test below generates a random array of 10 million signals between 0 and 100 to test the performance of DolphinDB and pandas. The test environment setup is as follows:

CPU: Intel(R) Core(TM) i7-7700 CPU @3.60GHz 3.60 GHz

Memory: 16 GB

OS: Windows 10

**The executions take 171.73ms (DolphinDB) and 3.28 seconds (pandas), respectively.**

DolphinDB script:

```
t1= 10
t10 = 6
t20 = -6
t2 = -10
signal = rand(100.0, 10000000)
direction = (iif(signal>t1, 1, iif(signal<t2, -1, iif(signal between t20:t10, 0, NULL)))).ffill().nullFill(0)
```

pandas script:

```python
import time
t1= 60
t10= 50
t20= 30
t2= 20
signal= pd.Series(np.random.random(10000000) * 100)
start= time.time()
direction1=(signal.apply(lambda signal: 1 if signal > t1 else(-1 if signal<t2 else(0 if t20 < signal < t10 else np.nan)))).ffill().fillna(0)
end= time.time()
print(end- start)
```