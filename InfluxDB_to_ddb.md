# Data Migration: From InfluxDB to DolphinDB

This tutorial introduces how to migrate data from InfluxDB to DolphinDB with an IoT example.

- [Data Migration: From InfluxDB to DolphinDB](#data-migration-from-influxdb-to-dolphindb)
  - [1. Migration Methods](#1-migration-methods)
  - [2. Migration Steps with an IoT case](#2-migration-steps-with-an-iot-case)
    - [2.1 Import Sample Data to InfluxDB](#21-import-sample-data-to-influxdb)
    - [2.2 Create a DolphinDB Database and Table](#22-create-a-dolphindb-database-and-table)
    - [2.3 Deployment](#23-deployment)
    - [2.4 Configure a Migration Job](#24-configure-a-migration-job)
      - [2.4.1 Create a Configuration File](#241-create-a-configuration-file)
      - [2.4.2 Convert the Date and Time Values](#242-convert-the-date-and-time-values)
    - [2.5 Synchronize Data](#25-synchronize-data)
  - [3. Appendices](#3-appendices)
    - [3.1 Configuration Parameters for InfluxDB2 Reader](#31-configuration-parameters-for-influxdb2-reader)
    - [3.2 Configuration Parameters for DolphinDBWriter Plugin](#32-configuration-parameters-for-dolphindbwriter-plugin)


## 1. Migration Methods

There are multiple methods for accessing InfluxDB. Regarding data export, however, users tend to migrate data from InfluxDB to other platforms with APIs, which comes with a cost in development.

Tools such as Addax have been introduced to implement efficient data synchronization between heterogeneous databases. We recommend Addax-DolphinDBWriter plugin, which is developed based on Addax, to migrate data from InfluxDB to DolphinDB. 

## 2. Migration Steps with an IoT case

This tutorial takes IoT monitoring scenario as an example to demonstrate how to migrate device metrics from InfluxDB to DolphinDB.

### 2.1 Import Sample Data to InfluxDB

The sample data used in the following case is obtained from InfluxDB official documentation: [Machine production sample data](https://docs.influxdata.com/influxdb/v2.5/reference/sample-data/#machine-production-sample-data).

**Note**: Pay attention to the data types of the migrated data. For the specific data types supported by DolphinDB, you can refer to [Data Types](https://www.dolphindb.com/help200/DataTypesandStructures/DataTypes/index.html).

Create an InfluxDB bucket, and import sample data to the bucket ([genMockData.flux](script/InfluxDB_to_ddb/genMockData.flux)).

```
import "influxdata/influxdb/sample"

sample.data(set: "machineProduction")
    |> to(bucket: "demo-bucket")
```

### 2.2 Create a DolphinDB Database and Table

Create a database and a table in DolphinDB to store the migrated data. You need to define a database with reasonable partition scheme according to the data to be migrated. For more instructions, see [DolphinDB Partitioned Database Tutorial](https://github.com/dolphindb/Tutorials_EN/blob/master/database.md).

The following script creates database "dfs://demo" and partitioned table "pt" [createTable.dos](script/InfluxDB_to_ddb/createTable.dos).

```
login("admin","123456")

dbName="dfs://demo"
tbName="pt"

colNames=`time`stateionID`grinding_time`oil_temp`pressure`pressure_target`rework_time`state
colTypes=[NANOTIMESTAMP,SYMBOL,DOUBLE,DOUBLE,DOUBLE,DOUBLE,DOUBLE,SYMBOL]
schemaTb=table(1:0,colNames,colTypes)

db = database(dbName, VALUE,2021.08.01..2022.12.31)
pt = db.createPartitionedTable(schemaTb, "pt", `time)
```

### 2.3 Deployment

- Deploy Addax

There are two methods for installing [Addax](https://wgzhao.github.io/Addax/develop/quickstart/):

(1) Download the compiled binary package;

(2) Download and compile with the source code.

- Deploy Addax-DolphinDBWriter Plugin

Download the compiled [Addax-DolphinDBWriter plugin](https://github.com/dolphindb/AddaxDolphinDBWriter/tree/master/dolphindbwriter) and copy it to the addax/plugin/writer directory. Alternatively, you can choose to compile on your own.

### 2.4 Configure a Migration Job

Create a configuration file to define the migration job based on Addax's job configuration. Pay attention to the format conversion of date and time values (refer to [Convert the Date and Time Values](#242-convert-the-date-and-time-values)).

#### 2.4.1 Create a Configuration File

The specific content of the configuration file is as follows ([influx2ddb.json](script/InfluxDB_to_ddb/influx2machine.json)). For detailed information on parameters, refer to [Appendices](#3-appendices).

```
{
  "job": {
    "content": {
      "reader": {
        "name": "influxdb2reader",
        "parameter": {
          "column": ["*"],
          "connection": [
            {
              "endpoint": "http://183.136.170.168:8086",
              "bucket": "demo-bucket",
              "table": [
                  "machinery"
              ],
              "org": "zhiyu"
            }
          ],
          "token": "GLiPjQFQIxzVO0-atASJHH4b075sTlyEZGrqW20XURkelUT5pOlfhi_Yuo2fjcSKVZvyuO00kdXunWPrpJd_kg==",
          "range": [
            "2007-08-09"
          ]
        }
      },
      "writer": {
        "name": "dolphindbwriter",
        "parameter": {
          "userId": "admin",
          "pwd": "123456",
          "host": "115.239.209.122",
          "port": 3134,
          "dbPath": "dfs://demo",
          "tableName": "pt",
          "batchSize": 1000000,
          "saveFunctionName": "transData",
          "saveFunctionDef": "def parseRFC3339(timeStr) {if(strlen(timeStr) == 20) {return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ssZ'));} else if (strlen(timeStr) == 24) {return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ss.SSSZ'));} else {return timeStr;}};def transData(dbName, tbName, mutable data) {timeCol = exec time from data; timeCol=each(parseRFC3339, timeCol);  writeLog(timeCol);replaceColumn!(data,'time', timeCol); loadTable(dbName,tbName).append!(data); }",
          "table": [
              {
                "type": "DT_STRING",
                "name": "time"
              },
              {
                "type": "DT_SYMBOL",
                "name": "stationID"
              },
              {
                "type": "DT_DOUBLE",
                "name": "grinding_time"
              },
              {
                "type": "DT_DOUBLE",
                "name": "oil_temp"
              },
              {
                "type": "DT_DOUBLE",
                "name": "pressure"
              },
              {
                "type": "DT_DOUBLE",
                "name": "pressure_target"
              },
              {
                "type": "DT_DOUBLE",
                "name": "rework_time"
              },
              {
                "type": "DT_SYMBOL",
                "name": "state"
              }
          ]
        }
      }
    },
    "setting": {
      "speed": {
        "bytes": -1,
        "channel": 1
      }
    }
  }
}
```

#### 2.4.2 Convert the Date and Time Values

InfluxDB 2.0 stores date and time values in RFC3339 format with timezone information, while DolphinDB only stores local time. A conversion error will be raised when date and time values from InfluxDB is migrated to DolphinDB directly. We need to define a function in DolphinDBWriter plugin (with the saveFunctionName and saveFunctionDef parameters) to convert the data.  

Below is the user-defined function specified for *saveFunctionDef* in the configuration file:

```
def parseRFC3339(timeStr) {
	if(strlen(timeStr) == 20) {
		return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ssZ'));
	} else if (strlen(timeStr) == 24) {
		return localtime(temporalParse(timeStr,'yyyy-MM-ddTHH:mm:ss.SSSZ'));
	} else {
		return timeStr;
	}
}

def transData(dbName, tbName, mutable data) {
	timeCol = exec time from data; writeLog(timeCol);
	timeCol=each(parseRFC3339, timeCol);
	replaceColumn!(data, 'time', timeCol);
	loadTable(dbName,tbName).append!(data);
}
```

In the example above, function `parseRFC3339` is nested within function `transData`. Therefore, parameter *saveFunctionName* is specified as “transData” as it is called by the plugin directly. 

Function `parseRFC3339` uses the [temporalParse](https://www.dolphindb.com/help200/FunctionsandCommands/FunctionReferences/t/temporalParse.html) function to convert a string to a DolphinDB temporal data type, and the [localtime](https://www.dolphindb.com/help200/FunctionsandCommands/FunctionReferences/l/localtime.html) function to convert it to local time. With the time column returned by function `parseRFC3339`, function `transData` then calls [append!](https://www.dolphindb.com/help200/FunctionsandCommands/FunctionReferences/a/append%21.html) to write data to the DolphinDB DFS table.

Note: If your business does not require time zone conversion, you can just use the result returned by `temporalParse`.

For time zone-related issues, refer to [Time Zones in DolphinDB](https://github.com/dolphindb/Tutorials_EN/blob/master/timezone.md).

### 2.5 Synchronize Data

Run the migration job configured in the file above.

```
./bin/addax.sh ~/addax/job/influx2ddb.json
```

**Note**: The configuration file influx2ddb.json is placed in the addax/job directory in this case. You can change to the directory where the configuration file is located.

The log is displayed as follows:

```
2022-12-13 21:17:17.870 [job-0] INFO  JobContainer         -
Start Time                     : 2022-12-13 21:17:14
End Time                       : 2022-12-13 21:17:17
Elapsed Time                   :                  3s
Average Flow                   :          345.07KB/s
Write Speed                    :           6568rec/s
Total Read Records             :               19705
Total Failed Attempts          :                   0
```

You can specify the filtering condition in the parameter range to the "reader" part of *influxdb2ddb.json* to incrementally synchronize the selected data.

The above case illustrates the process of migrating data from InfluxDB 2.0 to DolphinDB. For InfluxDB 1.0, replace the InfluxDB2 Reader plugin with InfluxDB Reader plugin in the configuration file (influx2ddb.json).

## 3. Appendices

### 3.1 Configuration Parameters for InfluxDB2 Reader

| **Parameters** | **Required** | **Data Type** | **Default** | **Description** |
| --- | --- | --- | --- | --- |
| endpoint | ✔   | string |  /   | InfluxDB connection string   |
| token | ✔   | string | /   | Token to access to the database |
| table |    | list | /   | The name of the table to be synchronize |
| org | ✔   | string | /   | InfluxDB org name |
| bucket | ✔   | string | /   | InfluxDB bucket name |
| column |    | list | /   | A JSON array indicating column names of the table to be synchronized. A asterisk symbol (\*) indicates that all columns are to be synchronized, e.g. ["*"] |
| range | ✔   | list | /   | The time range of the data to be read |
| limit |    | int | /   | The limit to the number of records acquired |

### 3.2 Configuration Parameters for DolphinDBWriter Plugin

| **Parameters** | **Required** | **Data Type** | **Default** | **Description** |
| --- | --- | --- | --- | --- |
| host | ✔   | string | /    | Server Host |
| port | ✔   | int | /    | Server Port |
| userId | ✔   | string | /    | DolphinDB username  <br> Note that when importing data to a DFS database, the user must be granted appropriate privileges. |
| pwd | ✔   | string | /    | Password for DolphinDB user |
| dbPath | ✔   | string | /    | The target database to be written to, e.g., "dfs://MYDB". |
| tableName | ✔  | string | /    | The target table |
| batchSize |    | int | 10000000 | The number of records to be written for each batch |
| table | ✔  |     |     | Column names of the table to be written to. For more information, refer to the details below. |
| saveFunctionName |    | string | /    | User-defined function to process data. If it is not specified, the data will be inserted into DolphinDB with function `tableInsert`. If specifed, the data will be processed with the specified function. |
| saveFunctionDef |    | string | /    | User-defined function to append data to the database. It takes three arguments: *dfsPath*, *tbName*, and *data* (the table to be imported). |

**Details of parameter *table*:**

*table* specifies the columns of the table to be written to.

```
 {"name": "columnName", "type": "DT_STRING", "isKeyField":true}
```

Note that the order of specified columns must be consistent with the table to be imported.

- name: the column names;
- isKeyField: to determine whether the column is the key column. The default value is true. It is used to identify the primary key when updating data.
- type: the mapping between the DolphinDB data type and its value is listed below:


| DolphinDB Data Type | Value of Type |
| --- | --- |
| DOUBLE | DT\_DOUBLE |
| FLOAT | DT\_FLOAT |
| BOOL | DT\_BOOL |
| DATE | DT\_DATE |
| MONTH | DT\_MONTH |
| DATETIME | DT\_DATETIME |
| TIME | DT\_TIME |
| SECOND | DT\_SECOND |
| TIMESTAMP | DT\_TIMESTAMP |
| NANOTIME | DT\_NANOTIME |
| NANOTIMETAMP | DT\_NANOTIMETAMP |
| INT | DT\_INT |
| LONG | DT\_LONG |
| UUID | DT\_UUID |
| SHORT | DT\_SHORT |
| STRING | DT\_STRING |
| SYMBOL | DT\_SYMBOL |