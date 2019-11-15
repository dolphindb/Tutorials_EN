## DolphinDB User Guide

DolphinDB User Guide includes dolphindb server package, DolphinDB GUI, web-based cluster manager, Java/Python/C# API and various plugins.

### Install DolphinDB

#### Download from
http://www.dolphindb.com/downloads.html

#### DolphinDB Community Trial

Unzip DolphinDB package. It has DolphinDB executable, license file, and web-based cluster manager, etc. No need to install after unzipping. To request Enterprise Trial, click "Request" to apply for an enterprise license. 

#### DolphinDB GUI (recommended)

DolphinDB GUI supports syntax colorizing, autoprompt, data visualization, data browse, etc. DolphinDB GUI requires Java 8 or more recent versions.

After unzipping DolphinDB GUI, to start GUI:
* Windows: double click *gui.bat*
* Linux: sh gui.sh

#### Python/Java/C# API
Please check http://dolphindb.com/help/12API.html for how to install and use Python/Java/C# API. 

### Cluster Configuration

#### Single node
To use DolphinDB on a single node, please check
https://github.com/dolphindb/Tutorials_EN/blob/master/standalone_server.md 

#### Single server cluster
To configure a cluster on a physical server, please check
https://github.com/dolphindb/Tutorials_EN/blob/master/single_machine_cluster_deploy.md

#### Multi-server cluster
To configure a cluster on multiple physical servers, please check
https://github.com/dolphindb/Tutorials_EN/blob/master/multi_machine_cluster_deploy.md

### Use DolphinDB

1. On the web-based cluster manager, we can configure the cluster, start or close data nodes, monitor performance of the nodes, check the partition schemes of distributed databases, and browse data. 

2. For how to use DolphinDB GUI, please check 
http://www.dolphindb.com/gui_help/

3. Regarding how to create distributed databases in DolphinDB, please check
https://github.com/dolphindb/Tutorials_EN/blob/master/database.md

### User Access Control
Regarding the user access control functionalities in DolphinDB, please check
https://github.com/dolphindb/Tutorials_CN/blob/master/ACL_and_Security.md

### Possible problems
1. After starting a server, the system immediately exists. The error message in the log file is "The license has been expired". 
Cause: license expired
Solution: contact support@dolphindb.com and update the license file. 

2. After starting the nodes on the web-based cluster manager, the nodes are still shown as stopped. 
Cause: need to refresh nodes status. 
Solution: click on the "refresh" button. If the log file has error message  "Failed to bind the socket on XXXX" in the log file where XXXX is the port number of a data node to be started, this could mean that the port number is occupied by another application. If so, just close that application and try again. It could also mean the port is not yet released by the Linux kernel if you just closed the data node with this port number. For this case, just wait around 30 seconds and restart the nodes.

For any problem in using DolphinDB database, please first check the log file for more information. There is a log file on each of the data nodes and on the controller node. The default folder of the log file is the home directory. You can post your questions on www.stackoverflow.com or contact us at support@dolphindb.com. 

