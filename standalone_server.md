# DolphinDB Single Node Deployment

Download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

#### 1. Update License File 

If you have obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```
Otherwise, you can continue to use the community version of DolphinDB, which allows up to 4GB of memory use. 

#### 2. Run DolphinDB Server

Go to folder /DolphinDB/server/, and run dolphindb executable. 

Linux console mode: 
```
./dolphindb
```
Linux background mode: 
```
nohup ./dolphindb -console 0 &
```
In Linux, we recommend starting in the background mode with Linux command **nohup** (header) and **&** (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, we need to set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

Windows: execute dolphindb.exe

The default port number of the system is 8848. To change it (to 8900), use the following command line:

Linux:
```
./dolphindb -localSite localhost:8900:local8900
```
Windows:
```
dolphindb.exe -localSite localhost:8900:local8900
```

The license file specifies the maximum amount of memory that DolphinDB can use. Users can lower the limit by specifying the configuration parameter -maxMemSize when starting DolphinDB. 

Linux:
```
./dolphindb -localSite localhost:8900:local8900 -maxMemSize 32
```
Windows:
```
dolphindb.exe -localSite localhost:8900:local8900 -maxMemSize 32
```

#### 3. Connect to DolphinDB Server from Web

Go to your web browser (currently supporting Chrome and Firefox) and enter localhost:8848 in the address bar to open DolphinDB notebook. If you have started DolphinDB server with another port number, change 8848 to the port number you have used.


#### 4. Run DolphinDB Script from Web

Run the following DolphinDB script in the editor panel of DolphinDB notebook. The figure below shows the output. 

```
n=1000000
date=take(2006.01.01..2006.01.31, n);
x=rand(10.0, n);
t=table(date, x);

login("admin","123456")
db=database("dfs://valuedb", VALUE, 2006.01.01..2006.01.31)
pt = db.createPartitionedTable(t, `pt, `date);
pt.append!(t);

pt=loadTable("dfs://valuedb","pt")
select top 100 * from pt
```
![the result](/../../../tutorials_cn/raw/master/images/single_notebook.jpg)

To use DolphinDB to work with huge volumes of data, we need to use partitioned database in DolphinDB. Regarding partitioned database please refer to [DolphinDB Partitioned Database Tutorial](https://github.com/dolphindb/Tutorials_EN/blob/master/database.md).

Different from traditional databases, DolphinDB integrates database, programming language and distributed computing into one system. Table is one of the many data forms in DolphinDB. To use a table, we need to use function `loadTable` to assign the table to a variable. The variable name may be different from the table name.  

```
tmp=loadTable("dfs://valuedb","pt")
select top 100 * from tmp
```

By default, database files are stored under the directory of 
```
"DolphinDB package"/server/local8848
```
To change the directory we can specify the parameter 'volumes' in dolphindb.cfg.

> Note:
> 1. Starting from version 0.98, DolphinDB single node mode supports DFS databases. 
> 2. Please note that if the session in DolphinDB notebook is idle for 10 minutes, the session will be automatically closed to release resources on the server. We recommend users to work on DolphinDB GUI where all sessions remain open until terminated by users.

## 5. Change configuration 

There are 2 ways to change single node mode configuration parameters:

- update the configuration file dolphindb.cfg. 

- Specify configuration parameters in the command line when starting the node. For example, specify port number to be 8900 and the maximum memory to be 4GB:

Linux:

```sh
./dolphindb -localSite localhost:8900:local8900 -maxMemSize 4
```

Windows:

```sh
dolphindb.exe -localSite localhost:8900:local8900 -maxMemSize 4
```

For more information about DolphinDB configuration parameters please refer to [Cluster Setup](https://www.dolphindb.com/help/ClusterSetup.html)。

#### 6. Reference

For details about more configuration parameters, please refer to DolphinDB [help](http://dolphindb.com/help/).

