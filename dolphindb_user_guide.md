# DolphinDB User Guide

- [DolphinDB User Guide](#dolphindb-user-guide)
  - [Install DolphinDB](#install-dolphindb)
    - [Download from](#download-from)
    - [DolphinDB Community Trial](#dolphindb-community-trial)
    - [DolphinDB GUI (recommended)](#dolphindb-gui-recommended)
    - [Python/Java/C# API](#pythonjavac-api)
  - [Configuration](#configuration)
    - [Single Node](#single-node)
    - [Single-server Cluster](#single-server-cluster)
    - [Multi-server Cluster](#multi-server-cluster)
  - [Use DolphinDB](#use-dolphindb)
  - [User Access Control](#user-access-control)
  - [Possible Problems](#possible-problems)

DolphinDB User Guide includes dolphindb server package, DolphinDB GUI, web-based cluster manager, Java/Python/C# API and various plugins.

User manual: http://dolphindb.com/help/index.html 

Tutorials: https://github.com/dolphindb/Tutorials_EN 

Stack Overflow: https://stackoverflow.com/questions/tagged/dolphindb 

## Install DolphinDB

### Download from
http://www.dolphindb.com/downloads.html

### DolphinDB Community Trial

Unzip DolphinDB package. It has DolphinDB executable, license file, and web-based cluster manager, etc. No need to install after unzipping. To request Enterprise Trial, click "Request" to apply for an enterprise license. 

### DolphinDB GUI (recommended)

DolphinDB GUI supports syntax colorizing, autoprompt, data visualization, data browse, etc. DolphinDB GUI requires 64-bit Java Runtime Environment (JRE) 8 or more recent versions.

After unzipping DolphinDB GUI, to start GUI:
* Windows: double click *gui.bat*
* Linux: sh gui.sh

### Python/Java/C# API
Please check [User Manual](https://dolphindb.com/help/ProgrammingAPIs/index.html) for how to install and use Python/Java/C# API. 

## Configuration

### Single Node
To use DolphinDB on a single node, please check [DolphinDB Standalone Deployment](standalone_deployment.md).  

### Single-server Cluster
To configure a cluster on a physical server, please check [DolphinDB Single-Server Cluster Deployment](single_machine_cluster_deploy.md). 

### Multi-server Cluster
To configure a cluster on multiple physical servers, please check [DolphinDB Multi-Machine Cluster Deployment](multi_machine_cluster_deployment.md).

## Use DolphinDB

1. On the web-based cluster manager, we can configure the cluster, start or close data nodes and compute nodes, , monitor performance of the nodes, check the partition schemes of distributed databases, and browse data. 

2. For how to use DolphinDB GUI, please check [DolphinDB GUI Help](http://www.dolphindb.com/gui_help/).

3. Regarding how to create distributed databases in DolphinDB, please check [DolphinDB Partitioned Database Tutorial](database.md).

4. Regarding how to use the DolphinDB streaming engines for real-time data processing and analyzing, see [Stream for DolphinDB](streaming_tutorial.md) and [Time-Series Stream Engine](stream_aggregator.md).

## User Access Control
Regarding the user access control functionalities in DolphinDB, please check [DolphinDB Database User Access Control and Security](ACL_and_Security.md).

## Possible Problems
1. After starting a server, the system immediately exists. The error message in the log file is "The license has expired". 

Cause: license expired

Solution: contact support@dolphindb.com and update the license file. 

2. After starting the nodes on the web-based cluster manager, the nodes are still shown as stopped. 

Cause: need to refresh nodes status. 

Solution: click on the "refresh" button. If the log file has error message  "Failed to bind the socket on XXXX" in the log file where XXXX is the port number of a data node to be started, this could mean that the port number is occupied by another application. If so, just close that application and try again. It could also mean the port is not yet released by the Linux kernel if you just closed the data node with this port number. For this case, just wait around 30 seconds and restart the nodes.

For any problem in using DolphinDB database, please first check the log file for more information. There is a log file on each of the data nodes and on the controller node. The default folder of the log file is the home directory. You can post your questions on www.stackoverflow.com or contact us at support@dolphindb.com. 
