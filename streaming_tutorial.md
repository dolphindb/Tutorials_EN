# DolphinDB Streaming Tutorial

Data streaming is the continuous transfer of data at a high-speed rate. 

The advantages of DolphinDB streaming system over other streaming systems are:
- High throughput and low latency
- One-stop solution that integrates time series database and data warehouse
- Natural support of stream-table duality and SQL statements

DolphinDB streaming system provides numerous convenient features, such as:
- Built-in time-series and cross sectional aggregators
- High frequency data replay
- Streaming data filtering

This tutorial will cover the following topics about streaming:
- Flowchart and related concepts
- Core functionalities
- Java API
- Status monitoring
- Performance tuning
- Visualization

### 1. Flowchart and related concepts

Streaming in DolphinDB is based on the publish-subscribe model. Streaming data is injected into and published by a streaming table. A data node or a third-party application can subscribe to and consume the streaming data through DolphinDB script or API.

![image](images/DolphinDB_Streaming_Framework.jpg)

The figure above is the DolphinDB streaming flowchart. After injecting real-time data into a streaming table on a publishing node, the data can be subscribed by various types of parties:
- Streaming data can be subscribed and saved by the data warehouse for further analysis and reporting.
- Streaming data can be subscribed by the aggregation engine to perform aggregate calculations and to output the results to another streaming table. The aggregation results can be displayed in real time in a platform such as Grafana and can also serve as a data source for event processing by another subscription.
- Streaming data can be subscribed by an API. For example, a third-party Java application can subscribe to streaming data with Java API.

#### 1.1 Streaming table

Streaming table is a type of in-memory table that stores streaming data and supports concurrent reading and writing. Publishing a message is equivalent to inserting a record into a streaming table. SQL statements can be used on streaming tables.

#### 1.2 Publish-subscribe
Streaming in DolphinDB uses the classic publish-subscribe model. When new data is written to a streaming table, the publisher notifies all subscribers to process the new streaming data. A data node uses function `subscribeTable` to subscribe to the streaming data.

#### 1.3 Real-time aggregation engine

The real-time aggregation engine refers to a module dedicated to real-time calculation and analysis of streaming data. DolphinDB provides function `createStreamAggregator` for continuous real-time calculation with streaming data. It continuously outputs the results to the specified table. 

### 2. Core functionalities

To enable the streaming module, the following configurations parameters need to be specified.

Configuration parameters required for the publishing node:
```
maxPubConnections: the maximum number of connections of a publishing node. If maxPubConnections>0，the node is a publishing node. The default value is 0.
persisitenceDir: the folder path where the shared streaming table is saved. This parameter must be specified to save the streaming table.
persistenceWorkerNum: the number of worker threads responsible for saving the streaming table in asynchronous mode. The default value is 0.
maxPersistenceQueueDepth: the maximum depth (number of records) of the message queue when the streaming table is saved in asynchronous mode. The default value is 10,000,000.
maxMsgNumPerBlock: the maximum number of records in a message block. The default value is 1024.
maxPubQueueDepthPerSite: the maximum depth (number of records) of the message queue at a publishing node. The default value is 10,000,000.
```

Configuration parameters required for the subscribing nodes:
```
subPort: subcription port number. It is required for a subscribing node. The default value is 0.
subExecutors: the number of message processing threads in a subscribing node. The default value is 0, which indicates that the parsing message thread also processes the message.
maxSubConnections: the maximum number of subscription connections a data node can have. The default value is 64.
subExecutorPooling: a Boolean value indicating whether the streaming threads are in pooling mode. The default value is false.
maxSubQueueDepth: the maximum depth (number of records) of the message queue at a subscribing node. The default value is 10,000,000.
```
#### 2.1 Publish streaming data

Use function `streamTable` to define a streaming table. Writing data to it means publishing data. Since a streaming table needs to be accessed by multiple sessions, the streaming table must be shared with command `share`. Streaming tables that are not shared cannot publish data.

