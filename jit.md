# DolphinDB Tutorial: Just-in-time (JIT) Compilation

Starting from version 1.01, DolphinDB supports JIT. 

## 1 Introduction

Programming languages are generally either compiled language or interpreted language. For compiled language, the source code is translated into machine code before the program is executed. For interpreted language, source code is interpreted and executed. Compiled language generally runs faster than interpreted language, but interpreted language is more flexible.

With just-in-time compilation, the source code is translated into machine code at runtime, which can achieve execution efficiency similar to compiled languages. Python's third-party implementation, PyPy, significantly improves interpreter performance through JIT. Most Java implementations rely on JIT to improve efficiency.

## 2 The role of JIT

The programming language of DolphinDB is an interpreted language. The program is first parsed to generate a syntax tree and then executed recursively. The interpretive overhead is high where vectorization cannot be used. DolphinDB is implemented in C++, and a function call in DolphinDB script is converted into multiple virtual function calls in C++. This process is time consuming in for- loops, while- loops and if-else statements and may not meet performance requirements in some scenarios, such as factor calculation with high-frequency data and real-time stream processing applications, etc.

JIT in DolphinDB significantly improves the execution speed of for- loops, while- loops and if-else statements. It is especially useful for scenarios where vectorized calculations cannot be conducted but fast execution speed is needed.

Next, we use a very simple example to compare the performance with and without JIT for a do-while loop that calculates the sum of all integers from 1 to 1,000,000 100 times.
``` 
def sum_without_jit(n) {
  s = 0l
  i = 1
  do {
    s += i
    i += 1
  } while(i <= n)
  return s
}

@jit
def sum_with_jit(n) {
  s = 0l
  i = 1
  do {
    s += i
    i += 1
  } while(i <= n)
  return s
}

timer(100) sum_without_jit(1000000) //  91017 ms
timer(100) sum_with_jit(1000000)    //    217 ms
```

It takes more than 400 times longer without JIT than with JIT.

Please note that the purpose of the example above is to show the performance advantage of JIT in a loop. For simple loops similar to the example above, we should generally use DolphinDB built-in functions that conduct vectorized calculations, as many built-in functions are further optimized and it is more convenient to use built-in functions. In the example above, if we use DolphinDB built-in function `sum`, the execution time is about 20% of the JIT. In general, the more complicated the loop, the greater the advantage of JIT over built-in functions.

The following is an example of a more complicated loop:
``` 
def signal_without_jit(signal, n, t1, t10, t20, t2) {
  cur = 0
  idx = 0
  output = array(INT, n, n)
  for (s in signal) {
    if(s > t1) {           // (t1, inf)
      cur = 1
    } else if(s >= t10) {  // [t10, t1]
      if(cur == -1) cur = 0
    } else if(s > t20) {   // [t20, t10)
      cur = 0
    } else if(s >= t2) {   // [t2, t20]
      if(cur == 1) cur = 0
    } else {               // (-inf, t2)
      cur = -1
    }
    output[idx] = cur
    idx += 1
  }
  return output
}
```
can be rewritten as vectorized calculation:
``` 
direction = (iif(signal>t1, 1h, iif(signal<t10, 0h, 00h)) - iif(signal<t2, 1h, iif(signal>t20, 0h, 00h))).ffill().nullFill(0h)
```
This, however, requires that the user is familiar with DolphinDB built-in function `iif`. 

The JIT-version of function `signal_without_jit`:
``` 
@jit
def signal_with_jit(signal, n, t1, t10, t20, t2) {
  cur = 0
  idx = 0
  output = array(INT, n, n)
  for (s in signal) {
    if(s > t1) {           // (t1, inf)
      cur = 1
    } else if(s >= t10) {  // [t10, t1]
      if(cur == -1) cur = 0
    } else if(s > t20) {   // [t20, t10)
      cur = 0
    } else if(s >= t2) {   // [t2, t20]
      if(cur == 1) cur = 0
    } else {               // (-inf, t2)
      cur = -1
    }
    output[idx] = cur
    idx += 1
  }
  return output
}
```

