# Tutorial: Stream for DolphinDB

The advantages of Stream for DolphinDB over other streaming analytics systems are:
- High throughput and low latency
- One-stop solution that is seamlessly integrated with time-series database and data warehouse
- Natural support of stream-table duality and SQL statements

Stream for DolphinDB provides numerous convenient features, such as:
- Built-in time-series, cross-sectional and anomaly detection aggregators
- High frequency data replay
- Streaming data filtering

This tutorial will cover the following topics:
- Flowchart and related concepts
- Core functionalities
- Replay
- API
- Status monitoring
- Performance tuning
- Visualization

### 1. Flowchart and related concepts

Stream for DolphinDB is based on the publish-subscribe model. Streaming data is ingested into and published by a stream table. A data node or a third-party application can subscribe to and consume the streaming data through DolphinDB script or API.

![image](images/DolphinDB_Streaming_Framework.jpg)

The figure above is the DolphinDB streaming flowchart. Real-time data is ingested into a stream table on a publisher node. The streaming data can be subscribed by various types of objects:
- Streaming data can be subscribed and saved by the data warehouse for further analysis and reporting.
- Streaming data can be subscribed by an aggregation engine to perform calculations and to output the results to another stream table. The aggregation results can be displayed in real time in a platform such as Grafana and can also serve as a data source for event processing by another subscription.
- Streaming data can be subscribed by an API. For example, a third-party Java application can subscribe to streaming data with Java API.

#### 1.1 Stream table

Stream table is a special type of in-memory table to store and publish streaming data. Stream table supports concurrent read and write. We can append to stream tables, but cannot delete or modify the records of stream tables. Publishing a message is equivalent to inserting a record into a stream table. SQL statements can be used on stream tables.

#### 1.2 Publish-subscribe

Stream for DolphinDB uses the classic publish-subscribe model. When new data is written to a stream table, the publisher notifies all subscribers to process the new data. A data node uses function `subscribeTable` to subscribe to the streaming data.

#### 1.3 Real-time aggregation engine

The real-time aggregation engine refers to a module dedicated to real-time calculation and analysis of streaming data. DolphinDB provides functions `createTimeSeriesAggregator` and `createCrossSectionalAggregator` for continuous real-time calculation with streaming data. The results are continuously output to the specified tables. 

### 2. Core functionalities

To enable the streaming module, the following configuration parameters need to be specified.

Configuration parameters required for the publisher node:

- maxPubConnections: the maximum number of subscriber nodes that the publisher can connect to. If maxPubConnections>0，the node is a publisher node. The default value is 0.
- persisitenceDir: the folder path where the shared stream table is saved. This parameter must be specified to save the stream table.
- persistenceWorkerNum: the number of worker threads responsible for saving the stream table in asynchronous mode. The default value is 0.
- maxPersistenceQueueDepth: the maximum depth (number of records) of the message queue when the stream table is saved in asynchronous mode. The default value is 10,000,000.
- maxMsgNumPerBlock: the maximum number of records in a message block. The default value is 1024.
- maxPubQueueDepthPerSite: the maximum depth (number of records) of the message queue at the publisher node. The default value is 10,000,000.


Configuration parameters required for the subscriber nodes:

- subPort: subcription port number. It is required for a subscriber node. The default value is 0.
- subExecutors: the number of message processing threads in the subscriber node. The default value is 0, which indicates that the parsing message thread also processes the message.
- maxSubConnections: the maximum number of publishers that the subscriber node can connec to. The default value is 64.
- subExecutorPooling: a Boolean value indicating whether the streaming threads are in pooling mode. The default value is false.
- maxSubQueueDepth: the maximum depth (number of records) of the message queue at the subscriber node. The default value is 10,000,000.

#### 2.1 Publish streaming data

Use function `streamTable` to define a stream table. Writing data to it means publishing data. Since for any publisher there are usually multiple subscribers in multiple sessions, a stream table must be shared with command `share` before it can publish streaming data. Stream tables that are not shared cannot publish streaming data.