Define and share the streaming table "pubTable":
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
```

#### 2.2 Subscribe to streaming data

Use function [`subscribeTable`](https://www.dolphindb.com/help/subscribeTable.html) to subscribe to streaming data. 

Syntax of function `subscribeTable`:
```
subscribeTable([server], tableName, [actionName], [offset=-1], handler, [msgAsTable=false], [batchSize=0], [throttle=1], [hash=-1], [reconnect=false], [filter])
```

Only parameters 'tableName' and 'handler' are required. All other parameters are optional.

- server: a string indicating the alias or the remote connection handle of a server where the streaming table is located. If it is unspecified or an empty string (""), it means the local instance.

There are 3 possibilities regarding the locations of the publisher and the subscriber: 

1. Publisher and subscriber are on the same local data node：use empty string ("") for 'server' or leave it unspecified. 
```
subscribeTable(, "pubTable", "actionName", 0, subTable, true)
```
2. Publisher and subscriber are not on the same data node but in the same cluster: use the publisher node's alias for 'server'.
```
subscribeTable("NODE2", "pubTable", "actionName", 0, subTable, true)
```
3. The publisher is not in the same cluster as the subscriber: use the remote connection handle of the publisher node for 'server'.
```
pubNodeHandler=xdb("192.168.1.13",8891)
subscribeTable(pubNodeHandler, "pubTable", "actionName", 0, subTable, true)
```
- tableName: a string indicating the shared streaming table name.
```
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable
subscribeTable(, "pubTable", "actionName", 0, subTable, true)
```
- actionName: a string indicating the subscription task name. It can have letters, digits and underscores. 
```
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable
topic1 = subscribeTable(, "pubTable", "actionName_realtimeAnalytics", 0, subTable, true)
topic2 = subscribeTable(, "pubTable", "actionName_saveToDataWarehouse", 0, subTable, true)
```
Function `subscribeTable` returns the subscription topic. It is the combination of the alias of the node where the streaming table is located, the name of the streaming table, and the subscription task name (if 'actionName' is specified), separated by forward slash "/". If the local node alias is NODE1, the two topics returned by the example above are as follows:

topic1:
```
NODE1/pubTable/actionName_realtimeAnalytics
```
topic2:
```
NODE1/pubTable/actionName_saveToDataWarehouse
```
- offset：an integer indicating the position of the first message where the subscription begins. If it is unspecified, or is negative, or exceeds the number of rows in the streaming table, the subscription will start from the current row of the streaming table. The value of 'offset' always corresponds to the first row when the streaming table was created. If some rows are deleted due to cache size limit, they are still taken into account when deciding where to start the subscription.
- 
The following example illustrates the role of 'offset'. We write 100 rows of data to 'pubTable' and create 3 subscriptions topics:
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable3
vtimestamp = 1..100
vtemp = norm(2,0.4,100)
tableInsert(pubTable,vtimestamp,vtemp)
topic1 = subscribeTable(, "pubTable", "actionName1", 102,subTable1, true)
topic1 = subscribeTable(, "pubTable", "actionName2", -1, subTable2, true)
topic1 = subscribeTable(, "pubTable", "actionName3", 50,subTable3, true)
```
subTable1 and subTable2 are empty; 'subTable3' has 50 rows. When 'offset' is negative or exceeds the number of rows in the streaming table, the subscription will start from the current row, and the subscription returns nothing until new data enters the streaming table.

- handler: a unary function or a table. It is used to process the subscribed data. The function only has one parameter which is the subscribed data, which can be a table (the subscribed table) or a tuple of the subscribed table columns. Quite often we need to insert the subscribed data into a table. For this purpose handler can also be a table, and the subscribed data will be inserted into the handler table directly.

