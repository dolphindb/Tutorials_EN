# DolphinDB Cluster Deployment on Multiple Servers

A DolphinDB Cluster consists of 3 types of nodes: data node, agent, and controller. 
  *  Data are stored and queries (and more complex computations) are executed on the data nodes. 
  *  An agent node executes the commands issued by the controller to start or close local data nodes. 
  *  The controller collects heartbeats of agents and data nodes, and monitors the status of each node. It provides the web interface for cluster management.

This tutorial uses as an example a DolphinDB cluster with 5 physical servers: **P1**, **P2**, **P3**, **P4** and **P5**.

The corresponding intranet addresses of the 5 physical servers are:

```
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
P4: 10.1.1.7
P5: 10.1.1.9
```

We set up the controller node on **P4**. We set up an agent node and data nodes on each of the other nodes. It should be noted here that each physical server must have an agent node to start to close the local data nodes. Each cluster has one and only one controller.

### 1. Download DolphinDB

On each physical server, download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a directory. For example, extract it to the following directory:

```
/DolphinDB
```

### 2. Update the License File

If the user has obtained the Enterprise Edition license, please use it to replace the following file:

```
/DolphinDB/server/dolphindb.lic
```
The license file of each physical server needs to be updated. The Enterprise Edition supports more nodes, CPU cores and memory than the community version.

### 3. Initial Configuration

To start a cluster, we must configure the controller node and the agent nodes. The data nodes can be configured either in this initial stage or on the web interface after the cluster is started. 

#### 3.1 Controller Configuration

Please make sure the number of nodes and the number cores per node do not exceed the limits set in the license file. Otherwise the cluster will not start properly. To check the limits please execute license() in DolphinDB single node mode. 

Log in server **P4** and go to "server" subdirectory to create the config, data, and log subdirectories. Users can also specify these subdirectories to other locations they see fit.
```
cd /DolphinDB/server/

mkdir /DolphinDB/server/config
mkdir /DolphinDB/server/data
mkdir /DolphinDB/server/log
```
##### 3.1.1 Configuration File of the Controller
In "config" directory, create the configuration file of the controller (controller.cfg). As an example, we can specify the following commonly used parameters in controller.cfg. Only the parameter "localSite" is mandatory. All other parameters are optional.

```
localSite=10.1.1.7:8990:master
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
|localSite=10.1.1.7:8990:master|     Host address, port number and alias of the local node.|
|localExecutors=3          |      The number of local executors. The default value is the number of cores of the CPU - 1.   |
|maxConnections=128     |         The maximum number of inward connections.|
|maxMemSize=16          |        The maximum memory (in terms of GB) allocated to DolphinDB. If set to 0, it means no limit on memory usage.|
|webWorkerNum=4              |   The size of the worker pool to process http requests. The default value is 1.|
|workerNum=4        |         The size of the worker pool for regular interactive jobs. The default value is the number of cores of the CPU.       |
|dfsReplicationFactor=1         | The number of replicas for each table partition or file block. The default value is 2.   |
|dfsReplicaReliabilityLevel=0     |  Whether multiple replicas can reside on the same server. 0: Yes; 1: No. The default value is 0.|


##### 3.1.2 Configure the cluster member parameter file

In "config" directory, create the file cluster.nodes to store information about agent nodes and data nodes. This file has two columns: "localSite" and "mode". The parameter "localSite" contains the node IP address, port number and node alias, separated by a colon ":". Node aliases are case sensitive and must be unique in a cluster. The parameter "mode" specifies the node type. This tutorial uses 4 agent nodes and 4 data nodes on **P1**, **P2**, **P3** and **P5**.

```
localSite,mode
10.1.1.1:8960:P1-agent,agent
10.1.1.1:8961:P1-NODE1,datanode
10.1.1.3:8960,P2-agent,agent
10.1.1.3:8961:P2-NODE1,datanode
10.1.1.5:8960:P3-agent,agent
10.1.1.5:8961:P3-NODE1,datanode
10.1.1.9:8960:P5-agent,agent
10.1.1.9:8961:P5-NODE1,datanode
```

#### 3.1.3 Data Nodes Configuration File

In "config" directory, create the configuration file for the data nodes (cluster.cfg). The configuration parameters in this file apply to each data node in the cluster.

```
maxConnections=128
maxMemSize=32
workerNum=8
localExecutors=7
webWorkerNum=2
```


#### 3.2 Agent Configuration

Log in each of the servers **P1**,**P2**,**P3**,**P5** and go to "server" directory to create the config, data, and log subdirectories. Users can also specify these subdirectories to other locations they see fit.

```
cd /DolphinDB/server/
mkdir /DolphinDB/server/config
mkdir /DolphinDB/server/data
mkdir /DolphinDB/server/log
```

In "config" directory of each server, create the configuration file of the agent (agent.cfg). We give an example of agent.cfg on each of **P1**, **P2**, **P3** and **P5**. Only "LocalSite" and "controllerSite" are mandatory in agent.cfg. All others are optional.

#### P1
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.1:8960:P1-agent
controllerSite=10.1.1.7:8990:master
```

