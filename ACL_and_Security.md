# DolphinDB User Access Control and Security

Main functionalities:  
* Can conveniently grant/deny access privileges to groups of users
* 8 types of access privileges for various scenarios
* Various access control functions/commands
* Function views can provide analysis results without sacrificing data privacy
* Access Privilege control for scheduled jobs and streaming tasks
* RSA encryption for key information
* Support SSO to simplify cross domain access

### 1. Access Control

#### 1.1 Users and Groups

A user can belong to 0, 1, or multiple groups; a group can have 1 or multiple users.

A user's access privileges are determined by her own access privileges and the privileges of the groups that she belongs to.

#### 1.2 Administrators

When a DolphinDB cluster is started for the first time, it creates an administrator with user ID of "admin" and password of "123456". This administrator has all access privileges in 1.3 and cannot be deleted. This administrator can create or delete other administrators. By default, these newly created administrators can create or delete administrators, users or groups, but they don't have any access privileges in 1.3. However, they can grant these privileges themselves. 

An administrator can use functions or commands `createUser`, `deleteUser`, `createGroup`, `deleteGroup`, `addGroupMember`, `deleteGroupMember`, `getUserAccess`, `getUserList`, `getGroupList` and `resetPwd` to conduct operations regarding users and groups. 

#### 1.3 Access Privilege Types

DolphinDB supports the following 8 types of access privileges: 

1. TABLE_READ: read tables
2. TABLE_WRITE: write to tables
3. DBOBJ_CREATE: create database objects (tables) in a database
4. DBOBJ_DELETE: delete database objects (tables) in a database
5. VIEW_EXEC: execute view functions
6. DB_MANAGE: create and delete databases 
7. SCRIPT_EXEC: execute script 
8. TEST_EXEC: execute testing script

When setting the first 5 privileges, we also need to specify the objects that these privileges apply to. 

Please note that all the databases and tables related to access privileges are created in the distributed file system (DFS). 

#### 1.4 Set Access Privileges

Only administrators can set access privileges and it must be done on the controller. Newly created users and groups do not have any access privilege, nor are they denied any access privilege. Administrators can use commands `grant`, `deny` and `revoke` to set access privileges. The 8 access privileges in 1.3 are used as values for the parameter "accessType" in these commands. 

We use 3 examples below to illustrate how to set access privileges. 

#### Example 1
Log in as "admin":
```
login(`admin, `123456)
```
Create user NickFoles with password AB123!@. Users can change their own password with command `changePwd`.
```
createUser("NickFoles","AB123!@")  
```
Grant the privilege to read any DFS table to user NickFoles:
```
grant("NickFoles",TABLE_READ,"*") 
```
Deny user NickFoles the privilege to create or manage databases:
```
deny("NickFoles",DB_MANAGE)   
```
Create group "SBMVP", and add NickFoles to the group: 
```
createGroup("SBMVP","NickFoles")  
```
Grant the privilege to create tables in databases "dfs://db1" and "dfs://db2" to group SBMVP:
```
grant("SBMVP",DBOBJ_CREATE,["dfs://db1","dfs://db2"])    
```

In the end, the access privileges of user NickFoles are: 
1. Can read all tables.
2. Cannot create or delete databases.
3. Can create tables in databases "dfs://db1" and "dfs://db2".

#### Example 2

```
createUser("EliManning", "AB123!@")  
createUser("JoeFlacco","CD234@#")  
createUser("DeionSanders","EF345#$")  
createGroup("football", ["EliManning","JoeFlacco","DeionSanders"])  
grant("football", TABLE_READ, "dfs://TAQ/quotes")  
grant("DeionSanders", DB_MANAGE)  
```

We created 3 users and 1 group. All these users belong to the group. Grant the group the privilege to read table dfs://TAQ/quotes, and grant user DeionSanders the privilege to create or delete databases. 