The following example shows two uses of 'handler'. SubTable1 directly writes the subscribed data to the target table; subTable2 filters and writes the data with the user-defined function `myHandler`.
```
def myhandler(msg){
	t = select * from msg where temperature>0.2
	if(size(t)>0)
		subTable2.append!(t)
}
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
topic1 = subscribeTable(, "pubTable", "actionName1", -1, subTable1, true)
topic1 = subscribeTable(, "pubTable", "actionName2", -1, myhandler, true)

vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)
```
From the result, it can be seen that pubTable writes 10 records of data, subTable1 receives all, subTable2 is filtered by myhandler, and 9 pieces of data are received (0.13 is filtered).

- msgAsTable： a Boolean value indicating whether the subscribed data is a table. The default value is false, which means that the subscription data is a tuple of columns.

The following example shows the difference in the subscription data format:
```

def myhandler1(table){
	subTable1.append!(table)
}
def myhandler2(tuple){
	tableInsert(subTable2,tuple[0],tuple[1])
}
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
//msgAsTable = true
topic1 = subscribeTable(, "pubTable", "actionName1", -1, myhandler1, true)
//msgAsTable = false
topic2 = subscribeTable(, "pubTable", "actionName2", -1, myhandler2, false)

vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)
```
- batchSize：an integer indicating the number of messages for batch processing. If it is positive, the handler does not process incoming messages until their number reaches batchSize. If it is unspecified or non-positive, the handler processes the incoming messages as soon as they come in.

In the following example, `batchSize` is set to 11. 
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
topic1 = subscribeTable(, "pubTable", "actionName1", -1, subTable1, true, 11)
vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)