#### P2
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.3:8960:P2-agent
controllerSite=10.1.1.7:8990:master
```

#### P3
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.5:8960:P3-agent
controllerSite=10.1.1.7:8990:master
```

#### P5
```
workerNum=3
localExecutors=2
maxMemSize=4
localSite=10.1.1.9:8960:P5-agent
controllerSite=10.1.1.7:8990:master
```

Parameter "localSite" in controller.cfg should have the same value as parameter "controllerSite" of agent.cfg for all agents, as agent nodes looks for the controller at the address specified by parameter "controllerSite" in agent.cfg. If "localSite" in controller.cfg is changed (even if just an alias change), "controllerSite" in agent.cfg of all agents must be changed accordingly.


#### 3.3 Start DolphinDB Cluster

#### 3.3.1 Start Agent

Log in each of **P1**, **P2**, **P3** and **P5**, and run the command line described below in the directory where the DolphinDB executable is located. If you haven't changed the directory of the DolphinDB executable, it is located in "server" directory. The file agent.log is located in "log" subdirectory. If the agent fails to start properly, open this log file to find more information about the error.

#### Start in background mode (Linux)
```
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```
In Linux, we recommend starting in the background mode with Linux command `nohup` (header) and `&` (tail). Even if the terminal is disconnected, DolphinDB will keep running. "-console" is set to 1 by default. To run in the background mode, we need to set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. 

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

Log in server **P4**. Run the following command line in the directory where the DolphinDB executable is located. If you haven't changed the directory of the DolphinDB executable, it is located in "server" directory. The file controller.log is located in the log subdirectory. If the controller fails to start properly, open this log file to find more information about the error.

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

#### 3.3.3 How to stop agent and controller nodes

If the node was started in background mode, we need to use the Linux system `kill` command. Assume the Linux system user name is "ec2-user":

```
ps aux | grep dolphindb  | grep -v grep | grep ec2-user|  awk '{print $2}' | xargs kill -TERM
```

If the node was started in console mode (in Linux or Windows), we can enter "quit" in the console to exit.

```
quit
```

#### 3.3.4 Start the web-based cluster manager

After both the controller and all the agent nodes are started, we can start or stop data nodes on DolphinDB cluster management web interface. Enter the following in the address bar of your browser (currently supporting Chrome and Firefox) where 8990 is the port number of the controller. 

```
 localhost:8990
```
![](images/multi_web.JPG)

#### 3.3.5 DolphinDB access control

Only system administrators have permission to conduct cluster deployment. When using DolphinDB web-based cluster management interface for the first time, you need to log in with the following default administrator account.

```
Administrator Username: admin
Default Password      : 123456
```

Click on the login link.

![](images/login_logo.JPG)

Enter the administrator username and password.

![](images/login.JPG)


#### 3.3.6 Start data nodes

Select all nodes, click on the "execute" button and confirm. It may take 30 second to 1 minute for all the nodes to successfully start. Click on the "refresh" button to check the status of the nodes. When you see the "State" column is full of green check marks, this mean all the nodes have been successfully started. 

![](images/multi_start_nodes.JPG)

If a node fails to start, please check the log file of the node in "log" directory. For example, if the node alias of the problematic node is P1-NODE1, then check log/P1-NODE1.log.

If you see an error message "Failed to bind the socket on XXXX" in the log file where XXXX is the port number of a data node to be started, this could mean that the port number is occupied by another application. If so, just close that application and try again. It could also mean the port is not yet released by the Linux kernel if you just closed the data node with this port number. For this case, just wait around 30 seconds and restart the nodes. 

Alternatively, we can start the data nodes with DolphinDB script on the controller node:

```
startDataNode(["P1-NODE1", "P2-NODE1","P3-NODE1","P5-NODE1"])
```
### 3.3.7 Common reasons why nodes cannot start

1. **Port is occupied**. If you find in the log file an error message "Failed to bind the socket on XXXX" where XXXX is the port number on the node to be started, it means this port may be occupied by another program. Close the other program or reassign a port number and then restart the node. It may also be that this node has just been closed and the Linux kernel has not released this port number. Just wait about 30 seconds and then restart the node. 
2. **Port is blocked by firewall**. Some ports may be blocked by the firewall. To use these ports, we need to open them in the firewall.
3. **Incorrect IP address, port number or node alias in the configuration files.**
4. **UDP ports might not have been openned.** DolphinDB uses UDP broadcast to send heartbeats. 
5. To deploy in the cloud or k8s, we may need to add 'lanCluster=0' in 'agent.cfg' and 'cluster.cfg'. If all cloud nodes are located in the same LAN, we don't need to add 'lanCluster=0'. In AWS, however, the nodes are not in the same LAN, so we need to add 'lanCluster=0'.  