Let's compare the performance of the vectorized calculation, for-loop without JIT and for-loop with JIT. 
``` 
n = 10000000
t1= 60
t10 = 50
t20 = 30
t2 = 20
signal = rand(100.0, n)

timer (iif(signal >t1, 1h, iif(signal < t10, 0h, 00h)) - iif(signal <t2, 1h, iif(signal > t20, 0h, 00h))).ffill().nullFill(0h) // 410.920 ms
timer signal_with_jit(calculate, signal, size(signal), t1, t10, t20, t2)       //    170.751 ms
timer signal_without_jit(signal, size(signal), t1, t10, t20, t2)               //  14044.064 ms
```

In this example, for-loop with JIT is 2.4 times as fast as vectorized calculation and 82 times faster than for-loop without JIT. Here JIT is faster than vectorized calculation, as the vectorized calculation calls the built-in functions of DolphinDB many times. This involves memory allocation and virtual function calls for many times and produces a large number of intermediate results. In comparison, JIT-generated machine code does not have these additional overhead.

Some calculations cannot use vectorization. For example, the implied volatility of an option is calculated with Newton's method instead of vectorization. To improve performance for this type of calculation, we can either use DolphinDB's [plugin](https://github.com/dolphindb/DolphinDBPlugin) or use JIT. The difference between them is that plugins can be used in any scenario but they need to be written in C++; JIT is relatively easy to write but the applicable scenarios are limited. The speed of JIT is very close to the speed of C++ plugin.


## 3 How to use JIT

### 3.1 Declare

DolphinDB currently only supports JIT for user-defined functions. Just write @jit in the line before the definition of a function:
``` 
@jit
def myFunc(/* arguments */) {
  /* implementation */
}
```

When this function is called, DolphinDB will compile the function definition to machine code at runtime and execute it.

### 3.2 Supported statements

Currently DolphinDB supports the following statements in JIT:

- Assignment statements. For example:
``` 
@jit
def func() {
  y = 1
}
```

Please note that multiple assign is currently not supported. For example, execution of the following function will throw an exception:
``` 
@jit
def func() {
  a, b = 1, 2
}
func()
```

- Return statement. For example:
``` 
@jit
def func() {
  return 1
}
```

- If-else statement. For example：
``` 
@jit
def myAbs(x) {
  if(x > 0) return x
  else return -x
}
```

- Do-while statement. For example：

``` 
@jit
def mySqrt(x) {
    diff = 0.0000001
    guess = 1.0
    guess = (x / guess + guess) / 2.0
    do {
        guess = (x / guess + guess) / 2.0
    } while(abs(guess * guess - x) >= diff)
    return guess
}
```

- For statement. For example：

``` 
@jit
def mySum(vec) {
  s = 0
  for(i in vec) {
    s += i
  }
  return s
}
```

- break and continue statements. For example:

``` 
@jit
def mySum(vec) {
  s = 0
  for (i in vec) {
    if(i % 2 == 0) continue
    s += i
  }
  return s
}
```

JIT in DolphinDB supports arbitrary nesting of the statements above.

### 3.3 Supported operators and functions

<!-- add, sub, multi, div, bitor, bitand, bitxor, seq, eq, neq, lt, le, gt, ge, neg, at, mod -->
Currently the following operators are supported in JIT: add (+), sub (-), multiply (*), divide (/), and (&&), or (||), bitand (&), bitor (|), bitxor (^ ), eq (==), neq (! =), ge (> =), gt (>), le (<=), lt (<), neg (-), mod (%), seq (.... ), at ([]). The implementation of the operators above for all data types is identical with the implementation in non-JIT.

Currently the following mathematical functions are supported in JIT: `exp`,` log`, `sin`,`asin`, `cos`,`acos`, `tan`,` atan`, `abs`,`ceil`,`floor` and `sqrt`. When these mathematical functions appear in the JIT, if function parameter is a scalar, the corresponding function in glibc or the optimized C-implemented function is called in the machine code; if function parameter is an array, these DolphinDB built-in mathematical functions will be called in the machine code. The advantage of this approach is that the code implemented by directly calling C improves efficiency and reduces unnecessary virtual function calls and memory allocation.

Currently the following built-in functions are supported in JIT: `take`,`array`, `size`,` isValid`, `rand` and `cdfNormal`. 

Please note that the first parameter of function `array` must be a constant indicating a data type and cannot be a variable. This is because JIT compilation must know the data types of all variables before compilation. 

### 3.4 Null values

Each data type in DolphinDB uses the minimum value of the type to represent the Null value. JIT adopts the same approach.

### 3.5 Call another JIT function from a JIT function

A JIT function can call another JIT function:

``` 
@jit
def myfunc1(x) {
  return sqrt(x) + exp(x)
}

@jit
def myfunc2(x) {
  return myfunc1(x)
}

myfunc2(1.5)
```

In the example above, `myfunc1` is compiled internally to generate a native function with the signature 'double myfunc1 (double)'. This function is called directly in the machine code generated by `myfunc2` instead of after determining whether `myfunc1` is a JIT function during execution. This ensures the fastest execution speed.

Please note that non-JIT user-defined functions cannot be called within JIT functions, as type inference is not possible. Type inference will be discussed in more detail below.

### 3.6 JIT compilation cost and caching mechanism

JIT in DolphinDB is implemented with [LLVM](https://llvm.org/). Each user-defined function generates its own module when it is compiled. Compilation includes the following steps:

1. Initialization of LLVM related variables and environment.
2. Generate LLVM intermediate representations (IR) based on syntax tree of DolphinDB script.
3. Use LLVM to optimize the IR generated in the second step, and then compile it to machine code. 

The first step usually takes less than 5ms, and the time for the next two steps depends on the complexity of the script. In general, compilation time is no more than 50ms.

For each combination of data types of parameters, a JIT function is complied only once. The results of JIT function compilation are cached. When a JIT function is called with a combination of parameter data types that has been compiled, the function is executed immediately; otherwise the function is compiled and executed with the compilation results saved in a table. 

JIT can significantly improve performance for tasks that need to be executed repeatedly or for tasks with much longer execution time than compilation time. 

### 3.7 Limitations

Currently, JIT in DolphinDB can only be used in limited scenarios:

- JIT only supports user-defined functions.
- JIT functions only accept parameters with data forms of scalar or array. Other data forms such as pair, dict or table are not supported. 
- JIT functions cannot accept parameters with data types of string or symbol.
- A subarray cannot be used as a parameter.


## 4 Type Inference

The data form/type of all variables in the script must be known before LLVM is used to generate IR. Type inference in DolphinDB JIT is local derivation. For example:

``` 
@jit
def foo() {
  x = 1
  y = 1.1
  z = x + y
  return z
}
```
In this example, the system determines the data type of x as INT from x=1; determines the type of y as DOUBLE from y=1.1; determines the type of z as DOUBLE from z=x+y and that x is INT and y is DOUBLE.

If a function has parameters, such as
``` 
@jit
def foo(x) {
  return x + 1
}
```
The data form/type of the result of the `foo` function depends on the data form/type of parameter x.

If a data form/type that is not supported by JIT appears inside a JIT function, or if the data form/type of an input variable is not supported by JIT, type inference fails and an exception will be thrown. 

``` 
@jit
def foo(x) {
  return x + 1
}

foo (123)             // executed successfully
foo ("abc")           // throws an exception because STRING is not supported in JIT
foo (1:2)             // throws an exception because pair is not supported in JIT
foo ((1 2, 3 4, 5 6)) // throws an exception because tuple is not supported in JIT

@jit
def foo(x) {
  y = cumprod(x)
  z = y + 1
  return z
}

foo (1..10)          // throws an exception. As function cumprod is not currently supported, the data type of the result is unknown, resulting in type inference failure
```

In JIT, please avoid using unsupported data form/type in functions or parameters such as tuple, string, etc., or functions that are not yet supported in JIT.


## 5 Examples

### 5.1 Implied volatility of options

The calculation of implied volatility of options is an example of calculations that cannot be vectorized. 
``` 
@jit
def GBlackScholes(future_price, strike, input_ttm, risk_rate, b_rate, input_vol, is_call) {
  ttm = input_ttm + 0.000000000000001;
  vol = input_vol + 0.000000000000001;

  d1 = (log(future_price/strike) + (b_rate + vol*vol/2) * ttm) / (vol * sqrt(ttm));
  d2 = d1 - vol * sqrt(ttm);

  if (is_call) {
    return future_price * exp((b_rate - risk_rate) * ttm) * cdfNormal(0, 1, d1) - strike * exp(-risk_rate*ttm) * cdfNormal(0, 1, d2);
  } else {
    return strike * exp(-risk_rate*ttm) * cdfNormal(0, 1, -d2) - future_price * exp((b_rate - risk_rate) * ttm) * cdfNormal(0, 1, -d1);
  }
}

@jit
def ImpliedVolatility(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call) {
  high=5.0;
  low = 0.0;

  do {
    if (GBlackScholes(future_price, strike, ttm, risk_rate, b_rate, (high+low)/2, is_call) > option_price) {
      high = (high+low)/2;
    } else {
      low = (high + low) /2;
    }
  } while ((high-low) > 0.00001);

  return (high + low) /2;
}

@jit
def test_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call) {
	n = size(future_price)
	ret = array(DOUBLE, n, n)
	i = 0
	do {
		ret[i] = ImpliedVolatility(future_price[i], strike[i], ttm[i], risk_rate[i], b_rate[i], option_price[i], is_call[i])
		i += 1
	} while(i < n)
	return ret
}

n = 100000
future_price=take(rand(10.0,1)[0], n)
strike_price=take(rand(10.0,1)[0], n)
strike=take(rand(10.0,1)[0], n)
input_ttm=take(rand(10.0,1)[0], n)
risk_rate=take(rand(10.0,1)[0], n)
b_rate=take(rand(10.0,1)[0], n)
vol=take(rand(10.0,1)[0], n)
input_vol=take(rand(10.0,1)[0], n)
multi=take(rand(10.0,1)[0], n)
is_call=take(rand(10.0,1)[0], n)
ttm=take(rand(10.0,1)[0], n)
option_price=take(rand(10.0,1)[0], n)

timer(10) test_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)          //   2621.73 ms
timer(10) test_non_jit(future_price, strike, ttm, risk_rate, b_rate, option_price, is_call)      // 302714.74 ms
```

Function `ImpliedVolatility` calls function `GBlackScholes`. Remove @jit before function definition `test_jit` to get function `test_non_jit`. The JIT version `test_jit` is 115 times as fast as the non-JIT version `test_non_jit`. 

### 5.2 Greeks

This example uses JIT to calculates charm (delta decay), which is one of the [Greeks](https://www.wikiwand.com/en/Greeks_(finance)). 
```
@jit
def myMax(a,b){
	if(a>b){
		return a
	}else{
		return b
	}
}

@jit
def NormDist(x) {
  return cdfNormal(0, 1, x);
}

@jit
def ND(x) {
  return (1.0/sqrt(2*pi)) * exp(-(x*x)/2.0)
}

@jit
def CalculateCharm(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
  day_year = 245.0;

  d1 = (log(future_price/strike_price) + (b_rate + (vol*vol)/2.0) * input_ttm) / (myMax(vol,0.00001) * sqrt(input_ttm));
  d2 = d1 - vol * sqrt(input_ttm);

  if (is_call) {
    return -exp((b_rate - risk_rate) * input_ttm) * (ND(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) + (b_rate-risk_rate) * NormDist(d1)) * future_price * multi / day_year;
  } else {
    return -exp((b_rate - risk_rate) * input_ttm) * (ND(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) - (b_rate-risk_rate) * NormDist(-d1)) * future_price * multi / day_year;
  }
}

@jit
def test_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
	n = size(future_price)
	ret = array(DOUBLE, n, n)
	i = 0
	do {
		ret[i] = CalculateCharm(future_price[i], strike_price[i], input_ttm[i], risk_rate[i], b_rate[i], vol[i], multi[i], is_call[i])
		i += 1
	} while(i < n)
	return ret
}


def ND_validate(x) {
  return (1.0/sqrt(2*pi)) * exp(-(x*x)/2.0)
}

def NormDist_validate(x) {
  return cdfNormal(0, 1, x);
}

def CalculateCharm_vectorized(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call) {
	day_year = 245.0;

	d1 = (log(future_price/strike_price) + (b_rate + pow(vol, 2)/2.0) * input_ttm) / (max(vol, 0.00001) * sqrt(input_ttm));
	d2 = d1 - vol * sqrt(input_ttm);
	return iif(is_call,-exp((b_rate - risk_rate) * input_ttm) * (ND_validate(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) + (b_rate-risk_rate) * NormDist_validate(d1)) * future_price * multi / day_year,-exp((b_rate - risk_rate) * input_ttm) * (ND_validate(d1) * (b_rate/vol/sqrt(input_ttm) - d2/2.0/input_ttm) - (b_rate-risk_rate) * NormDist_validate(-d1)) * future_price * multi / day_year)
}

n = 1000000
future_price=rand(10.0,n)
strike_price=rand(10.0,n)
strike=rand(10.0,n)
input_ttm=rand(10.0,n)
risk_rate=rand(10.0,n)
b_rate=rand(10.0,n)
vol=rand(10.0,n)
input_vol=rand(10.0,n)
multi=rand(10.0,n)
is_call=rand(true false,n)
ttm=rand(10.0,n)
option_price=rand(10.0,n)

timer(10) test_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)                     //   1834 ms
timer(10) test_none_jit(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)                // 224099 ms
timer(10) CalculateCharm_vectorized(future_price, strike_price, input_ttm, risk_rate, b_rate, vol, multi, is_call)    //   3118 ms
```

The JIT version is faster than the non-JIT version by 120 times, and is faster than vectorized calculation by 70%. 

### 5.3 Stop loss

The following example calculates where the maximum drawdown exceeds a predetermined threshold for the first time. 
``` 
@jit
def stoploss_JIT(ret, threshold) {
	n = ret.size()
	i = 0
	curRet = 1.0
	curMaxRet = 1.0
	indicator = take(true, n)

	do {
		indicator[i] = false
		curRet *= (1 + ret[i])
		if(curRet > curMaxRet) { curMaxRet = curRet }
		drawDown = 1 - curRet / curMaxRet;
		if(drawDown >= threshold) {
      break
		}
		i += 1
	} while(i < n)

	return indicator
}

def stoploss_no_JIT(ret, threshold) {
	n = ret.size()
	i = 0
	curRet = 1.0
	curMaxRet = 1.0
	indicator = take(true, n)

	do {
		indicator[i] = false
		curRet *= (1 + ret[i])
		if(curRet > curMaxRet) { curMaxRet = curRet }
		drawDown = 1 - curRet / curMaxRet;
		if(drawDown >= threshold) {
      break
		}
		i += 1
	} while(i < n)

	return indicator
}

def stoploss_vectorization(ret, threshold){
	cumret = cumprod(1+ret)
 	drawDown = 1 - cumret / cumret.cummax()
	firstCutIndex = at(drawDown >= threshold).first() + 1
	indicator = take(false, ret.size())
	if(isValid(firstCutIndex) and firstCutIndex < ret.size())
		indicator[firstCutIndex:] = true
	return indicator
}
ret = take(0.0008 -0.0008, 1000000)
threshold = 0.10
timer(10) stoploss_JIT(ret, threshold)              //      59 ms
timer(10) stoploss_no_JIT(ret, threshold)           //   14622 ms
timer(10) stoploss_vectorization(ret, threshold)    //     152 ms
```

### 5.4 Cost of inventory shares

If we frequently add and trim the position of a stock, we need to calculate the average cost of inventory shares in order to calculate realized profit-and-loss for each sell order. Assuming we never have a short position in the stock, after the first (purchase) transaction, the transaction price is the cost of the inventory shares. After a subsequent purchase transaction, the average holding cost is a weighted average of the previous average holding cost and the latest transaction price. After a sell, the average holding cost remains unchanged. If we sell all positions, then the calculation of holding costs starts over. This is a typical path dependence problem and cannot be solved by vectorization.

In the following example, column "price" in table "trades" is the transaction price, and column "amount" is the number of shares that are bought (positive) or sold (negative). 

Calculate cost of inventory shares without JIT:
```
def holdingCost_no_JIT(price, amount){
	holding = 0.0
	cost = 0.0
	avgPrice = 0.0
	n = size(price)
	avgPrices = array(DOUBLE, n, n, 0)
	for (i in 0:n){
		holding += amount[i]
		if (amount[i] > 0){
			cost += amount[i] * price[i]
			avgPrice = cost/holding
		} 
		else{
			cost += amount[i] * avgPrice
		}
	    avgPrices[i] = avgPrice
	}
	return avgPrices
}
```
Calculate cost of inventory shares with JIT:
```
@jit
def holdingCost_JIT(price, amount){
	holding = 0.0
	cost = 0.0
	avgPrice = 0.0
	n = size(price)
	avgPrices = array(DOUBLE, n, n, 0)
	for (i in 0..n){
		holding += amount[i]
		if (amount[i] > 0){
			cost += amount[i] * price[i]
			avgPrice = cost/holding
		} 
		else{
			cost += amount[i] * avgPrice
		}
		avgPrices[i]=avgPrice
	}
	return avgPrices
}
```
Performance comparison:
```
n=1000000
id = 1..n
price = take(101..109,n)
amount =take(1 2 3 -2 -1 -3 4 -1 -2 2 -1,n)
trades = table(id, price, amount)

timer (10)
t = select *, iif(amount < 0, amount*(avgPrice - price), 0) as profit 
from (
  select *, holdingCost_no_JIT(price, amount) as avgPrice
  from trades
)    // 29,509ms

timer (10)
select *, iif(amount < 0, amount*(avgPrice - price), 0) as profit 
from (
  select *, holdingCost_JIT(price, amount) as avgPrice
  from trades
)     // 148 ms
```
With 1 million rows of data in this example, the JIT version and the non-JIT version are executed 10 times on the same machine. The JIT version takes 148 ms and the non-JIT version takes 29509 ms. The JIT version is about 200 times faster than the non-JIT version.

## 6 Future work

In subsequent releases, we plan to add the following features in DolphinDB JIT:

1. Support more data forms such as dictionary and more data types such as STRING. 
2. Support more mathematical and statistical functions.
3. Enhance type inference. Can infer the data types of results for more built-in functions.
4. Support declaration of data types for parameters, results and local variables in user-defined functions.
 

## 7 Summary

DolphinDB database now supports JIT, which significantly improves the execution speed of for- loops, while- loops and if-else statements. It is especially useful for scenarios that require fast execution speed but vectorized calculations cannot be conducted, such as factor calculation with high frequency data and real-time stream processing applications, etc. 