print size(subTable1)
```
10 rows were written to pubTable. Now the subscribing table is empty. 

```
insert into pubTable values(11,3.1)
print size(subTable1)
```
Now 1 more row was written to pubTable. We can see from the result the subscribing table has 11 records. 

- throttle：An integer that represents the amount of time, in seconds, that the handler waits before processing incoming messages. The default is 1. If you don't specify a batchSize, the throttle will not work.
- 
'batchSize' and 'throttle' are used for data buffering. If the speed of streaming data overwhelms data consumption capacity of the subscribing nodes, flow control is required. Otherwise, data will accumulate at the buffer on subscribing nodes and may use up memory. We can use 'throttle' to periodically send a batch of data based on the consumption speed of the subscribers to ensure a relatively stable amount of data in the buffer of the subscribing nodes.

- hash：a hash value (a nonnegative integer) indicating which subscription executor will process the incoming messages for this subscription. If it is unspecified, the system automatically assigns an executor. To make multiple subscriptions be processed by the same executor, assign the same hash value to these subscriptions.

- reconnect: a Boolean value indicating whether the subscription may be automatically resumed successfully if it is interrupted. With a successfully resubscription, the subscriber receives all streaming data since the interruption. The default value is false. If reconnect=true, depending on how the subscription is interrupted, we have the following 3 scenarios:

(1)If the network is disconnected while both the publisher and the subscriber node remain on, the subscription will be automatically reconnected if the network connection is resumed.
(2)If the publisher node crashes, the subscriber node will keep attempting to resubscribe after the publisher node restarts.

- If the publisher node adopts data persistence mode for the streaming table, the publisher will first load persisted data into memory after restarting. The subscriber won't be able to successfully resubscribe until the publisher reaches the row of data where the subscription was interrupted.

- If the publisher node does not adopt data persistence mode for the streaming table, the automatic resubscription will fail.

(3)If the subscriber node crashes, even after the subscriber node restarts, it won't automatically resubscribe. For this case we need to execute subscribeTable again.

When both the publisher and the subscriber nodes are relatively stable with routine tasks, such as in IoT applications, we recommend setting reconnect=true. On the other hand, if the subscriber node is tasked with complicated queries with large amounts of data, we recommend setting reconnect=false.
If we need to use the same thread to process messages for multiple subscription tasks, set 'hash' of all the subscription tasks to the same value. When we need to keep the messages synchronized from multiple subscriptions, we can set 'hash' of all these subscriptions to be the same, so that the same thread will be used to synchronize multiple data sources. 

- filter: a vector of selected values in the filtering column. Only the messages with specified filtering column values are subscribed. The filtering column is set with function [setStreamTableFilterColumn](https://www.dolphindb.com/help/setSystem1.html).


#### 2.3 Unsubscribe

Each subscription is uniquely identified with a subscription topic. If an existing subscription has the same topic as a new subscription, the new subscription will fail. To make a new subscription with the same subscription topic as an existing subscription, we need to cancel the existing subscription with command `unsubscribeTable`. 

Unsubscribe from a local table:
```
unsubscribeTable(,"pubTable","actionName1")
```

Unsubscribe from a remote table:
```
unsubscribeTable("NODE_1","pubTable","actionName1")
```
To delete a shared streaming table, we can use command `undef`:
```
undef("pubStreamTable", SHARED)
```
#### 2.4 Streaming data persistence

By default, the streaming table keeps all data in memory. Streaming data can be persisted to disk based on the following two considerations.
1. Avoid out of memory problems.
2. Backup streaming data. When a node reboots, the persisted data can be automatically loaded into the streaming table.

If the number of rows in the streaming table reaches a preset threshold, the first half of the table will be presisted to disk. The persisted data can be resubscribed, and when subscribing to a specified data subscript, the subscript's calculation contains persisted data.

To initiate streaming data persistence, we need to add a persistence path to the configuration file of the publishing node:
```
persisitenceDir = /data/streamCache
```
Execute command [`enableTablePersistence`](https://www.dolphindb.com/help/enableTablePersistence.html) in the script to enable persistence for streaming tables.

The following example enables persistence for pubTable. When the streaming table reaches 1 million rows, 50% of the rows are compressed to disk asynchronously.

```
enableTablePersistence(pubTable, true, true, 1000000)
```

When `enableTablePersistence` is executed, if the persisted data of pubTable already exists on the disk, then the system will load the latest cacheSize=1000000 line record into the memory.

Whether to enable persistence in asynchronous mode is a trade-off between data consistency and latency. If data consistency is the priority, we should use the synchronous mode. This ensures that data enter the publishing queue after the persistence is completed. On the other hand, if low latency is more important and we don't want disk I/O to affect latency, we should use asynchronous mode. The configuration parameter 'persistenceWorkerNum' only works when asynchronous mode is enabled. With multiple publishing tables to be persisted, increasing the value of 'persistenceWorkerNum' can improve the efficiency of persistence in asynchronous mode.

Persisted data can be deleted with function `clearTablePersistence`.
```
clearTablePersistence(pubTable)
```

When the stream data writing is finished, we can use command [`disableTablePersistence`] (https://www.dolphindb.com/cn/help/disableTablePersistence.html) to turn off persistence.
```
disableTablePersistence(pubTable)
```

### 3. Java API

The consumer of streaming data may be the aggregation engine, or a third-party message queue, or a third-party program. DolphinDB provides streaming API for third-party programs to subscribe to streaming data. When new data arrives, API subscribers receive notifications in a timely manner. This allows DolphinDB streaming modules to be integrated with third-party applications. Currently, DolphinDB provides Java streaming API. We will provide streaming APIs for more languages such as C++ and C# in the near future.

The Java API handles data in two ways: polling and eventHandler.

- Polling method sample code:
```
PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, offset);

