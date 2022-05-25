# DolphinDB Multi-Machine Cluster Deployment

This tutorial introduces how to deploy a multi-machine cluster in DolphinDB and the common reasons for node startup failures. 

- [DolphinDB Multi-Machine Cluster Deployment](#dolphindb-multi-machine-cluster-deployment)
  - [1. Cluster Architecture](#1-cluster-architecture)
  - [2. Download DolphinDB](#2-download-dolphindb)
  - [3. Update the License](#3-update-the-license)
  - [4. Upgrade DolphinDB Server](#4-upgrade-dolphindb-server)
  - [5. Initial Configuration](#5-initial-configuration)
    - [5.1 Cluster Configuration Files](#51-cluster-configuration-files)
    - [5.2 Agent Configuration Files](#52-agent-configuration-files)
    - [5.3 Start a DolphinDB Cluster](#53-start-a-dolphindb-cluster)
  - [6. Common Reasons Why Nodes Cannot Start](#6-common-reasons-why-nodes-cannot-start)
  - [7. Web-Based Cluster Management](#7-web-based-cluster-management)
    - [7.1 Configuration Parameters for Controller](#71-configuration-parameters-for-controller)
    - [7.2 Add/Remove Data Node](#72-addremove-data-node)
    - [7.3 Configuration Parameters for Data Nodes](#73-configuration-parameters-for-data-nodes)
    - [7.4 Access Cluster Manager via External Address](#74-access-cluster-manager-via-external-address)
    - [7.5 Specify Volume Path](#75-specify-volume-path)
  - [8. Cloud Deployment](#8-cloud-deployment)


## 1. Cluster Architecture

A DolphinDB cluster has 4 types of nodes: data node, compute node, agent and controller.

- The data node is used for data storage and computation. We can create distributed databases and tables on a data node.

- The compute node is only used for computation, including stream computing, distributed join and machine learning. Data is not stored on a compute node, and therefore we cannot create a database or table on it. 

- The agent starts or stops the local data nodes.

- The controller manages the cluster metadata and coordinates tasks among data nodes. 

This tutorial uses a DolphinDB cluster with 5 physical servers: **P1**, **P2**, **P3**, **P4**, **P5**.

The internal IP addresses of the 5 physical servers are:

```txt
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
P4: 10.1.1.7
P5: 10.1.1.9
```

The controller is set on **P4**. We set up an agent node and a data node on each of the other servers.

Note:
- **The IP address of a node must be an internal address. If an external address is used, the performance of network communication between nodes cannot be guaranteed.**

- Each physical server must have an agent to start or close the local data nodes.

- A DolphinDB cluster (except a high-availability cluster) can only have one controller.

## 2. Download DolphinDB

Download DolphinDB from [DolphinDB](http://www.dolphindb.com/downloads.html) website and extract it to a given directory. For example, extract it to the following directory:

```sh
/DolphinDB
```

Please note that the installation path cannot contain space characters, otherwise the data node will fail to start.

## 3. Update the License

Compared with the Community Edition, the Enterprise version allows more nodes, CPU cores and memory. If you have an Enterprise Trial license, please use it to replace the following license file on each physical server. 

```sh
/DolphinDB/server/dolphindb.lic
```

## 4. Upgrade DolphinDB Server 

After downloading a new version, please make sure not to overwrite `dolphindb.lic` and `dolphindb.cfg` to keep your license and customized configuration.

## 5. Initial Configuration

To start a cluster, we must configure the controller and the agents. Data nodes can be configured either before the cluster is started via configuration files, or afterwards via the web-based manager.

### 5.1 Cluster Configuration Files

Please make sure the number of nodes and the number of cores per node do not exceed the limits set in the license file. Otherwise the cluster will not start properly and the errors can be found in the log files.

DolphinDB by default uses the server directory as home directory and all configuration and log files are stored under it.

The default paths for configuration files, data files and log files are: 

```sh
cd /DolphinDB/server/clusterDemo/config
cd /DolphinDB/server/clusterDemo/data
cd /DolphinDB/server/clusterDemo/log
```


#### 5.1.1 controller.cfg

Log in server **P4**, open `controller.cfg` under the `config` directory to specify the following commonly used parameters. Only the parameter *localSite* is mandatory. All other parameters are optional.

```txt
localSite=10.1.1.7:8990:master
mode=controller
dfsReplicationFactor=1
dfsReplicaReliabilityLevel=2
dataSync=1
workerNum=4
localExecutors=3
maxConnections=512
maxMemSize=8
lanCluster=0
```

The parameters are described in the table below.

| Parameter Configuration        | Description          |
|:------------- |:-------------|
|localSite=10.1.1.7:8990:master|     Node LAN information in the format of IP address:port number:alias of the local node. All fields are mandatory.|
|localExecutors=3          |         The number of local executors. The default value is the number of cores of the CPU - 1.|
|maxConnections=512     |            The maximum number of inward connections.|
|maxMemSize=16          |            The maximum memory (in terms of GB) allocated to DolphinDB. If set to 0, it means no limit on memory usage.|
|webWorkerNum=4              |       The number of workers to process HTTP requests. The default value is 1.|
|workerNum=4        |                The number of workers for regular interactive jobs. The default value is the number of cores of the CPU.|
|dfsReplicationFactor=2         |    The number of replicas for each table partition or file block. The default value is 2.|
|dfsReplicaReliabilityLevel=1     |  Whether multiple replicas can reside on the same server. 0: Yes; 1: No. The default value is 0.|
|dataSync=1         |   Whether to enable the redo log. 0: Enable; 1: Disable. When dataSync=1, chunkCacheEngineMemSize must also be specified in the file cluster.cfg.|


#### 5.1.2 cluster.nodes

Specify the following information in the file `cluster.nodes` under the `config` directory of P4. This file stores information on the agent nodes and data nodes. It has two columns: *localSite* and *mode*, separated by a comma. The parameter *localSite* contains the node IP address, port number and node alias, separated by a colon ":". Node aliases are case sensitive and must be unique in a cluster. The parameter *mode* specifies the node type.

This tutorial uses 4 agent nodes and 4 data nodes on **P1**, **P2**, **P3** and **P5**.

```txt
localSite,mode
10.1.1.1:8960:P1-agent,agent
10.1.1.1:8961:P1-NODE1,datanode
10.1.1.3:8960:P2-agent,agent
10.1.1.3:8961:P2-NODE1,datanode
10.1.1.5:8960:P3-agent,agent
10.1.1.5:8961:P3-NODE1,datanode
10.1.1.9:8960:P5-agent,agent
10.1.1.9:8961:P5-NODE1,datanode
```

#### 5.1.3 cluster.cfg

In the `config` directory of P4, open the configuration file `cluster.cfg` and specify the following configuration parameters. These configuration parameters apply to each data node and compute node in the cluster. For details of these parameters, see [Standalone Mode](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/StandaloneMode.html) in the user guide.

```txt
maxConnections=512
maxMemSize=32
workerNum=8
localExecutors=7
webWorkerNum=2
newValuePartitionPolicy=add
chunkCacheEngineMemSize=2

```

### 5.2 Agent Configuration Files

Log in the servers **P1**, **P2**, **P3** and **P5** and go to the `config` directory of each server, open the file `agent.cfg` and specify the following configuration parameters. Only *localSite* and *controllerSite* are mandatory in `agent.cfg`. All others are optional. 

#### P1

```txt
mode=agent
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
localSite=10.1.1.1:8960:P1-agent
controllerSite=10.1.1.7:8990:master
```

#### P2

```txt
mode=agent
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
localSite=10.1.1.3:8960:P2-agent
controllerSite=10.1.1.7:8990:master
```

#### P3

```txt
mode=agent
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
localSite=10.1.1.5:8960:P3-agent
controllerSite=10.1.1.7:8990:master
```

#### P5

```txt
mode=agent
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
localSite=10.1.1.9:8960:P5-agent
controllerSite=10.1.1.7:8990:master
```

Parameter *localSite* in `controller.cfg` should have the same value as parameter *controllerSite* in `agent.cfg` for all agents, as agent nodes looks for the controller at the address specified by parameter *controllerSite* in `agent.cfg`. If *localSite* in `controller.cfg` is modified (even if just an alias change), *controllerSite* in `agent.cfg` of all agents must be changed accordingly.

### 5.3 Start a DolphinDB Cluster

There are two ways to start a DolphinDB cluster: One is to use systemd on Linux and the other is to start from command line.

#### 5.3.1 Use systemd to Start DolphinDB

- **Add Scripts**

First, add the scripts `controller.sh` and `agent.sh` to \<dolphindbServer>/server/clusterDemo with the following content: 

```
#!/bin/bash
#controller.sh
workDir=$PWD

start(){
    cd ${workDir} && export LD_LIBRARY_PATH=$(dirname "$workDir"):$LD_LIBRARY_PATH
    nohup ./../dolphindb -console 0 -mode controller -home data -script dolphindb.dos -config config/controller.cfg -logFile log/controller.log -nodesFile config/cluster.nodes -clusterConfig config/cluster.cfg > controller.nohup 2>&1 &
}

stop(){
    ps -o ruser=userForLongName -e -o pid,ppid,c,time,cmd |grep dolphindb|grep -v grep|grep $USER|grep controller| awk '{print $2}'| xargs kill -TERM
}

case $1 in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
esac
```

```
#!/bin/bash
#agent.sh


workDir=$PWD

start(){
    cd ${workDir} && export LD_LIBRARY_PATH=$(dirname "$workDir"):$LD_LIBRARY_PATH
    nohup ./../dolphindb -console 0 -mode agent -home data -script dolphindb.dos -config config/agent.cfg -logFile log/agent.log  > agent.nohup 2>&1 &
}

stop(){
    ps -o ruser=userForLongName -e -o pid,ppid,c,time,cmd |grep dolphindb|grep -v grep|grep $USER|grep agent| awk '{print $2}'| xargs kill -TERM
}

case $1 in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
esac
```

- **Controller**

**Step 1: Configure Daemon**

Configure the daemon for the controller:

```shell
$ vim /usr/lib/systemd/system/ddbcontroller.service
```

**Step 2: Configure Parameters**

The following configuration parameters should be specified:

```
[Unit]
Description=ddbcontroller
Documentation=https://www.dolphindb.com/

[Service]
Type=forking
WorkingDirectory=/home/jwu/hav1.30.16/server/clusterDemo
ExecStart=/bin/sh controller.sh start
ExecStop=/bin/sh controller.sh stop
ExecReload=/bin/sh controller.sh restart
Restart=always
RestartSec=10s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity

[Install]
WantedBy=multi-user.target
```

**Note:** Please specify *WorkingDirectory* in the following format: 
\<dolphindbServer>/server/clusterDemo.


**Step 3: Start Controller**

```
systemctl enable ddbcontroller.service   #enable the service
systemctl start ddbcontroller.service  #start the service
systemctl stop  ddbcontroller.service   #stop the service
systemctl status  ddbcontroller.service  #check the status
```

- **Agent**

**Step 1: Configure Daemon**

Configure the daemon for the agent:

```shell
$ vim /usr/lib/systemd/system/ddbagent.service
```


**Step 2: Configure Parameters**

The following configuration parameters should be specified:

```
[Unit]
Description=ddbagent
Documentation=https://www.dolphindb.com/

[Service]
Type=forking
WorkingDirectory=/home/jwu/hav1.30.16/server/clusterDemo
ExecStart=/bin/sh agent.sh start
ExecStop=/bin/sh agent.sh stop
ExecReload=/bin/sh agent.sh restart
Restart=always
RestartSec=10s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity

[Install]
WantedBy=multi-user.target
```

**Note:** Please specify WorkingDirectory in the following format: 
\<dolphindbServer>/server/clusterDemo.

**Step 3: Start Controller**

```
systemctl enable ddbagent.service   #enable the service
systemctl start ddbagent.service  #start the service
systemctl stop  ddbagent.service   #stop the service
systemctl status  ddbagent.service  #check the status
```

#### 5.3.2 Start DolphinDB from Command Line

**Start Agent**

Log in each of **P1**,**P2**,**P3**, and **P5**, and run the command line described below in the directory where the DolphinDB executable is located. If the agent fails to start, you can troubleshoot according to the agent.log which is stored in "log" subdirectory.


- **Start in Background (Linux)**

```sh
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

It is recommended to start DolphinDB in the background with Linux command nohup (header) and & (tail). This way, DolphinDB will keep running even if the terminal is disconnected.

"-console" indicates whether to start the DolphinDB terminal. It is set to 1 by default, meaning to start the terminal. To run in the background mode, set it to 0 ("-console 0"). Otherwise, the system will quit after running for a while. "-mode" indicates the node type; "-home" specifies the data and the metadata storage path; "-config" specifies the configuration file path; "-logFile" specifies the log file path.


- **Start in Console Mode (Linux)**

```sh
./dolphindb -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

The above code is equivalent to the command ``sh startAgent.sh`` .

- **Start on Windows**

```sh
dolphindb.exe -mode agent -home data -config config/agent.cfg -logFile log/agent.log
```

**Start Controller**

Log in server **P4**. Run the following command line in the directory where the DolphinDB executable is located. If the controller fails to start, you can troubleshoot according to controller.log which is stored in "log" subdirectory.

"-clusterConfig" specifies the path to the cluster node configuration file; "-nodesFile" specifies node type, IP address, port number, and node alias.


- **Start in Background (Linux)**
```
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

- **Start in Console Mode (Linux)**
```
./dolphindb -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

The above code is equivalent to command ``sh startController.sh``.

- **Start on Windows**

```sh
dolphindb.exe -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes
```

**Stop Controller and Agents**

If the node was started in console mode, enter "quit" in the console to exit.

```sh
quit
```

If the node was started in background, use the Linux kill command. Assume the Linux system username is "ec2-user":

```sh
ps aux | grep dolphindb  | grep -v grep | grep ec2-user|  awk '{print $2}' | xargs kill -TERM
```

The above code is equivalent to command ``sh stopAllNode.sh``.


#### 5.3.3 Start the Web-Based Cluster Manager

After both the controller and all the agent nodes are started, we can start or stop data nodes in the DolphinDB cluster management web interface. Enter the IP and port number of the controller in the address bar of your browser (currently supporting Chrome and Firefox) where 8990 is the port number of the controller.

```sh
 localhost:8990
```

![Cluster Managment](images/multi_web.JPG)

#### 5.3.4 DolphinDB Access Control

Only system administrators have permission to conduct cluster deployment. When using DolphinDB web-based cluster management interface for the first time, you need to log in with the following default administrator account.

```txt
Administrator Username: admin
Default Password      : 123456
```

Click on the login link.

![Login Link](images/login_logo.JPG)

Enter the administrator username and password.

![Enter Name And Password](images/login.JPG)

After logging in the "admin" account, we can change the password and add users or other administrators.

#### 5.3.5 Start Data Nodes

Select all nodes, click on the "execute" icon and confirm. It may take 30 seconds to 1 minute for all the nodes to successfully start. Click on the "refresh" icon to check the status of the nodes. When all items in the "State" column are green check marks, this means all the nodes have been successfully started.


![Start](images/multi_start_nodes.JPG)

![Refresh](images/multi_started.JPG)


Alternatively, we can start the data nodes with DolphinDB script on the controller node:

```txt
startDataNode(["P1-NODE1", "P2-NODE1","P3-NODE1","P5-NODE1"])
```

If a node fails to start, please check the log file of the node in "log" directory. For example, if the node alias is P1-NODE1, then check `log/P1-NODE1.log`.


## 6. Common Reasons Why Nodes Cannot Start

If the nodes cannot start after a long time, it may be due to the following reasons:
1. **Port is occupied.** If you find in the log file an error message "Failed to bind the socket on XXXX" where XXXX is the port number on the node to be started, it means this port may be occupied by another program. Close the other program or reassign a port number and then restart the node. It may also be that this node has just been closed and the Linux kernel has not released this port number. Just wait about 30 seconds and then restart the node.

2. **Port is blocked by firewall.** If the ports used are blocked, we need to open them in the firewall.

3. **Incorrect IP address, port number or node alias in the configuration files.**

4. DolphinDB cluster uses UDP broadcast to send heartbeats. **If an agent node has been started but the web-based cluster manager shows it's offline**, it may be because UDP is not supported by the networks where the cluster is located. Try switching to TCP for heartbeats by adding the configuration parameter *lanCluster*=0 to `agent.cfg` and `cluster.cfg`. 

5. **The first line in the configuration file for cluster nodes (`cluster.nodes`) is empty**. If you find in the log file an error message "Failed to load the nodes file [XXXX/cluster.nodes] with error: The input file is empty.", it means the first line in the file *cluster.nodes* is empty. In this case just remove the empty line from the file and restart the node.

6. **The macro variable\<ALIAS> has no effect when the node is specified explicitly.** In `cluster.cfg`, if the macro variable\<ALIAS> is used when a node is specified, e.g., P1-NODE1.persistenceDir = /hdd/hdd1/streamCache/\<ALIAS>, the node will not start properly. In this case just remove \<ALIAS> and replace it with a specific node alias, e.g., P1-NODE1.persistenceDir = /hdd/hdd1/streamCache/P1-NODE1. To use macro variables for all nodes, specify persistenceDir = /hdd/hdd1/streamCache/\<ALIAS>. For more information about how to use the macro variable, see [DolphinDB user guide](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/ClusterMode.html).


## 7. Web-Based Cluster Management

After the above steps, we have successfully deployed DolphinDB cluster. We can modify the cluster configuration parameters with DolphinDB web-based cluster manager.

### 7.1 Configuration Parameters for Controller

Click on the button "Controller Config" and a window pops up. The parameters *localExectors*, *maxConnections*, *maxMemSize*, *webWorkerNum* and *workerNum* displayed in the window were specified in `controller.cfg` in [Sect 5.1.1](#511-controller.cfg). We can modify the configuration parameters in the window, and they will take effect after the controller is restarted. 

Please note that to modify the configuration parameter *localSite*, the parameter *controllerSite* in each `agent.cfg` should also be changed, otherwise the cluster will not run properly. For a high-availability cluster, manual modification of the configuration files will not take effect. It is required to modify the configuration parameters in the web interface, and the modification will be automatically synchronized to all configuration files in the cluster.

![controller_config](images/multi_controller_config.JPG)

### 7.2 Add/Remove Data Node

Click on the button "Nodes Setup", a window pops up displaying cluster nodes information as specified in `cluster.nodes` in [Sect 5.1.2](#512-cluster.nodes). We can add or remove a data node in this window. The configuration will take effect after the cluster is restarted. Follow the steps below to restart a cluster:

1.	stop the data nodes
2.	stop the agents
3.	stop the controller
4.	start the controller
5.	start the agents
6.	start the data nodes

Please note that removing a data node may cause data loss.

![nodes_setup](images/multi_nodes_setup.JPG)

If the newly-added data node is on a new physical server, we must configure and start a new agent as described in [Sect 5.2](#52-agent-configuration-files) on the server, add the information of the agent and data node to `cluster.nodes`, and restart the controller.

### 7.3 Configuration Parameters for Data Nodes

Click on the button "Nodes Config" to modify the configuration parameters of the data nodes. The configuration parameters shown below are in `cluster.cfg` as specified in [Sect 5.1.3](#513-cluster.cfg). We can also add other parameters to be configured here and they will take effect after all the data nodes are restarted.

![nodes_config](images/multi_nodes_config.JPG)

### 7.4 Access Cluster Manager via External Address

If the nodes in a cluster are located within the same LAN, set the site information to the internal IP address for optimal network communication. To access the cluster manager via an external address, the *publicName* should be configured on the controller to specify the external address. The parameter *publicName* can be a domain name or an IP address. It must be a domain name if HTTPS is used. The following script in `cluster.cfg` sets up the external addresses of all nodes on **P1**, **P2**, **P3** and **P5**, where % is a wildcard character for the node alias.

```txt
P1-%.publicName=19.56.128.21
P2-%.publicName=19.56.128.22
P3-%.publicName=19.56.128.23
P5-%.publicName=19.56.128.25
```

We also need to add the corresponding external domain name or IP address in `controller.cfg`.

```txt
publicName=19.56.128.24
```

### 7.5 Specify Volume Path

A volume is a folder on a data node that holds data in a DFS database in DolphinDB. A node can have multiple volumes. It is most efficient when each volume represents a unique hard disk, so multiple volumes can be written to or read in parallel. 

We can specify the volume path in `cluster.cfg`. If it is not specified, the system will use the data node alias as the path name. For example, if the node alias is P5-NODE1, the system automatically creates a "P5-NODE1" subdirectory under the home directory of the node to store data. Please note that only an absolute path can be used to specify a volume.

There are 3 ways to specify the volume path:

- #### Specify Separately for Each Node

```txt
P3-NODE1.volumes=/DFS/P3-NODE1
P5-NODE1.volumes=/DFS/P5-NODE1
```

- #### Specify with Wildcard Characters "%" and "?"

"?" represents a single character; "%" can represent 0, 1 or more characters.

To store the data of all the nodes ending with "-NODE1" to /VOL1/:

```txt
%-NODE1.volumes=/VOL1/
```

This is equivalent to the following:

```txt
P1-NODE1.volumes=/VOL1/
P2-NODE1.volumes=/VOL1/
P3-NODE1.volumes=/VOL1/
P5-NODE1.volumes=/VOL1/
```

- #### Specify with Symbol ALIAS

If each volume path contains a node alias, we can use \<ALIAS> to specify the volume paths. For example, to configure 2 volumes (/VOL1/ and /VOL2/) on each node:

```txt
volumes=/VOL1/<ALIAS>,/VOL2/<ALIAS>
```

This is equivalent to the following:

```txt
P1-NODE1.volumes=/VOL1/P1-NODE1,/VOL2/P1-NODE1
P2-NODE1.volumes=/VOL1/P2-NODE1,/VOL2/P2-NODE1
P3-NODE1.volumes=/VOL1/P3-NODE1,/VOL2/P3-NODE1
P5-NODE1.volumes=/VOL1/P5-NODE1,/VOL2/P5-NODE1
```

## 8. Cloud Deployment

A DolphinDB cluster can be deployed on a Local Area Network (LAN), or on private or public cloud. By default, DolphinDB assumes the cluster is on a LAN (lanCluster=1) and uses UDP heartbeats. However, the nodes on a cloud server are not necessarily located within the same LAN, and the cluster may not support UDP. On a cloud server, it is required to specify *lanCluster=0* in `controller.cfg` and `agent.cfg` to implement communication between nodes in a non-UDP mode. Otherwise, the cluster may not work normally as the nodes' heartbeats may not be detected properly.

For more information on configuration, please see DolphinDB documentation [Configuration](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/index.html).
