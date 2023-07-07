# DolphinDB Standalone Deployment on Docker

- [DolphinDB Standalone Deployment on Docker](#dolphindb-standalone-deployment-on-docker)
  - [Environment Setup](#environment-setup)
  - [Quick Starts](#quick-starts)
    - [Docker (X86 Architecture)](#docker-x86-architecture)
    - [Docker (ARM Architecture)](#docker-arm-architecture)
  - [Production Environment for Deployment (X86 Architecture)](#production-environment-for-deployment-x86-architecture)
    - [Online Deployment](#online-deployment)
    - [Offline Deployment](#offline-deployment)
  - [FAQ](#faq)
    - [How to modify a configuration file?](#how-to-modify-a-configuration-file)
    - [How to upgrade?](#how-to-upgrade)
    - [Troubleshooting](#troubleshooting)

This tutorial is a quick start guide describing how to deploy the DolphinDB server standalone on Docker.

## Environment Setup

- **Install Docker**

You can download and install Docker Desktop from its [offical website](https://www.docker.com/products/docker).

- **Pull the Docker image of DolphinDB**

The latest Docker images are available on [Docker hub repository](https://hub.docker.com/u/dolphindb). 

Take the tag v2.00.5 for example:

```bash
docker pull dolphindb/dolphindb:v2.00.5
```

- **Host**

| Host | IP            | Docker Service  | Mount Point |
| :----- | :------------ | :-------- | :--------- |
| host1  | xxx.xxx.xx.xx | dolphindb | /ddbdocker |

## Quick Starts

### Docker (X86 Architecture)

(1) Run the following script on your machine to create a Docker container:

  ```shell
  docker run -itd --name dolphindb \
    --hostname host1 \
    -p 8848:8848 \
    -v /etc:/dolphindb/etc \
    dolphindb/dolphindb:v2.00.5 \
    sh
  ```
  
Parameters:
- `--hostname`: The host name (which is used to collect machine fingerprint for Enterprise Edition License). You can check the host name with the hostname shell command.
- `-p`: The first port 8848 is the host port, and the latter one is the port mapped to the DolphinDB container (the default port). After startup, you can access DolphinDB through the local port 8848.  
- `-v`: Map the /etc directory of the host to the container (/dolphindb/etc). It is used to collect machine fingerprint for Enterprise Edition License. 
- `--name`: The name of the container. You can perform operations on the container, such as checking container-related information, by specifying a container name. If not specified, a random name will be assigned. Note that the container name must be unique.
- `dolphindb/dolphindb:v2.00.5`: It is a required parameter, which is used to specify the image. The image name must be complete (including dolphindb repository and version), for example, dolphindb/dolphindb:v2.00.5.
  
(2) Run the following script to check whether the container is successfully created:

  ```shell
  docker ps|grep dolphindb
  ```

  The following information indicates a successful operation:

  ```shell
  347bfa54df86   dolphindb/dolphindb:v2.00.5   "sh -c 'cd /data/ddb…"   20 seconds ago   Up 19 seconds   0.0.0.0:8848->8848/tcp, :::8848->8848/tcp   dolphindb
  ```

(3) Connect to DolphinDB with the client and conduct a test. <!--For detailed instructions, refer to DolphinDB: Client Tools.-->
  

### Docker (ARM Architecture)

(1) Run the following script on your machine to create a Docker container:

```
docker run -itd --name dolphindb \
  --hostname cnserver10 \
  -p 8848:8848 \
  -v /etc:/dolphindb/etc \
  dolphindb/dolphindb-arm64:v2.00.7 \
  sh
```

Parameters:
- `--hostname`: The host name (which is used to collect machine fingerprint for Enterprise Edition License). You can check the host name with the hostname shell command.
- `-p`: The first port 8848 is the host port, and the latter one is the port mapped to the DolphinDB container (the default port). After startup, you can access DolphinDB through the local port 8848.
- `-v`: Map the /etc directory of the host to the container (/dolphindb/etc). It is used to ccollect machine fingerprint for Enterprise Edition License.
- `--name`: The name of the container. You can perform operations on the container, such as checking container-related information, by specifying a container name. If not specified, a random name will be assigned. Note that the container name must be unique.
- `dolphindb/dolphindb-arm64:v2.00.7`: It is a required parameter, which is used to specify the image. The image name must be complete (including dolphindb repository and version), for example, dolphindb/dolphindb-arm64:v2.00.7.

(2) Run the following script to check whether the container is successfully created:

  ```
  docker ps|grep dolphindb
  ```

  The following information indicates a successful operation:

  ```
  347bfa54df86   dolphindb/dolphindb-arm64:v2.00.7   "sh -c 'cd /data/ddb…"   20 seconds ago   Up 19 seconds   0.0.0.0:8848->8848/tcp, :::8848->8848/tcp   dolphindb
  ```

(3) Connect to DolphinDB with the client and conduct a test. <!--For detailed instructions, refer to DolphinDB: Client Tools.-->

## Production Environment for Deployment (X86 Architecture)

###  Online Deployment

(1) Run the following script to download the installation package and configure the mapping file (take v2.00.5 for example):

  ```shell
  git clone --depth=1 https://github.com/dolphindb/dolphindb-k8s && \
  cd dolphindb_k8s/docker-single && \
  sh map_dir.sh
  ```

  <!-- >> 注意: 由于新建的目录是 `/ddbdocker`，可能遇到用户新建权限问题，需自行修改可以用户可以创建权限的文件夹 -->

  (2) Run the following command:

  ```
  tree /ddbdocker
  ```

  Expected output:

  ```
  ├── ddbdocker
  │   ├── data
  │   ├── ddb_related
  │   │   ├── dolphindb.cfg
  │   │   └── dolphindb.lic
  │   └── plugins
  │       ├── hdf5
  │       │   ├── libPluginHdf5.so
  │       │   └── PluginHdf5.txt
  │       ├── mysql
  │       │   ├── libPluginMySQL.so
  │       │   └── PluginMySQL.txt
  │       ├── odbc
  │       │   ├── libPluginODBC.so
  │       │   └── PluginODBC.txt
  │       └── parquet
  │           ├── libPluginParquet.so
  │           └── PluginParquet.tx
  ```

  Description for the above files/folders:

  | Name          | Function                                   | Directory of Host                      | Directory of Container         |
  | ------------- | ------------------------------------------- | ------------------------------------- | ------------------------------ |
  | dolphindb.cfg | the configuration file for a standalone mode           | /ddbdocker/ddb_related/dolphindb.cfg  | /data/ddb/server/dolphindb.cfg |
  | dolphindb.lic | license file of DolphinDB (contact the IT for an Enterprise Edition License)| /ddbdocker/ ddb_related/dolphindb.lic | /data/ddb/server/dolphindb.lic |
  | plugins       | stores DolphinDB plugins                       | /ddbdocker/plugins                    | /data/ddb/server/plugins       |
  | data          | stores DolphinDB files on data nodes (e.g., metadata, stream data, tables, etc.) | /ddbdocker/data | /data/ddb/server/data          |

  (3) Start the container with the following script:

  ```shell
  docker run -itd --name dolphindb \
  -p 8848:8848 \
  --ulimit nofile=1000000:1000000 \
    -v /etc:/dolphindb/etc \
    -v /ddbdocker/ddb_related/dolphindb.cfg:/data/ddb/server/dolphindb.cfg \
    -v /ddbdocker/ddb_related/dolphindb.lic:/data/ddb/server/dolphindb.lic \
    -v /ddbdocker/plugins:/data/ddb/server/plugins \
    -v /ddbdocker/data:/data/ddb/server/data \
    dolphindb/dolphindb:v2.00.5 \
    sh \
    -stdoutLog 1
  ```

  The expected container ID: `3cdfbab788d0054a80c450e67d5273fb155e30b26a6ec6ef8821b832522474f5`。

(4) Connect to DolphinDB with the client and conduct a test. <!--For detailed instructions, refer to DolphinDB: Client Tools.-->

### Offline Deployment

(1) Download the corresponding DolphinDB server image from the [official website](https://dolphindb.com/downloads/).

(2) Add `map_dir.sh` to the same directory as the downloaded ZIP archives as follows:

  ```bash
  #!/bin/bash
  set -e
  clear
  # Create a new folder to store the corresponding files
  dir1=/ddbdocker
  dir2=/ddbdocker/ddb_related
  
  if [ ! -e "$dir1" ]; 
  then
      mkdir $dir1
  fi
  
  if [ ! -e "$dir2" ]; 
  then
      mkdir $dir2
  fi
  
  
  # Obtain the installation package
  ddb_zip=$(ls ./DolphinDB_Linux64_V*.zip)
  ddb_name=$(basename $ddb_zip .zip)
  
  if [ -e $ddb_zip ];
  then
      echo -e "Upload installation package successfully" "\033[32m UpLoadSuccess\033[0m"
  else
      echo -e "The installation package cannot be found, please upload to this directory" "\033[31m UpLoadFailure\033[0m"
      echo ""
      sleep 1
      exit
  fi
  #解压安装包
  unzip "${ddb_zip}" -d "${ddb_name}" 
  if [ -d ./$ddb_name ];then
      echo -e "Unzip installation package successfully" "\033[32m UnzipSuccess\033[0m"
  else
      echo -e "Unzip installation package failed, check if the installation package is downloaded completely" "\033[31m UnzipFailure\033[0m"
      echo ""
      sleep 1
      exit
  fi
  
  # Get the source and target files (folders) under the corresponding paths
  source_f1=./${ddb_name}/server/dolphindb.cfg
  source_f2=./${ddb_name}/server/dolphindb.lic
  source_dir4=./${ddb_name}/server/plugins
  
  f1=/ddbdocker/ddb_related/dolphindb.cfg
  f2=/ddbdocker/ddb_related/dolphindb.lic
  dir3=/ddbdocker/data
  dir4=/ddbdocker/plugins
  
  
  # Iterate over the target paths and set conditional statements to determine if existing files are to be overwritten
  function isCovered() {  
  
  for i in $*;
  do
      if [ -e $i ];
      then
          #echo $i
          read -p "The $i has already existed, would you want to recover or clean it and other similar ones?(y/n)" answer
          if [ $answer=="y" ];
          then
              break
          else
              echo ""
              sleep 1
              exit
          fi
      fi
  done
  }
  
  isCovered $f1 $f2 $dir3 $dir4
  
  # Make a copy of the corresponding file (folder)
  cp -rpf $source_f1 $f1
  cp -rpf $source_f2 $f2
  
  if [ -e "$dir3" ]; 
  then
      rm -rf $dir3
  fi
  
  mkdir $dir3
  cp -rpf $source_dir4 $dir4
  
  # Delete the installation package
  rm -rf ./${ddb_name}
  
  ```
  
(3) Run the following command:

  ```
  sh map_dir.sh && tree /ddbdocker
  ```

Expected output:

  ```
  ├── ddbdocker
  │   ├── data
  │   ├── ddb_related
  │   │   ├── dolphindb.cfg
  │   │   └── dolphindb.lic
  │   └── plugins
  │       ├── hdf5
  │       │   ├── libPluginHdf5.so
  │       │   └── PluginHdf5.txt
  │       ├── mysql
  │       │   ├── libPluginMySQL.so
  │       │   └── PluginMySQL.txt
  │       ├── odbc
  │       │   ├── libPluginODBC.so
  │       │   └── PluginODBC.txt
  │       └── parquet
  │           ├── libPluginParquet.so
  │           └── PluginParquet.tx
  ```

  Description for the above files/folders:

| Name  | Function                              | Directory of Host                        | Directory of Container                   |
| ------------- | ------------------------------------------- | ------------------------------------- | ------------------------------ |
| dolphindb.cfg | the configuration file for a standalone mode            | /ddbdocker/ddb_related/dolphindb.cfg  | /data/ddb/server/dolphindb.cfg |
| dolphindb.lic | license file of DolphinDB (contact the IT for an Enterprise Edition License) | /ddbdocker/ ddb_related/dolphindb.lic | /data/ddb/server/dolphindb.lic |
| plugins       | stores DolphinDB plugins                       | /ddbdocker/plugins                    | /data/ddb/server/plugins       |
| data          | stores DolphinDB files on data nodes (e.g., metadata, stream data, tables, etc.)| /ddbdocker/data | /data/ddb/server/data          |

  (4) Start the container with the following script:

```shell
docker run -itd --name dolphindb \
  -p 8848:8848 \
  --ulimit nofile=1000000:1000000 \
  -v /etc:/dolphindb/etc \
  -v /ddbdocker/ddb_related/dolphindb.cfg:/data/ddb/server/dolphindb.cfg \
  -v /ddbdocker/ddb_related/dolphindb.lic:/data/ddb/server/dolphindb.lic \
  -v /ddbdocker/plugins:/data/ddb/server/plugins \
  -v /ddbdocker/data:/data/ddb/server/data \
  dolphindb/dolphindb:v2.00.5 \
  sh \
  -stdoutLog 1
```

The expected container ID: `3cdfbab788d0054a80c450e67d5273fb155e30b26a6ec6ef8821b832522474f5`。

(5) Connect to DolphinDB with the client and conduct a test. <!--For detailed instructions, refer to DolphinDB: Client Tools.-->

## FAQ

### How to modify a configuration file?

Find the mapped DolphinDB configuration file *dolphindb.cfg* on the host, e.g., */ddbdocker/ddb_related/dolphindb.cfg*.

```shell
localSite=localhost:8848:local8848
mode=single
maxMemSize=32
maxConnections=512
workerNum=4
localExecutors=3
dataSync=1
chunkCacheEngineMemSize=2
newValuePartitionPolicy=add
maxPubConnections=64
subExecutors=4
subPort=8849
lanCluster=0
```

- `localSite`: IP address, port number and alias of the controller node. The default localSite for a standalone mode is *localhost:8848:local8848*, where 8848 is the the port number (mandatory) on which DolphinDB is running.
- `workerNum`: The size of worker pool for regular interactive jobs. The default value is the number of CPU cores.
- `localExecutors`: The number of local executors. The default value is the number of CPU cores - 1.
- `maxMemSize`: The maximum memory (in units of GB) allocated to DolphinDB. If set to 0, it means no limits on memory usage. It is recommended to set it to a value lower than the machine's memory capacity.

  For more configuration parameters, refer to [DolphinDB Configuration: Standalone Mode](https://www.dolphindb.com/help200/DatabaseandDistributedComputing/Configuration/StandaloneMode.html).

### How to upgrade?

(1) Pull the new version of DolphinDB image (take version 2.00.6 for example):

```shell
  docker pull dolphindb/dolphindb:v2.00.6
```

(2) Upgrade with the following commands:

```shell
  docker run -itd --name dolphindb \
    -p 8848:8848 \
    --ulimit nofile=1000000:1000000 \
    -v /etc:/dolphindb/etc \
    -v /ddbdocker/ddb_related/dolphindb.cfg:/data/ddb/server/dolphindb.cfg \
    -v /ddbdocker/ddb_related/dolphindb.lic:/data/ddb/server/dolphindb.lic \
    -v /ddbdocker/plugins:/data/ddb/server/plugins \
    -v /ddbdocker/data:/data/ddb/server/data \
    dolphindb/dolphindb:v2.00.6 \
    sh \
    -stdoutLog 1
```
The upgrade operation of DolphinDB server only applies to the installation package. Therefore, to avoid unnecessary replacement of configuration files, license files, plugins, and built-in data files that are beyond the scope of upgrade operation, make sure to back up the following files and directories before upgrading:

- Configuration file: dolphindb.cfg;
- License file: dolphindb.lic;
- Directory where plugins are located: /plugins/;
- Data file: /data/.

**Note**: 
* Since the name of Docker container must be unique, if the previous container is kept, the new container name must be different from the previous one;
* The port number is not occupied.

(3) Connect to the node via GUI and execute the following command to check the version number to see whether the upgrade is successful.

```shell
  version()
```

  期望输出:

```shell
  2.00.6
```

### Troubleshooting

(1) **Error messages**:

  ```bash
  Can't find time zone database. Please use parameter tzdb to set the root directory of time zone database.
  ```

**Solution**: If the Docker image does not contain the `tzdata` package (e.g., `ubuntu:latest`), the above error will be reported at startup. Execute the following command to install the `tzdata` package:
  
    ```bash
    apt-get install tzdata
    ```

(2) **Error messages**:
  
    ```bash
    <ERROR> : Failed to retrieve machine fingerprint
    ```
  
**Solution**: Since the official license requires machine fingerprint which Docker does not have access to, the above exception will be thrown in the logs at startup. You need to add the following parameters to `docker run`:

    ```bash
    -v /etc:/dolphindb/etc 
    ```
  
(3) **Error messages**:
  
    ```bash
    docker: Error response from daemon: driver failed programming external connectivity on endpoint dolphindb (178a842284d64fbe128ff3f1188ead76ef4072c9149226f8bf62dc7795a58603): Error starting userland proxy: listen tcp4 0.0.0.0:8848: bind: address already in use.
    ```
  
**Solution**: Change the port number of the host, or use the following command to check whether the port is available or not:
  
    ```shell
    lsof -i:8848
    COMMAND     PID USER   FD   TYPE    DEVICE SIZE/OFF NODE NAME
    dolphindb 17238 root    6u  IPv4 231927135      0t0  TCP *:8848 (LISTEN)
    ```
  
    



