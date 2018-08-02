# DolphinDB Cluster Deployment on Single Server

A DolphinDB cluster consists of 3 types of nodes: data node, agent, and controller. 
  *  Data are stored and queries (and more complex computations) are executed on the data nodes. 
  *  An agent node executes the commands issued by the controller to start or close local data nodes. 
  *  The controller collects heartbeats of agents and data nodes, and monitors the status of each node. It provides the web interface for cluster management.

### 1. Download DolphinDB

Download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

### 2. Update the License File

If the user has obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```
The Enterprise Edition supports more nodes, CPU cores and memory than the community version.
 
### 3. Initial Configuration

To start a cluster, we must configure the controller node and the agent node. The data nodes can be configured either in this initial stage or on the web interface after the cluster is started. 

#### 3.1.  Controller Configuration

Please make sure the number of nodes and the number cores per node do not exceed the limits set in the license file. Otherwise the cluster will not start properly. To check the limits please execute license() in DolphinDB single node mode. 

Go to the **server** subdirectory to create the config, data, and log subdirectories. Users can also specify these subdirectories to other locations they see fit.

```
cd /DolphinDB/server/
mkdir /DolphinDB/server/config
mkdir /DolphinDB/server/data
mkdir /DolphinDB/server/log
```

#### 3.1.1 Configuration File of the Controller
In "config" directory, create the configuration file of the controller (**controller.cfg**). As an example, we can specify the following commonly used parameters in **controller.cfg**. Only **localSite** is mandatory. All other parameters are optional.

```
localSite=localhost:8920:ctl8920
localExecutors=3
maxConnections=128
maxMemSize=16
webWorkerNum=4
workerNum=4
dfsReplicationFactor=1
dfsReplicaReliabilityLevel=0
```


| Parameter Configuration        | Explanation          |
|:------------- |:-------------|
|localSite=10.1.1.7::master|     Host address, port number and alias of the local node.|
|localExecutors=3          |      The number of local executors. The default value is the number of cores of the CPU - 1.   |
|maxConnections=128     |         The maximum number of inward connections.|
|maxMemSize=16          |        The maximum memory (in terms of GB) allocated to DolphinDB. If set to 0, it means no limit on memory usage.|
|webWorkerNum=4              |   The size of the worker pool to process http requests. The default value is 1.|
|workerNum=4        |         The size of the worker pool for regular interactive jobs. The default value is the number of cores of the CPU.       |
|dfsReplicationFactor=1         | The number of replicas for each table partition or file block. The default value is 2.   |
|dfsReplicaReliabilityLevel=0     |  Whether multiple replicas can reside on the same server. 0: Yes; 1: No. The default value is 0.|


##### 3.1.2 Cluster Nodes File

In "config" directory, create the file **cluster.nodes** to store information about agent nodes and data nodes. This file has two columns: **localSite** and **mode**. **localSite** contains the node IP address, port number and node alias, separated by a colon ":". Node aliases are case sensitive and must be unique in a cluster. **mode** specifies the node type. This tutorial uses 1 agent node and 4 data nodes.


```
localSite,mode
localhost:8910:agent,agent
localhost:8921:DFS_NODE1,datanode
localhost:8922:DFS_NODE2,datanode
localhost:8923:DFS_NODE3,datanode
localhost:8924:DFS_NODE4,datanode
```
#### 3.1.3 Data Nodes Configuration File

In "config" directory, create the configuration file for the data nodes (**cluster.cfg**). The configuration parameters in this file apply to each data node in the cluster.

```
maxConnections=128
maxMemSize=32
workerNum=8
localExecutors=7
webWorkerNum=2
```

#### 3.2 Agent Configuration

In "config" directory, create the configuration file of the agent (**agent.cfg**). The following is an example of **agent.cfg**. Of the configuration parameters in **agent.cfg**, only **LocalSite** and **controllerSite** are mandatory. All others are optional.
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=localhost:8910:agent
controllerSite=localhost:8920:ctl8920
```

Parameter **localSite** in **controller.cfg** should have the same value as parameter **controllerSite** of **agent.cfg** for all agents, as agent nodes looks for the controller at the addresses specified by parameter **controllerSite** in **agent.cfg**. If **localSite** in **controller.cfg** is changed (even if just an alias change), **controllerSite** in **agent.cfg** of all agents must be changed accordingly.


#### 3.3. Start DolphinDB Cluster

#### 3.3.1 Start Agent

Run the command line described below in the directory where the DolphinDB executable is located. If you haven't changed the directory of the DolphinDB executable, it is located in "server" directory. The file **agent.log** is located in "log" subdirectory. If the agent fails to start properly, open this log file to find more information about the error.