Define and share the stream table "pubTable":
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
```

#### 2.2 Subscribe to streaming data

Use function [`subscribeTable`](https://www.dolphindb.com/help/subscribeTable.html) to subscribe to streaming data. 

Syntax of function `subscribeTable`:
```
subscribeTable([server],tableName,[actionName],[offset=-1],handler,[msgAsTable=false],[batchSize=0],[throttle=1],[hash=-1],[reconnect=false],[filter],[persistOffset=false])
```
Only parameters 'tableName' and 'handler' are required. All other parameters are optional.

- server: a string indicating the alias or the remote connection handle of a server where the stream table is located. If it is unspecified or an empty string (""), it means the local instance.

There are 3 possibilities regarding the locations of the publisher and the subscriber: 

1. Publisher and subscriber are on the same local data node: use empty string ("") for 'server' or leave it unspecified. 
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
- tableName: a string indicating the shared stream table name.
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
Function `subscribeTable` returns the subscription topic. It is the combination of the alias of the node where the stream table is located, the stream table name, and the subscription task name (if 'actionName' is specified), separated by forward slash "/". If the local node alias is NODE1, the two topics returned by the example above are as follows:

topic1:
```
NODE1/pubTable/actionName_realtimeAnalytics
```
topic2:
```
NODE1/pubTable/actionName_saveToDataWarehouse
```
- offset: an integer indicating the position of the first message where the subscription begins. A message is a row of the stream table. The offset is relative to the first row of the stream table when it is created. If offset is unspecified, or -1, or above the number of rows of the stream table, the subscription starts with the next new message. If offset=-2, the system will get the persisted offset on disk and start subscription from there. If some rows were cleared from memory due to cache size limit, they are still considered in determining where the subscription starts.

The following example illustrates the role of 'offset'. We write 100 rows to 'pubTable' and create 3 subscription topics:
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable2
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable3
vtimestamp = 1..100
vtemp = norm(2,0.4,100)
tableInsert(pubTable,vtimestamp,vtemp)
topic1 = subscribeTable(, "pubTable", "actionName1", 102, subTable1, true)
topic1 = subscribeTable(, "pubTable", "actionName2", -1, subTable2, true)
topic1 = subscribeTable(, "pubTable", "actionName3", 50, subTable3, true)
```
subTable1 and subTable2 are empty and subTable3 has 50 rows. When 'offset' is negative or exceeds the number of rows in the stream table, the subscription will start from the current row, and the subscription returns nothing until new data enters the stream table.

- handler: a unary function or a table. It is used to process the subscribed data. The function only has one parameter which is the subscribed data. The subscribed data can be a table (the subscribed table) or a tuple of the subscribed table columns. Quite often we need to insert the subscribed data into a table. For this purpose 'handler' can also be a table, and the subscribed data will be inserted into the handler table directly.

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
The result shows that 10 messages are written to pubTable. SubTable1 receives all of them whereas subTable2 receives 9 messages as the row with vtemp=0.13 is filtered by `myhandler`.

- msgAsTable: a Boolean value indicating whether the subscribed data is a table. The default value is false, which means that the subscribed data is a tuple of columns.

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

- batchSize: an integer indicating the number of messages to trigger batch processing. If it is positive, the handler does not process incoming messages until their number reaches 'batchSize'. If it is unspecified or non-positive, the handler processes the incoming messages as soon as they come in.

In the following example, 'batchSize' is set to 11. 
```
share streamTable(10000:0,`timestamp`temperature, [TIMESTAMP,DOUBLE]) as pubTable
share streamTable(10000:0,`ts`temp, [TIMESTAMP,DOUBLE]) as subTable1
topic1 = subscribeTable(, "pubTable", "actionName1", -1, subTable1, true, 11)
vtimestamp = 1..10
vtemp = 2.0 2.2 2.3 2.4 2.5 2.6 2.7 0.13 0.23 2.9
tableInsert(pubTable,vtimestamp,vtemp)

print size(subTable1)
```
10 messages are written to pubTable. Now the subscribing table subTable1 is empty. 

```
insert into pubTable values(11,3.1)
print size(subTable1)
```
Now 1 more message is written to pubTable. Now the subscribing table subTable1 has 11 records. 

- throttle: an integer indicating the maximum waiting time (in seconds) before the handler processes the incoming messages. The default value is 1. This optional parameter has no effect if 'batchSize' is not specified. 