while (true) {
   ArrayList<IMessage> msgs = poller1.poll(1000);
   if (msgs.size() > 0) {
         BasicInt value = msgs.get(0).getEntity(2);  // Take the second field in the first row of the data
   }
}
```

Poller1 pulls new data each time the streaming table publishes new data. When no new data is released, the program will block waiting for the poller1.poll method.

The Java API uses pre-configured MessageHandler to get and process new data. First, the caller needs to define the data Handler. The Handler needs to implement the com.xxdb.streaming.client.MessageHandler interface.

- Event mode sample code:
```
public class MyHandler implements MessageHandler {
       public void doEvent(IMessage msg) {
               BasicInt qty = msg.getValue(2);
               //..Message processing
       }
}
```

When the subscription is started, the handler instance is passed as a parameter to the subscription function.
```
ThreadedClient client = new ThreadedClient(subscribePort);
client.subscribe(serverIP, serverPort, tableName, new MyHandler(), offsetInt);
```
Whenever new data is published in the streaming table, the Java API calls the MyHandler method and passes the new data through parameter 'msg'.


### 4. Status monitoring

As streaming calculations are conducted in the background, DolphinDB provides function `getStreamingStat` to monitor streaming. Function `getStreamingStat` returns a dictionary with 4 tables: pubConns, subConns, persistWorkers and subWorkers.

#### 4.1 pubConns

Table pubConns displays the status of the connections between the local publisher node and all of its subscriber nodes. Each row represents a subscriber node.

Column|Description
---|---
Client|IP address and port number of a subscriber node
queueDepthLimit|The maximum depth (number of records) of the message queue that is allowed on the publisher node. There is only one publishing message queue for each publisher node.
queueDepth|Current depth (number of records) of the message queue on the publisher node
Tables|All shared streaming tables in the publisher node, separated by commas.

Run getStreamingStat().pubConns in the GUI to view the contents of the table:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/pubconn.png?raw=true)

The pubConns table lists all the subscription node information, the release queue status, and the stream data table names for the node.

#### 4.2 subConns

Table subConns displays the status of the connections between the local subscriber node and the publisher nodes. Each row is a publisher node that the local node subscribes to.

Column|Description
---|---
Publisher|A publisher node alias
cumMsgCount|The number of messages that have been received
cumMsgLatency|The average latency (in milliseconds) of all received messages. Latency refers to the time it takes for a message from entering the release queue to entering the subscription queue.
lastMsgLatency|The latency (in milliseconds) of the last received message
lastUpdate|The last time a message is received

Run getStreamingStat().subConns in DolphinDB GUI to browse the table:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subconn.png?raw=true)


#### 4.3 persistWorkers

Table persistWorkers monitors the status of workers (threads) responsible for streaming data persistence. Each row represents a worker thread.

Column|Description
---|---
workerId|Worker ID
queueDepthLimit|The maximum depth (number of records) of a message queue that is allowed for table persistence
queueDepth|Current depth (number of records) of the message queue for table persistence
Tables|Names of the persisted tables, separated by commas.

Table persistWorkers can be obtained with function `getStreamingStat` only if persistence is enabled. The number of records of the table is the value of the configuration parameter 'persistenceWorkerNum'. 

The following example runs getStreamingStat().persistWorkers in DolphinDB GUI.

When persistenceWorkerNum=1:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persistworker.png?raw=true)

When persistenceWorkerNum=3:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persisWorders_2.png?raw=true)

To persist multiple tables in parallel, we need to set `persistenceWorkerNum`>1. 

#### 4.4 subWorkers

Table subWorkers displays the status of workers of subscriber nodes responsible for streaming. Each record represents a subscriber worker thread.

Column|Description
---|---
queueDepthLimit|The maximum depth (number of records) of a message queue that is allowed on the subscriber node
queueDepth|Current depth (number of records) of the message queue on the subscriber node
processedMsgCount|The number of messages that have been processed
failedMsgCount|The number of messages that failed to be processed
lastErrMsg|The last error message
Topics|Subscription topics, separated by commas.

The following example shows the results of executing getStreamingStat().subWorkers in DolphinDB GUI with various values of configuration parameters 'subExecutorPooling' and 'subExecutors'.

subExecutorPooling=false, subExecutors=1:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_1.png?raw=true)

The subscribed messages of both tables share the same subscriber worker. 

subExecutorPooling=false, subExecutors=2:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_2.png?raw=true)

The subscribed messages of each table are assigned to a different subscriber worker queue.

subExecutorPooling=true,subExecutors=2:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_pool.png?raw=true)

The subscribed messages of both tables share a thread pool with two threads.

We can monitor the amount of processed messages and other information in this table:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subworker_msg.png?raw=true)

### 5. Performance tuning

If an extremely large amount of streaming data arrive in a short period of time, system performance may suffer. You may see an extremely high value of 'queueDepth' in table subWorkers on the subscriber node. When the message queue depth on the a subscriber node reaches 'queueDepthLimit', new messages from the publisher node are blocked from entering subscriber nodes. This leads to a growing message queue on the publisher node. When the message queue depth of the publisher node reaches 'queueDepthLimit', the system blocks new messages from entering the streaming table on the publisher node.

There are several ways to optimize streaming performance:

1. Adjust parameters 'batchSize' and 'throttle' to balance the cache on the publisher and the subscriber nodes. This can achieve a dynamic balance between streaming data injection speed and data processing speed. To take full advantage of batch processing, we can set 'batchSize' to wait for streaming data to accumulate to a certain amount before consumption. This, however, needs a certain amount of memory usage. If 'batchSize' is too large, it is possible that some data below the threshold of 'batchSize' get stuck in the buffer for a long time. To handle this issue, we can set parameter 'throttle' to consume the buffer data even if 'batchSize' is not met.

2. Increase parallelism by adjusting the configuration parameter 'subExecutors' to speed up message queue processing on the subscriber node. 

3. When each executor processes a different subscription, if there is great difference in throughput of different subscriptions or the complexities of calculation, some executors may idle. If we set subExecutorPooling=true, all executors form a shared thread pool to process all subscribed messages together. All subscribed messages enter the same queue and multiple executors read messages from the queue for parallel processing. With the shared thread pool, however, there is no guarantee that messages will be processed in the order they arrive. Therefore parameter 'subExecutorPooling' should not be turned on when messages need to be processed in the order they arrive. By default, the system uses a hash algorithm to assign an executor to each subscription. If we would like to ensure the messages in two subscriptions are processed by the order as they arrive, we can specify the same value for parameter 'hash' in function `subscribeTable` of the two subscriptions, so that the same executor processes the messages of the two subscriptions.

4. If the streaming table enables synchronous persistence, disk I/O maybe become a bottleneck. One way to handle this is to use the method in section 2.4 to persist data in asynchronous mode while setting up a reasonable persistence queue by specifying 'maxPersistenceQueueDepth' (default 10 million messages). Alternatively, we can also use SSD hard drives to improve write performance.

5. Publisher node maybe become a bottleneck. For example, there may be too many subscribing clients. We can use the following methods to handle this problem. First, we can reduce the number of subscriptions for each publisher node with multi-level cascading. Applications that can tolerate delay can subscribe to secondary or even third tier publisher nodes. Second, some parameters can be adjusted to balance throughput and latency. The parameter 'maxMsgNumPerBlock' sets the size of the messages batches. The default value is 1024. In general, larger batches increase throughput but increase network latency.

6. If the injection speed of streaming data fluctuates greatly and peak periods cause the consumption queue to reach the queue depth limit (default 10 million), then we can modify configuration parameters 'maxPubQueueDepthPerSite' and 'maxSubQueueDepth' to increase the maximum queue depth of the publisher and the subscriber. However, as memory consumption increases as queue depth increases, memory usage should be planned and monitored to properly allocate memory.

### 6. Visualization

Streaming data visualization can be divided into two types:
- Real-time value monitoring: refresh aggregated value of streaming data in rolling window periodically.

- Trend monitoring: generate dynamic chart with newly release data and previous related data.

Various data visualization platforms support real-time monitoring of streaming data, such as the popular open source data visualization framework Grafana. DolphinDB has implemented the interface between the server and client of Grafana. For details, please refer to the tutorial：https://github.com/dolphindb/grafana-datasource/blob/master/README.md
