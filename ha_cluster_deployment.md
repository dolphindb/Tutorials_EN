# High Availability for DolphinDB

- [High Availability for DolphinDB](#high-availability-for-dolphindb)
	- [1. Introduction](#1-introduction)
	- [2. High availability of data nodes](#2-high-availability-of-data-nodes)
	- [3. High availability of controllers](#3-high-availability-of-controllers)
	- [4. APIs' support of high availability](#4-apis-support-of-high-availability)
	- [5. Add data nodes without restarting the cluster](#5-add-data-nodes-without-restarting-the-cluster)
	- [6. Summary](#6-summary)

## 1. Introduction

DolphinDB provides high availability for data nodes, controllers and API clients. It ensures that the database can continue to work when one or more database nodes become unavailable due to network interruption or node crash. 

Multiple replicas of the same data chunk can be stored on different data nodes. Even if one or more data nodes are unavailable, the database continues to work as long as at least one replica is still available in the cluster. The data consistency among multiple replicas is achieved by two-phase commit protocol.

Metadata is stored on controllers in DolphinDB. To ensure high availability of metadata, DolphinDB adopts Raft protocol and forms a Raft group with multiple controllers. If less than half of the controllers are unavailable, the cluster can continue to work. 

DolphinDB APIs also support high availability. When the data node an API is connecting with becomes unavailable, the API will attempt to reconnect to the data node. If the reconnecting attempt fails, the API will automatically connect to another data node that is available. 

High availability is offered in clusters but not in standalone mode. Regarding how to deploy a multi-machine cluster please refer to [DolphinDB Multi-Machine Cluster Deployment](/multi_machine_cluster_deployment.md).

![images](images/ha_cluster/arc.png?raw=true)

<div align='center'>DolphinDB High Availability Architecture Diagram  </div>

## 2. High availability of data nodes

DolphinDB supports storing replicas of data chunks on different servers, with strong consistency across all replicas. If data on one machine is corrupted, the database can still be accessed by visiting other machines. 

The number of replicas can be specified with parameter *dfsReplicationFactor* in controller.cfg. For example, to set the number of replicas to 2:

```
dfsReplicationFactor=2
```

By default, DolphinDB allows replicas of the same data chunk to be stored on the same machine. To ensure high availability of data nodes, replicas of the same data chunk must be stored on different machines. We need to add the following configuration parameter in controller.cfg:

```
dfsReplicaReliabilityLevel=1
```

For Example:

```
n=1000000
date=rand(2018.08.01..2018.08.03,n)
sym=rand(`AAPL`MS`C`YHOO,n)
qty=rand(1..1000,n)
price=rand(100.0,n)
t=table(date,sym,qty,price)
if(existsDatabase("dfs://db1")){
	dropDatabase("dfs://db1")
}
db=database("dfs://db1",VALUE,2018.08.01..2018.08.03)
trades=db.createPartitionedTable(t,`trades,`date).append!(t)
```

![images](https://github.com/dolphindb/Tutorials_CN/blob/master/images/ha_cluster/chunk_location.jpg?raw=true)

On the web interface of DolphinDB cluster manager, click on "DFS Explorer" to see where each partition is stored. The column 'Sites' shows that the partition for date=2018.08.01 is saved on 18104datanode and 18103datanode. If 18104datanode is unavailable, users can still work with the partition of date=2018.08.01 as long as 18103datanode is available. 

## 3. High availability of controllers

Metadata is stored on controllers. If metadata is corrupted, the database cannot be accessed even if all data nodes work fine. You can deploy multiple controllers in a cluster to ensure that metadata service is uninterrupted if one or more controllers become unavailable. All controllers in a cluster form a Raft group. One controller is the leader and the rest controllers are the followers. Metadata on the leader and on the followers maintains strong consistency. Data nodes can only interact with the leader. If the leader is not available, a new leader is immediately elected to provide the metadata service. The Raft group can tolerate less than half of the controllers become unavailable. For examples, a cluster with 3 controllers can tolerate 1 unavailable controller node; a cluster with 5 controllers can tolerate 2 unavailable controllers. To enable high availability for controllers, the number of controllers is at least 3, and we must set the configuration parameter *dfsReplicationFactor* to be greater than 1. 

The following example explains how to enable high availability of controllers for an existing cluster. Assume the controller is on machine P1. Now we add a controllers on P2 and another controller on P3. Their intranet IP addresses are: 

```
P1: 10.1.1.1
P2: 10.1.1.3
P3: 10.1.1.5
```

(1) Update the configuration file of the existing controller node

Add the following configuration parameters in controller.cfg of P1: dfsReplicationFactor=2, dfsReplicaReliabilityLevel=1, dfsHAMode=Raft. 

Now controller.cfg has the following parameters:

```
localSite=10.1.1.1:8900:controller1
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

(2) Deploy 2 new controllers

Download DolphinDB on P2 and P3, unzip to the directory /DolphinDB (or another directory the user chooses). 

Create directory 'config' under /DolphinDB/server. Create controller.cfg under directory 'config' and enter the following parameters:

P2

```
localSite=10.1.1.3:8900:controller2
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

P3

```
localSite=10.1.1.5:8900:controller3
dfsReplicationFactor=2
dfsReplicaReliabilityLevel=1
dfsHAMode=Raft
```

(3) Update the configuration file of existing agents

Add parameter 'sites' to agent.cfg to indicate IP address and port number of the agent node on the local machine and those of all controllers. The information about the agent node must appear before all the controllers. Now agent.cfg on P1 has the following paramaters:

```
localSite=10.1.1.1:8901:agent1
controllerSite=10.1.1.1:8900:controller1
sites=10.1.1.1:8901:agent1:agent,10.1.1.1:8900:controller1:controller,10.1.1.3:8900:controller2:controller,10.1.1.5:8900:controller3:controller
```

If there are multiple existing agents, we need to update the configuration file of each agent nodes.

(4) Update cluster.nodes on the existing controller

Update the controller information in cluster.nodes on P1. For example, cluster.nodes on P1 can be:

```
localSite,mode
10.1.1.1:8900:controller1,controller
10.1.1.2:8900:controller2,controller
10.1.1.3:8900:controller3,controller
10.1.1.1:8901:agent1,agent
10.1.1.1:8911:datanode1,datanode
10.1.1.2:8912:datanode2,datanode
```

(5) Add cluster.nodes and cluster.cfg on new controllers

Copy cluster.nodes and cluster.cfg on P1 to 'config' directory on P2 and P3.

(6) Start the cluster

- Start the controllers

Execute the following command on each of the machines where the controllers are located:

```bash
nohup ./dolphindb -console 0 -mode controller -home data -config config/controller.cfg -clusterConfig config/cluster.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```

- Start the agents

Execute the following command on each of the machines where the agent nodes are located:

```bash
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

> Only on the web-based cluster manager of the leader node can we start/close data nodes or update cluster configurations.  

- How to determine which controller is the leader

Enter the IP address and port number (e.g., 10.1.1.1:8900) of any controller on a web browser to open DolphinDB web-based cluster manager. Click on a controller in column "Node" to open a DolphinDB Notebook.

![images](https://github.com/dolphindb/Tutorials_CN/blob/master/images/ha_cluster/ha_web.jpg?raw=true)

Execute `getActiveMaster()` to return the alias of the leader node.

![images](https://github.com/dolphindb/Tutorials_CN/blob/master/images/ha_cluster/leader_en.png?raw=true)

Enter the IP address and port number on the web browser to open the web interface of the leader node. 


## 4. APIs' support of high availability 

DolphinDB Java, Python, C++ and C# APIs support high availability. When the data node an API is connecting with becomes unavailable, the API will attempt to reconnect to the data node. If the reconnecting attempt fails, the API will automatically connect to another data node that is available. Data node switching is transparent to the user. He or she is not aware that the connecting data node has been switched. 

The method `connect` for these APIs:

```
connect(host,port,username,password,startup,highAvailability,highAvailabilitySites,keepAliveTime)
```

To enable high availability of data nodes when we use these APIs, just specify *highAvailability* to be true in method `connect`. 

For example, to enable high availability of data nodes for Java API:

```java
import com.xxdb;
DBConnection conn = new DBConnection();
String[] sites = {"192.168.1.189:22207","192.168.1.224:22207","192.168.1.228:22207","192.168.1.189:22208","192.168.1.224:22208","192.168.1.228:22208"};
boolean success = conn.connect("192.168.1.228", 22207,"admin","123456","",true, sites);
```

If the data node 192.168.1.228:22207 goes down, API will automatically connect to another data node. 

## 5. Add data nodes without restarting the cluster

If some data nodes go down, you can use command `addNode` to add data nodes without restarting the cluster. 

The following example explains how to add a new data node datanode3 (port number 8911) on a new machine P4 with Intranet IP address of 10.1.1.7. To add new data nodes on new machines, we need to deploy an agent (port number 8901 with alias 'agent2' for this example) to start the new data nodes on the machine. 

Download DolphinDB on P4 and unzip it to a directory (/DolphinDB for this example). Enter directory /DolphinDB/server and create a subdirectory 'config'. 

Create agent.cfg under the subdirectory 'config' with the following content:

```
localSite=10.1.1.7:8901:agent2
controllerSite=10.1.1.1:8900:controller1
sites=10.1.1.7:8901:agent2:agent,10.1.1.1:8900:controller1:controller,10.1.1.3:8900:controller2:controller,10.1.1.5:8900:controller3:controller
```

Create cluster.nodes under the subdirectory 'config' with the following content:

```
localSite,mode
10.1.1.1:8900:controller1,controller
10.1.1.2:8900:controller2,controller
10.1.1.3:8900:controller3,controller
10.1.1.1:8901:agent1,agent
10.1.1.7:8901:agent2,agent
10.1.1.1:8911:datanode1,datanode
10.1.1.2:8912:datanode2,datanode
```

Update cluster.nodes on P1, P2 and P3 so that they are the same as cluster.nodes on P1. 

Execute the following command in Linux to start the agent node on P4:

```bash
nohup ./dolphindb -console 0 -mode agent -home data -config config/agent.cfg -logFile log/agent.log &
```

Execute the following command on any data node:

```
addNode("10.1.1.7",8911,"datanode3")
```

Then refresh the cluster manager, we can see that a new data node has been added to the cluster. Start the new data node on the web interface, then it's ready to be used. 


## 6. Summary

By offering high availability for data nodes, controllers and API clients, DolphinDB database can meet the needs of 24×7 hours availability for systems in IoT, finance and other areas. 
