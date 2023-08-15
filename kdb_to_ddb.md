# Data Migration and Function Mapping: From kdb+ to DolphinDB

- [Data Migration and Function Mapping: From kdb+ to DolphinDB](#data-migration-and-function-mapping-from-kdb-to-dolphindb)
  - [1. Overview](#1-overview)
  - [2. Importing Data from kdb+ to DolphinDB](#2-importing-data-from-kdb-to-dolphindb)
  - [3. DolphinDB Reference for kdb+ Users](#3-dolphindb-reference-for-kdb-users)
    - [3.1 Datatypes](#31-datatypes)
      - [3.1.1 Basic Datatypes](#311-basic-datatypes)
      - [3.1.2 Other Datatypes](#312-other-datatypes)
      - [3.1.3 Data Type Checking Functions](#313-data-type-checking-functions)
    - [3.2 Keywords by Category](#32-keywords-by-category)
      - [3.2.1 control](#321-control)
      - [3.2.2 env](#322-env)
      - [3.2.3 interpret](#323-interpret)
      - [3.2.4 join](#324-join)
      - [3.2.5 list](#325-list)
      - [3.2.6 logic](#326-logic)
      - [3.2.7 math](#327-math)
      - [3.2.8 meta](#328-meta)
      - [3.2.9 query](#329-query)
      - [3.2.10 sort](#3210-sort)
      - [3.2.11 table](#3211-table)
      - [3.2.12 text](#3212-text)
      - [3.2.13 User-Defined Functions](#3213-user-defined-functions)
    - [3.3 Overloaded Glyphs and Operators](#33-overloaded-glyphs-and-operators)
      - [3.3.1 `.` dot](#331--dot)
      - [3.3.2 `@` at](#332--at)
      - [3.3.3 `$` dollar](#333--dollar)
      - [3.3.4 `!` bang](#334--bang)
      - [3.3.5 `?` query](#335--query)
      - [3.3.6 `##` hash](#336--hash)
      - [3.3.7 Operators](#337-operators)
    - [3.4 Iterators](#34-iterators)
      - [3.4.1 `'` quote](#341--quote)
      - [3.4.2 Other Iterators](#342-other-iterators)
    - [3.5 Evaluation Control](#35-evaluation-control)

## 1. Overview

This tutorial introduces how to use the DolphinDB kdb+ plugin to import data from kdb+ into DolphinDB. It also provides mappings between the data types, functions, keywords, and other features of kdb+ and their DolphinDB equivalents.

## 2. Importing Data from kdb+ to DolphinDB

Use the DolphinDB kdb+ plugin to import data from kdb+ to DolphinDB. You can find the plugin and a detailed tutorial on our [GitHub](https://github.com/dolphindb/DolphinDBPlugin/tree/release200/kdb) page.

First, execute `loadPlugin("/path/to/plugin/Pluginkdb.txt")` to load the plugin in DolphinDB, so you can use its provided functions.

The plugin provides two importing options, importing from kdb+ online or from disk. Both options import the data into DolphinDB as an in-memory table.

- Import from a live kdb+ server: 

1. Connect to the running kdb+ server with `connect`, which returns a connection handle. 
2. Use `loadTable` to import the data into DolphinDB by passing in the connection handle, the path to the kdb+ table and optionally the path to the sym file for the table.

3. After importing, `close` the connection.

```
// load plugin
loadPlugin("/home/DolphinDBPlugin/kdb/build/Pluginkdb.txt")

// make sure the subsequent code is executed after the plugin has been loaded
go

// connect to a kdb+ database. Leave username and password empty if the database does not require authentication
handle = kdb::connect("127.0.0.1", 5000, "admin:123456")

// specifiy file path
DATA_DIR="/home/kdb/data/kdb_sample"

// use loadTable to import data into DolphinDB
Daily = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Daily/", DATA_DIR + "/sym")
Minute = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Minute", DATA_DIR + "/sym")
Ticks = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Ticks/", DATA_DIR + "/sym")
Orders = kdb::loadTable(handle, DATA_DIR + "/2022.06.17/Orders", DATA_DIR + "/sym")

// close connection
kdb::close(handle)
```

- Import from kdb+ data files on disk:

Use `loadFile` to read data from disk by specifying the path to the kdb+ table and optionally the path to the sym file for the table.

```
// load plugin
loadPlugin("/home/DolphinDBPlugin/kdb/build/Pluginkdb.txt")

// make sure the subsequent code is executed after the plugin has been loaded
go

// specifiy file path
DATA_DIR="/home/kdb/data/kdb_sample"

// use loadFile to import data into DolphinDB
Daily2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Daily", DATA_DIR + "/sym")
Minute2= kdb::loadFile(DATA_DIR + "/2022.06.17/Minute/", DATA_DIR + "/sym")
Ticks2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Ticks/", DATA_DIR + "/sym")
Orders2 = kdb::loadFile(DATA_DIR + "/2022.06.17/Orders/", DATA_DIR + "/sym")
```

## 3. DolphinDB Reference for kdb+ Users

This section explains the mapping between the data types, functions, keywords and other elements of kdb+ and the DolphinDB equivalents. For more information, see [kdb+ and q documentation](https://code.kx.com/q/ref/) and DolphinDB user manual.



### 3.1 Datatypes

#### 3.1.1 Basic Datatypes

| **kdb+ Datatype** | **DolphinDB Data Type** | **DolphinDB Examples**                                       | **Size** | **Range**        |
| :---------------- | :---------------------- | :----------------------------------------------------------- | :------- | :--------------- |
|                   | VOID                    | NULL                                                         |          |                  |
| boolean           | BOOL                    | 1b, 0b, true, false                                          | 1        | 0~1              |
| byte              |                         |                                                              |          |                  |
| char              | CHAR                    | 'a', 97c                                                     | 1        | -2 7 +1~2 7 -1   |
| short             | SHORT                   | 122h                                                         | 2        | -2 15 +1~2 15 -1 |
| int               | INT                     | 21                                                           | 4        | -2 31 +1~2 31 -1 |
| long              | LONG                    | 22, 22l                                                      | 8        | -2 63 +1~2 63 -1 |
| real              | FLOAT                   | 2.1f                                                         | 4        | Sig. Fig. 06-09  |
| float             | DOUBLE                  | 2.1                                                          | 8        | Sig. Fig. 15-17  |
| date              | DATE                    | 2013.06.13                                                   | 4        |                  |
| month             | MONTH                   | 2012.06M                                                     | 4        |                  |
| time              | TIME                    | 13:30:10.008                                                 | 4        |                  |
| minute            | MINUTE                  | 13:30m                                                       | 4        |                  |
| second            | SECOND                  | 13:30:10                                                     | 4        |                  |
| (datetime)        | DATETIME                | 2012.06.13 13:30:10 or 2012.06.13T13:30:10                   | 4        |                  |
| (datetime)        | TIMESTAMP               | 2012.06.13 13:30:10.008 or 2012.06.13T13:30:10.008           | 8        |                  |
|                   | DATEHOUR                | 2012.06.13T13                                                | 4        |                  |
| timespan          | NANOTIME                | 13:30:10.008007006                                           | 8        |                  |
| timestamp         | NANOTIMESTAMP           | 2012.06.13 13:30:10.008007006 or 2012.06.13T13:30:10.008007006 | 8        |                  |
| symbol            | SYMBOL                  |                                                              | 4        |                  |
| symbol            | STRING                  | "Hello" or 'Hello' or `Hello                                 |          |                  |
| guid              | UUID                    | 5d212a78-cc48-e3b1-4235-b4d91473ee87                         | 16       |                  |

**Note:**

- There is no DolphinDB equivalent to the *byte* type of kdb+.
- The *char* type of kdb+ is enclosed in double quotes whereas its DolphinDB equivalent, *CHAR*, is enclosed in single quotes. For example, `"c"` is treated as a string in DolphinDB.
- The type indicator of *long* is “j“ in kdb+ whereas the type indicator of *LONG* in DolphinDB *is “l“*. If a *long* value has the trailing type indicator “j“, for example, `42j`, it will not be recognized by DolphinDB.  
- In kdb+, the type indicator of *month* is "m". In DolphinDB, the type indicator of *MONTH* is "M" and the type indicator of *MINUTE* is "m". Therefore, format such as `2006.07m` is not accepted in DolphinDB.
- kdb+ uses an 8-byte *datetime* type whereas DolphinDB uses a 4-byte *DATETIME* type.
- The *SYMBOL* type of DolphinDB is a special *STRING* type and is equivalent to [enumerated types](http://en.wikipedia.org/wiki/Enumerated_type) in C++, java and C#. *SYMBOL* stores strings as integers, which greatly improves query performance and storage efficiency. For more information, see DolphinDB user manual.

##### NULL and INF

Unlike kdb+, DolphinDB does not provide special lexical forms representing positive/negative infinity in various data types. To represent the lexical form for NULL values of integral, floating or temporal data type, you can use `00<data type symbol>` . When a data type overflow occurs, DolphinDB treats the data as NULL value of this data type. When an assignment statement or expression uses a function without a return value, you will also get a NULL of VOID type. 

In DolphinDB, you can use the `isVoid` function to check if a NULL value is VOID type. Use `isNull` or `isValid` to check the existence of NULL values of any type. If you are not concerned with the data type of a NULL value, it is recommended to use `isNull` or `isValid`.

For more information about the initialization, calculation, and usage in vectorized functions, aggregate functions and higher-order functions, see DolphinDB user manual. 

#### 3.1.2 Other Datatypes 

| **kdb+ Datatypes** | **DolphinDB Data Types / Data Forms** | **DolphinDB Examples** |
| :----------------- | :------------------------------------ | :--------------------- |
| list               | ANY, matrix, dictionary               | (1,2,3)                |
| enums              |                                       |                        |
| anymap             | ANY DICTIONARY, dictionary            | {a:1,b:2}              |
| dictionary         | ANY DICTIONARY, dictionary            | {a:1,b:2}              |
| table              | in-memory table                       |                        |

**Note:**

- ANY DICTIONARY is the data type in DolphinDB for JSON.
- In DolphinDB, a dictionary key must be a scalar while a value can be of any data type in any data forms. Nested dictionaries are supported. When a kdb+ dictinary is printed or iterated through, the system preservers the order in which keys are inserted. By contrast, whether a DolpinDB dictionary is ordered is determined by the *ordered* parameter during creation. When *ordered* is set to true, the created dictionary tracks the insertion order of the key-value pairs. By default, *ordered* is set to false.

-  In kdb+, a matrix is a list of lists all having the same count and is stored in row-major-order. In DolphinDB, MATRIX is an independent data form of which data is stored in column-major-order. To import a kdb+ matrix into DolphinDB, it must be transposed.
- DolphinDB provides various data forms including scalar, vector, pair, matrix, set, dictionary and table with optimization for specific scenarios. For more information, see DolphinDB user manual. 

#### 3.1.3 Data Type Checking Functions

The DolphinDB built-in function `typestr` returns a string indicating the data type of an object and `type` returns an integer indicating the data type ID of the object.

### 3.2 Keywords by Category

#### 3.2.1 control 

| **kdb+** | **DolphinDB** |
| :------- | :------------ |
| do       | do-while      |
| exit     |               |
| if       | if-else       |
| while    | do-while      |

#### 3.2.2 env

| **kdb+** | **DolphinDB** |
| :------- | :------------ |
| getenv   | `getEnv`      |
| gtime    | `gmtime`      |
| ltime    | `localtime`   |
| setenv   |               |

#### 3.2.3 interpret

| **kdb+** | **DolphinDB**                                                |
| :------- | :----------------------------------------------------------- |
| eval     | `eval`                                                       |
| parse    | `parseExpr`                                                  |
| reval    |                                                              |
| show     | `print`                                                      |
| system   | `shell`                                                      |
| value    | `values` - Returns values of a dictionary or a table<br/>`print` - Prints variable contents<br/>`parseExpr` - Converts string to metacode for execution<br/>`expr` - Converts list to metacode for execution |

 

#### 3.2.4 join

| **Table Joiners** | **kdb+**                 | **DolphinDB** |
| :---------------- | :----------------------- | :------------ |
| asof join         | aj, aj0, ajf, ajf0, asof | aj            |
| equi join         | ej                       | ej, sej       |
| inner join        | ij, ijf                  | inner join    |
| left join         | lj, ljf                  | lj, lsj       |
| plus join         | pj                       |               |
| union join        | uj, ujf                  |               |
| window join       | wj, wj1                  | wj, pwj       |

#### 3.2.5 list

| **kdb+** | **DolphinDB**                                                |
| :------- | :----------------------------------------------------------- |
| count    | `count` - number of non-NULL elements`size` - number of all elements |
| mcount   | `mcount`                                                     |
| cross    | `join:C`, `cross(join, X, Y)`                                |
| cut      | `cut`                                                        |
| enlist   | `[]`, array, bigArray                                        |
| except   |                                                              |
| fills    | `ffill`, `ffill!`                                            |
| first    | `first`                                                      |
| last     | `last`                                                       |
| flip     | `flip`, `transpose`                                          |
| group    | `groups`                                                     |
| in       | `in`                                                         |
| inter    | `intersection(set(X), set(Y))`                               |
| next     | `next`                                                       |
| prev     | `prev`                                                       |
| xprev    | `move`                                                       |
| raze     | `flat` - Converts a matrix or a list of vectors into a one dimensional vector |
| reverse  | `reverse`                                                    |
| rotate   |                                                              |
| sublist  | head, tail, subarray, subtuple                               |
| sv       | `concat` - Forms new string by concatenating strings/char:   |
| til      | `til`                                                        |
| union    | `union(set(X), set(Y))` or `distinct(join(X, Y))`            |
| vs       | `split` - Splits a string                                    |
| where    |                                                              |

#### 3.2.6 logic

| **kdb+** | **DolphinDB** |
| :------- | :------------ |
| all      | all           |
| and      | and           |
| any      | any           |
| not      | not           |
| or       | or            |

#### 3.2.7 math

| **kdb+**   | **DolphinDB** |
| :--------- | :------------ |
| abs        | abs           |
| cos        | cos           |
| acos       | acos          |
| sin        | sin           |
| asin       | asin          |
| tan        | tan           |
| atan       | atan          |
| avg        | avg, mean     |
| avgs       | cumavg        |
| ceiling    | ceil          |
| cor        | corr          |
| cov        |               |
| scov       | covar         |
| deltas     | deltas        |
| dev        | stdp          |
| mdev       | mstdp         |
| sdev       | std           |
| div        | div           |
| ema        | ema           |
| exp        | exp           |
| xexp       | pow           |
| floor      | floor         |
| inv        | inverse       |
| log        | log           |
| xlog       |               |
| lsq        |               |
| mavg       | mavg          |
| wavg       | wavg          |
| max        | max           |
| maxs       | cummax        |
| mmax       | mmax          |
| med        | med           |
| min        | min           |
| mins       | cummin        |
| mmin       | mmin          |
| mmu        | dot           |
| mod        | mod           |
| sum        | sum           |
| sums       | cumsum        |
| msum       | msum          |
| wsum       | wsum          |
| neg        | neg           |
| prd        | prod          |
| prds       | cumprod       |
| rand       | rand          |
| ratios     | ratios        |
| reciprocal | reciprocal    |
| signum     | signum        |
| sqrt       | sqrt          |
| within     | between, in   |
| var        | varp          |
| svar       | var           |

**Note:**

- Unlike kdb+, the TA-lib functions in DolphinDB ignore the NULL values at the beginning of the object in calculation and keep them in the output. The calculation with the sliding windows starts from the first non-NULL value.

  For count-based windows, the calculation will be performed only when elements fill the window completely. This means that the result of the first (window - 1) elements will be NULL.

- In DolphinDB, the windowing logic of the moving (`m-`) functions is to return NULL for the first (*window*-1) windows by default. If you want the same result as the kdb+ equivalents, specify the parameter *minPeriod* as 1.

- For the DolphinDB function `ratios`, if the input is a vector, the first element of the result is always NULL.

#### 3.2.8 meta

| **kdb+**    | **DolphinDB**             |
| :---------- | :------------------------ |
| attr        |                           |
| null        | isNull, isNothing, isVoid |
| tables      | getTables                 |
| type        | type, typestr, form       |
| view, views |                           |

#### 3.2.9 query

| **kdb+** | **DolphinDB**                                                |
| :------- | :----------------------------------------------------------- |
| delete   | delete, sqlDelete                                            |
| exec     | exec                                                         |
| fby      | contextby                                                    |
| select   | select                                                       |
| update   | Update records: update, sqlUpdate Append records: insert into Append columns: alter, addColumn |

#### 3.2.10 sort

| **kdb+**  | **DolphinDB** |
| :-------- | :------------ |
| asc       | sort, sort!   |
| iasc      | isort, isort! |
| xasc      | sortBy!       |
| bin, binr | binsrch       |
| desc      | sort, sort!   |
| idesc     | isort, isort! |
| xdesc     | sortBy!       |
| differ    | valueChanged  |
| distinct  | distinct      |
| rank      | rank          |
| xbar      | bar           |
| xrank     | bucket        |

#### 3.2.11 table

| **kdb+**               | **DolphinDB**                            |
| :--------------------- | :--------------------------------------- |
| cols                   | columnNames                              |
| xcol                   | rename!                                  |
| xcols                  | reorderColumns!                          |
| csv                    | CSV delimiter: `,`                       |
| fkeys, key, keys, xkey |                                          |
| insert                 | insert into, tableInsert, append!, push! |
| meta                   | schema                                   |
| ungroup, xgroup        |                                          |
| upsert                 | insert into, tableInsert, append!, push! |
| xasc                   | sortBy!                                  |
| xdesc                  | sortBy!                                  |

#### 3.2.12 text

| **kdb+** | **DolphinDB** |
| :------- | :------------ |
| like     | like, ilike   |
| lower    | lower         |
| upper    | upper         |
| trim     | trim          |
| ltrim    | ltrim         |
| rtrim    | rtrim         |
| md5      | md5           |
| ss       | regexFind     |
| ssr      | regexReplace  |
| string   | string        |

#### 3.2.13 User-Defined Functions

| **kdb+**                                                     | **DolphinDB**                                                |
| :----------------------------------------------------------- | :----------------------------------------------------------- |
| - An example of a signed lambda: `f:{[x;y](x*x)+(y*y)+2*x*y}`<br/>- An example of an unsigned lambda: `{(x*x)+(y*y)+2*x*y}[20;4]` | - An example of a named function: `def func(x, y) { return (x*x)+(y*y)+2*x*y; }`<br/>- An example of an anonymous function: `def (x, y) { return (x*x)+(y*y)+2*x*y; }`<br/>- Examples of lambda expressions (a function definition with only one statement): <br/>-- `def func(x,y)：(x*x)+(y*y)+2*x*y;`<br/>-- `def(x,y)：(x*x)+(y*y)+2*x*y;`<br/>-- `def(x,y)-> (x*x)+(y*y)+2*x*y;``x->x*x` |

**Note:**

- In kdb+, function notation is also known as the *lambda notation* and the defined functions as *lambdas*. The term *lambda* is used to denote any function defined using the lambda notation. In DolphinDB, “lambda expression“ only refers to a function definition with one statement.
- In kdb+, functions with 3 or fewer arguments may omit the signature and instead use default argument names `x`, `y` and `z` to mean the first, second, and third arguments. In DolphinDB, functions must have an explicit list of parameters.
- DolphinDB supports specifying default parameter values. The parameter with a default value is not mutable, and the default value must be a constant. Qualify a parameter by the “mutable“ keyword if it can be modified within function body.

```
// default argument
def func(x=1): x+1;

// mutable argument
def i2t(mutable tb) { return tb.replaceColumn!(`time, time(tb.time/10); }
```

- DolphinDB user-defined functions supports JIT compilation for performance optimization.
- In DolphinDB, user-defined functions can call built-in functions in various forms: 
  - standard function call format: <func>(parameters)
  - object-method call format: x.<func>(parameters) where x is the first parameter. 
  - if the user-defined function has only one or two parameters, we can also use the infix notation.

```
def f(x, y): x+y+1;
p = 2;
q = 3;

f(p, q);   // standard notation

p.f(q);    // postfix notation

p f q;     // infix operator
```

### 3.3 Overloaded Glyphs and Operators

Like kdb+, there are two types of operators in DolphinDB: unary (performs an action with a single operand) and binary (performs an action with two operands). DolphinDB supports many types of basic operators, including arithmetic operators, Boolean operators, relational operators, membership operators, etc., as well as a variety of operational data types, including scalars, vectors, sets, matrices, dictionaries, and tables.

**Evaluation Order:** While kdb+ expressions are evaluated right-to-left with no rules for operator precedence, DolphinDB adopts the traditional notion of operator precedence adopted by most programming languages, and operators with the same precedence are evaluated from left to right.

#### 3.3.1 `.` dot

| **kdb+ Semantics** | **DolphinDB** |
| :----------------- | :------------ |
| Apply              | `call()`      |
| Index              | `[]`          |
| Trap               | try-catch     |
| Amend              |               |

#### 3.3.2 `@` at

| **kdb+ Semantics** | **DolphinDB** |
| :----------------- | :------------ |
| Apply At           | `call()`      |
| Index At           | `[]`          |
| Trap At            | try-catch     |
| Amend At           |               |

#### 3.3.3 `$` dollar

| **kdb+ Semantics** | **DolphinDB**                                                |
| :----------------- | :----------------------------------------------------------- |
| Cast               | `$`, `cast()`                                                |
| Tok                | Data type conversion functions can interpret a string directly |
| Enumerate          |                                                              |
| Pad                | `lpad()`, `rpad()`                                           |
| mmu                | `**`                                                         |

#### 3.3.4 `!` bang

| **kdb+ Semantics**                                | **DolphinDB**           |
| :------------------------------------------------ | :---------------------- |
| Dict                                              | `dict()`                |
| Enkey, Unkey, Enumeration, Flip Splayed, internal |                         |
| Display                                           | `print()`               |
| Update                                            | `update()`, `update!()` |
| Delete                                            | `erase!()`              |

#### 3.3.5 `?` query

| **kdb+ Semantics** | **DolphinDB**    |
| :----------------- | :--------------- |
| Find               | `in()`, `find()` |
| Roll               | `rand()`         |
| Deal, Enum Extend  |                  |
| Select             | `select`         |
| Exec, Simple Exec  | `exec`           |
| Vector Conditional | `iif()`          |

#### 3.3.6 `##` hash

| **kdb+ Semantics** | **DolphinDB** |
| :----------------- | :------------ |
| Take               | `take()`      |
| Set Attribute      |               |

#### 3.3.7 Operators

| **kdb+ Operator** | **kdb+ Semantics**                         | **DolphinDB**              |
| :---------------- | :----------------------------------------- | :------------------------- |
| `+`               | Add                                        | `+`                        |
| `-`               | Substract                                  | `-`                        |
| `*`               | Multiply                                   | `*`                        |
| `%`               | Divide                                     | `\`                        |
| `=`               | Equals                                     | `==`                       |
| `<>`              | Not Equals                                 | `!=`                       |
| `~`               | Match                                      |                            |
| `<`               | Less Than                                  | `<`                        |
| `<=`              | Up To                                      | `<=`                       |
| `>=`              | At Least                                   | `>=`                       |
| `>`               | Greater Than                               | `>`                        |
| `                 | `                                          | Greater                    |
| `                 | `                                          | OR                         |
| `&`               | Lesser                                     | `min()`                    |
| `&`               | AND                                        | `&`                        |
| `_`               | Cut                                        | `cut()`                    |
| `_`               | Drop                                       | `drop()`                   |
| `:`               | Assign                                     | `=`                        |
| `^`               | Fill                                       | `ffill()`, `ffill!()`      |
| `^`               | Coalesce                                   | `append!()`                |
| `,`               | Join                                       | `<-`                       |
| `'`               | Compose                                    |                            |
| `0: 1: 2:`        | File Text, File Binary, Dynamic Load       | `loadText()`, `saveText()` |
| `0 ±1 ±2 ±n`      | write to console, stdout, stderr, handle n | `print()`                  |

### 3.4 Iterators

The iterators (once known as *adverbs* in kdb+) are built-in higher-order functions in DolphinDB, which can extend or enhance a function or an operator: they take a function and some objects as input. In general, the input data is dissembled into multiple pieces (which may or may not overlap) in a preset way at first; then the individual pieces of data are applied to the given function to produce results one at a time; finally all individual results are assembled into one object to return. 

In both kdb+ and DolphinDB, the input data for a higher order function can be vectors, matrices, tables, scalars and dictionaries. In DolphinDB, a vector is dissembled into scalars, a matrix into columns (vectors), and a table into rows (represented by dictionaries). In the assembly phase, the results of scalar type are merged to form a vector, vectors to a matrix, and dictionaries to a table. A higher-order function iterates over a vector by elements, a matrix by columns, and a table by rows.

#### 3.4.1 `'` quote

| **kdb+ Semantics**   | **DolphinDB**       |
| :------------------- | :------------------ |
| Each, each           | `each()` or `:E`    |
| Case                 |                     |
| Each Parallel, peach | `peach()`           |
| Each Prior, prior    | `eachPre()` or `:P` |

#### 3.4.2 Other Iterators

| **kdb+ Glyphs** | **kdb+ Semantics** | **DolphinDB**          |
| :-------------- | :----------------- | :--------------------- |
| `/:`            | Each Right         | `eachRight()` or `:R`  |
| `\:`            | Each Left          | `eachLeft()` or `:L`   |
| `/`             | Over, over         | `reduce()` or `:T`     |
| `\`             | Scan, scan         | `accumulate()` or `:A` |

### 3.5 Evaluation Control

| **kdb+**                                         | **kdb+ Semantics**      | **DolphinDB**                                                |
| :----------------------------------------------- | :---------------------- | :----------------------------------------------------------- |
| `.[f;x;e]`                                       | Trap                    | try-catch                                                    |
| `@[f;x;e]`                                       | Trap-At                 | try-catch                                                    |
| `:`                                              | Return                  | return                                                       |
| `'`                                              | Signal                  | throw                                                        |
| do                                               |                         | do-while                                                     |
| exit                                             |                         | quit                                                         |
| while                                            |                         | do-while                                                     |
| if                                               |                         | if-else                                                      |
| `$[x;y;z]`                                       | Cond                    | if-else                                                      |
| `x:y`                                            | Assign                  | `<variable>=<object>`                                        |
| `x[i]:y`                                         | Indexed assign          | `<variable>[index]=<object>`                                 |
| `x op:y`, `op:[x;y]` or `x[i]op:y`, `op:[x i;y]` | Assign through operator | The  following assignments operators are supported:`+=`, `-=`. `*=`, `/=`, `\=` |
| `\t`                                             | Timer                   | timer                                                        |

**Note:**

- DolphinDB supports multiple variable assignment, which allows us to assign multiple variables at the same time in one single line of code.
- DolphinDB uses “&” to indicate assignment by reference. Assignment by reference does not make a new copy of the original value, but points to the original value to avoid unnecessary object copying. When swapping two variables, assignment by reference is more efficient than assignment by value.

```
n=20000000;
x=rand(200000.0, n);
y=rand(200000.0, n);

timer x, y = y, x;        // Time elapsed: 1240.119 ms
timer {&t=x;&x=y;&y=t;}      // Time elapsed: 0.004 ms
```

- In DolphinDB, you can manually release variables or functions from memory by using the `undef` command or the expression `<variable>=NULL`. For more information, see DolphinDB User Manual.