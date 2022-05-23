# DolphinDB Standalone Deployment

- [DolphinDB Standalone Deployment](#dolphindb-standalone-deployment)
  - [1. Update License File](#1-update-license-file)
  - [2. Run DolphinDB Server](#2-run-dolphindb-server)
  - [3. Connect to DolphinDB Server in DolphinDB GUI](#3-connect-to-dolphindb-server-in-dolphindb-gui)
    - [3.1 Download DolphinDB GUI](#31-download-dolphindb-gui)
    - [3.2 Start GUI](#32-start-gui)
    - [3.3 After Starting GUI](#33-after-starting-gui)
  - [4. Run DolphinDB Script in GUI](#4-run-dolphindb-script-in-gui)
  - [5. Change Configuration](#5-change-configuration)


Download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

> Please note that the directory name cannot contain any space characters, otherwise it will fail to start the data node. For example, please do not extract it to the *Program Files* folder on Windows.

## 1. Update License File 

If you have obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```

Otherwise, you can continue to use the community version of DolphinDB, which allows up to 8GB of memory use for 20 years.


## 2. Run DolphinDB Server

Go to folder /DolphinDB/server/ and run dolphindb executable. 

- Linux:

First, modify the file permissions:
```sh
chmod +x dolphindb
```

Linux console mode: 
```
./dolphindb
```
Linux background mode: 
```
nohup ./dolphindb -console 0 &
```

In Linux, we recommend starting in the background mode with Linux command **nohup** (header) and **&** (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, please set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

In console mode, you can execute DolphinDB code from the command line. Otherwise, you can execute scripts via a user interface such as GUI or VS Code Extension.

- Windows: 

Execute dolphindb.exe

The default port number of the system is 8848. To change it (e.g., to 8900), use the following command line:

Linux:
```
./dolphindb -localSite localhost:8900:local8900
```
Windows:
```
dolphindb.exe -localSite localhost:8900:local8900
```

The license file specifies the maximum amount of memory that DolphinDB can use. Users can lower the limit by specifying the configuration parameter *maxMemSize* (in units of GB) when starting DolphinDB. 

Linux:

```
./dolphindb -localSite localhost:8900:local8900 -maxMemSize 32
```

Windows:

```
dolphindb.exe -localSite localhost:8900:local8900 -maxMemSize 32
```

## 3. Connect to DolphinDB Server in DolphinDB GUI

### 3.1 Download DolphinDB GUI

You can download GUI [here](https://www.dolphindb.com/downloads/DolphinDB_GUI_V1.30.15.zip) and unzip the package to a directory. For example, unzip it to /DolphinDB_GUI. 64-bit Java Runtime Environment (JRE) 8 or above is required to run the GUI. You can download JRE 8 at https://www.java.com/en/download. 

### 3.2 Start GUI 

In Linux,  execute the following command to start GUI:

```sh
sh gui.sh
```
In Windows, double click gui.bat to start GUI. 

If DolphinDB GUI cannot start normally, most likely it's because of one of the following 2 reasons:

- Java not installed. 
- Java not added to system path. Check *Path* environment variable
- Unsupported Java version. Note that only 64-bit version is supported. Use the command `java -version` to check the version.

### 3.3 After Starting GUI

Follow the prompts to select a folder as the workspace. 

Click "Server" in the menu bar to add a server or edit servers:

![Sever](images/single_GUI_server.png)

![AddSever](images/single_GUI_addserver.PNG)

Use the drop-down box at the right side of the toolbar to select the DolphinDB server where the script is to be executed:

![SwitchSever](images/single_GUI_tool.png)


## 4. Run DolphinDB Script in GUI

In the "Project Explorer" panel on the left side of the DolphinDB GUI, right click "workspace" and select "New Project" to create a new project:

![New Project](images/single_GUI_newproject.PNG)

Click on the small dot to the left of the newly created project to expand folders, then right click on the folder "scripts", choose "New File", enter the new file name demo.txt. 

Now we are ready to write DolphinDB script. Enter the following script in the editor panel:

```txt
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
Click the ![execute](images/execute.JPG) button in the toolbar to execute the script. The following figure shows the result of the operation:
![result](images/single_GUI.PNG)

By default, database files are stored under the directory of /server/local8848. To change the directory, please specify the configuration parameter 'volumes'. 

> Note:
> 1. Starting from version 0.98, distributed databases are supported in DolphinDB standalone server.
> 2. All sessions remain open in GUI until terminated by users. 
> 3. For deployment on Linux, mounting NAS partitions as volumes via LAN or WAN is not recommended. If a user has to do that, the volumes mounted in NFS protocol can only be read or written by a DolphinDB process started by ROOT instead of common or SUDO users.


## 5. Change Configuration 

There are 2 ways to change single-node mode configuration parameters:

- update the configuration file dolphindb.cfg. 

- Specify configuration parameters in the command line when starting the node. For example, change the port number to be 8900 and the maximum memory to be 8 GB:

Linux:

```sh
./dolphindb -localSite localhost:8900:local8900 -maxMemSize 8
```

Windows:

```sh
dolphindb.exe -localSite localhost:8900:local8900 -maxMemSize 8
```

For more configuration parameters, please see [Configuration](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/index.html).

<!--

## 6. Update DolphinDB Server

1. Close the server.

2. Backup the metadata of the old version. The default directory to save the metadata for a standalone mode is:

   ```sh
   /DolphinDB/server/local8900/dfsMeta/
   ```
   ```sh
   /DolphinDB/server/local8900/storage/CHUNK_METADATA/
   ```

   You can execute the following command on Linux to back up the metadata:

   ```sh
   mkdir backup
   cp -r local8900/dfsMeta/ backup/dfsMeta
   cp -r local8900/storage/CHUNK_METADATA/ backup/CHUNK_METADATA
   ```
   
>  If the backup files are not in the above default directories, please check the directories specified by the configuration parameters dfsMetaDir and chunkMetaDir. If the configuration parameters are not modified but the configuration parameter volumes is specified, then you can find the CHUNK_METADATA under the directory specified by volumes.

3. Download a new version of server package from [DolphinDB website](https://dolphindb.com/alone/alone.php?id=75). You can also download a server using the following Linux command:

   ```sh
   wget https://www.dolphindb.cn/downloads/DolphinDB_Linux64_V1.30.6.zip
   ```

>  Note

4. Unzip the package. Execute the following Linux command to unzip the 1.30.6 package to the directory v1.30.6:

   ```sh
   unzip DolphinDB_Linux64_V1.30.6.zip -d v1.30.6
   ```

5. Replace the files in the original folder except

>  Note: Please do not overwrite the existing server folder. If you have customized the parameters in the file *dolphindb.cfg*,  added scripts to the init file *dolphindb.dos*, or updated the license *dolphindb.lic*, make sure not to overwrite those files. Otherwise, you will lose your changes.

1. Restart the server and GUI. Execute the following command to check the version information:

   ```sh
   version()
   ```



For more information, please see [DolphinDB help](https://www.dolphindb.com/help/index.html).

-->
