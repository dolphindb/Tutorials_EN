# DolphinDB Single Node Deployment

To run DolphinDB on a single node, just download the DolphinDB package and unzip.  

#### 1. Download DolphinDB

Download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

#### 2. Update License File 

If the user has obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```

#### 3. Run DolphinDB Server

Go to folder /DolphinDB/server/, and run dolphindb executable. 

Linux: execute the following command:
```
./dolphindb
```
Windows: execute dolphindb.exe

The default port number of the system is 8848. To change it (to 8900), use the following command line:

Linux:
```
./dolphindb -localhost:8900:local8900
```

Windows:
```
dolphindb.exe -localhost:8900:local8900
```

The license file specifies the maximum amount of memory that DolphinDB can use. Users can reduce the limit by specifying the configuration parameter -maxMem when starting DolphinDB. 

Linux:
```
./dolphindb -localHost:8900:local8900 -maxMem 32
```
Windows:
```
dolphindb.exe -localHost:8900:local8900 -maxMem 32
```

#### 4. Connect to DolphinDB Server From Web

Go to your browser (currently supporting Chrome and Firefox) and enter localhost:8848 in the address bar to open DolphinDB notebook. If you have started DolphinDB server with another port number, change 8848 to the port number you have used.


#### 5. Run DolphinDB Script From Web

Run the following DolphinDB script in the editor window of DolphinDB notebook. The figure below shows the output.

```
table(1..5 as id, 6..10 as v)
```
![](images/single_web.JPG)


#### 6. Reference

For details about more configuration parameters, please refer to DolphinDB [help](http://dolphindb.com/help/).

