# DolphinDB Startup Scripts

From version 1.0 onwards, users can create a startup script to specify the jobs which need to be executed automatically every time DolphinDB starts. The script is normally used to initialize streaming, define or share variables, load plugins, etc. Since version 1.30.15/2.00.3, a postStart script is provided to execute scheduled jobs on system startup.

- [DolphinDB Startup Scripts](#dolphindb-startup-scripts)
	- [1. DolphinDB Startup Process](#1-dolphindb-startup-process)
	- [2. Script Configuration](#2-script-configuration)
		- [2.1 Init Script](#21-init-script)
		- [2.2 Startup Script](#22-startup-script)
		- [2.3 postStart Script](#23-poststart-script)
	- [3. Application Scenarios](#3-application-scenarios)

## 1. DolphinDB Startup Process

The startup process of DolphinDB is as shown below:

![img](./images/startup.png?raw=true)

## 2. Script Configuration

You can specify the init script, startup script, and postStart script with configuration parameters *init*, *startup* and *postStart*, respectively. The configuration file is *dolphindb.cfg* for standalone mode, and *cluster.cfg* for a cluster. You can specify an absolute or relative path for each configuration parameter. If a relative path is specified, DolphinDB will search the home directory, working directory and executable directory on the local node in order. For example:

```
init=dolphindb.dos
startup=/home/streamtest/init/server/startup.dos
postStart=D://dolphindb/server/postStart.dos
```

 

### 2.1 Init Script

The init script is specified by the configuration parameter *init*. The default file is *dolphindb.dos* under the home directory *\<homeDir>*. It usually contains definitions of system-level functions that are visible to all users and cannot be overwritten. It is not recommended to modify the init script.

 

### 2.2 Startup Script

The startup script is specified by the configuration parameter *startup*. The default value is *\<homeDir>/startup.dos*. It can be used to execute reusable modules, define user-defined functions, or even access remote clusters. Note that the startup script is executed by an administrator without access to clusters. To remotely implement the functionalities of controller or access a DFS table in a cluster, you need to log in as an administrator or a user with granted privileges in the script.

You can also call function views in the startup script. If the definition of a function view contains a plugin function, the plugin must be first loaded in the init script. However, as the function view is stored on the controller, using a plugin function requires the plugin be loaded in the init scripts on all nodes in the cluster, which is not recommended.

To debug the startup script, you can write functions such as `print` and `writeLog` in the script. The system will output the execution information of startup script to the log. You can use the `try-catch` statement to capture the exceptions so as to prevent a startup failure.

The following jobs cannot be executed in the startup script:

- Functions related to scheduled jobs, including `scheduleJob`, `getScheduledJobs` and `deleteScheduledJob`. The scheduled jobs are initialized after the startup script is executed, so functions that are related to scheduled jobs cannot be executed in this step.
- Definitions on system-level functions. These functions can only be defined in the init script *dolphindb.dos*. 

Note: The execution of jobs that need to access other nodes may fail as other nodes have not yet initialized.

If error occurs when executing the startup script, the subsequent execution will be skipped and the system will proceed to the next step.

 

### 2.3 postStart Script

The postStart script is specified by the configuration parameter *postStart*. The default value is *\<homeDir>/postStart.dos*. It is used to execute scheduled jobs when the system is starting up.

After the startup script is executed, the system will initialize the job manager of scheduled jobs. If a scheduled job involves plugin functions (or shared objects), then the plugins must be preloaded (or the objects must be shared) first in the startup script. Otherwise the deserialization of scheduled jobs fails and the system will be shut down.

For example:

```
if(getScheduledJobs().jobDesc.find("daily resub") == -1){
    scheduleJob(jobId=`daily, jobDesc="daily resub", jobFunc=run{"/home/appadmin/server/resubJob.dos"}, scheduleTime=08:30m, startDate=2021.08.30, endDate=2023.12.01, frequency='D')   
} 
```



## 3. Application Scenarios

Operations that are performed during the system startup normally include defining and sharing in-memory tables and stream tables, subscribing to stream tables, loading plugins, etc.

**Example 1**: define and share in-memory tables

Define an in-memory table *t* and share it as *st*. Users can insert, update, delete or query records in the table *st* from other sessions.

```
t=table(1:0,`date`sym`val,[DATE,SYMBOL,INT])
share(t, `st); 
```

**Example 2**: share and subscribe to stream tables

- share and persist a stream table

The definitions of stream tables are not persisted in DolphinDB, and you can initialize the stream tables in the startup script. The following example defines and shares the stream table st1.

```
login("admin","123456")
t1=streamTable(1:0,`date`sym`val,[DATE,SYMBOL,INT])
enableTableShareAndPersistence(table=t1,tableName=`st1,cacheSize=1000)
```

- subscribe to the stream table

You can also subscribe to a stream table in the startup script. For example, subscribe to stream table st1 and save the data to table tb.

```
tb=loadTable("dfs://db1","tb")
subscribeTable(tableName="st1",actionName="subst",offset=-1,handler=append!{tb},msgAsTable=true)
```

**Example 3**: load plugins before loading scheduled jobs

If a scheduled job references a plugin function, the plugin must be preloaded in the startup script, otherwise the server startup may fail due to deserialization issues. 

The scheduled job “jobDemo” calls a function provided by the plugin “odbc“.

```
use odbc
def jobDemo(){
	conn = odbc::connect("dsn=mysql_factorDBURL");
	//...
}
scheduleJob("job demo","example of init",jobDemo,15:48m, 2019.01.01, 2020.12.31, 'D')
```

If the plugin “odbc“ is not loaded when the system loads the scheduled jobs, DolphinDB server will be shut down with the following message output to log:

```
<ERROR>:Failed to unmarshall the job [job demo]. Failed to deserialize assign statement. Invalid message format.
```

To start the system, load the plugin in the startup script as follows:

```
loadPlugin("plugins/odbc/odbc.cfg")
```

 