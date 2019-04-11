# DolphinDB ARM Single Node Deployment

#### System Requirements

Operating system: Linux (kernel 3.10 or above)

RAM: 2GB or above

Flash memory: 8GB or above

Supported ARM CPU: CORTEXA15, CORTEXA9, ARMV7, ARMV8, CORTEXA53, CORTEXA57, CORTEXA72, CORTEXA73, FALKOR, THUNDERX, THUNDERX2T99, TSV110.

The cross compiler used in DolphinDB ARM is arm-linux-gnueabihf4.9 for 32-bit systems and aarch64-linux-gnu_4.9.3 for 64-bit systems. 

#### 1. Download DolphinDB

Download DolphinDB for ARM from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

#### 2. Update License File 

If the user has obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```

#### 3. Run DolphinDB Server

Go to folder /DolphinDB/server/ and run the executable file dolphindb 

Before running the executable, please change its access permissions  :

```
chmod 777 dolphindb
```

Then we can change configuration parameters in the file dolphindb.cfg:

	The default port number is 8848. We can set the port number with parameter 'localSite'. To set it to 8900:
```
localSite=localhost:8900:local8900
```

    We can specify the maximum amount of memory allocated to DolphinDB with parameter 'maxMemSize' (in terms of GB). To set it to 0.8GB：
```
maxMemSize=0.8 
```
	We can specify the maximum amount of memory allocated to an array with parameter 'regularArrayMemoryLimit' (in terms of MB). It must be the exponential power of 2 with the default value of 512. To set it to 64MB:
```
regularArrayMemoryLimit=64
```

	We recommend setting parameter 'maxLogSize' based on your RAM size (in terms of MB). When the log file reaches this size it will be archived. The default value is 1024MB and the minimum permissible value is 100MB. To set it to 100MB:
```
maxLogSize=100
```
Linux console mode: 
```
./dolphindb
```
Linux background mode: 
```
nohup ./dolphindb -console 0 &
```
In Linux, we recommend starting in the background mode with Linux command **nohup** (header) and **&** (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, we need to set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

#### 4. Connect to DolphinDB Server From Web

Go to your browser (currently supporting Chrome and Firefox) and enter localhost:8848 in the address bar to open DolphinDB notebook. If you have started DolphinDB server with another port number, change 8848 to the port number you have used.


#### 5. Run DolphinDB Script From Web

Run the following DolphinDB script in the editor window of DolphinDB notebook. The figure below shows the output. Please note that if there is no execution on the web for 10 minutes, the session will be automatically closed to release resources on the server. We recommend users to work on DolphinDB GUI where all sessions remain open until terminated by users. 

```
table(1..5 as id, 6..10 as v)
```
![](images/single_web.JPG)


#### 6. Reference

For details about more configuration parameters, please refer to DolphinDB [help](http://dolphindb.com/help/).