### 4. Web-based cluster management

We can change cluster configuration and add/delete data nodes on the web-based cluster manager. 

The bottom left panel shows all the agents, and the main panel displays the controller and the data nodes. Click on the "DFS Explorer" button in the upper left corner to browse the distributed databases stored in the distributed file system.

![](images/multi_started.JPG)

#### 4.1 Controller node parameter configuration

Clicking on the button "Controller Config" will open up a control interface, where "localExectors", "maxConnections", "maxMemSize", "webWorkerNum" and "workerNum" were specified when we created controller.cfg in 3.1.1. These configuration parameters can be modified, and will take effect after the controller node is restarted.

![](images/multi_controller_config.JPG)

#### 4.2 Add/delete data nodes

Click on the button "Nodes Setup" to enter the cluster nodes configuration interface. The figure below shows the parameters in "cluster.nodes" that we created in 3.1.2. We can add or delete data nodes here. The new configuration will take effect after the entire cluster is restarted. The steps to restart the cluster include: (1) close all data nodes (2) close the controller, (3) start the controller, and (4) start the data nodes. Deleting a data node may result in loss of data that were saved on the node. 

![](images/multi_nodes_setup.JPG)

If the new data node is on a new physical server, we must configure and start an agent node as in 3.2 on the new physical server, revise cluster.nodes with the information about the new agent node and new data node, and restart the controller node. 

#### 4.3 Modify data node configuration
Click on the button "Nodes Config" to configure the data nodes. This figure below displays parameters we specified in cluster.cfg in 3.1.3. We can also add other parameters to be configured here. They will take effect after all the data nodes are restarted.

![](images/multi_nodes_config.JPG)


#### 4.4 How to set up external network access

We can set up external network access with domain name or IP address. To start HTTPS, the external network address must be a domain name. The following script in cluster.cfg sets up the external network addresses of all nodes on **P1**, **P2**, **P3** and **P5**. % is a wildcard character.

```
P1-%.publicName=19.56.128.21
P2-%.publicName=19.56.128.22
P3-%.publicName=19.56.128.23
P5-%.publicName=19.56.128.25
```

We also need to add the corresponding external domain name or IP in controller.cfg.

```
publicName=19.56.128.24
```

#### 4.5 Volumes

Volumes are folders on the data nodes used to store data produced by the distributed file system in DolphinDB. A node can have multiple volumes. It is most efficient when each volume represents an independent I/O device and can be written to or read in parallel. If multiple volumes correspond to the same I/O device, performance will be affected. 

We can specify volumes path in cluster.cfg. If it is not specified, the system will use the data node alias in volumes path. For example, if the node alias is P5-NODE1, the system automatically creates a "P5-NODE1" subdirectory under the home directory of the node to store data. Note: when we specify volumes path, we can only use absolute paths.

There are 3 ways to specify volumes path:

####  With absolute path

```
P3-NODE1.volumes=/DFS/P3-NODE1
P5-NODE1.volumes=/DFS/P5-NODE1
```

#### With wildcard characters "%" and "?"

"?" represents a single character; "%" can represent 0, 1 or more characters.

To store the data of all the nodes ending with "-NODE1" to /VOL1/
```
%-NODE1.volumes=/VOL1/
```
This is equivalent to the following:
```
P1-NODE1.volumes=/VOL1/
P2-NODE1.volumes=/VOL1/
P3-NODE1.volumes=/VOL1/
P5-NODE1.volumes=/VOL1/
```

####  With symbol **ALIAS**

If all volumes paths contain node alias, we can use <ALIAS> to specify the volumes paths. For example, to configure 2 volumes (/VOL1/ and /VOL2/) on each node:

```
volumes=/VOL1/<ALIAS>,/VOL2/<ALIAS>
```
This is equivalent to the following:
```
P1-NODE1.volumes=/VOL1/P1-NODE1,/VOL2/P1-NODE1
P2-NODE1.volumes=/VOL1/P2-NODE1,/VOL2/P2-NODE1
P3-NODE1.volumes=/VOL1/P3-NODE1,/VOL2/P3-NODE1
P5-NODE1.volumes=/VOL1/P5-NODE1,/VOL2/P5-NODE1
```
### 5. Cloud Deployment

A DolphinDB cluster can be deployed on a LAN, or on private or public cloud. By default, DolphinDB assumes the cluster is on a LAN  (lanCluster=1) and uses UDP broadcast to send heartbeats. All the nodes on a cloud server, however, are not necessarily located in the same LAN, and may not support UDP. On a cloud server, we need to specify lanCluster=0 in controller.cfg and agent.cfg to implement communication between nodes in non-UDP mode. Otherwise, the cluster may not work properly as the heartbeats of the nodes may not be detected normally.

### 6. Reference

For a complete list of the cluster configuration parameters and details, please refer to Chapter 10 of DolphinDB [help](http://dolphindb.com/help/ClusterSetup.html).