'batchSize' and 'throttle' are used for data buffering. If the speed of streaming data overwhelms data consumption capacity of the subscriber nodes, flow control is required. Otherwise, data will accumulate at the buffer on subscriber nodes and may use up memory. We can use 'throttle' to periodically send a batch of data based on the consumption speed of the subscribers to ensure a relatively stable amount of data in the buffer of the subscriber nodes.

- hash: a hash value (a nonnegative integer) indicating which subscription executor will process the incoming messages for this subscription. If it is unspecified, the system automatically assigns an executor. When we need to keep the messages synchronized from multiple subscriptions, we can set 'hash' of all these subscriptions to be the same, so that the same executor is used to synchronize multiple data sources. 

- reconnect: a Boolean value indicating whether the subscription may be automatically resumed successfully if it is interrupted. With a successfully resubscription, the subscriber receives all streaming data since the interruption. The default value is false. If reconnect=true, depending on how the subscription is interrupted, we have the following 3 scenarios:

(1) If the network is disconnected while both the publisher and the subscriber node remain on, the subscription will be automatically reconnected if the network connection is resumed.

(2) If the publisher node crashes, the subscriber node will keep attempting to resubscribe after the publisher node restarts.

If the publisher node adopts data persistence mode for the stream table, the publisher will first load persisted data into memory after restarting. The subscriber won't be able to successfully resubscribe until the publisher reaches the row of data where the subscription was interrupted. If the publisher node does not adopt data persistence mode for the stream table, the automatic resubscription will fail.

(3) If the subscriber node crashes, even after the subscriber node restarts, it won't automatically resubscribe. For this case we need to execute function `subscribeTable` again.

When both the publisher and the subscriber nodes are relatively stable with routine tasks, such as in IoT applications, we recommend setting reconnect=true. On the other hand, if the subscriber node is tasked with complicated queries with large amounts of data, we recommend setting reconnect=false.

- filter: a vector of values in the filtering column. Only the messages with specified filtering column values are subscribed. The filtering column is set with function [`setStreamTableFilterColumn`](https://www.dolphindb.com/help/setSystem1.html).

- persistOffset: a Boolean value indicating whether to persist the offset of the last processed message in the current subscription. It is used for resubscription and can be obtained with function `getTopicProcessedOffset`. The default value is false. 

#### 2.3 Automatic reconnection

To enable automatic reconnection after network disruption, the stream table must be persisted on the publisher. Please refer to section 2.6 for enabling persistence. When parameter 'reconnect' is set to true, the subscriber will record the offset of the streaming data. When the network connection is interrupted, the subscriber will automatically resubscribe from the offset. If the subscriber crashes or the stream table is not persisted on the publisher, the subscriber cannot automatically reconnect.

#### 2.4 Filtering of streaming data

Streaming data can be filtered at the publisher to significantly reduce network traffic. Use command `setStreamTableFilterColumn` on the stream table to specify the filtering column, then specify a vector for parameter 'filter' in function `subscribeTable`. Only the rows with filtering column values in vector 'filter' are published to the subscriber. As of now a stream table can have only one filtering column. In the following example, the stream table 'trades' on the publisher only publishes data for 'IBM' and 'GOOG' to the subscriber:

```
share streamTable(10000:0,`time`symbol`price, [TIMESTAMP,SYMBOL,INT]) as trades
setStreamTableFilterColumn(trades, `symbol)
trades_slave=table(10000:0,`time`symbol`price, [TIMESTAMP,SYMBOL,INT])

filter=symbol(`IBM`GOOG)

