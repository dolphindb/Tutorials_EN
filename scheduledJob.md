# Scheduled Jobs

- [Scheduled Jobs](#scheduled-jobs)
	- [1. Creating a Scheduled Job](#1-creating-a-scheduled-job)
	- [2. Viewing Scheduled Jobs](#2-viewing-scheduled-jobs)
	- [3. Deleting a Scheduled Job](#3-deleting-a-scheduled-job)
	- [4. Access Control](#4-access-control)
	- [5. Serialization and Deserialization](#5-serialization-and-deserialization)
		- [5.1 Compiled Functions](#51-compiled-functions)
		- [5.2 Script Functions](#52-script-functions)
	- [6. Executing Scripts with Scheduled Jobs](#6-executing-scripts-with-scheduled-jobs)
	- [7. Troubleshooting](#7-troubleshooting)

Scheduled Jobs are automated pieces of work that can be performed at a specific time or on a recurring schedule. Scheduled jobs are widely used for performing data analysis on a regular basis (e.g., monthly reports or daily 1-minute OHLC after market close), database administration (e.g., backup, synchronization), operating system management (e.g., log cleanup), and many other scenarios.

## 1. Creating a Scheduled Job

Create a scheduled job with the [scheduleJob](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html) function. The job definition will be serialized and saved to file `<homeDir>/sysmgmt/jobEditlog.meta`. 

```
scheduleJob(jobId, jobDesc, jobFunc, scheduledTime, startDate, endDate, frequency, [days],[onComplete])
```

Note:

1. *jobFunc* is a function with no parameters, usually a [partial application](https://dolphindb.com/help/Functionalprogramming/PartialApplication.html). It can be a user-defined function, built-in function, function view, or function in a module or plugin. This means scheduling jobs in DolphinDB is very flexible - you can schedule any job that can be represented by a function. For example, you can use a user-defined function or a plugin function to perform recurring data analysis, use the `run` function to execute script automatically, or `shell` to run operating system commands.
2. The function returns the ID of the scheduled job. If the specified *jobId* is the same as the ID of an existing scheduled job, the system appends a suffix of the current date, or “000”, “001”, ….. or both to the specified *jobId* to generate a unique scheduled job ID.
3. The scheduled job will run in the background at the scheduled time.

- Example 1. The scheduled job calls the user-defined function `getMaxTemperature` to get the maximum temperature of a device in the previous day. The job is scheduled at 00:00 every day.   

```
def getMaxTemperature(deviceID){
    maxTemp=exec max(temperature) from loadTable("dfs://dolphindb","sensor")
            where ID=deviceID ,ts between (today()-1).datetime():(today().datetime()-1)
    return  maxTemp
}
scheduleJob(`testJob, "getMaxTemperature", getMaxTemperature{1}, 00:00m, today(), today()+30, 'D');
```

Note: With the job function specified as `getMaxTemperature{1}`, the argument *deviceID* is fixed to "1" in the scheduled job.

- Example 2. The scheduled job calls the `run` function to execute the script file *monthlyJob.dos* at 00:00 on the first day of each month. Please note that the full path of the script file is specified as the parameter of `run`.

```
scheduleJob(`monthlyJob, "Monthly Job 1", run{"/home/DolphinDB/script/monthlyJob.dos"}, 00:00m, 2020.01.01, 2020.12.31, 'M', 1);
```

- Example 3. The scheduled job calls the `shell` function to remove log files at 01:00 on Sundays. The operating system command `rm/home/DolphinDB/server/dolphindb.log` is passed in as the argument to `shell`. 

```
scheduleJob(`weeklyjob, "rm log", shell{"rm /home/DolphinDB/server/dolphindb.log"}, 01:00m, 2020.01.01, 2021.12.31, 'W', 0);
```

In many cases, it is a common practice to retrieve data from a database and pass it to the job function, and save the execution result to a database. The more common In the following example, the user-defined function `computeK` fetches market data from the DFS table “trades” for calculation and saves the results to the DFS table “OHLC“.

- Example 4. Calculate 1 minute OHLC at 15:00 on weekdays.

```
def computeK(){
	barMinutes = 7
	sessionsStart=09:30:00.000 13:00:00.000
	OHLC =  select first(price) as open, max(price) as high, min(price) as low,last(price) as close, sum(volume) as volume 
		from loadTable("dfs://stock","trades")
		where time > today() and time < now()
		group by symbol, dailyAlignedBar(timestamp, sessionsStart, barMinutes*60*1000) as barStart
	append!(loadTable("dfs://stock","OHLC"),OHLC)
}
scheduleJob(`kJob, "7 Minutes", computeK, 15:00m, 2020.01.01, 2021.12.31, 'W', [1,2,3,4,5]);
```

<!-- 记得改之后例子的标序- Example 5.  After each execution of the scheduled job, you can send an email to notify specific users of the result. *onComplete* is a callback function with 4 arguments, which gets executed upon the completion (with errors or not) of each job execution. 

Note: Installation of the [HttpClient plugin](上线加教程链接) is required to run the following script.

def sendEmail(jobId, jobDesc, success, result){
desc = "jobId=" + jobId + " jobDesc=" + jobDesc
if(success){
desc += " successful " + result
res = httpClient::sendEmail('patrick.mahomes@dolphindb.com','password','andy.reid@dolphindb.com','This is a subject',desc)
}
else{
desc += " with error: " + result
res = httpClient::sendEmail('patrick.mahomes@dolphindb.com','password','andy.reid@dolphindb.com','This is a subject',desc)
}
}
scheduleJob(jobId=`PnL, jobDesc="Calculate Profit & Loss", jobFunc=run{"PnL.dos"}, scheduleTime=[12:00m, 02:00m, 14:50m], startDate=2018.01.01, endDate=2018.12.31, frequency='W', days=[1,2,3,4,5], onComplete=sendEmail);
-->

## 2. Viewing Scheduled Jobs

Use [getScheduledJobs](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) to check the definitions of scheduled jobs:

```
getScheduledJobs([jobIdPattern])
```

Note:

1. *jobIdPattern* is a string indicating a job ID or a pattern of job ID. It supports wildcard characters “%” and “?”.
2. Return a table of scheduled jobs. If *jobIdPattern* is not specified, return all scheduled jobs.
3. To view all scheduled jobs in a cluster, call `pnodeRun(getScheduledJobs)`, or log in to the web-based cluster manager and go to the “Job“ tab > “Scheduled Jobs“ table.

The execution log of a scheduled job are saved in *<jobId>.msg*; the result of a scheduled job is saved in <*jobId>.object*. Both files are saved under `<homeDir>/batchJobs`. Use functions [getJobMessage](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getJobMessage.html) and [getJobReturn](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getJobReturn.html) to view these 2 files.

About the job ID of a scheduled job:

1. When creating a scheduled job, if the specified jobId is the same as the ID of an existing scheduled job, a suffix will be added to generate a unique ID. (see section 1 Creating a Scheduled Job](#1-creating-a-scheduled-job)). 
2. For recurring jobs, the job ID is different in each execution. Use the function `getRecentJobs` to check the job ID of the recently finished scheduled jobs.

- Example 5. Schedule a recurring job and check the executions.

```
def foo(){
	print "test scheduled job at"+ now()
	return now()
}
scheduleJob(`testJob, "foo", foo, 17:00m+0..2*30, today(), today(), 'D');
```

After several executions, call `getRecentJobs`. The result is as follows:

```
jobId	            jobDesc	startTime	            endTime
------              ------- ----------------------- ----------------------
testJob	            foo1	2020.02.14T17:00:23.636	2020.02.14T17:00:23.639
testJob20200214	    foo1	2020.02.14T17:30:23.908	2020.02.14T17:30:23.910
testJob20200214000  foo1	2020.02.14T18:00:23.148	2020.02.14T18:00:26.749
```

We can see that the *jobId* is different in each execution: “testJob“, “testJob20200214“, “testJob20200214000”, and so on. 

```
>getJobMessage(`testJob20200214000);
2020-02-14 18:00:23.148629 Start the job [testJob20200214000]: foo
2020-02-14 18:00:23.148721 test the scheduled job at 2020.02.14T18:00:23.148
2020-02-14 18:00:26.749111 The job is done.

>getJobReturn(`testJob20200214000);
2020.02.14T18:00:23.148
```

## 3. Deleting a Scheduled Job

Delete a scheduled job with function [deleteScheduledJob](https://dolphindb.com/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html):

```
deleteScheduledJob(jobId)
```

Note: 

- Use [getScheduledJobs](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) to get the ID of the job you want to delete.
- With this command, administrators can delete all scheduled jobs; users can only delete the scheduled jobs created by themselves.

## 4. Access Control

When creating a scheduled job, make sure you have the access required by the job. For example, if a job scheduled to read a DFS table is created by a user without access to the table, the execution would fail. 

- Example 6. Log in as “guestUser1“ to create a scheduled job. “guestUser1” does not have the access to read the specified DFS table.

```
def foo1(){
	print "Test scheduled job "+ now()
	cnt=exec count(*) from loadTable("dfs://FuturesContract","tb")
	print "The count of table is "+cnt
	return cnt
}
login("guestUser1","123456")
scheduleJob(`guestGetDfsjob, "dfs read", foo1, [12:00m, 21:03m, 21:45m], 2020.01.01, 2021.12.31, "D");
```

After the job has been executed, call `getJobMessage("guestGetDfsjob")` to check the execution log. The result shows the job does not have the access to read the DFS table: 

```
2020-02-14 21:03:23.193039 Start the job [guestGetDfsjob]: dfs read
2020-02-14 21:03:23.193092 Test the scheduled job at 2020.02.14T21:03:23.193
2020-02-14 21:03:23.194914 Not granted to read table dfs://FuturesContract/tb
```

## 5. Serialization and Deserialization

When a scheduled job is created, the job ID,  job description, job function, scheduled time, frequency, and user ID of the creator are serialized and persisted to `<homeDir>/sysmgmt/jobEditlog.meta` on the local disk. When the node restarts, all scheduled jobs will be deserialized and loaded.

Specifically, the job function is a set of statements which may reference other functions or global objects (e.g., shared variables). As shared variables are serialized by name, when the system deserializes and loads scheduled jobs when starting up, the referenced shared variables must exist in the memory.

Job functions (including the functions that are referenced) can be divided into 2 categories based on whether they are compiled:

1. Compiled functions, including built-in functions and functions in plugins (plugin functions)
2. Script functions, including user-defined functions, function views and functions in modules

The two categories of functions are serialized differently, which affects how the corresponding scheduled jobs are deserialized and loaded on system startup.

### 5.1 Compiled Functions

For compiled functions, only the function names and module names are serialized. When the system deserializes the scheduled jobs, it searches for these functions and modules by name. If the functions or modules are not found, the deserialization fails.

When the system is starting up, the resources related to scheduled jobs are loaded in the following order: *dolphindb.dos*, function views, *startup.dos*, and scheduled jobs. If a scheduled job references a plugin function, the plugin must be loaded before the scheduled job.

- Example 7. The job function `jobDemo` of the scheduled job calls a function in the plugin “odbc“.

```
use odbc
def jobDemo(){
	conn = odbc::connect("dsn=mysql_factorDBURL");
}
scheduleJob("job demo","example of init",jobDemo,15:48m, 2019.01.01, 2020.12.31, 'D')
```

If the plugin “odbc“ is not loaded when the system starts, the system does not recognize the plugin function when loading the scheduled job and exits with the following message:

```
<ERROR>:Failed to unmarshall the job [job demo]. Failed to deserialize assign statement. Invalid message format
```

 To start the system properly, add the following line to *startup.dos* to load the plugin “odbc“.

```
loadPlugin("plugins/odbc/odbc.cfg")
```

### 5.2 Script Functions

For script functions, all parameters and statements in the function definition are serialized. If the statements reference other script functions, the definition of the referenced functions is also serialized.

Once a scheduled job is created, it will run as scheduled even if the job function or the script functions referenced by the job function are deleted or modified. The scheduled job will execute the original functions as they have been serialized when the job is created. To implement the changes in the scheduled job, you must delete the scheduled job and create a new one. Make sure you also redefine the referenced functions before creating the new job.

- Example 8. After creating a scheduled job, modify the job function `f`.

```
def f(){
	print "The old function is called " 
}
scheduleJob(`test, "f", f, 11:05m, today(), today(), 'D');
go
def f(){
	print "The new function is called " 
}
```

After the scheduled job is executed, call `getJobMessage("test")`. We can see that the scheduled job executed the old function:

```
2020-02-14 11:05:53.382225 Start the job [test]: f
2020-02-14 11:05:53.382267 The old function is called 
2020-02-14 11:05:53.382277 The job is done.
```

- Example 9. The function view `fv` is the job function of the scheduled job and it references the function view `foo`. After creating the scheduled job, modify the definition of `foo` and generate a new function view with the same name `fv`.

```
def foo(){
	print "The old function is called " 
}
def fv(){
	foo()
}
addFunctionView(fv)  

scheduleJob(`testFvJob, "fv", fv, 11:36m, today(), today(), 'D');
go
def foo(){
	print "The new function is called " 
}
dropFunctionView(`fv)
addFunctionView(fv)  
```

After the scheduled job is executed, call `getJobMessage("testFvJob")`. We can see that the scheduled job executed the old function:

```
2020-02-14 11:36:23.069892 Start the job [testFvJob]: fv
2020-02-14 11:36:23.069939 The old function is called 
2020-02-14 11:36:23.069951 The job is done.
```

- Example 10. Create a module *printLog.dos*:

```
module printLog
def printLogs(logText){
	writeLog(string(now()) + " : " + logText)
	print "The old function is called"
}
```

Then create a scheduled job to call the function `printLog::printLogs`:

```
use printLog
def f5(){
	printLogs("test my log")
}
scheduleJob(`testModule, "f5", f5, 13:32m, today(), today(), 'D');
```

Before the scheduled job is executed, modify the module:

```
module printLog
def printLogs(logText){
	writeLog(string(now()) + " : " + logText)
	print "The new function is called"
}
```

After the scheduled job is executed, call `getJobMessage("testModule")`. We can see that the scheduled job executed the old function:

```
2020-02-14 13:32:22.870855 Start the job [testModule]: f5
2020-02-14 13:32:22.871097 The old function is called
2020-02-14 13:32:22.871106 The job is done.
```

## 6. Executing Scripts with Scheduled Jobs

When serializing a scheduled job that runs script file with the `run` function, the system saves the name of the script file rather than the file content. Therefore, please make sure the script file contains the definitions of all the user-defined functions that are referenced by the scheduled job. Otherwise the job would fail as it cannot find these functions.

- Example 11. Create a script file *testjob.dos*:

```
foo()
```

Execute the following script in DolphinDB GUI:

```
def foo(){
	print ("Hello world!")
}
run "/home/user/testjob.dos"
```

The execution is successful:

```
2020.02.14 13:47:00.992: executing code (line 104-108)...
Hello world!
```

Then schedule a job to run the script file:

```
scheduleJob(`dailyfoofile1, "Daily Job 1", run {"/home/user/testjob.dos"}, 16:14m, 2020.01.01, 2020.12.31, `D`);
```

The following exception is thrown during execution:

```
Exception was raised when running the script [/home/user/testjob.dos]:Syntax Error: [line #3] Cannot recognize the token foo
```

This is because the function `foo` and the scheduled job are not in the same session and the job could not find the function definition of `foo`.

Add the definition of `foo` to the script file *testjob.dos*.

```
def foo(){
	print ("Hello world!")
}
foo()
```

Delete the current scheduled job and create a new one to run the script file. The new job is successfully executed.

## 7. Troubleshooting

| **Issue**                                                    | **Solution**                                                 |
| :----------------------------------------------------------- | :----------------------------------------------------------- |
| The job function references a shared variable. When loading the scheduled job, the system cannot find the shared variable. | Define the referenced shared variables in the startup script *startup.dos*. |
| The job function references a plugin function. When loading the scheduled job, the system cannot find the plugin function. | Load the plugin in the startup script *startup.dos*.         |
| Schedule a job to run a script file. The job cannot find the referenced functions in the script file during execution. | The script file specified in the scheduled job must contain the definition of all the functions referenced by the job. |
| The scheduled job involves accessing a DFS table but its creator doesn’t have the required privileges. | Grant the required privileges to the user.                   |
| The startup script *startup.dos* contains functions [scheduleJob](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/s/scheduleJob.html), [getScheduledJobs](https://dolphindb.com/help/FunctionsandCommands/FunctionReferences/g/getScheduledJobs.html) or [deleteScheduledJob](https://dolphindb.com/help/FunctionsandCommands/CommandsReferences/d/deleteScheduledJob.html). An exception is thrown when the startup script is loaded. | When the system is starting up, the startup script is loaded before the module for scheduled jobs, so the script must not contain any functions related to scheduled jobs, including `scheduleJob`, `getScheduledJobs` and `deleteScheduledJob`. To load scheduled job-related tasks on startup, add the tasks to the script file *postStart.dos*, which is loaded after the scheduled jobs.  The file path of *postStartup.dos* is specified by the parameter *postStart*. (See example below*) |

\* Example:

```
if(getScheduledJobs().jobDesc.find("daily resub") == -1){
	scheduleJob(jobId=`daily, jobDesc="daily resub", jobFunc=run{"/home/appadmin/server/resubJob.dos"}, scheduleTime=08:30m, startDate=2021.08.30, endDate=2023.12.01, frequency='D')	
}
```



On very rare occasions, scheduled jobs may fail to load, which may cause server startup failure. Particularly during a version upgrade, changes in the APIs for built-in functions and plugin functions may cause failure to load scheduled jobs, and compatibility issues may lead to system restart failure. Therefore, it is recommended to save the scripts you use when defining the scheduled jobs. When the system fails to start due to scheduled jobs, delete `<homeDir>/sysmgmt/jobEditlog.meta` (the file storing the serialized data of scheduled jobs) and try again. After the system is restarted, create the scheduled jobs again. 