#### Example 3
We can use command `grant` or `deny` to grant or deny certain privileges on all objects (\*). For example, to grant user JoeFlacco the privilege to read all DFS tables:
```
grant("JoeFlacco",TABLE_READ,"*")  
```
After we grant or deny privileges on all objects to a user or a group, we can only revoke the privilege on all objects. If we try to revoke the privilege on any specific object, the operation would not be effective:
```
revoke("JoeFlacco",TABLE_READ,"dfs://db1/t1")
```
The command above has no effect. 

```
revoke("JoeFlacco",TABLE_READ,"*")
```
The command above successfully revokes the privilege of JoeFlacco to read all DFS tables. 

In a similar vein, after we grant or deny certain privileges to a group, we can revoke the privilege from the group, but we cannot revoke the privilege from a group member. 

#### 1.5 Rules about access privileges
A user's access privileges are determined by her own access privileges and the privileges of the groups that she belongs to. Different groups may specify different access privileges to the same user. For these situations the following rules apply:
* If a user is granted a privilege in at least one group and is not denied this privilege in any other group, then the user has this privilege. 
* If a user is denied a privilege in at least one group, then the user does not have this privilege, even though she may have been granted the privilege in other groups. The user can have this privilege if an administrator revokes the denial and then grants the privilege if it has not been granted in other groups. 

Please note that when discussing the rules above, for convenience, we can view a user as belonging to a special group with herself as the only member.

```  
createUser("user1","123456")  
createUser("user2","123456")  
createGroup("group1")  
createGroup("group2")  
addGroupMember(["user1","user2"],"group1")
addGroupMember(["user1","user2"],"group2")
grant("user1",TABLE_READ,"*")  
deny("group1",TABLE_READ,"dfs://db1/t1")  
deny("group2",TABLE_READ,"dfs://db1/t2")   
```  
The result of the 3 lines above: user1 can read any table except dfs://db1/t1 and dfs://db1/t2.  

``` 
grant("user2",TABLE_WRITE,"*")  
deny("group1",TABLE_WRITE,"*")  
grant("group2",TABLE_WRITE,"dfs://db1/t2")  
```
The result of the 3 lines above: user1 and user2 cannot write to any table.  

#### 1.6 Function View

Users can get the result of a function view on a table when they don't have the privilege to read the table. Only administrators can define or delete a function view. 

For example, an administrator defines the following function view:
```
login(`admin, `123456)
def countTradeAll(){  
	return exec count(*) from loadTable("dfs://TAQ","Trades")  
}
addFunctionView(countTradeAll)  
grant("NickFoles",VIEW_EXEC,"countTradeAll")  
```
Log in as "NickFoles", and execute function view `countTradeAll`
```
countTradeAll()
```
Although NickFoles cannot read table dfs://TAQ/Trades, he can execute function view `countTradeAll` to get the number of rows in table dfs://TAQ/Trades.

Function views can have parameters. In the following example, we create a function view to get the average bid-ask spread of a specified stock on a specified date:
```
login(`admin, `123456)
def getSpread(s, d){
	return select avg((ofr-bid)/(ofr+bid)*2) as spread from loadTable("dfs://TAQ","quotes") where symbol=s, date=d
}
addFunctionView(getSpread)  
grant("NickFoles", VIEW_EXEC, "getSpread")

```
Log in as "NickFoles", and execute function view `getSpread` with specified stock symbol and date：
```
getSpread("IBM", 2018.07.09)
```

### 2. Access control for scheduled jobs and streaming

Scheduled jobs and streaming are jobs that run in the background. Whether these jobs can be executed depends on whether the users who created these jobs have the access privilege for these jobs. 

#### 2.1 Access control for scheduled jobs

When a user schedules a job, she does not need to have access privileges on the objects that are involved. However, if the user does not have privileges to access the objects when the scheduled job is set to be executed, the scheduled job will not be executed.