subscribeTable(, `trades,`trades_slave,,append!{trades_slave},true,,,,,filter)
```
#### 2.5 Unsubscribe

Each subscription is uniquely identified with a subscription topic. If a new subscription has the same topic as an existing subscription, the new subscription cannot be established. To make a new subscription with the same subscription topic as an existing subscription, we need to cancel the existing subscription with command `unsubscribeTable`. 

Unsubscribe from a local table:
```
unsubscribeTable(,"pubTable","actionName1")
```
Unsubscribe from a remote table:
```
unsubscribeTable("NODE_1","pubTable","actionName1")
```
To delete a shared stream table, use command `undef`:
```
undef("pubStreamTable", SHARED)
```
#### 2.6 Streaming data persistence

By default, the stream table keeps all streaming data in memory. Streaming data can be persisted to disk for the following 3 reasons:
1. Mitigate out-of-memory problems.
2. Backup streaming data. When a node reboots, the persisted data can be automatically loaded into the stream table.
3. Resubscribe from any position. 

If the number of rows in the stream table reaches a preset threshold, the first half of the table will be persisted to disk. The persisted data can be resubscribed. 

To initiate streaming data persistence, we need to add a persistence path to the configuration file of the publisher node:
```
persisitenceDir = /data/streamCache
```
Execute command [`enableTablePersistence`](https://www.dolphindb.com/help/enableTablePersistence.html) to enable persistence for stream tables.

The following example enables persistence for pubTable. When the stream table reaches 1 million rows, the first half of them are compressed to disk asynchronously.
```
enableTablePersistence(pubTable, true, true, 1000000)
```

After `enableTablePersistence` is executed, if the persisted data of pubTable already exists on the disk, the system will load the latest cacheSize=1000000 rows into the memory.

Whether to enable persistence in asynchronous mode is a trade-off between data consistency and latency. If data consistency is the priority, we should use the synchronous mode. This ensures that data enters the publishing queue after the persistence is completed. On the other hand, if low latency is more important and we don't want disk I/O to affect latency, we should use asynchronous mode. The configuration parameter 'persistenceWorkerNum' only works when asynchronous mode is enabled. With multiple publishing tables to be persisted, increasing the value of 'persistenceWorkerNum' can improve the efficiency of persistence in asynchronous mode.

Persisted data can be deleted with command `clearTablePersistence`.
```
clearTablePersistence(pubTable)
```

To turn off persistence, use command [`disableTablePersistence`](https://www.dolphindb.com/cn/help/disableTablePersistence.html).
```
disableTablePersistence(pubTable)
```

Use function `getPersistenceMeta` to get detailed information regarding the persistence of a stream table:
```
getPersistenceMeta(pubTable);
```
The result is a dictionary with the following keys:
```
//The number of rows in memory:
sizeInMemory->0
//Whether asynchronous mode is enabled:
asynWrite->true
//The total number of rows of the stream table:
totalSize->0
//Whether the data is persisted with compression:
compress->true
//The offset of data in memory relative to the total number of rows. memoryOffset = totalSize - sizeInMemory. 
memoryOffset->0
//The number of rows that have been persisted to disk:
sizeOnDisk->0
//How long the log file will be kept in terms of minutes. The default value is 1440 minutes (one day).
retentionMinutes->1440
//The path where the persisted data is saved
persistenceDir->/hdd/persistencePath/pubTable
//hashValue is the identifier of the worker for persistence of the stream table.
hashValue->0
//The offset of the first of the persisted streaming messages on disk relative to the entire stream table. 
diskOffset->0
```
### 3. Data Replay

DolphinDB provides function `replay` to replay historical data like live trading data. For details please refer to [Data Replay Tutorial](historical_data_replay.md). 

### 4. Streaming API

The consumer of streaming data may be an aggregation engine, a third-party message queue, or a third-party program. DolphinDB provides streaming API for third-party programs to subscribe to streaming data. When new data arrives, API subscribers receive notifications in a timely manner. This allows DolphinDB streaming modules to be integrated with third-party applications. Currently, DolphinDB provides Java, Python, C++ and C# streaming API.

#### 4.1 Java API

Java API handles data in two ways: polling and eventHandler.

1. Polling method sample code:
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

Poller1 pulls new data when the stream table publishes new data. When no new data is published, the program will wait at the poller1.poll method.

The Java API uses pre-configured MessageHandler to get and process new data. First, the caller needs to define the Handler. The Handler needs to implement the com.xxdb.streaming.client.MessageHandler interface.

2. Event mode sample code:
```
public class MyHandler implements MessageHandler {
       public void doEvent(IMessage msg) {
               BasicInt qty = msg.getValue(2);
               //..Message processing
       }
}
```

When the subscription is initiated, the handler instance is passed as a parameter to the subscription function.
```
ThreadedClient client = new ThreadedClient(subscribePort);
client.subscribe(serverIP, serverPort, tableName, new MyHandler(), offsetInt);
```
Whenever new data is published by the stream table, the Java API calls the MyHandler method and passes the new data through parameter 'msg'.

3. Reconnection

The parameter 'reconnect' is a Boolean value indicating whether to automatically reconnect after a network disconnection. The default value is false. 

Parameter 'reconnect' is set to true in the following example.

```
PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, offset, true);
```

4. Filtering

The parameter 'filter' is a vector. Use `setStreamTableFilterColumn` on the publisher node to specify the filtering column of the stream table. Only the rows with values of the filtering column in the vector specified by the parameter 'filter' are published to the subscriber. 

In the following example, parameter 'filter' takes the value of an integer vector with 1 and 2. 

```
BasicIntVector filter = new BasicIntVector(2);
filter.setInt(0, 1);
filter.setInt(1, 2);

PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, actionName, offset, filter);
```

#### 4.2 Python API

Please note that right now only [Python API](https://github.com/dolphindb/python3_api_experimental) supports streaming.

1. Specify the subscriber port number

```
import dolphindb as ddb
conn = ddb.session()
conn.enableStreaming(8000)
```

2. Call function `subscribe`

Use function `subscribe` in Python API to subscribe to stream tables in DolphinDB. 

Syntax of function `subscribe`:
```
conn.subscribe(host, port, handler, tableName, actionName="", offset=-1, resub=False, filter=None)
```
- host is the IP address of the publisher node. 
- port is the port number of the publisher node.
- handler is a user-defined function to process the subscribed data. 
- tableName is a string indicating the name of the publishing stream table. 
- actionName is a string indicating the name of the subscription task. 
- offset is an integer indicating the position of the first message where the subscription begins. A message is a row of the stream table. Offset is relative to the first row of the stream table when it is created. If offset is unspecified, or -1, or above the number of rows of the stream table, the subscription starts with the next new message. If some rows were cleared from memory due to cache size limit, they are still considered in determining where the subscription starts.
- resub is a Boolean value indicating whether to resubscribe after network disconnection.
- filter is a vector indicating filtering condition. Only the rows with values of the filtering column in the vector specified by the parameter 'filter' are published to the subscriber. 

Example: Create a shared stream table 'trades' in DolphinDB and insert data into the table.
```
share streamTable(1:0,`id`price`qty,[INT,DOUBLE,INT]) as trades
trades.append!(table(1..10 as id,rand(10.0,10) as price,rand(10,10) as qty))
```

Subscribe to table 'trades' in Python:
```
def printMsg(msg):
    print(msg)

conn.subscribe("192.168.1.103", 8941, printMsg, "trades", "sub_trades", 0)

[1, 0.47664969926699996, 8]
[2, 5.543625105638057, 4]
[3, 8.10016839299351, 4]
[4, 5.821204076055437, 9]
[5, 9.768875930458307, 0]
[6, 3.7460641632787883, 7]
[7, 2.4479272053577006, 6]
[8, 9.394394161645323, 5]
[9, 5.966209815815091, 6]
[10, 0.03534660907462239, 2]

```

3. Unsubscribe

Use `conn.unsubscribe` to unsubscribe. 

Syntax of `conn.unsubscribe`:
```
conn.unsubscribe(host,port,tableName,actionName="")
```
Unsubscribe in the example of the previous section:
```
conn.unsubscribe(192.168.1.103", 8941,"sub_trades")
```

#### 4.3 C++ API

There are 3 ways for a C++ API to process streaming data: ThreadedClient, ThreadPooledClient and PollingClient.

#### 4.3.1 ThreadedClient

Each time the stream table publishes new messages, a single thread acquires and processes the messages.

1. Create an instance of ThreadedClient 
```
ThreadedClient::ThreadClient(int listeningPort);
```
- listeningPort is the port number on the subscriber node. 

2. Call function `subscribe`:
```
ThreadSP ThreadedClient::subscribe(string host, int port, MessageHandler handler, string tableName, string actionName = DEFAULT_ACTION_NAME, int64_t offset = -1);
```
- host is the IP address of the publisher node. 
- port is the port number of the publisher node.
- handler is a user-defined function to process the subscribed data. The signature of the message handler is void(Message) where Message is a row. 
- tableName is a string indicating the name of the publishing stream table. 
- actionName is a string indicating the name of the subscription task. 
- offset is an integer indicating the position of the first message where the subscription begins. A message is a row of the stream table. Offset is relative to the first row of the stream table when it is created. If offset is unspecified, or -1, or above the number of rows of the stream table, the subscription starts with the next new message. If some rows were cleared from memory due to cache size limit, they are still considered in determining where the subscription starts.
- resub is a Boolean value indicating whether to resubscribe after network disconnection.
- filter is a vector indicating filtering condition. Only the rows with values of the filtering column in the vector specified by the parameter 'filter' are published to the subscriber. 

Function `subscribe` returns a pointer of the thread that calls the message handler repeatedly. 

Example:
```
auto t = client.subscribe(host, port, [](Message msg) {
    // user-defined routine
    }, tableName);
t->join();
```

3. Unsubscribe
```
void ThreadClient::unsubscribe(string host, int port, string tableName, string actionName = DEFAULT_ACTION_NAME);
```
- host is the IP address of the publisher node. 
- port is the port number of the publisher node.
- tableName is a string indicating the name of the publishing stream table.
- actionName is a string indicating the name of the subscription task. 

#### 4.3.2 ThreadPooledClient

Each time the stream table publishes new messages, multiple threads acquires and processes the messages.

1. Create an instance of ThreadPooledClient 
```
ThreadPooledClient::ThreadPooledClient(int listeningPort, int threadCount);
```
- listeningPort is the port number on the subscriber node. 
- threadCount is the size of the thread pool.

2. Call function `subscribe`
```
vector\<ThreadSP\> ThreadPooledClient::subscribe(string host, int port, MessageHandler handler, string tableName, string actionName = DEFAULT_ACTION_NAME, int64_t offset = -1);
```
The parameters are the same as those of ThreadedClient::subscribe in section 4.3.1. Function `subscribe` returns a vector of pointers, each of which for a thread that calls the message handler repeatedly. 

Example:
```
auto vec = client.subscribe(host, port, [](Message msg) {
    // user-defined routine
    }, tableName);
for(auto& t : vec) {
    t->join();
}
```

3. Unsubscribe
```
void ThreadPooledClient::unsubscribe(string host, int port, string tableName, string actionName = DEFAULT_ACTION_NAME);
```
The parameters are the same as those of ThreadedClient::unsubscribe in section 4.3.1. 

#### 4.3.3 PollingClient

We can acquire and process data by polling for a message queue generated by subscription. 

1. Create an instance of PollingClient 
```
PollingClient::PollingClient(int listeningPort);
```
- listeningPort is the port number on the subscriber node.

2. Subscribe
```
MessageQueueSP PollingClient::subscribe(string host, int port, string tableName, string actionName = DEFAULT_ACTION_NAME, int64_t offset = -1);
```
The parameters are the same as those of ThreadedClient::unsubscribe in section 4.3.1. The function returns a pointer of the message queue that calls the message handler repeatedly. 

Example:
```
auto queue = client.subscribe(host, port, handler, tableName);
Message msg;
while(true) {
    if(queue->poll(msg, 1000)) {
        if(msg.isNull()) break;
        // handle msg
    }
}
```

3. Unsubscribe
```
void PollingClient::unsubscribe(string host, int port, string tableName, string actionName = DEFAULT_ACTION_NAME);
```
The parameters are the same as those of ThreadedClient::unsubscribe in section 4.3.1. 

#### 4.4 C# API

When streaming data arrives at the subscriber nodes, there are 2 ways to process data in C# API:

1. The subscriber node periodically checks whether new data has arrived. If new data has arrived, the subscriber node acquires the new data and then processes it.
```
PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, offset);

while (true) {
   ArrayList<IMessage> msgs = poller1.poll(1000);

   if (msgs.size() > 0) {
       BasicInt value = msgs.get(0).getValue<BasicInt>(2);  //take the second field in the first row of the table
   }
}
```

2. Process new data directly through a predefined MessageHandler.

First, define a handler that inherits dolphindb.streaming.MessageHandler. 
```
public class MyHandler implements MessageHandler {
       public void doEvent(IMessage msg) {
               BasicInt qty = msg.getValue<BasicInt>(2);
               //..Processing data
       }
}
```

Use the handler as a parameter of function `subscribe`.
```
ThreadedClient client = new ThreadedClient(subscribePort);
client.subscribe(serverIP, serverPort, tableName, new MyHandler(), offsetInt);
```

Call function `subscribe`
```
ThreadPooledClient client = new ThreadPooledClient(subscribePort);
client.subscribe(serverIP, serverPort, tableName, new MyHandler(), offsetInt);
```

3. Reconnect

Parameter 'reconnect' is a Boolean value indicating whether to resubscribe after network disconnection. The default value is false.

In the following example, parameter 'reconnect' is set to true. 
```
PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, offset, true);
```

4. Filtering

The parameter 'filter' is a vector. Use `setStreamTableFilterColumn` on the publisher node to specify the filtering column of the stream table. Only the rows with values of the filtering column in the vector specified by the parameter 'filter' are published to the subscriber. 

In the following example, parameter 'filter' takes the value of an integer vector with 1 and 2. 
```
BasicIntVector filter = new BasicIntVector(2);
filter.setInt(0, 1);
filter.setInt(1, 2);

PollingClient client = new PollingClient(subscribePort);
TopicPoller poller1 = client.subscribe(serverIP, serverPort, tableName, actionName, offset, filter);
```

### 5. Status monitoring

As streaming calculations are conducted in the background, DolphinDB provides function `getStreamingStat` to monitor streaming. It returns a dictionary with 4 tables: pubConns, subConns, persistWorkers and subWorkers.

#### 5.1 pubConns

Table pubConns displays the status of the connections between the local publisher node and all of its subscriber nodes. Each row represents a subscriber node.

Column|Description
---|---
Client|IP address and port number of a subscriber node
queueDepthLimit|The maximum depth (number of records) of the message queue that is allowed on the publisher node. There is only one publishing message queue for each publisher node.
queueDepth|Current depth (number of records) of the message queue on the publisher node
Tables|All shared stream tables in the publisher node, separated by commas.

Run getStreamingStat().pubConns in DolphinDB GUI to view the contents of the table:
![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/pubconn.png?raw=true)

Table pubConns lists information about all the subscription nodes of the publisher node, as well as the status of the message queue and the names of stream tables on the publisher node.

#### 5.2 subConns

Table subConns displays the status of the connections between the local subscriber node and the publisher nodes. Each row is a publisher node that the local node subscribes to.

Column|Description
---|---
Publisher|A publisher node alias
cumMsgCount|The number of messages that have been received
cumMsgLatency|The average latency (in milliseconds) of all received messages. Latency refers to the time it takes for a message from entering the release queue to entering the subscription queue.
lastMsgLatency|The latency (in milliseconds) of the last received message
lastUpdate|The last time a message is received

Run getStreamingStat().subConns in DolphinDB GUI:
![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/subconn.png?raw=true)


#### 5.3 persistWorkers

Table persistWorkers monitors the status of workers (threads) responsible for streaming data persistence. Each row represents a worker thread.

Column|Description
---|---
workerId|Worker ID
queueDepthLimit|The maximum allowed depth (number of records) of a message queue for table persistence
queueDepth|Current depth (number of records) of the message queue for table persistence
Tables|Names of the persisted tables, separated by commas.

Table persistWorkers can be obtained with function `getStreamingStat` only if persistence is enabled. The number of rows of the table is the value of the configuration parameter 'persistenceWorkerNum'. 

The following example runs getStreamingStat().persistWorkers in DolphinDB GUI.

When persistenceWorkerNum=1:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persistworker.png?raw=true)

