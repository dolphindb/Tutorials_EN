# DolphinDB High-availability Cluster Deployment

A DolphinDB cluster consists of 4 types of nodes: controller, agent，data node, and compute node.

- **Controller**: The controllers are the core of a DolphinDB cluster. They collect heartbeats of agents and data nodes, monitor the status of each node, and manage metadata and transactions of the distributed file system. A high-availability cluster (HA cluster) forms a Raft group with multiple controllers. To ensure strong consistency of metadata across controllers, DolphinDB adopts Raft protocol.
- **Agent**: An agent executes the commands issued by a controller to start/stop local data nodes. Each physical server has one and only one agent within a cluster.
- **Data node**: Data are stored and queries (or more complex computations) are executed on data nodes. A physical server can be configured with multiple data nodes.
- **Compute node**: The compute node is used for queries and computation, including historical data queries, distributed joins, batch processing, streaming, and machine learning model training. A physical server can be configured with multiple compute nodes. Since data is not stored on a compute node, you can use `loadTable` to load data from a data node to a compute node for computational work. On a compute node, you can create the database and partitioned tables, and write data to the partitioned tables by calling a write interface. However, writing data on a compute node will lead to more network overhead than a data node as the compute node need to send data to data nodes for storage.

This tutorial describes how to deploy the DolphinDB HA cluster, and update the cluster and license file on Linux Distros. It serves as a quick start guide for you.


  - [1. Deploy HA Cluster on Linux Distros](#1-deploy-ha-cluster-on-linux-distros)
    - [Step 1: Download](#step-1-download)
    - [Step 2: Update License File](#step-2-update-license-file)
    - [Step 3: Configure a DolphinDB Cluster](#step-3-configure-a-dolphindb-cluster)
    - [Step 4: Start DolphinDB Cluster](#step-4-start-dolphindb-cluster)
    - [Step 5: Create Databases and Partitioned Tables on Data Nodes](#step-5-create-databases-and-partitioned-tables-on-data-nodes)
    - [Step 6: Perform Queries and Computation on Compute Nodes](#step-6-perform-queries-and-computation-on-compute-nodes)
  - [2. Web-Based Cluster Management](#2-web-based-cluster-management)
    - [2.1 Controller Configuration](#21-controller-configuration)
    - [2.2 Data Nodes and Compute Nodes Configuration](#22-data-nodes-and-compute-nodes-configuration)
  - [3. Upgrade DolphinDB Cluster](#3-upgrade-dolphindb-cluster)
    - [Step 1: Close all nodes](#step-1-close-all-nodes)
    - [Step 2: Back up the Metadata](#step-2-back-up-the-metadata)
    - [Step 3: Upgrade](#step-3-upgrade)
    - [Step 4: Restart the Cluster](#step-4-restart-the-cluster)
  - [4. Update License File](#4-update-license-file)
    - [Step 1: Replace the License File](#step-1-replace-the-license-file)
    - [Step 2: Update License File](#step-2-update-license-file-1)
  - [5. High Availability](#5-high-availability)
    - [5.1 High Availability of Metadata](#51-high-availability-of-metadata)
    - [5.2 High Availability of Data](#52-high-availability-of-data)
    - [5.3 High Availability For API Clients](#53-high-availability-for-api-clients)
  - [6. FAQ](#6-faq)
    - [Q1: Common reasons of node startup failure](#q1-common-reasons-of-node-startup-failure)
    - [Q2: Use the systemd command to start DolphinDB cluster](#q2-use-the-systemd-command-to-start-dolphindb-cluster)
    - [Q3: Failed to access the web interface](#q3-failed-to-access-the-web-interface)
    - [Q4: Roll back a failed upgrade on Linux](#q4-roll-back-a-failed-upgrade-on-linux)
    - [Q5: Failed to update license file online](#q5-failed-to-update-license-file-online)
    - [Q6: Failed to start nodes on a cloud server](#q6-failed-to-start-nodes-on-a-cloud-server)
    - [Q7: Specify volume path](#q7-specify-volume-path)
    - [Q8: Change configuration](#q8-change-configuration)
  - [7. See Also](#7-see-also)


## 1. Deploy HA Cluster on Linux Distros

The cluster architecture in this tutorial is as follows:

<img src="./images/ha_cluster_deployment/1_1.png" width=50%>

The internal IP addresses of the 3 servers are:

```
P1：10.0.0.80
P2：10.0.0.81
P3：10.0.0.82

```

Requirements and preparation before deployment:

- The number of nodes in the sample cluster of this tutorial exceeds the limit of the Community Edition License. So you must apply for [Enterprise Edition License](https://www.dolphindb.com/mx_form/mx_form.php?id=98) and update the license as described in [Step 2, Chapter 1](#step-2-update-license-file).
- The IP address of nodes should be an internal address with 10 Gigabit Ethernet. Using an external address may have an impact on the network communication between nodes.
- Each server must have an agent to start or close the local data nodes.



### Step 1: Download

Download DolphinDB installation package and unzip it on each physical server.

- Official website: [DolphinDB](https://www.dolphindb.com/alone/alone.php?id=75)
- Or you can download DolphinDB with a shell command:

```sh
wget https://www.dolphindb.com/downLinux64-Current.php -O dolphindb.zip
```

Then extract the installation package to the specified directory (`/path/to/directory`):

```sh
unzip dolphindb.zip -d </path/to/directory>
```

> ❗ The directory name cannot contain any space characters, otherwise the startup of the data node will fail.



### Step 2: Update License File

With a license for Enterprise edition, you can deploy DolphinDB across multiple nodes with more CPU cores and memory. If you have an Enterprise License, please use it to replace the following license file **on each physical server**.

```
/DolphinDB/server/dolphindb.lic
```



### Step 3: Configure a DolphinDB Cluster

**(1) Configuration Files of P1 Server**

Log in the **P1** server and then navigate to */DolphinDB/server/clusterDemo/config*.

- ***controller.cfg***

Execute the following shell command to modify *controller.cfg*:

```
vim ./controller.cfg
```

```
mode=controller
localSite=10.0.0.80:8800:controller1
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dataSync=1
workerNum=4
localExecutors=3
maxConnections=512
maxMemSize=8
dfsHAMode=Raft
lanCluster=0
```

Parameter *localSite* must be configured to specify IP address, port number, and alias of the controller. `dfsHAMode=Raft`, an option to configure a HA cluster, means all controllers in the cluster form a Raft group. Other parameters can be modified as needed.

To access the cluster web interface via an external address, the parameter *publicName* should be configured on the controller to specify the external address (e.g. 19.56.128.21 for **P1**):

```
 publicName=19.56.128.21
```

- ***cluster.nodes*** 

*cluster.nodes* stores detailed configuration details about controllers, agents, data nodes and compute nodes in a HA cluster. The cluster configuration file in this tutorial contains 3 controllers, 3 agents, 3 data nodes and 3 compute nodes. You can configure the number of nodes as required. The configuration file is divided into two columns (*localSite* and *mode*). The parameter *localSite* contains the node IP address, port number and alias, which are separated by colons ":". The parameter *mode* specifies the node type.

> ❗ Node aliases are case sensitive and must be unique in a cluster.

Execute the following shell command to modify *cluster.nodes* of servers **P1**, **P2**, and **P3**:

```
vim ./cluster.nodes
```

```
localSite,mode
10.0.0.80:8800:controller1,controller
10.0.0.81:8800:controller2,controller
10.0.0.82:8800:controller3,controller
10.0.0.80:8801:agent1,agent
10.0.0.80:8802:datanode1,datanode
10.0.0.80:8803:computenode1,computenode
10.0.0.81:8801:agent2,agent
10.0.0.81:8802:datanode2,datanode
10.0.0.81:8803:computenode2,computenode
10.0.0.82:8801:agent3,agent
10.0.0.82:8802:datanode3,datanode
10.0.0.82:8803:computenode3,computenode
```

> ❗  The configuration information of the three servers must be consistent.

- ***cluster.cfg***

Execute the following shell command to modify *cluster.cfg*:

```
vim ./cluster.cfg
```

```
maxMemSize=32
maxConnections=512
workerNum=4
localExecutors=3
maxBatchJobWorker=4
OLAPCacheEngineSize=2
TSDBCacheEngineSize=2
newValuePartitionPolicy=add
maxPubConnections=64
subExecutors=4
lanCluster=0
enableChunkGranularityConfig=true
```

These configuration parameters apply to each data node and compute node in the cluster. You can modify them based on your own device.

To access the web interface of data nodes and compute nodes via an external address, the parameter *publicName* should be configured to specify the external addresses for different servers:

```
datanode1.publicName=19.56.128.21
computenode1.publicName=19.56.128.21
datanode2.publicName=19.56.128.22
computenode2.publicName=19.56.128.22
datanode3.publicName=19.56.128.23
computenode3.publicName=19.56.128.23
```

> ❗ The configuration information of the three servers must be consistent.

- ***agent.cfg***

Execute the following shell command to modify *agent.cfg*:

```
vim ./agent.cfg
```

```
mode=agent
localSite=10.0.0.80:8801:agent1
controllerSite=10.0.0.80:8800:controller1
sites=10.0.0.80:8801:agent1:agent,10.0.0.80:8800:controller1:controller,10.0.0.81:8800:controller2:controller,10.0.0.82:8800:controller3:controller
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
```

In this config file, the parameters *localSite, controllerSite* and *sites* must be configured. 

- *localSite*: specifies IP address, port and alias of agents.
- *controllerSite*: specifies IP address, port and alias of the controller with which the agent first interacts in a cluster. This parameter must be set the same as *localSite* in *controller.cfg* of **P1**.
- *sites*: specifies IP address, port number and alias about the agent on the **P1** and all controllers, where the information about the agent must be placed before all the controllers.

Other parameters are optional.

**(2) Configuration Files of P2 Server**

Log in the **P2** server and then navigate to */DolphinDB/server/clusterDemo/config*.

- ***controller.cfg***

Execute the following shell command to modify *controller.cfg*:

```
vim ./controller.cfg
```

```
mode=controller
localSite=10.0.0.81:8800:controller2
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dataSync=1
workerNum=4
localExecutors=3
maxConnections=512
maxMemSize=8
dfsHAMode=Raft
lanCluster=0
```

Parameter *localSite* must be configured to specify IP address, port number, and alias of the controller. `dfsHAMode=Raft`, an option to configure a HA cluster, means all controllers in the cluster form a Raft group. Other parameters can be modified based on your device.

To access the cluster web interface via an external address, the parameter *publicName* should be configured on the controller to specify the external address (e.g. 19.56.128.22 for **P2**):

```
 publicName=19.56.128.22
```

- ***cluster.nodes*** 

*cluster.nodes* stores detailed configuration details about controllers, agents, data nodes and compute nodes in a HA cluster. The cluster configuration file in this tutorial contains 3 controllers, 3 agents, 3 data nodes and 3 compute nodes. You can configure the number of nodes as required. The configuration file is divided into two columns (*localSite* and *mode*). The parameter *localSite* contains the node IP address, port number and alias, which are separated by colons ":". The parameter *mode* specifies the node type.

> ❗ Node aliases are case sensitive and must be unique in a cluster.

Execute the following shell command to modify *cluster.nodes* of servers **P1**, **P2**, and **P3**:

```
vim ./cluster.nodes
```

```
localSite,mode
10.0.0.80:8800:controller1,controller
10.0.0.81:8800:controller2,controller
10.0.0.82:8800:controller3,controller
10.0.0.80:8801:agent1,agent
10.0.0.80:8802:datanode1,datanode
10.0.0.80:8803:computenode1,computenode
10.0.0.81:8801:agent2,agent
10.0.0.81:8802:datanode2,datanode
10.0.0.81:8803:computenode2,computenode
10.0.0.82:8801:agent3,agent
10.0.0.82:8802:datanode3,datanode
10.0.0.82:8803:computenode3,computenode
```

> ❗ The configuration information of the three servers must be consistent.

- ***cluster.cfg***

Execute the following shell command to modify *cluster.cfg*:

```
vim ./cluster.cfg
```

```
maxMemSize=32
maxConnections=512
workerNum=4
localExecutors=3
maxBatchJobWorker=4
OLAPCacheEngineSize=2
TSDBCacheEngineSize=2
newValuePartitionPolicy=add
maxPubConnections=64
subExecutors=4
lanCluster=0
enableChunkGranularityConfig=true
```

These configuration parameters apply to each data node and compute node in the cluster. You can modify them based on your own device.

To access the web interface of data nodes and compute nodes via an external address, the parameter *publicName* should be configured to specify the external addresses for different servers:

```
datanode1.publicName=19.56.128.21
computenode1.publicName=19.56.128.21
datanode2.publicName=19.56.128.22
computenode2.publicName=19.56.128.22
datanode3.publicName=19.56.128.23
computenode3.publicName=19.56.128.23
```

> ❗ The configuration information of the three servers must be consistent.

- ***agent.cfg***

Execute the following shell command to modify *agent.cfg*:

```
vim ./agent.cfg
```

```
mode=agent
localSite=10.0.0.81:8801:agent2
controllerSite=10.0.0.80:8800:controller1
sites=10.0.0.81:8801:agent2:agent,10.0.0.80:8800:controller1:controller,10.0.0.81:8800:controller2:controller,10.0.0.82:8800:controller3:controller
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
```

In this config file, the parameters *localSite, controllerSite* and *sites* must be configured.  

- *localSite*: specifies IP address, port and alias of agents.
- *controllerSite*: specifies IP address, port number and alias of the controller with which the agent first interacts in a cluster. This parameter must be set the same as *localSite* in *controller.cfg* of **P2**.
- *sites*: specifies IP address, port number and alias about the agent on the **P2** and all controllers, where the information about the agent must be placed before all the controllers.

Other parameters are optional.

**(3) Configuration Files of P3 Server**

Log in the **P3** server and then navigate to */DolphinDB/server/clusterDemo/config*.

- ***controller.cfg***

Execute the following shell command to modify *controller.cfg*:

```
vim ./controller.cfg
```

```
mode=controller
localSite=10.0.0.82:8800:controller3
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dataSync=1
workerNum=4
localExecutors=3
maxConnections=512
maxMemSize=8
dfsHAMode=Raft
lanCluster=0
```

Parameter *localSite* must be configured to specify IP address, port number, and alias of the controller. `dfsHAMode=Raft`, an option to configure a HA cluster, means all controllers in the cluster form a Raft group. Other parameters can be modified based on your device.

To access the cluster web interface via an external address, the parameter *publicName* should be configured on the controller to specify the external address (e.g. 19.56.128.23 for **P3**):

```
 publicName=19.56.128.23
```

- ***cluster.nodes*** 

*cluster.nodes* stores detailed configuration details controllers, agents, data nodes and compute nodes in a HA cluster. The cluster configuration file in this tutorial contains 3 controllers, 3 agents, 3 data nodes and 3 compute nodes. You can configure the number of nodes as required. The configuration file is divided into two columns (*localSite* and *mode*). The parameter *localSite* contains the node IP address, port number and alias, which are separated by colons ":". The parameter *mode* specifies the node type.

> ❗ Node aliases are case sensitive and must be unique in a cluster.

Execute the following shell command to modify *cluster.nodes* of servers **P1**, **P2**, and **P3**:

```
vim ./cluster.nodes
```

```
localSite,mode
10.0.0.80:8800:controller1,controller
10.0.0.81:8800:controller2,controller
10.0.0.82:8800:controller3,controller
10.0.0.80:8801:agent1,agent
10.0.0.80:8802:datanode1,datanode
10.0.0.80:8803:computenode1,computenode
10.0.0.81:8801:agent2,agent
10.0.0.81:8802:datanode2,datanode
10.0.0.81:8803:computenode2,computenode
10.0.0.82:8801:agent3,agent
10.0.0.82:8802:datanode3,datanode
10.0.0.82:8803:computenode3,computenode
```

> ❗ The configuration information of the three servers must be consistent.

- ***cluster.cfg***

Execute the following shell command to modify *cluster.cfg*:

```
vim ./cluster.cfg
```

```
maxMemSize=32
maxConnections=512
workerNum=4
localExecutors=3
maxBatchJobWorker=4
OLAPCacheEngineSize=2
TSDBCacheEngineSize=2
newValuePartitionPolicy=add
maxPubConnections=64
subExecutors=4
lanCluster=0
enableChunkGranularityConfig=true
```

These configuration parameters apply to each data node and compute node in the cluster. You can modify them based on your own device.

To access the web interface of data nodes and compute nodes via an external address, the parameter *publicName* should be configured to specify the external addresses for different servers:

```
datanode1.publicName=19.56.128.21
computenode1.publicName=19.56.128.21
datanode2.publicName=19.56.128.22
computenode2.publicName=19.56.128.22
datanode3.publicName=19.56.128.23
computenode3.publicName=19.56.128.23
```

> ❗ The configuration information of the three servers must be consistent.

- ***agent.cfg***

Execute the following shell command to modify *agent.cfg*:

```
vim ./agent.cfg
```

```
mode=agent
localSite=10.0.0.82:8801:agent3
controllerSite=10.0.0.80:8800:controller1
sites=10.0.0.82:8801:agent3:agent,10.0.0.80:8800:controller1:controller,10.0.0.81:8800:controller2:controller,10.0.0.82:8800:controller3:controller
workerNum=4
localExecutors=3
maxMemSize=4
lanCluster=0
```

In this config file, the parameters *localSite, controllerSite* and *sites* must be configured.  

- *localSite*: specifies IP address, port and alias of agents.
- *controllerSite*: specifies IP address, port number and alias of the controller with which the agent first interacts in a cluster. This parameter must be set the same as *localSite* in *controller.cfg* of **P3**.

- *sites*: specifies IP address port number and alias about the agent on the **P3** and all controllers, where the information about the agent must be placed before all the controllers.

Other parameters are optional. 



### Step 4: Start DolphinDB Cluster

Log in the servers **P1**, **P2**, and **P3**. Then navigate to */DolphinDB/server* of each server. The file permissions need to be modified for the first startup. Execute the following shell command:

```
chmod +x dolphindb
```

- **Start Controller**

Navigate to */DolphinDB/server/clusterDemo* of each server and start the controllers. Execute the following shell command:

```
sh startController.sh
```

To check whether the node was started, execute the following shell command:

```
ps aux|grep dolphindb
```

The following information indicates a successful startup:

<img src="./images/ha_cluster_deployment/1_2.png" width=80%>

- **Start Agent**

Navigate to */DolphinDB/server/clusterDemo* of each server and start the agents. Execute the following shell command:

```
sh startagent.sh
```

To check whether the node was started, execute the following shell command:

```
ps aux|grep dolphindb
```

The following information indicates a successful startup:

<img src="./images/ha_cluster_deployment/1_3.png" width=80%>

- **Start Data Nodes and Compute Nodes**

You can start or stop data nodes and compute nodes, and modify cluster configuration parameters on DolphinDB cluster management web interface. Enter the IP address and port number of any controller  in the browser to navigate to the DolphinDB Web. For example, the server address (*ip:port*) of the server **P2** in this tutorial is 10.0.0.81:8800. 

A prompt may appear when you try to access the Web interface, which indicates that the current controller is not the leader of the Raft. Click **OK** to go to the leader site, (e.g.10.0.0.80:8800:controller1).

Below is the web interface. Log in with the default administrator account (username: admin, password: 123456). Then select the required data nodes and compute nodes, and click on the **execute**/**stop** button.

<img src="./images/ha_cluster_deployment/1_4.png" width=80%>

Click on the **refresh** button to check the status of the nodes. The following green check marks mean all the selected nodes have been turned on:

<img src="./images/ha_cluster_deployment/1_5.png" width=80%>

 



### Step 5: Create Databases and Partitioned Tables on Data Nodes

Data nodes can be used for data storage, queries and computation. The following example shows how to create databases and write data on data nodes.

 First, open the web interface of the **Controller**, and click on the corresponding **Data node** to open its **Shell** interface (e.g. P1-datanode):

<img src="./images/ha_cluster_deployment/1_6.png" width=80%>

<img src="./images/ha_cluster_deployment/1_7.png" width=80%>

You can also enter IP address and port number of the data node in your browser to navigate to the **Shell** interface.

Execute the following script to create a database and a partitioned table：

```
// create a database and a partitioned table
login("admin", "123456")
dbName = "dfs://testDB"
tbName = "testTB"
if(existsDatabase(dbName)){
        dropDatabase(dbName)
}
db = database(dbName, VALUE, 2021.01.01..2021.12.31)
colNames = `SecurityID`DateTime`PreClosePx`OpenPx`HighPx`LowPx`LastPx`Volume`Amount
colTypes = [SYMBOL, DATETIME, DOUBLE, DOUBLE, DOUBLE, DOUBLE, DOUBLE, INT, DOUBLE]
schemaTable = table(1:0, colNames, colTypes)
db.createPartitionedTable(table=schemaTable, tableName=tbName, partitionColumns=`DateTime)

```

Then, run the following scripts to generate 1-minute OHLC bars and append the data to the created partitioned table “tbName”:

```
// simulate OHLC data and append it to the partitioned table
n = 1210000
randPrice = round(10+rand(1.0, 100), 2)
randVolume = 100+rand(100, 100)
SecurityID = lpad(string(take(0..4999, 5000)), 6, `0)
DateTime = (2023.01.08T09:30:00 + take(0..120, 121)*60).join(2023.01.08T13:00:00 + take(0..120, 121)*60)
PreClosePx = rand(randPrice, n)
OpenPx = rand(randPrice, n)
HighPx = rand(randPrice, n)
LowPx = rand(randPrice, n)
LastPx = rand(randPrice, n)
Volume = int(rand(randVolume, n))
Amount = round(LastPx*Volume, 2)
tmp = cj(table(SecurityID), table(DateTime))
t = tmp.join!(table(PreClosePx, OpenPx, HighPx, LowPx, LastPx, Volume, Amount))
dbName = "dfs://testDB"
tbName = "testTB"
loadTable(dbName, tbName).append!(t)

```

For more details about the above functions, see [DolphinDB user manual](https://www.dolphindb.com/help/FunctionsandCommands/index.html) or the function documentation popup on the web interface.

<img src="./images/ha_cluster_deployment/1_8.png" width=80%>

You can check the created database and table in the **Database** on the left side of the web interface.

<img src="./images/ha_cluster_deployment/1_9.png" width=30%>

Variables you created can be checked in **Local Variables**. You can click on the corresponding variable name to preview the related information (including data type, size, and occupied memory size).

<img src="./images/ha_cluster_deployment/1_10.png" width=80%>

Return to the **DFS** file page of the controller to check the created partitions under the databases.

<img src="./images/ha_cluster_deployment/1_11.png" width=70%>



### Step 6: Perform Queries and Computation on Compute Nodes

Compute nodes are used for queries and computation. The following example shows how to perform these operations in partitioned tables on a compute node. First, open the web interface of the **Controller**, and then click the corresponding **Compute node** to open its **Shell** interface (e.g. computenode1):

<img src="./images/ha_cluster_deployment/1_12.png" width=80%>

<img src="./images/ha_cluster_deployment/1_13.png" width=80%>

You can also enter IP address and port number of the compute node in your browser to navigate to the **Shell** interface.

Execute the following script to load the partitioned table: 

```
// load the partitioned table
pt = loadTable("dfs://testDB", "testTB")

```

Note that only metadata of the partitioned table is loaded here. Then execute the following script to count the records for each day in table “pt“:

```
// If the result contains a small amount of data, you can download it to display on the client directly.
select count(*) from pt group by date(DateTime) as Date
```

The result will be displayed at the bottom of the web interface:

<img src="./images/ha_cluster_deployment/1_14.png" width=25%>

Execute the following script to caculate OHLC bars for each stock per day:

```
// If the result contains a large amount of data, you can assign it to a variable that occupies the server memory, and download it to display in separate pages on the client.
result = select first(LastPx) as Open, max(LastPx) as High, min(LastPx) as Low, last(LastPx) as Close from pt group by date(DateTime) as Date, SecurityID
```

The result is assigned to the variable `result`. It will not be displayed on the client directly, thus reducing the memory of the client. To check the results, click `result` in the **Local Variables**.

<img src="./images/ha_cluster_deployment/1_15.png" width=80%>



## 2. Web-Based Cluster Management

After completing the deployment, you can modify the cluster configuration through the web interface of the controller.

> ❗ All configuration information of the HA cluster is managed by the Raft group, so the configuration parameters must be modified through the web interface. The changes will take effect after the corresponding node is restarted, and be automatically synchronized to all other configuration files in the cluster. 

### 2.1 Controller Configuration

Click **Controller Config** to modify the configuration parameters of controller. The following parameters are specified in *controller.cfg*. You can add, remove, and modify them in this web interface, and they will take effect after the controller is restarted.

<img src="./images/ha_cluster_deployment/2_1.png" width=80%>



### 2.2 Data Nodes and Compute Nodes Configuration

Click **Nodes Config** to modify the configuration parameters of data nodes and compute nodes. The following parameters are specified in *cluster.cfg*. You can add, remove, and modify them, and they will take effect after the data nodes and compute nodes are restarted.

<img src="./images/ha_cluster_deployment/2_2.png" width=80%>

 



## 3. Upgrade DolphinDB Cluster

### Step 1: Close all nodes

Log in the servers **P1**, **P2**, and **P3**. Then navigate to */DolphinDB/server/clusterDemo* of each server to execute the following shell command:

```
./stopAllNode.sh
```

### Step 2: Back up the Metadata

- Back up the Metadata of Controller

By default, the metadata of controllers in the Raft group is stored in */DolphinDB/server/clusterDemo/data/\<controller alias>/raft* of each controller. Take **P1** as an example:

```
/DolphinDB/server/clusterDemo/data/controller1/raft
```

Log in the servers **P1**, **P2**, and **P3**. Execute the following shell commands in */DolphinDB/server/clusterDemo/data/\<controller alias>* of each server:

```
mkdir controllerBackup
cp -r raft controllerBackup
```

If the metadata exceeds certain size limits, a *DFSMasterMetaCheckpoint.0* file will also be generated in */DolphinDB/server/clusterDemo/dfsMeta*. You can navigate to */DolphinDB/server/clusterDemo/dfsMeta*, then execute the following shell command to back up the metadata to the *controllerBackup* folder.

```
cp -r dfsMeta controllerBackup
```

- Back up the Metadata of Data Nodes

By default, the metadata of data nodes is stored in */DolphinDB/server/clusterDemo/data/\<data node alias>/storage/CHUNK_METADATA*. Take **P1** as an example:

```
/DolphinDB/server/clusterDemo/data/datanode1/stroage/CHUNK_METADATA
```

Log in the servers **P1**, **P2**, and **P3**. Execute the following shell commands in */DolphinDB/server/clusterDemo/data/\<data node alias>/storage*：

```
mkdir dataBackup
cp -r CHUNK_METADATA dataBackup
```

> ❗ If the backup files are not in the above default directory, check the directory specified by the configuration parameters *dfsMetaDir* and *chunkMetaDir*. If the two parameters are not modified but the configuration parameter *volumes* is specified, then you can find the CHUNK_METADATA under the *volumes* directory.

### Step 3: Upgrade

> ❗ When the server is upgraded to a certain version, the plugin should also be upgraded to the corresponding version.

- Online upgrade

Log in the servers **P1**, **P2**, and **P3**. Then navigate to */DolphinDB/server/clusterDemo* to execute the following command:

```
sh upgrade.sh
```

The following prompt is returned:

<img src="./images/ha_cluster_deployment/3_1.png" width=60%>

Type y and press Enter:

<img src="./images/ha_cluster_deployment/3_2.png" width=70%>

Type 1 and press Enter:

<img src="./images/ha_cluster_deployment/3_3.png" width=70%>

Type a version number and press Enter. To upgrade to version 2.00.9.1, for example, type 2.00.9.1 and press Enter. The following prompt indicates a successful upgrade.

<img src="./images/ha_cluster_deployment/3_4.png" width=80%>

- Offline upgrade

Download a new version of server package from [DolphinDB website](https://dolphindb.com/).

Upload the installation package to */DolphinDB/server/clusterDemo* of the servers **P1**, **P2**, and **P3**. Take version 2.00.9.1 as an example.

<img src="./images/ha_cluster_deployment/3_5.png" width=35%>

Log in the servers **P1**, **P2**, and **P3**. Then navigate to */DolphinDB/server/clusterDemo* to execute the following command:

```
sh upgrade.sh
```

The following prompt is returned:

<img src="./images/ha_cluster_deployment/3_6.png" width=60%>

Type y and press Enter:

<img src="./images/ha_cluster_deployment/3_7.png" width=70%>

Type 2 and press Enter:

<img src="./images/ha_cluster_deployment/3_8.png" width=70%>

Type a version number and press Enter. To upgrade to version 2.00.9.1, for example, type 2.00.9.1 and press Enter. The following prompt indicates a successful upgrade.

<img src="./images/ha_cluster_deployment/3_9.png" width=70%>

 

### Step 4: Restart the Cluster

- Start Controller

Execute the following shell command in */DolphinDB/server/clusterDemo* of each server:

```
sh startController.sh
```

- Start Agent

Execute the following shell command in */DolphinDB/server/clusterDemo* of each server:

```
sh startagent.sh
```

- Start Data Nodes and Compute Nodes

You can start or stop data nodes and compute nodes, and modify cluster configuration parameters on DolphinDB cluster management web interface. Enter the IP address and port number of any controller in the browser to navigate to the DolphinDB Web. For example, the server address (*ip:port*) of the server **P2** in this tutorial is 10.0.0.81:8800. 

A prompt may appear when you try to access the Web interface, which indicates that the current controller is not the leader of the Raft. Click **OK** to go to the leader site, (e.g.10.0.0.80:8800:controller1).

Below is the web interface. Log in with the default administrator account (username: admin, password: 123456). Then select the required data nodes and compute nodes, and click on the **execute**/**stop** button.

<img src="./images/ha_cluster_deployment/3_10.png" width=80%>

Click on the **refresh** button to check the status of the nodes. The following green check marks mean all the selected nodes have been turned on:

<img src="./images/ha_cluster_deployment/3_11.png" width=80%>

Open the web interface and execute the following script to check the current version of DolphinDB.

```
version()
```

 

## 4. Update License File

Before updating, open the web interface of any node and execute the following code to check the expiration time:

```
use ops
getAllLicenses()

```

<img src="./images/ha_cluster_deployment/4_1.png" width=30%>

Check the “end_date“ to confirm whether the update is successful.

### Step 1: Replace the License File

Log in the servers **P1**, **P2**, and **P3**. Replace an existing license file with a new one.

License file path on Linux:

```
/DolphinDB/server/dolphindb.lic
```

### Step 2: Update License File

- Online Update

Open the web interface of any node to execute the following script:

```
use ops
updateAllLicenses()

```

<img src="./images/ha_cluster_deployment/4_2.png" width=30%>

 

💡**Note:**

> The client name of the license cannot be changed.
>
> The number of nodes, memory size, and the number of CPU cores cannot be smaller than the original license.
>
> The update takes effect only on the node where the function is executed. Therefore, in a cluster mode, the function needs to be run on all controllers, agents, data nodes, and compute nodes.
>
> The license type must be either commercial (paid) or free.

- Offline Update

Restart DolphinDB cluster to complete the updates.



## 5. High Availability 

DolphinDB HA cluster offers high availability for metadata and data, and DolphinDB APIs support high availability for API clients. DolphinDB HA cluster can tolerate the failure of a single node. If any node become unavailable, the database can continue working without any operation interrupted. 

Metadata is stored on controllers. To ensure high availability of metadata, DolphinDB adopts Raft protocol to form a Raft group with multiple controllers. The cluster can continue to operate as long as more than half of the controllers are available.

DolphinDB supports storing replicas of data chunks on different data nodes. If one or more data nodes fail, the database can still work with at least one available replica. During the process, data consistency among multiple replicas is ensured by a two-phase commit protocol.

DolphinDB API supports automatic reconnection and switching for high availability. If the data node which an API is connecting with is unavailable, the API will attempt to reconnect to it. If the attempt fails, the API will automatically switch to another available data node or compute node. 

<figure align="left">
    <img src="./images/ha_cluster_deployment/5_1.png" width=50%>
    <figcaption>DolphinDB High Availability Architecture</figcaption>
</figure>



### 5.1 High Availability of Metadata

Metadata is generated when data is stored, which contains storage information of data. If the metadata is unavailable, the database can not be accessed even if all data chunks work fine. Metadata is stored on controllers. You can deploy multiple controllers in a HA cluster to increase metadata redundancy to ensure that metadata service is uninterrupted. All controllers in a HA cluster form a Raft group. There is only one controller being leader in the Raft group, and the rest are followers. Metadata on the leader and the followers maintains strong consistency. Data nodes and compute nodes can only interact with the leader. If the leader is not available, a new leader is immediately elected to provide the metadata service. The Raft group can tolerate the failure of less than half of the controllers. For example, 1 cluster with 3 controllers can tolerate 1 unavailable controller, and 1 cluster with 5 controllers can tolerate 2 unavailable controllers. To enable high availability of metadata, the number of controllers is at least 3, and the number of replicas must be specified to be more than 1 with the configuration parameter *dfsReplicationFactor* in *controller.cfg*. You can configure the parameters as follows:

```
dfsHAMode=Raft
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1

```

### 5.2 High Availability of Data

To ensure security and high availability of data, DolphinDB supports storing multiple replicas of data chunks on different servers. DolphinDB also adopts two-phase commit (2PC) protocol to achieve strong consistency among data replicas and between data and metadata. If data on one machine is corrupted, the database can still be accessed by visiting other machines. Here, 2PC is used for three reasons: 

(1) DolphinDB cluster can hold more than 10 million partitions. It is costly to create such a large number of protocol groups with Raft or Paxos;

(2) With Raft or Paxos, only one replica is available for data query, which is wasteful of resources in the processing of massive data; 

(3) If the appended data crosses partitions, 2PC is still required to guarantee the ACID of the transaction.

The number of replicas can be specified with parameter *dfsReplicationFactor* in *controller.cfg*. For example, to set the number of replicas to 2:

```
dfsReplicationFactor=2
```

By default, DolphinDB allows replicas of the same data chunk to be stored on the same machine. To ensure high availability of data, these replicas must be stored on different machines. You need to add the following configuration parameter in *controller.cfg*:

```
dfsReplicaReliabilityLevel=1
```

Here is an example: Log in to the web interface of any controller and navigate to the **DFS** interface. Then click “testDB” (created in Chapter 1) to check its information:

<img src="./images/ha_cluster_deployment/5_2.png" width=70%>

Click on the “20230108” partition:

 <img src="./images/ha_cluster_deployment/5_3.png" width=70%>

 

You can see the partition is saved on datanode1 and datanode3. If datanode1 is unavailable, data exchange with this partition remains as long as datanode3 is active.

<img src="./images/ha_cluster_deployment/5_4.png" width=70%>

 

### 5.3 High Availability For API Clients

When a data node or compute node which an API is connecting with becomes unavailable, the API will attempt to reconnect to the node. If the attempt fails, the API will automatically connect to another available data node or compute node. Now, Java, Python, C++ and C# APIs support high availability.

Here, the method `connect` is used to connect a data node or compute node:

```
connect(host,port,username,password,startup,highAvailability)
```

To enable high availability of data nodes or compute nodes, just specify *highAvailability* to be true.

Here is an example for Java API:

```
import com.xxdb;
DBConnection conn = new DBConnection();
String[] sites = {"10.0.0.80:8902","10.0.0.81:8902","10.0.0.82:8902"};
boolean success = conn.connect("Linux OS10.0.0.80", 8902,"admin","123456","",true, sites);
```

If the data node “10.0.0.80:8902” goes down, API will automatically connect to another available data node or compute node specified with the parameter *sites*. For more detailed information, see [DolphinDB user manual](https://www.dolphindb.com/help/FunctionsandCommands/index.html).

## 6. FAQ

### Q1: Common reasons of node startup failure

- **Port is occupied.**

If you cannot start the server, you can first check the log file of nodes under */DolphinDB/server/clusterDemo/log.*

If the following error occurs, it indicates that the specified port is occupied by other programs.

```
<ERROR> :Failed to bind the socket on port 8800 with error code 98
```

In such case, you can change to another free port in the config file.

- **The first line in** ***cluster.nodes*** **is empty.**

If you cannot start the server, you can first check the log file of nodes under */DolphinDB/server/clusterDemo/log.*

If the following error occurs, it it means the first line in the file *cluster.nodes* is empty. 

```
<ERROR> :Failed to load the nodes file [/home/DolphinDB/server/clusterDemo/config/cluster.nodes] with error: The input file is empty.
```

In this case, just remove the empty line from the file and restart the node.

### Q2: Use the systemd command to start DolphinDB cluster

First, create the script files *controller.sh* and *agent.sh* in the *DolphinDB/server/clusterDemo* directory on each server with the following scripts:

```
vim ./controller.sh
```

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
vim ./agent.sh
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

Then, execute the following shell command to configure the daemon for the controller:

```
vim /usr/lib/systemd/system/ddbcontroller.service
```

The following parameters should be configured:

```
[Unit]
Description=ddbcontroller
Documentation=https://www.dolphindb.com/

[Service]
Type=forking
WorkingDirectory=/home/DolphinDB/server/clusterDemo
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

> ❗ Specify *WorkingDirectory* as */DolphinDB/server/clusterDemo*.

Execute the following shell command to configure the daemon for the agent:

```
vim /usr/lib/systemd/system/ddbagent.service
```

The following parameters should be configured:

```
[Unit]
Description=ddbagent
Documentation=https://www.dolphindb.com/

[Service]
Type=forking
WorkingDirectory=/home/DolphinDB/server/clusterDemo
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

> ❗ Specify *WorkingDirectory* as */DolphinDB/server/clusterDemo*.

Finally, execute the following shell command to start the controller:

```
systemctl enable ddbcontroller.service   #enable the service
systemctl start ddbcontroller.service    #start the service
systemctl stop  ddbcontroller.service    #stop the service
systemctl status  ddbcontroller.service  #check the status
```

Execute the following shell command to start the agent:

```
systemctl enable ddbagent.service   #enable the service
systemctl start ddbagent.service    #start the service
systemctl stop  ddbagent.service    #stop the service
systemctl status  ddbagent.service  #check the status
```

### Q3: Failed to access the web interface

Despite the server running and the URL being correct, the web interface remains inaccessible.

<img src="./images/ha_cluster_deployment/6_1.jpg" width=50%>

A common reason for the above problem is that the browser and DolphinDB are not deployed on the same server, and a firewall is enabled on the server where DolphinDB is deployed. You can solve this issue by turning off the firewall or by opening the corresponding port.

### Q4: Roll back a failed upgrade on Linux

If you cannot start DolphinDB multi-machine cluster after upgrade, you can follow steps below to roll back to the previous version.

> ❗ This operation can be performed only when no new data has been written since the upgrade.

**Step 1: Restore metadata files**

- Restore metadata files of controller

Log in the server where controller is deployed (e.g. **P1**). Navigate to */DolphinDB/server/clusterDemo/data/controller1* to restore metadata files from *controllerBackup* with the following command:

```
cp -r backup/raft ./
```

And navigate to */DolphinDB/server/clusterDemo/dfsMeta* to restore metadata files from *controllerBackup* with the following command:

```
cp -r backup/dfsMeta ./
```

- Restore metadata files of data nodes

Log in the server where data nodes are deployed (e.g. **P1**). Navigate to the folder*/DolphinDB/server/clusterDemo/data/datanode1/storage* to restore metadata files from *dataBackup* with the following command:

```
cp -r dataBackup/CHUNK_METADATA ./
```

**Step 2: Restore program files**

Download the previous version of server package from the official website. Replace the server that failed to upgrade with all files (except *dolphindb.cfg*, *clusterDemo* and *dolphindb.lic*) just downloaded.

### Q5: Failed to update license file online

Updating the license file online requires meeting the requirements described in [Step 2, Chapter 4](#step-2-update-license-file-1). Otherwise, you can update offline or apply for an [Enterprise Edition License](https://www.dolphindb.com/mx_form/mx_form.php?id=98).

### Q6: Failed to start nodes on a cloud server

A DolphinDB cluster can be deployed on a LAN, or on cloud environment. By default, the DolphinDB cluster is deployed within a LAN (`lanCluster=1`) and uses UDP to monitor the heartbeats of nodes. However, the nodes on a cloud server are not necessarily located within the same LAN, and the cluster may not support UDP. On a cloud server, you must specify `lanCluster=0` in *controller.cfg* and *agent.cfg* to implement communication between nodes in a non-UDP mode. Otherwise, the cluster may malfunction due to the possible failure to detect the heartbeat of a node.

### Q7: Specify volume path

A volume is a folder on a data node that holds data in a DFS database in DolphinDB. A node can have multiple volumes. For optimal performance, each volume represents a unique hard disk.

The volume path can be specified in *cluster.cfg*. If it is not specified, the system will use the data node alias as the path name. For example, if the node alias is P1-datanode, the system automatically creates a subdirectory *P1-datanode* under the home directory */DophinDB/server/clusterDemo/data* of the node to store data. Note that only an absolute path can be used to specify a volume.

> ❗ It is recommended not to mount a remote NAS volume, which may affect the performance. If the partitions have been mounted with NFS protocol, please switch user to root to access the database. A database process started by a regular user is not allowed to read or write to the NAS disk, whereas a process started by a sudo user will cause access errors.

There are 3 ways to specify the volume path:

- **Specify separately for each node**

```
P1-datanode.volumes=/DFS/P1-datanode
P2-datanode.volumes=/DFS/P2-datanode

```

- **Specify with wildcard characters** `%` **and** `?`

`?`  represents a single character; `%` can represent 0, 1 or more characters.

To store the data of all the nodes ending with "-datanode" to */VOL1*:

```
%-datanode.volumes=/VOL1
```

This is equivalent to the following:

```
P1-datanode.volumes=/VOL1
P2-datanode.volumes=/VOL1

```

- **Specify with symbol ALIAS**

If each volume path contains a node alias, you can use \<ALIAS> to specify the volume paths. For example, to configure 2 volumes (*/VOL1* and */VOL2*) on each node:

```
volumes=/VOL1/<ALIAS>,/VOL2/<ALIAS>
```

This is equivalent to the following:

```
P1-datanode.volumes=/VOL1/P1-datanode,/VOL2/P1-datanode
P2-datanode.volumes=/VOL1/P2-datanode,/VOL2/P2-datanode

```

### Q8: Change configuration

For more details on configuration parameters, refer to [Configuration](https://www.dolphindb.com/help/DatabaseandDistributedComputing/Configuration/index.html).

If you encounter performance problems, you can contact our team on [Slack](https://dolphindb.slack.com/) for technical support.

## 7. See Also

For more information, refer to [DolphinDB Manual](https://www.dolphindb.com/help/index.html).