```
login("NickFoles","AB123!@")
def readTable(){  
	read_t1=loadTable("dfs://db1","t1")  
	return exec count(*) from read_t1  
}  
scheduleJob("noreadJob","read dfs table",readTable,minute(now()) , date(now()),date(now())+1,'D');  
```
In the example above, job `readTable` can be scheduled even if user NickFoles does not have privilege to read table dfs://db1/t1. When the job is set to be executed, however, if NickFoles does not have privilege to read table dfs://db1/t1 the job will not be executed. 

Administrators can delete all scheduled job with command `deleteScheduledJob`; a non-administrator user can only delete scheduled jobs created by herself. 

#### 2.2 Access control for streaming

When a user uses function `subscribeTable` to subscribe to a streaming table, she should make sure that she has the access privilege to write to the local table where the subscribed data will be saved. 

```
login("NickFoles","AB123!@")
def saveTradesToDFS(mutable dfsTrades, msg): dfsTrades.append!(select today() as date, * from msg)  
subscribeTable("NODE1", "trades_stream", "trades", 0, saveTradesToDFS{trades}, true, 1000, 1)  
```

In the example above, the streaming handler `saveTradesToDFS` saves subscribed data to table dfsTrades. If NickFoles does not have privilege to write to table dfsTrades, then the streaming task will fail. 

### 3. Secure communication with HTTPS

DolphinDB supports HTTPS for secure communication over the web. 

#### 3.1 Enable HTTPS

There are 2 ways to enable HTTPS:

+ Add "enableHTTPS=true" in the configuration file of the cluster controller (controller.cfg)

+ Add "-enableHTTPS true" in the command line when starting the cluster controller. 

#### 3.2 HTTPS Certificate

We need to install server authentication certificate at each server in DolphinDB for secure connections. There should be a certificate on the controller and each of the agent nodes. Data nodes use the certificate located at the agent node on the same server. 

##### 3.2.1 Use an authentication certificate from a certificate authority

Get a certificate from a certificate authority, rename it as server.crt, and copy to the folder "keys" under the home directory of the controller. If the folder "keys" does not exist, we need to create it. The certificate does not need to be installed as it is from a certificate authority. This is recommended in most use cases. 

##### 3.2.2 Install a self-signed authentication certificate

Sometimes we may want to install a self-signed authentication certificate. For example, in a small isolated cluster or in a research (non-production) setting. Please take the following steps:

> 1. Set the configuration parameter "publicName" as the domain name of the computer
The following is an example of the command line in Linux to start the controller, where www.ABCD.com is the domain name of the server where the controller is located:
```
./dolphindb -enableHTTPS true -home master -publicName www.ABCD.com -mode controller -localSite 192.168.1.30:8500:rh8500 -logFile  ./log/master.log
```
> 2. Check if the authentication certificate and private key have been generated 
Start the controller node and check if the certificate file *server.crt* and the private key for the server serverPrivate.key exist in the folder "keys" under the home directory. 

> 3. Install the self-signed certificate to the certificate authority of the web browser

In Google Chrome, choose Settings -> Advanced -> Manage certificates -> AUTHORITIES-> Import to install the self-signed certificate server.crt. In other web browsers, there might be slight differences in this process. 

![](images/Selection_047.png)  

Now enter https://www.ABCD.com:8500/ in the web browser to connect to DolphinDB cluster manager, where 8500 is the port number of the controller. If you see a green lock sign and "Secure" in the address bar, the authentication certifiate has been successfully installed.
![](images/Selection_046.png)

### 4. SSO （Single Sign On)

On the web-based cluster manager, we can click any data node to open a notebook on this node. The data node may be located on a different physical server as the controller node. DolphinDB provides SSO so that we don't need to log in the system again when we visit different servers in a cluster. 

DolphinDB provides 2 API functions for SSO:
+ `getAuthenticatedUserTicket()`: issue the current user's encrypted ticket
+ `authenticateByTicket(ticket)`: use the ticket generated by getAuthenticatedUserTicket() to log in the system. 

DolphinDB developers can use these API functions to develop more functionalities. 