#### Start in background mode (Linux)
```
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```
In Linux, we recommend starting in the background mode with Linux command **nohup** (header) and **&** (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, we need to set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

"-mode agent" means that the node is started as an agent; "-home" specifies the data and the metadata storage path; "-config" specifies the configuration file path; "-logFile" specifies the log file path.

#### Start in console mode (Linux)

```
./dolphindb -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

#### Windows
```
dolphindb.exe -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

#### 3.3.2 Start Controller

Run the following command line in the directory where the DolphinDB executable is located. If you haven't changed the directory of the DolphinDB executable, it is located in "server" directory. The file **controller.log** is located in the log subdirectory. If the controller fails to start properly, open this log file to find more information about the error.

"-clusterConfig" specifies the cluster node configuration file path; "-nodesFile" specifies the file that has information about cluster nodes, such as node type, IP address, port number, and node alias.

#### Start in background mode (Linux)
```
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

#### Start in console mode (Linux)
```
./dolphindb -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

#### Windows
```
dolphindb.exe -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

#### 3.3.3 How to stop controller or agent nodes

If the node was started in background mode, we need to use the Linux system **kill** command. Assume the Linux system user name is "ec2-user":

```
ps aux | grep dolphindb  | grep -v grep | grep ec2-user|  awk '{print $2}' | xargs kill -TERM
```

If the node was started in console mode (in Linux or Windows), we can enter "quit" in the console to exit.

```
quit
```


#### 3.3.4 Start the web-based cluster manager

After both the controller and the agent node are started, we can start or stop data nodes on DolphinDB cluster management web interface. Enter the following in the address bar of your browser (currently supporting Chrome and Firefox) where 8920 is the port number of the controller. 


```
 localhost:8920
```
![](images/cluster_web.JPG)

#### 3.3.5  DolphinDB access control

Only system administrators have permission to conduct cluster deployment. When using DolphinDB web-based cluster management interface for the first time, you need to log in with the following default administrator account.

```
Administrator Username: admin
Default Password      : 123456
```

Click on the login link.

![](images/login_logo.JPG)

Enter the administrator username and password.

![](images/login.JPG)

After logging in, you can change the password of "admin", create users and other administrators, etc. 

#### 3.3.6 Start data nodes

Select all nodes, click on the "execute" button and confirm. It may take 30 second to 1 minute for all the nodes to successfully start. Click on the "refresh" button to check the status of the nodes. When you see the **State** column is full of green check marks, this mean all the nodes have been successfully started. 

![](images/cluster_web_start_node.JPG)

![](images/cluster_web_started.JPG)

If a node fails to start, please check the log file of the node in "log" directory. For example, if the node alias of the problematic node is DFS_NODE1, then check log/DFS_NODE1.log.

If you see an error message "Failed to bind the socket on XXXX" in the log file where XXXX is the port number of a data node to be started, this could mean that the port number is occupied by another application. If so, just close that application and try again. It could also mean the port is not yet released by the Linux kernel if you just closed the data node with this port number. For this case, just wait around 30 seconds and restart the nodes. 


Alternatively, we can start the data nodes with DolphinDB script on the controller node:
```
startDataNode(["DFS_NODE1", "DFS_NODE2","DFS_NODE3","DFS_NODE4"])
```


### 4. Web-based cluster management

We can change cluster configuration and add/delete data nodes on the web-based cluster manager. 

The bottom left panel shows all the agents, and the main panel displays the controller and the data nodes. Click on the "DFS Explorer" button in the upper left corner to browse the distributed databases stored in the distributed file system.

![](images/cluster_web_started.JPG)

#### 4.1. Controller node configuration

Clicking on the button **Controller Config** will open up a control interface, where **localExectors**, **maxConnections**, **maxMemSize**, **webWorkerNum** and **workerNum** were specified when we created **controller.cfg** in 3.1.1. These configuration parameters can be modified, and will take effect after the controller node is restarted.

![](images/cluster_web_controller_config.JPG)

#### 4.2. Add/delete data nodes

Click on the button **Nodes Setup** to enter the cluster nodes configuration interface. The figure below shows the parameters in **cluster.nodes** that we created in 3.1.2. We can add or delete data nodes here. The new configuration will take effect after the entire cluster is restarted. The steps to restart the cluster include: (1) close all data nodes (2) close the controller, (3) start the controller, and (4) start the data nodes. Deleting a data node may result in loss of data that were saved on the node. 

![](images/cluster_web_nodes_setup.JPG)

If the new data node is on a new physical server, we must configure and start an agent node as in 3.2 on the new physical server, revise **cluster.nodes** with the information about the new agent node and new data node, and restart the controller node. 

#### 4.3. Modify data node configuration

Click on the button **Nodes Config** to configure the data nodes. This figure below displays parameters we specified in **cluster.cfg** in 3.1.3. We can also add other parameters to be configured here. They will take effect after all the data nodes are restarted.

![](images/cluster_web_nodes_config.JPG)


### 5. Reference

For a complete list of the cluster configuration parameters and details, please refer to Chapter 10 of DolphinDB [help](http://dolphindb.com/help/ClusterSetup.html).
