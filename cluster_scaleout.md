# How to scale out a DolphinDB cluster

## 1. Introduction

This tutorial introduces how to scale out a DolphinDB cluster in order to increase its storage capacity and computing power. 

## 2. About a DolphinDB Cluster

A DolphinDB cluster consists of 3 types of nodes: controller, agent, and data node.
- The controller manages the metadata of a cluster and provides the web cluster management interface. 
  The controller has 3 core configuration files:
    - controller.cfg : the configuration parameters for the controller node, such as IP address, port number, the maximum number of connections, etc.
    - cluster.nodes : a list of nodes of the cluster. The controller node uses this file to get information of the cluster nodes.
    - cluster.cfg : personalized configuration of each node in the cluster, such as the volume attribute of a particular node.
- An agent is deployed on each physical machine and is responsible for starting and stopping local data nodes. The configuration file on the Agent is as follows
    - agent.cfg: Defines the properties of the proxy node, such as the proxy node IP and port, the cluster's controller node, etc.
- Data dodes for computing, querying, and data storing.

To add a new physical machine to a cluster, we need to take the following steps:
- Deploy an agent on the new server and configure the agent.cfg
- Register new Data Node information and Agent information with the Controller
- Restart the controller and all data nodes

To expand the storage space of an existing data node, we can modify the node configuration file of the node to add a path to the `volume` attribute.

## 3. Expand Data Nodes

In the example below, we add a new physical server to a cluster, and we deploy a data node on this new physical server.

Add new physical machine IP
```
172.18.0.14
```

The IP address, port number, and the unique alias name in the cluster.
```
172.18.0.14:8804:datanode4
```
The configuration of the original cluster is as follows:

controller.cfg
```
localSite=172.18.0.10:8990:ctl8990
```
cluster.nodes
```
localSite,mode
172.18.0.11:8701:agent1,agent
172.18.0.12:8701:agent2,agent
172.18.0.13:8701:agent3,agent
172.18.0.11:8801:node1,datanode
172.18.0.12:8802:node2,datanode
172.18.0.13:8803:node3,datanode
```
Start Controller
```
nohup ./dolphindb -console 0 -mode controller -script dolphindb.dos -config config/controller.cfg -logFile log/controller.log -nodesFile config/cluster.nodes &
```
Start Agent
```
./dolphindb -mode agent -home data -script dolphindb.dos -config config/agent.cfg -logFile log/agent.log
```

In order to verify the effect after the expansion work is completed, we create a partitioned database in the cluster and write the initial data.
```
data = table(1..1000 as id,rand(`A`B`C,1000) as name)
// we increase the partition range to 2000 to leave space for the subsequent writing task.
db = database("dfs://scaleout_test_db",RANGE,cutPoints(1..2000,10))
tb = db.createPartitionedTable(data,"scaleoutTB",`id)
tb.append!(data)
```
After the execution, you can navigate the generated data through the dfs explorer of the cluster web interface.

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp1.PNG?raw=true)

After the completion of the node and storage extensions, we append the data in the same way to verify that the new node and storage are enabled.

> * For the cluster initial configuration, please refer to [multi-physical deployment cluster tutorial] (https://github.com/dolphindb/Tutorials_CN/blob/master/multi_machine_cluster_deploy.md)*



### 3.1 Configure Agent

The agent on the original server is deployed in the /home/<DolphinDBRoot> directory, copy the files in the directory to the /home/<DolphinDBRoot> directory of the new machine, and modify /home/<DolphinDBRoot>/config/agent.cfg

```
#Specify the ip and port of the agent itself
localSite=172.18.0.14:8701:agent4
#Specify the controller position of this cluster
controllerSite=172.18.0.10:8990:ctl8990
Mode=agent
```

### 3.2 Configure Controller


Modify file cluster.nodes to configure the newly added Data Node and Agent

```
localSite,mode
172.18.0.11:8701:agent1,agent
172.18.0.12:8701:agent2,agent
172.18.0.13:8701:agent3,agent
172.18.0.11:8801:node1,datanode
172.18.0.12:8802:node2,datanode
172.18.0.13:8803:node3,datanode

#newly added agent and data node
172.18.0.14:8704:agent4,agent
172.18.0.14:8804:node4,datanode
```

#### 3.3 Restart the cluster

To make newly added data node and storage take effect, we need to restart the entire cluster, including the cluster controller and all Data Nodes.

- Access the cluster web management interface ```http://172.18.0.10:8990``` to close all data nodes.

 ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/controller_stopAll.PNG?raw=true)

- Execute ```pkill dolphindb``` on the 172.18.0.10 server to shut down the Controller.
- After waiting for half a minute (waiting for the port to be released, depending on the operating system), restart the Controller again.

- Back to the web management interface, you can see that an agent4 has been added and is started. All data nodes are started on the web interface.

 ![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/Controller_StartAll.PNG?raw=true)

At this point we have completed the addition of new nodes.

### 3.4 Verification

Let's verify that node4 is already enabled in the cluster by writing some data to the cluster.
```
Tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
Tb.append!(table(1001..1500 as id,rand(`A`B`C,500) as name))
```
Looking at the dfs explorer, you can see that the data has been distributed to the new node4 node.

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/scale_dfs_exp2.PNG?raw=true)

### 3.5. Data distribution mechanism after extending data nodes

In a cluster of popular MPP architectures, after adding nodes, some data must be resharding, because the hash value changes, and it usually takes a long time to perform resharding on big amount of data.
The data storage of DolphinDB is based on the underlying distributed file system, and the data copy is managed by metadata. Therefore, after the node is expanded, the original data does not need to be resharding, 
and the newly added data is saved to the new node according to the distribution policy. 

Of course, data distribution can be made more evenly distributed, and DolphinDB is developing such a tool.

## 4. Extended storage

Due to insufficient disk space on the server where node3 is located, a disk has been expanded with the path /dev/disk2, which is included in the storage of node3.

### 4.1 Steps

The node storage of DolphinDB can be configured through the volumes attribute in the configuration file. In the case above, if there is no configuration, 
the default storage path will be <HomeDir>/<Data Node Alias>/Storage. In this case, it is under /home/server/data/node3/storage.

> If you add a disk from the default path, you must explicitly set the original default path when setting the volumes property.
Otherwise, the metadata will be lost in the default path.


The default volume attribute is as follows. If there is no such line, you need to add it manually.

cluster.cfg
```
node3.volumes=/home/server/data/node3/storage 
```

To add the new disk path /dev/disk2/node3 to the node3 node, just separate the new path with a comma after the above configuration.

cluster.cfg
```
node3.volumes=/home/server/data/node3/storage,/dev/disk2/node3
```


After modifying the configuration file, execute loadClusterNodesConfigs() on the controller to reload the node configuration. If the above steps are completed on the cluster management web interface, the overload process will be completed automatically without manual execution.
After the configuration is complete, there is no need to restart the controller. Just restart the node3 node on the web interface to make the new configuration take effect.

>
If you want node3 not to restart, but the new storage will take effect immediately, you can add variables by executing function addVolumes("/dev/disk2/node3") on node3. However, the effect of this function will not be persisted unless you configure as above.

### 4.2 Verfication

After the configuration is complete, write the new data to the cluster through the following statement to see if the data is written to the new disk.
```
tb = database("dfs://scaleout_test_db").loadTable("scaleoutTB")
tb.append!(table(1501..2000 as id,rand(`A`B`C,500) as name))
```
Observed data has been written to the disk:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/scaleout/3.PNG?raw=true)



