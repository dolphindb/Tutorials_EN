# DECIMAL in DolphinDB

To meet various business requirements for numeric calculations, a database system usually supports both exact and approximate data types. The requirement for data precision is especially high in financial analysis. Since server version 2.00.8, DolphinDB has introduced two new data types, DECIMAL32 and DECIMAL64, to ensure data consistency and calculation accuracy.

This tutorial will briefly introduce the usage and calculation rules of the DECIMAL data types, as well as compare them with floating-point data types (DOUBLE/FLOAT) in DolphinDB.

- [1. Define Decimals](#1-define-decimals)
  - [1.1 Scalar](#11-scalar)
  - [1.2 Vector](#12-vector)
  - [1.3 Table](#13-table)
- [2. Range and Overflow](#2-range-and-overflow)
  - [2.1 Value Range](#21-value-range)
  - [2.2 Overflow Checks](#22-overflow-checks)
- [3. Binary Operation](#3-binary-operation)
  - [3.1 DECIMALs](#31-decimals)
  - [3.2 DECIMAL and Integer](#32-decimal-and-integer)
  - [3.3 DECIMAL and Floating-Point Number](#33-decimal-and-floating-point-number)
- [4.Load Data as DECIMALs](#4load-data-as-decimals)
- [5. DECIMAL32/DECIMAL64 v.s. DOUBLE/FLOAT](#5-decimal32decimal64-vs-doublefloat)
  - [5.1 Truncation](#51-truncation)
  - [5.2 Accuracy](#52-accuracy)
  - [5.3 Limitations of DECIMALs](#53-limitations-of-decimals)

## 1. Define Decimals

Different from the floating-point data types FLOAT and DOUBLE, creating a DECIMAL value in DolphinDB requires an input value and a specified precision range.

`decimal32(X, scale)` / `decimal64(X, scale)`, where:

- *X* is a scalar or vector of integral, floating-point, or STRING type.

- scale is an integer indicating the number of decimal places that DECIMAL value should retain.

For example, `decimal32(3, 2)` converts the integer 3 into a DECIMAL32 data type with two decimal digits.

As of the current version, DolphinDB supports the following data forms of DECIMAL type: scalar, vector, table, etc. In this chapter, we will demonstrate how to create DECIMAL values in DolphinDB.

### 1.1 Scalar

In MySQL, a DECIMAL value must be created with `decimal(p,s)` where *p* indicates the total number of digits in the DECIMAL and *s* represents the number of digits in the fractional part. While in DolphinDB, we only need to specify an integral/floating-point/string scalar with scale to define a DECIMAL value. For example:

```
a=decimal32(142, 2)
//output：142.00

b=decimal32(1.23456, 3)
//output: 1.234

c=decimal32(`1.23456, 3)
//output: 1.234 
```

### 1.2 Vector

There are several different ways to define a vector of DECIMAL32/DECIMAL64 type. Note that the elements in a DECIMAL vector must be of the same type and scale.

(1) Define a big array of DECIMAL32 or DECIMAL 64 type with function `bigarray`:

```
bigarray(DECIMAL32(scale), initialSize, [capacity], [defaultValue])
bigarray(DECIMAL64(scale), initialSize, [capacity], [defaultValue])

x=bigarray(DECIMAL32(3),0,10000000);
x.append!(1..1000)
//output:[1.000,2.000,3.000,4.000,5.000,6.000,7.000,8.000,9.000,10.000]
```

(2) Define an array of DECIMAL32 or DECIMAL 64 type with function `array`:

```
array(DECIMAL32(scale), [initialSize], [capacity], [defaultValue])
array(DECIMAL64(scale), [initialSize], [capacity], [defaultValue])

x=array(DECIMAL32(3), 10, 10, 2.3)
//output: [2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300,2.300]
```

Alternatively, you can convert the data type in the following ways:

```
m=[decimal32(1.2356, 3), decimal32(2.59874, 3), decimal32(-5.23564, 3)]
n=decimal32([1.2356, 2.59874, -5.23564], 3)
```

(3) Define an array vector of DECIMAL32 or DECIMAL 64 type:

```
array(DECIMAL32(scale)[], [initialSize], [capacity], [defaultValue])
array(DECIMAL64(scale)[], [initialSize], [capacity], [defaultValue])

x = array(DECIMAL32(5)[], 0, 10)
val1 = [1.77, 2.8, -3.77, -3.77, 77.32, 1.77]
val2 = [1.77, 2.8, NULL, -3.77, -3.77, 77.32, 1.77, NULL]
x.append!([val1, val2])
//output:[[1.77000,2.80000,-3.77000,-3.77000,77.31999,1.77000],[1.77000,2.80000,,-3.77000,-3.77000,77.31999,1.77000,]]
```

### 1.3 Table

You can define a DECIMAL column in DolphinDB:

```
t=table(100:0, `id`val1`val2, [INT, DECIMAL32(4), DECIMAL64(8)])
```

Data of DECIMAL, integral, floating-point and string types can be inserted into the table:

```
insert into t values(1, decimal32(2.345, 4), decimal64(2.3654, 8));
or
insert into t values(1, 2.345, 2.3654);
```

In addition to an in-memory table, DECIMAL data can also be stored in DFS databases with OLAP/TSDB storage engines. For example:

```
// OLAP engine
dbName="dfs://testDecimal_olap"
if(existsDatabase(dbName)){
	dropDatabase(dbName)
}
t=table(100:0, `id`sym`timev`val1`val2, [INT, SYMBOL, TIMESTAMP, DECIMAL32(4), DECIMAL64(8)])
db=database(dbName, VALUE, 1..10)
pt=db.createPartitionedTable(t, `pt, `id)
n=1000
data=table(rand(1..10, n) as id, rand("A"+string(1..10), n) as sym, rand(2022.11.24T12:23:45.456+1..100, n) as timev, rand(100.0, n) as val1, rand(100.0, n) as val2)
t.append!(data)
pt.append!(t)
select * from loadTable(dbName, `pt)

// TSDB engine
dbName="dfs://testDecimal_tsdb"
if(existsDatabase(dbName)){
	dropDatabase(dbName)
}
t=table(100:0, `id`sym`timev`val1`val2, [INT, SYMBOL, TIMESTAMP, DECIMAL32(4), DECIMAL64(8)])
db=database(dbName, VALUE, 1..10, , "TSDB")
pt=db.createPartitionedTable(t, `pt, `id, , `sym`timev)
n=1000
data=table(rand(1..10, n) as id, rand("A"+string(1..10), n) as sym, rand(2022.11.24T12:23:45.456+1..100, n) as timev, rand(100.0, n) as val1, rand(100.0, n) as val2)
t.append!(data)
pt.append!(t)
select * from loadTable(dbName, `pt)
```

## 2. Range and Overflow

### 2.1 Value Range

The value ranges of DECIMAL32 and DECIMAL64 are shown in the table below, where S indicates the number of decimal places retained.

|  	| Underlying Data Types 	| Number of Bytes 	| Scale Range 	| Valid Range 	| Maximum Precision 	|
|:---	|:---	|:---	|:---	|:---	|:---	|
| DECIMAL32(S) 	| int32_t 	| 4 	| [0, 9] 	| (-1 * 10 ^ (9 - S), 1 * 10 ^ (9 - S)) 	| 9 	|
| DECIMAL64(S) 	| int64_t 	| 8 	| [0, 18] 	| (-1 * 10 ^ (18 - S), 1 * 10 ^ (18 - S)) 	| 18 	|

### 2.2 Overflow Checks

When a numeric data type is converted to DECIMAL type, DolphinDB does not check its value range. The range is only examined when a string is parsed to DECIMAL type. So when a numeric data type is converted to DECIMAL32 and its integer part exceeds the valid value range of DECIMAL32 but still belongs to the valid value range of a 4-byte integer INT32 (i.e., in [-2147483648, 2147483647]), the data can still be successfully converted. However, when a string is forcibly converted to DECIMAL32, an exception will be thrown if its length exceeds the valid number of digits. For example, when an integer 1000000000 is converted to DECIMAL32, no error or overflow occurs because 1000000000 is in [-2147483647, 2147483648]. But when a string "1000000000" is converted to DECIMAL32, an exception will be thrown because the string contains 10 digits, while DECIMAL32 can only represent up to 9 digits.

When performing specific operations on DECIMAL32/DECIMAL64 types, the values may overflow. To ensure data consistency and accuracy, DolphinDB performs overflow checks on the calculation results. The following sections will introduce three common overflow checks.

#### 2.2.1 Data Creation

When a DECIMAL32/DECIMAL64 value is created, the valid range and scale is first examined. An overflow occurs when the specified range exceeds the valid value. If the decimal digits are out of the valid range, an error of "Scale is out of bounds" is reported. For example:

```
decimal32(1.2, 10)
decimal64(1.2, 19)
```

Similarly, an overflow occurs if the number of integers is out of range. In this case, an error of “Decimal math overflow” is reported:

```
decimal32(1000000000, 1)
decimal32(`1000000000, 1)
```

#### 2.2.2 Arithmetic Operation

Even if a value is within the valid value range when it is created, it may overflow as the number of decimal places increases or the value increases during calculation. For example:

```
6*decimal32(4.2, 8)
6*decimal32(100000000, 1)
```

#### 2.2.3 Comparison Operation

The overflow checks are also applied to comparison operations. When a numeric value is compared with a DECIMAL value, it is automatically converted to DECIMAL type for comparison. Overflow may occur during the data type conversion. For example:

```
decimal32(1, 8) < 100
//output: Decimal math overflow
```

## 3. Binary Operation

### 3.1 DECIMALs

(1) `DECIMAL32(S1) <op> DECIMAL32(S2) => DECIMAL32(S)`

```
m=decimal32(1.23, 3)+decimal32(2.45, 2)
//output:3.680
//typestr:DECIMAL32
```

(2) `DECIMAL64(S1) <op> DECIMAL64(S2) => DECIMAL64(S)`

```
m=decimal64(1.23, 3)+decimal64(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

​(3) `DECIMAL64(S1) <op> DECIMAL32(S2) => DECIMAL64(S)`

```
m=decimal64(1.23, 3)+decimal32(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

(4) `DECIMAL32(S1) <op> DECIMAL64(S2) => DECIMAL64(S)`

```
m=decimal32(1.23, 3)+decimal64(2.45, 2)
//output:3.680
//typestr:DECIMAL64
```

The scale of the binary operation result between DECIMALs is determined by the rules below:

- Addition and subtraction: `S = max(S1, S2)`
- Multiplication: `S = S1 + S2`

```
m=decimal64(1.23, 3)*decimal32(2.45, 2)
//output:3.01350
//typestr:DECIMAL64
```

- Division: `S = S1`

```
m=decimal64(1.23, 3)/decimal32(2.45, 2)
//output:0.502
//typestr:DECIMAL64
```

### 3.2 DECIMAL and Integer

When a binary operation involves an integer (of INT or LONG type) and a DECIMAL, the integer will be converted to a DECIMAL value of the same type. For example, `decimal32(10, 2)*6` is equivalent to `decimal32(10, 2)*decimal32(6, 0)`. Therefore, multiplying an integer by a DECIMAL with a scale of S, the scale of the multiplication is still S.

### 3.3 DECIMAL and Floating-Point Number

In DolphinDB, the binary operation between a DECIMAL and a floating-point number is not defined, but the system does not throw an exception. To perform such operation, it is recommended to force convert the floating-point value to DECIMAL first.

## 4.Load Data as DECIMALs

You can load data as DECIMALs by specifying the table schema with `loadText`. For example:

First we use function `saveText` to save a *.csv* file:

```
WORK_DIR="/hdd/hdd1/test_decimal/"
n=1000
t=table(rand(1..100, n) as id, rand(2022.11.23T12:39:56+1..100, n) as datetimev, rand(`AAPL`ARS`BSA, n) as sym, rand(rand(100.0, 10) join take(00f, 10), n) as val1, rand(rand(100.0, 10) join take(00f, 10), n) as val2)
saveText(t, WORK_DIR+"test_decimal.csv")
```

Then load the file by specifying the table schema:

```
schemaTable=table(`id`timev`sym`val1`val2 as name, [`INT, `DATETIME, `SYMBOL, "DECIMAL32(4)", "DECIMAL64(5)"] as type)
re=loadText(filePath, , schemaTable)
```

## 5. DECIMAL32/DECIMAL64 v.s. DOUBLE/FLOAT

### 5.1 Truncation

Representing an infinite number of real numbers with a finite number of bits requires an approximation. For most programs, the results of integer computations can be stored in 32 bits. However, given any fixed number of bits, some calculation results cannot be accurately represented with that many bits. Therefore, the results of floating-point calculations must typically be rounded to fit their finite representation.

The precision of DOUBLE and FLOAT types follows the IEEE 754 standard, which rounds the data when representing a finite number of decimal places. For example, reducing the decimal places of 1.2356789 to three results in an output of 1.236. The precision of DECIMAL32/DECIMAL64 types follows the IEEE 754-2008 standard, which reduces the decimal digits of 1.2356789 to three, resulting in an output of 1.235.

### 5.2 Accuracy

We use one of the most commonly used representations, the IEEE 754 standard (IEEE Floating-Point Representation), to represent real numbers. The floating-point representation has a base β (usually assumed to be even) and a precision p. If β=10 and p=3, the number 0.1 is represented as 1.00 × 10 -1; if β=2 and p=24, the decimal number 0.1 cannot be accurately represented and is approximated as 1.10011001100110011001101 × 2 -4.

Real numbers cannot be accurately represented as floating-point numbers for two reasons: 

- A number like 0.1 has a finite decimal representation, but in binary it has an infinite repeating representation, resulting in an approximate value.

- The out-of-range data are processed internally by the system.

FLOAT/DOUBLE data types are binary floating-point types. If an operation involves DOUBLE data, it converts the value to binary where the result can only be expressed as an infinite repeating decimal, resulting in calculation error. For the data that exceeds the value range of FLOAT and DOUBLE, the result is set to NULL in the DolphinDB, ensuring that data can continue to be calculated when overflow occurs. For example, the result of 0/0 is NULL. The DECIMAL type is a decimal floating-point type, where 0.1 is represented as 1.00 × 10 -1 without precision loss. In addition, the system reports an overflow error when data overflows to avoid precision loss.

### 5.3 Limitations of DECIMALs

In DolphinDB, compared with FLOAT/DOUBLE types, currently the DECIMAL types have the following limitations:

- Streaming data is not supported.
- Several built-in functions are not supported.
- DECIMAL types cannot be used in matrices or sets.
- BOOL/CHAR/SYMBOL/UUID/IPADDR/INT128 types and temporal types cannot be converted to the DECIMAL type. To convert STRING/BLOB type to DECIMAL type, the prerequisite is that the data can be converted to a numerical type.

In conclusion, using an appropriate data type for floating-point processing involves considering value range, approximation and accuracy requirements. The decimal data type offers an advantageous balance between range and precision, making it a useful choice for many applications where accuracy is paramount. By understanding the strengths and limitations of decimal, users can effectively leverage this data type to optimize the accuracy and reliability of calculations.