When persistenceWorkerNum=3:

![image](https://github.com/dolphindb/Tutorials_CN/blob/master/images/streaming/persisWorders_2.png?raw=true)

To persist multiple tables in parallel, we need to set persistenceWorkerNum>1. 

#### 5.4 subWorkers

Table subWorkers displays the status of workers of subscriber nodes responsible for streaming. Each row represents a subscription topic.

Column|Description
---|---
workerId|Subscriber node worker ID
Topic|Subscription topic
queueDepthLimit|The maximum allowed depth (number of records) of a message queue on the subscriber node
queueDepth|Current depth (number of records) of the message queue on the subscriber node
processedMsgCount|The number of messages that have been processed
failedMsgCount|The number of messages that failed to be processed
lastErrMsg|The last error message

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

### 6. Performance tuning

If an extremely large amount of streaming data arrive in a short period of time, we may see an extremely high value of 'queueDepth' in table subWorkers on the subscriber node. When the message queue depth on the a subscriber node reaches 'queueDepthLimit', new messages from the publisher node are blocked from entering subscriber nodes. This leads to a growing message queue on the publisher node. When the message queue depth of the publisher node reaches 'queueDepthLimit', the system blocks new messages from entering the stream table on the publisher node.

There are several ways to optimize streaming performance:

1. Adjust parameters 'batchSize' and 'throttle' to balance the cache on the publisher and the subscriber nodes. This can achieve a dynamic balance between streaming data injection speed and data processing speed. To take full advantage of batch processing, we can set 'batchSize' to wait for streaming data to accumulate to a certain amount before consumption. This, however, needs a certain amount of memory usage. If 'batchSize' is too large, it is possible that some data below the threshold of 'batchSize' get stuck in the buffer for a long time. To handle this issue, we can set parameter 'throttle' to consume the buffer data even if 'batchSize' is not met.

2. Increase parallelism by adjusting the configuration parameter 'subExecutors' to speed up message queue processing on the subscriber node. 

3. When each executor processes a different subscription, if there is great difference in throughput of different subscriptions or the complexities of calculation, some executors may idle. If we set subExecutorPooling=true, all executors form a shared thread pool to process all subscribed messages together. All subscribed messages enter the same queue and multiple executors read messages from the queue for parallel processing. With the shared thread pool, however, there is no guarantee that messages will be processed in the order they arrive. Therefore parameter 'subExecutorPooling' should not be turned on when messages need to be processed in the order they arrive. By default, the system uses a hash algorithm to assign an executor to each subscription. If we would like to ensure the messages in two subscriptions are processed by the order as they arrive, we can specify the same value for parameter 'hash' in function `subscribeTable` of the two subscriptions, so that the same executor processes the messages of the two subscriptions.

4. If the stream table enables synchronous persistence, disk I/O maybe become a bottleneck. One way to handle this is to use the method in section 2.4 to persist data in asynchronous mode while setting up a reasonable persistence queue by specifying 'maxPersistenceQueueDepth' (default 10 million messages). Alternatively, we can also use SSD hard drives to improve write performance.

5. Publisher node maybe become a bottleneck. For example, there may be too many subscribing clients. We can use the following methods to handle this problem. First, we can reduce the number of subscriptions for each publisher node with multi-level cascading. Applications that can tolerate delay can subscribe to secondary or even third tier publisher nodes. Second, some parameters can be adjusted to balance throughput and latency. The parameter 'maxMsgNumPerBlock' sets the size of the messages batches. The default value is 1024. In general, larger batches increase throughput but increase network latency.

6. If the injection speed of streaming data fluctuates greatly and peak periods cause the consumption queue to reach the queue depth limit (default 10 million), then we can modify configuration parameters 'maxPubQueueDepthPerSite' and 'maxSubQueueDepth' to increase the maximum queue depth of the publisher and the subscriber. However, as memory consumption increases as queue depth increases, memory usage should be planned and monitored to properly allocate memory.

### 7. Visualization

Streaming data visualization can be either real-time value monitoring or trend monitoring. 

- Real-time value monitoring: conduct rolling-window computation of aggregated functions with streaming data periodically.

- Trend monitoring: generate dynamic charts with streaming data and historical data.

Various data visualization platforms support real-time monitoring of streaming data, such as the popular open source data visualization framework Grafana. DolphinDB has implemented the interface between the server and client of Grafana. For details, please refer to the tutorial：https://github.com/dolphindb/grafana-datasource/blob/master/README.md
