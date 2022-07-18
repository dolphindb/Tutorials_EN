# DolphinDB Database Security and User Access Control

DolphinDB provides users with a powerful, flexible and secure access control system. 

- [DolphinDB Database Security and User Access Control](#dolphindb-database-security-and-user-access-control)
	- [1. Overview of Access Control](#1-overview-of-access-control)
		- [1.1 Users and Groups](#11-users-and-groups)
		- [1.2 Administrators](#12-administrators)
		- [1.3 Rules on Users' Access Privileges](#13-rules-on-users-access-privileges)
		- [1.4 Access Privilege Types](#14-access-privilege-types)
	- [2. Managing User Privileges](#2-managing-user-privileges)
		- [2.1 DFS Databases](#21-dfs-databases)
		- [2.2 Shared In-Memory Tables](#22-shared-in-memory-tables)
		- [2.3 Streaming](#23-streaming)
		- [2.4 Other Applications](#24-other-applications)
	- [3. Secure Communication with HTTPS](#3-secure-communication-with-https)
		- [3.1 Enable HTTPS](#31-enable-https)
		- [3.2 HTTPS Certificate](#32-https-certificate)
	- [4. SSO (Single Sign-On)](#4-sso-single-sign-on)

Main features of the access control system:
* Can conveniently grant/deny access privileges to groups of users
* 9 types of access privileges for various scenarios
* Various access control functions/commands
* Function views can provide analysis results without sacrificing data privacy
* Access control for scheduled jobs and streaming tasks
* RSA encryption for key information
* Support SSO to simplify cross domain access

## 1. Overview of Access Control

### 1.1 Users and Groups

DolphinDB access control system uses groups to manage users with the same access privileges. A user can belong to 0, 1 or multiple groups; a group can have 0, 1 or multiple users.

A user's access privileges are determined by her own access privileges and the privileges of the groups that she belongs to. You can grant or deny the access of a user or a group (See [Section 1.3](#13-rules-on-users-access-privileges)).

Users can log in (out) with command `login` (`logout`). Users can change the login password with `changePWd`. 

### 1.2 Administrators

There are 2 types of administrators in DolphinDB: super admin and admin.

When a DolphinDB cluster is started for the first time, it creates a super admin with user ID of "admin" and password of "123456". This super admin has all access privileges mentioned in [Section 1.4](#14-access-privilege-types) and cannot be deleted. 

The super admin can create or delete users (including admin) and add them to any group. By default, newly created users don't have any access privileges. However, administrators can `grant`/`deny`/`revoke` access to users or groups. Administrators can use `resetPwd` to modify the login password.

Functions or commands that an administrator can use:

* `addGroupMember`: Add a user to a group or multiple groups
* `createUser`: Create a user  
* `deleteUser`: Delete a user  
* `createGroup`: Create a group  
* `deleteGroup`: Delete a group
* `deleteGroupMember`: Remove a user from a group or multiple groups, or remove multiple users from a group  
* `getUserAccess`: Obtain the privileges for users, without taking into account the privileges for the groups the users belong to  
* `getUserList`: Obtain a list of user names other than the administrators  
* `getGroupList`: Obtain a list of group names  
* `resetPwd`: Reset a user's password

For detailed usage of the above commands and functions, please see [DolphinDB help](https://www.dolphindb.com/help/index.html).

The following table summarises the difference among super admin, admin and regular user.

|                                                      |      super admin      |       admin      |       user       |
|:-----------------------------------------------------|:----------------------|:-----------------|:-----------------|
| Need to be manually created                          | No                    | Yes              | Yes              |
| Initial privileges                                   | All Privileges        | None             | None             |
| Can be deleted                                       | No                    | Yes              | Yes              |
| Can be listed by `getUserList()`                     | No                    | Yes              | Yes              |
| Can create or delete admin/user/group                | Yes                   | Yes              | No               |
| Can grant or deny privilege for admin/user/group     | Yes                   | Yes              | No               |
| Can create or delete function view                   | Yes                   | Yes              | No               |
| Can delete scheduled jobs submitted by other users   | Yes                   | Yes              | No               |

### 1.3 Rules on Users' Access Privileges

> Please note that when discussing the rules below, a user is viewed as belonging to a special group with herself as the only member. The access privileges are determined by the privileges of the groups that she belongs to.

Different groups may specify different access privileges to the same user. For these situations the following rules apply:

* If a user is granted a privilege in at least one group and is not denied this privilege in any other group, then the user has this privilege.
* If a user is denied a privilege in at least one group, then the user does not have this privilege, even though she may have been granted the privilege in other groups.

For the second situation, there are 2 ways for an administrator to grant the privilege to the user:

* Execute `grant` in all groups where the user’s privilege is denied.
* `revoke` the denial in all groups where the user’s privilege is denied:
  * the user then has the privilege if it has been granted in other groups;
  * if it has not been granted in other groups, the user can have this privilege after an administrator grants it to her.


The following example describes how the privileges are determined when a user's privileges conflict with that of a group to which she belongs:

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

Now user1 can read any table except "dfs://db1/t1" and "dfs://db1/t2".

The following script shows the situation when the privileges of the users' groups conflict based on the above example:

``` 
grant("user2",TABLE_WRITE,"*")  
deny("group1",TABLE_WRITE,"*")  
grant("group2",TABLE_WRITE,"dfs://db1/t2")  
```

Now user1 and user2 cannot write to any table.  

### 1.4 Access Privilege Types

DolphinDB supports the following 9 types of access privileges: 

1. **TABLE_READ**: read tables
2. **TABLE_WRITE**: write to tables
3. **DBOBJ_CREATE**: create database objects (tables) in a database
4. **DBOBJ_DELETE**: delete database objects (tables) in a database
5. **VIEW_EXEC**: execute view functions
6. **DB_MANAGE**: create and delete databases 
7. **DB_OWNER**: create databases. For the databases she created, she can delete these databases, create or delete tables or partitions in these databases, grant/deny/revoke the following privileges of other users: **TABLE_READ**, **TABLE_WRITE**, **DBOBJ_CREATE**, **DBOBJ_DELETE**
8. **SCRIPT_EXEC**: execute scripts 
9. **TEST_EXEC**: execute testing scripts

Note: 
- All the 9 types of access privileges are applicable to DFS databases and tables; 
- Only **TABLE_READ** and **TABLE_WRITE** are applicable to shared in-memory tables, stream tables and streaming engines.

## 2. Managing User Privileges

Administrators can use commands `grant`, `deny` and `revoke` to set access privileges on a controller. A user can also use function `addAccessControl` to apply access control to a shared in-memory table or streaming engine created by herself so that other users can access the table only after an administrator grants them the **TABLE_READ** privilege.

This chapter will explain how to manage the user privileges in DFS databases, in-memory tables, stream tables and streaming engines.

### 2.1 DFS Databases

In DFS databases, administrators can set the users' privileges with `grant`/`deny`/`revoke`. You can specify one of the 9 access privileges in [Section 1.4](#14-access-privilege-types) for the parameter *accessType* in these commands. The parameter *objs* indicates the object to which it is applied. It must be specified when accessType is specified as one of the first 5 privileges.

The following 4 examples illustrate how to set access privileges.

**Example 1**

Log in as "admin":

```
login(`admin, `123456)
```

Create user NickFoles with password AB123!@. Users can change their own password with command `changePwd`.

```
createUser("NickFoles","AB123!@")  
```

Grant the privilege to read any DFS table to user "NickFoles":

```
grant("NickFoles",TABLE_READ,"*") 
```

Deny user "NickFoles" the privilege to create or manage databases:

```
deny("NickFoles",DB_MANAGE)   
```

Create group "SBMVP", and add "NickFoles" to the group: 

```
createGroup("SBMVP","NickFoles")  
```

Grant the privilege to create tables in databases "dfs://db1" and "dfs://db2" to group "SBMVP":

```
grant("SBMVP",DBOBJ_CREATE,["dfs://db1","dfs://db2"])    
```

Now, user "NickFoles" has the following access privileges:

* Can read all tables.
* Cannot create or delete databases.
* Can create tables in databases "dfs://db1" and "dfs://db2".

**Example 2**

You can add users to a group to set the access privileges conveniently:

```
createUser("EliManning", "AB123!@")  
createUser("JoeFlacco","CD234@#")  
createUser("DeionSanders","EF345#$")  
createGroup("football", ["EliManning","JoeFlacco","DeionSanders"])  
grant("football", TABLE_READ, "dfs://TAQ/quotes")  
grant("DeionSanders", DB_MANAGE)  
```

The example creates 3 users "EliManning", "JoeFlacco", and "DeionSanders" and 1 group "football". All these users belong to the group. Grant the group the privilege to read table "dfs://TAQ/quotes", and grant user "DeionSanders" the privilege to create or delete databases.

**Example 3**

We can use command `grant` or `deny` to grant or deny certain privileges on all objects (\*). For example, to grant user "JoeFlacco" the privilege to read all DFS tables:

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

The command above successfully revokes the privilege of "JoeFlacco" to read all DFS tables. 

Similarly, after we grant or deny certain privilege to a group, we can revoke the privilege from the group, but we cannot revoke the privilege from a group member.

**Example 4**

If a user possesses the **DB_OWNER** privilege, she can grant other users the privileges on the databases created by her.

Create two users "CliffLee" and "MitchTrubisky", and grant "MitchTrubisky" the privilege **DB_OWNER**.

```
createUser(`CliffLee, "GH456$%")
createUser(`MitchTrubisky, "JI3564^")
grant(`MitchTrubisky,DB_OWNER);
```

Log in as "MitchTrubisky". Create table "dfs://dbMT/dt" and grant "CliffLee" the privilege to read the table.

```
login(`MitchTrubisky, "JI3564^");
db = database("dfs://dbMT", VALUE, 1..10)
t=table(1..1000 as id, rand(100, 1000) as x)
dt = db.createTable(t, "dt").append!(t)
grant(`CliffLee, TABLE_READ, "dfs://dbMT/dt");
```

Now "CliffLee" is granted with the permission to access the data table "dfs://dbMT/dt" created by "MitchTrubisky".

### 2.2 Shared In-Memory Tables

Administrators can set the **TABLE_READ** and **TABLE_WRITE** privileges for the shared in-memory tables in the same manner as that for a DFS database.

Create an admin "MitchTrubisky"

```
createUser("MitchTrubisky","JI3564^",,true)
```

Log in as "MitchTrubisky". Create an in-memory table and share it as "st1". Grant user "CliffLee” the privilege to read the table.

```
login(`MitchTrubisky, "JI3564^")
share table(1:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as st1
grant("CliffLee", TABLE_READ, "st1")
```

Check the column TABLE_READ_allowed returned by `getUserAccess`. Now user "CliffLee" has the privilege to read the table "st1".

```
getUserAccess("CliffLee")
```

Please note that before "MitchTrubisky" uses command `grant` (or `deny`) on st1, the table can be read and written to by any user. However, after the table permission is modified, access control is applied and only the administrators or the table creator "MitchTrubisky" have the privileges to read or write to the table.

You can also revoke the granted privileges:

```
revoke("CliffLee", TABLE_READ, "st1")
```

You can execute `addAccessControl` to apply access control:

```
share table(1:0, `time`sym`volume, [TIMESTAMP, SYMBOL, INT]) as st2
addAccessControl(shareTable2)
```

### 2.3 Streaming

#### 2.3.1 Stream Tables

The users' privileges control on stream tables is similar to that on shared in-memory tables. Please ensure that both the publisher and the subscribers have the appropriate privileges of the tables involved in streaming.

To write to a shared stream table on the publisher side, a user must have the **TABLE_READ** and **TABLE_WRITE** privileges.

Before subscribing to a stream table, a user should make sure that she has the **TABLE_READ** privilege to read the stream table. The user must have both **TABLE_READ** and **TABLE_WRITE** privileges to write to the local table where the subscribed data will be saved.

```
login("NickFoles","AB123!@")
def saveTradesToDFS(mutable dfsTrades, msg): dfsTrades.append!(select today() as date, * from msg)  
subscribeTable("NODE1", "trades_stream", "trades", 0, saveTradesToDFS{trades}, true, 1000, 1)
```

In the example above, the streaming handler `saveTradesToDFS` saves subscribed data to table dfsTrades. If "NickFoles" does not have privilege to write to table dfsTrades, then the streaming task will fail. 

#### 2.3.2 Streaming Engines

You can also execute `addAccessControl` on streaming engines to prevent the engines from being written to or dropped by other users.

For example, log in as "MitchTrubisky" to create a time-series streaming engine and add access control on the engine:

```
login(`MitchTrubisky, "JI3564^")
agg1 = createTimeSeriesEngine(name="agg1", windowSize=60000, step=60000, metrics=<[sum(volume)]>, dummyTable=trades, outputTable=output1, keyColumn=`sym)
addAccessControl(agg1)
```

Similar with a shared in-memory table, if `addAccessControl` is not executed after the engine is created, then the engine can be written to or dropped by all users.

### 2.4 Other Applications

#### 2.4.1 Function View

[Function view](https://www.dolphindb.com/help/DatabaseandDistributedComputing/DatabaseOperations/FunctionView.html) provides a flexible way to control user access to databases and tables. Only administrators can define or delete a function view. Users can get the result of a function view on a table when they don't have the privileges to read the table. 

For example, an administrator defines the function view "countTradeAll" and grants user "NickFoles" the privilege to execute the function view:

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

Although NickFoles cannot read table "dfs://TAQ/Trades", he can execute function view `countTradeAll` to get the number of rows in the table.

Function views can have parameters. In the following example, we create a function view to get the trades of a specified stock on a specified date:

```
def getTrades(s, d){
	return select * from loadTable("dfs://TAQ","Trades") where sym=s, date=d
}
addFunctionView(getTrades)
grant("NickFoles",VIEW_EXEC,"getTrades")
```

Log in as "NickFoles", and execute function view `getTrades` with specified stock symbol and date：

```
getTrades("IBM", 2018.07.09)
```

#### 2.4.2 Scheduled Jobs

When a user schedules a job, she does not need to have access privileges on the objects that are involved. However, if the user does not have privileges to access the objects when the scheduled job is set to be executed, the scheduled job will not be executed.

```
login("NickFoles","AB123!@")  
def readTable(){  
	read_t1=loadTable("dfs://db1","t1")  
	return exec count(*) from read_t1  
}  
scheduleJob("readTableJob","read DFS table",readTable,minute(now()),date(now()),date(now())+1,'D');
```

In the example above, job `readTable` can be scheduled even if user NickFoles does not have privilege to read table "dfs://db1/t1". When the job is set to be executed, however, if "NickFoles" does not have privilege to read table "dfs://db1/t1", the job will not be executed. 

Administrators can delete all scheduled job with command `deleteScheduledJob`; a user can only delete scheduled jobs created by herself. 

## 3. Secure Communication with HTTPS

DolphinDB supports HTTPS for secure communication over the web. 

### 3.1 Enable HTTPS

There are 2 ways to enable HTTPS:

* Add "enableHTTPS=true" in the configuration file of the cluster controller (*controller.cfg*);

* Add `-enableHTTPS true` in the command line when starting the cluster controller. 

### 3.2 HTTPS Certificate

You need to install server authentication certificate at each server in DolphinDB for secure connections. There should be a certificate on the controller and each of the agent nodes. Data nodes use the certificate located at the agent node on the same server. 

#### 3.2.1 Certificate Authority (CA) Certificate

Get a certificate from a certificate authority, rename it as server.crt, and copy to the folder "keys" under the home directory of the controller. If the folder "keys" does not exist, we need to create it. The certificate does not need to be installed as it is from a certificate authority. This is recommended in most use cases. 

#### 3.2.2 Self-Signed Authentication Certificate

Sometimes we may want to install a self-signed authentication certificate. For example, in a small isolated cluster or in a research (non-production) setting. Please take the following steps:

(1) Set the configuration parameter *publicName* as the domain name of the computer.

The following is an example of the command line in Linux to start the controller, where www.ABCD.com is the domain name of the server where the controller is located:

```
./dolphindb -enableHTTPS true -home master -publicName www.ABCD.com -mode controller -localSite 192.168.1.30:8500:rh8500 -logFile  ./log/master.log
```

(2) Check if the authentication certificate and private key have been generated.

Start the controller node and check if the certificate file *server.crt* and the private key for the server serverPrivate.key exist in the folder "keys" under the home directory. 

(3) Install the self-signed certificate to the certificate authority of the web browser.

In Google Chrome, choose Settings -> Advanced -> Manage certificates -> AUTHORITIES-> Import to install the self-signed certificate server.crt. In other web browsers, there might be slight differences in this process. 

![](images/Selection_047.png)  

Now enter https://www.ABCD.com:8500/ in the web browser to connect to DolphinDB cluster manager, where 8500 is the port number of the controller. If you see a green lock sign and "Secure" in the address bar, the authentication certifiate has been successfully installed.

![](images/Selection_046.png)

## 4. SSO (Single Sign-On)

On the web-based cluster manager, we can click any data node to open a notebook on this node. The data node may be located on a different physical server from the controller node. DolphinDB provides SSO (Single Sign-On) so that users don't need to log in the system again when visiting different servers in a cluster.

DolphinDB provides 2 API functions for SSO:
+ `getAuthenticatedUserTicket()`: issue the current user's encrypted ticket
+ `authenticateByTicket(ticket)`: use the ticket generated by `getAuthenticatedUserTicket()` to log in the system. 

DolphinDB developers can use these API functions to develop more functionalities. 
