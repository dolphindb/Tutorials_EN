# DolphinDB ARM Standalone Deployment

- [DolphinDB ARM Standalone Deployment](#dolphindb-arm-standalone-deployment)
	- [1. System Requirements](#1-system-requirements)
	- [2. Download DolphinDB Database](#2-download-dolphindb-database)
	- [3. Update License File](#3-update-license-file)
	- [4. Run DolphinDB Server](#4-run-dolphindb-server)
	- [5. Connect to DolphinDB Server from Web](#5-connect-to-dolphindb-server-from-web)
	- [6. Run DolphinDB Script from Web](#6-run-dolphindb-script-from-web)

## 1. System Requirements

Operating system: Linux (kernel 3.10 or above)

RAM: 2 GB or above

Flash memory: 8 GB or above

Supported ARM CPU: 

- CORTEXA15
- CORTEXA9
- ARMV7  
- ARMV8
- CORTEXA53  
- CORTEXA57  
- CORTEXA72  
- CORTEXA73  
- FALKOR  
- THUNDERX  
- THUNDERX2T99  
- TSV110

The cross compiler used in DolphinDB ARM is arm-linux-gnueabihf4.9 for 32-bit systems and aarch64-linux-gnu_4.9.3 for 64-bit systems. 

## 2. Download DolphinDB Database

Download DolphinDB for ARM from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

## 3. Update License File 

If the user has obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```

## 4. Run DolphinDB Server

Go to folder /DolphinDB/server/ and run the executable file *dolphindb* 

Before running the executable, please change its access permissions:

```
chmod 777 dolphindb
```

Then modify configuration parameters in the file *dolphindb.cfg*:

The default port number is 8848. Set the port number with parameter *localSite* to 8900:

```
localSite=localhost:8900:local8900
```

Specify the maximum amount of memory allocated to DolphinDB with parameter *maxMemSize* (in terms of GB). To set it to 0.8 GB：

```
maxMemSize=0.8 
```

Specify the maximum amount of memory allocated to an array with parameter *regularArrayMemoryLimit* (in terms of MB). It must be the exponential power of 2 with the default value of 2048. To set it to 64 MB:

```
regularArrayMemoryLimit=64
```

It's recommended to set the parameter *maxLogSize* based on your RAM size (in terms of MB). When the log file reaches this size it will be archived. The default value is 1024 MB and the minimum permissible value is 100 MB. To set it to 100MB:

```
maxLogSize=100
```

Run DolphinDB server:

- Linux console mode: 

```
./dolphindb
```

- Linux background mode: 

```
nohup ./dolphindb -console 0 &
```

In Linux, we recommend starting in the background mode with Linux command **nohup** (header) and **&** (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, we need to set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

## 5. Connect to DolphinDB Server from Web

Go to your browser (currently supporting Chrome and Firefox) and enter localhost:8848 in the address bar to open DolphinDB notebook. If you have started DolphinDB server with another port number, change 8848 to the port number you have used. Please note that if there is no execution on the web for 10 minutes, the session will be automatically closed to release resources on the server. We recommend users to work on DolphinDB GUI where all sessions remain open until terminated by users. 

## 6. Run DolphinDB Script from Web

Run the following DolphinDB script in the editor window of DolphinDB notebook. The figure below shows the output. 

```
table(1..5 as id, 6..10 as v)
```
![](images/single_web.JPG)

<!---
## 7. Update DolphinDB Server


-->


For details about more configuration parameters, please refer to DolphinDB [help](http://dolphindb.com/help/).

