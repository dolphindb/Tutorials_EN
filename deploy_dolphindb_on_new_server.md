# DolphinDB Deployment on a New Server

This tutorial introduces how to deploy DolphinDB on a new server. It helps you find out an appropriate deployment option that improves the stability, maintainability, and efficiency of DolphinDB server, thus better meeting your business requirements.

- [DolphinDB Deployment on a New Server](#dolphindb-deployment-on-a-new-server)
  - [1. Environment Setup](#1-environment-setup)
    - [1.1 Platforms](#11-platforms)
    - [1.2 File System and inode](#12-file-system-and-inode)
    - [1.3 Mount on a New Disk](#13-mount-on-a-new-disk)
    - [1.4 Enable core dump](#14-enable-core-dump)
    - [1.5 Increase the Maximum Number of Open Files](#15-increase-the-maximum-number-of-open-files)
    - [1.6 NTPD](#16-ntpd)
    - [1.7 Configure a Firewall](#17-configure-a-firewall)
    - [1.8 Swap](#18-swap)
  - [2. DolphinDB Deployment](#2-dolphindb-deployment)
    - [2.1 Standalone/Single-Server Cluster/Multi-Machine Cluster](#21-standalonesingle-server-clustermulti-machine-cluster)
    - [2.2 Docker or Non-Docker Environment](#22-docker-or-non-docker-environment)
    - [2.3 Configuration Parameters for Production Environment](#23-configuration-parameters-for-production-environment)
    - [2.4 Deployment Procedures](#24-deployment-procedures)
    - [2.5 Startup Process](#25-startup-process)
  - [3. Appendices](#3-appendices)

## 1. Environment Setup

### 1.1 Platforms

#### 1.1.1 Supported Platforms <!-- omit in toc -->

<table>
    <thead>
        <tr>
            <th>Platforms</th>
            <th>Processor architecture</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=3>Linux</td>
            <td>x86</td>
        </tr>
        <tr>
            <td>arm</td>
        </tr>
        <tr>
            <td>Loongson</td>
        </tr>
        <tr>
            <td>Windows</td>
            <td>x86</td>
        </tr>
    </tbody>
</table>

We use CentOS 7.9.2009 as an example to introduce system configurations.

- If you use Linux system, it requires Linux kernel version 2.6.19 or higher. Stable release of CentOS 7 is recommended.

- If you use Ubuntu system: 
    -  Select the */home* partition and choose the XFS file system as the format type in the Storage configuration during setup, thus formatting the */home* folder with the XFS file system;
    -  Use command `sudo ufw` disable to turn off the firewall. See `man ufw` for more examples.
    -  If you need to customize the core dumps, use command `sudo systemctl disable apport.service` to disable apport.

#### 1.1.2 Software Dependency <!-- omit in toc -->

DolphinDB relies on GCC 4.8.5 or higher. Use the following command to install GCC on CentOS 7 stable release:

```console
# yum install -y gcc
```

#### 1.1.3 Recommended Hardware Configuration <!-- omit in toc -->

To optimize the system performance, the following hardware configurations are recommended:

- **Metadata & redo log**: It is recommended to use one SSD with small capacity; for higher reliability requirements, RAID1 with two SSDs are recommended;

- **Data entity**: Use SSDs for better performance; or implement concurrent operations with multiple mechanical hard drives as a more economic choice.
    
**Note**: The disk capacity and read/write performance using 1 SSD or multiple HDDs depend on actual business needs.

### 1.2 File System and inode

#### 1.2.1 Initialize the File System <!-- omit in toc -->

**Recommended**: For Linux system, XFS file system is recommended. It has the capability to not only accommodate hard links but also allows for the dynamic adjustment of the number of inode. If there are not enough inodes on the file system, you may encounter issues when DolphinDB attempts to write new files. In such case, additional inodes need to be added dynamically.

**Not Recommended**: File system that does not support hard links, such as beegfs, is not recommended, due to its slow update performance.

The root user or a user with root privileges (who has to add "sudo" to the beginning of the command) connects to the CentOS server via SSH. Use the `df -T` command to check the file system type:

```console
# df -T
Filesystem                Type    1K-blocks    Used   Avail Use% Mounted on
devtmpfs                devtmpfs  3992420       0  3992420    0% /dev
tmpfs                   tmpfs     4004356       0  4004356    0% /dev/shm
tmpfs                   tmpfs     4004356    8748  3995608    1% /run
tmpfs                   tmpfs     4004356       0  4004356    0% /sys/fs/cgroup
/dev/mapper/centos-root xfs      52403200 1598912 50804288    4% /
/dev/sda1               xfs       1038336  153388   884948   15% /boot
tmpfs                   tmpfs      800872       0   800872    0% /run/user/0
/dev/mapper/centos-home xfs      42970624   33004 42937620    1% /home
```

The */home* folder is formatted in xfs, and the DolphinDB data file can be put under this directory.

**Note**: The XFS file system is recommended only for the folder string data files. The installation, metadata, and log folder can be ext4 or other file systems.

If the */home* folder is formatted in ext4 or other file systems that cannot change the number of inodes, follow steps below to format it with the XFS file system:

1. Back up data in */home*
    

```console
# cd /
# cp -R /home /tmp
```

2. Unmount */home* and remove the corresponding logical volume

```console
# umount /home
# lvremove /dev/mapper/centos-home
Do you really want to remove active logical volume centos/home? [y/n]: y
  Logical volume "home" successfully removed
```

3. Check the available free space on your hard drive

```console
# vgdisplay | grep Free
  Free  PE / Size       10527 / 41.12 GiB # left 41.12 GB
```

4. Create a new logical volume */home* and format it in xfs

```console
# lvcreate -L 41G -n home centos # the size of new logical volume is determined by available free space
WARNING: xfs signature detected on /dev/centos/home at offset 0. Wipe it? [y/n]: y
  Wiping xfs signature on /dev/centos/home.
  Logical volume "home" created.
# mkfs.xfs /dev/mapper/centos-home
```

5. Mount the */home* directory, and restore the data

```console
# mount /dev/mapper/centos-home /home
# mv /tmp/home/* /home/
# chown owner /home/owner # Reassign privileges to the owner. It has to be modified with the user name.
```

#### 1.2.2 Set the Number of inodes for XFS File System <!-- omit in toc -->

If there is enough disk space for DolphinDB, but you cannot write data because there is no inode available, you can follow the steps below to increase the number of inodes:

1. Check the inode information:
    

```console
# xfs_info /dev/mapper/centos-home | grep imaxpct
data = bsize=4096 blocks=10747904, imaxpct=25
# df -i | grep /dev/mapper/centos-home
file system                Inode    used(I) avail(I) use(I)% Mounted on
/dev/mapper/centos-home 21495808       7 21495801       1% /home
```

The results show that 25% of the space under the */dev/mapper/centos-home* volume is allocated for inodes, and the number of available inodes is 21495801.

2. Increase the number of inodes:

```console
# xfs_growfs -m 30 /dev/mapper/centos-home
meta-data=/dev/mapper/centos-home isize=512    agcount=4, agsize=2686976 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0 spinodes=0
data     =                       bsize=4096   blocks=10747904, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal               bsize=4096   blocks=5248, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
inode max percent changed from 25 to 30
```

3. Check the inode information again:

```console
# df -i | grep /dev/mapper/centos-home
/dev/mapper/centos-home 25794944       7 25794937       1% /home
```

The number of available inodes has increased to 25794937.

#### 1.2.3 Set the Number of inodes for Ext File System <!-- omit in toc -->

When formatting a drive with an ext file system like ext4, it is important to consider the file size and growth to ensure the appropriate inode number. For example, you can specify the number of inodes with the `-N` option in the `mkfs.ext4` command. The default number of inode for the ext4 file system is relatively small, especially when the drive is particularly large, so it is recommended to set a larger value.

### 1.3 Mount on a New Disk

Performance improvement of disk I/O is crucial for big data processing. Recommended hardware configurations can be found in section 1.1.3.

After physically installing a new hard drive or adding one via a cloud service provider, you can connect to the CentOS server via SSH. To add a new hard drive with a capacity of 50G via a virtual machine, follow these steps:

1. Check the disk information by `fdisk -l`:
    

```console
# fdisk -l
...

Disk /dev/sdb: 53.7 GB, 53687091200 bytes, 104857600 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size(logical/physical): 512 bytes/ 512 bytes
I/O size(minimum/optimal): 512 bytes / 512 bytes

...
```

It can be seen that */dev/sdb* is the newly added 50G disk.

2. Use `fdisk` to create and modify partitions:

```console
# fdisk /dev/sdb
Welcome to fdisk (util-linux 2.23.2).

Changes will remain in memory only, until you decide to write them.
Be careful before using the write command.

Device does not contain a recognized partition table
Created a new DOS disklabel with disk identifier 0x7becd49e

Command(m for help): n  # create a new partition
Partition type:
   p   primary (0 primary, 0 extended, 4 free)
   e   extended
Select (default p): p
Partition number (1-4, default 1): 
First sector (2048-104857599, default 2048):
the default value 2048 is used
Last sector, +sectors or +size{K,M,G} (2048-104857599, default 104857599):
the default value 104857599 is used
Created a new partition 1 of type `Linux` and of size 50GiB

Command(m for help): q
```

3. Use command `mkfs.xfs` to create an XFS file system:

```console
# mkfs.xfs /dev/sdb
meta-data=/dev/sdb               isize=512    agcount=4, agsize=3276800 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0, sparse=0
data     =                       bsize=4096   blocks=13107200, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal log           bsize=4096   blocks=6400, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```

4. Create a mount point and mount the drive:

```console
# mkdir -p /mnt/dev1
# mount /dev/sdb /mnt/dev1
```

5. Check the file system type of the new disk:

```console
# df -Th
Filesystem                Type      Size  Used  Avail Use% Mounted on
devtmpfs                devtmpfs  3.9G     0  3.9G    0% /dev
tmpfs                   tmpfs     3.9G     0  3.9G    0% /dev/shm
tmpfs                   tmpfs     3.9G  8.6M  3.9G    1% /run
tmpfs                   tmpfs     3.9G     0  3.9G    0% /sys/fs/cgroup
/dev/mapper/centos-root xfs        50G  1.6G   49G    4% /
/dev/sda1               xfs      1014M  150M  865M   15% /boot
/dev/mapper/centos-home xfs        41G   33M   41G    1% /home
tmpfs                   tmpfs     783M     0  783M    0% /run/user/0
/dev/sdb                xfs        50G   33M   50G    1% /mnt/dev1
```

6. Set auto-mount at startup:

```console
# blkid /dev/sdb
/dev/sdb: UUID="29ecb452-6454-4288-bda9-23cebcf9c755" TYPE="xfs"
# vi /etc/fstab
UUID=29ecb452-6454-4288-bda9-23cebcf9c755 /mnt/dev1             xfs     defaults        0 0
```

Note that the UUID is used to identify the new disk, which avoids identification errors when the disk is replaced or its location is changed.

### 1.4 Enable core dump

[core dump](https://en.wikipedia.org/wiki/Core_dump) consists of the recorded state of the working memory of a computer program when the program has crashed or otherwise terminated abnormally. Therefore, if there is enough space, it is recommended to enable core dump. Below are steps to enable core dump:

1. Create a path to store core files:
    

```console
# mkdir /var/crash # The folder can be modified.
```

**Note**:
- Set aside enough space for the folder to hold core files, where the maximum value is about *maxMemSize*;
- Ensure that DolphinDB has write access to the folder.

2. Enable core dump.

```console
# vi /etc/security/limits.conf
* soft core unlimited
```

It takes effect for all processes. You can also specify the process name to enable core dump only for DolphinDB. Unlimited indicates unlimited size for core files.

3. Set the output path and format for core files.

```console
# vi /etc/sysctl.conf
kernel.core_pattern = /var/crash/core-%e-%s-%u-%g-%p-%t
```

Format:

- %e - the executable filename

- %s - number of signal causing dump

- %u - numeric real UID of dumped process

- %p - PID of dumped process

- %g - numeric real GID of dumped process

- %t - time of dump

- %h - hostname
    

4. Reboot and check if the changes take effect.

```console
# ulimit -c
unlimited
```

We recommend starting DolphinDB in single-node mode to verify whether the core dump configuration takes effect.

```console
$ cd /path_to_dolphindb
$ chmod +x ./startSingle.sh
$ ./startSingle.sh
$ kill -11 dolphindb_pid
$ ls /var/crash/ | grep dolphindb_pid # Check if there is a core file in the folder.
```

### 1.5 Increase the Maximum Number of Open Files

The number of files open simultaneously when running DolphinDB may exceed the default maximum number 1024 on CentOS 7. It is recommended to configure the maximum number of open files to 102400. You can follow steps below:

1. Check the maximum number of open files:
    

```console
# ulimit -n # on a process level
1024
# cat /proc/sys/fs/file-max # on a kernel level
763964
```

It can be seen that the maximum number of file descriptors open in a process is 1024, and 763964 in a Linux host.

2. Set the maximum limit to 102400 for the processes.

```console
# vi /etc/security/limits.conf
* soft nofile 102400
* hard nofile 102400
```

It takes effect for all processes. You can also specify the process name to enable core dump only for DolphinDB.

3. If the configured value for the maximum number of open files in a host is less than 102400, you need to change it to a value no less than 102400:

```console
# vi /etc/sysctl.conf
fs.file-max = 102400
```

The maximum limit of open files in the host here is 763964, which is greater than 102400, so it is not modified.

4. Reboot and check if the changes take effect.

```console
# ulimit -n # on a process level
102400
# cat /proc/sys/fs/file-max # on a kernel level
763964
```

### 1.6 NTPD

If a multi-machine cluster is deployed, it is necessary to configure NTPD (Network Time Protocol Daemon) for time synchronization to ensure the time order of transactions. We configure NTPD server and client on two virtual machines.


| Virtual Machine | IP           | Subnet Mask      | NTPD                                              |
| --------------- | ------------ | ---------------- | ------------------------------------------------- |
| VM 1            | 192.168.0.30 | 255.255.254.0    | server; time synchronization with cn.pool.ntp.org |
| VM 2            | 192.168.0.31 | 255.255.254.0    | client; time synchronization with 192.168.0.30    |

Configure with the following steps:

1. Install the NTP package.
    

```console
# yum install ntp
```

2. Set the time of VM 1 in synchronization with [cn.pool.ntp.org](http://cn.pool.ntp.org)

```console
# vi /etc/ntp.conf
...
# Hosts on local network are less restricted.
restrict 192.168.0.0 mask 255.255.254.0 nomodify notrap

# Use public servers from the pool.ntp.org project.
# Please consider joining the pool (http://www.pool.ntp.org/join.html).
server 0.cn.pool.ntp.org iburst
server 1.cn.pool.ntp.org iburst
server 2.cn.pool.ntp.org iburst
server 3.cn.pool.ntp.org iburst
...
```

The 4th line configures the IP subnet to request the NTP service on the local network with the address 192.168.0.0 and subnet mask 255.255.254.0. The nomodify option prevents client to modify the configuration of the server. The notrap option uses the trap facility for remote event logging.

3. Enable the firewall on VM 1 and add the NTP service.

```console
# firewall-cmd --add-service=ntp --permanent
# firewall-cmd --reload
```

4. Set the time of VM 2 in synchronization with VM 1.

```console
# vi /etc/ntp.conf
...
# Use public servers from the pool.ntp.org project.
# Please consider joining the pool (http://www.pool.ntp.org/join.html).
server 192.168.0.30 iburst
# server 0.centos.pool.ntp.org iburst
# server 1.centos.pool.ntp.org iburst
# server 2.centos.pool.ntp.org iburst
# server 3.centos.pool.ntp.org iburst
...
```

5. Start NTPD on VM 1 and VM 2.

```console
# systemctl enable ntpd
# systemctl restart ntpd
```

6. Wait for a few seconds, and then check the status of NTPD.

VM 1:

```console
# ntpstat
synchronised to NTP server (202.112.31.197) at stratum 2
   time correct to within 41 ms
   polling server every 64 s
```

VM 2:

```console
# ntpstat
synchronised to NTP server (192.168.0.30) at stratum 3
   time correct to within 243 ms
   polling server every 64 s
```

### 1.7 Configure a Firewall

Before running DolphinDB, you need to configure the firewall to open the ports of each node, or turn off the firewall.

Take 8900 ~ 8903 TCP ports for example:

```console
# firewall-cmd --add-port=8900-8903/tcp --permanent
# firewall-cmd --reload
# systemctl restart firewalld
```

Turn off the firewall using the following commands if it is not required:

```console
# systemctl stop firewalld
# systemctl disable firewalld.service
```

### 1.8 Swap

Swap space, also known as virtual memory, is used as an extension of RAM. If the system needs more memory resources and the RAM is full, inactive pages in memory are moved to the swap space. Swap space allows a computer to effectively utilize more memory than is physically available, but it can also cause performance degradation if it is used excessively. If system performance prioritize to memory, it is recommended to disable Swap with the following steps:

1. Check available swap space.
    

```console
# free -h
              total        used        free      shared  buff/cache   available
Mem:           7.6G        378M        7.1G        8.5M        136M        7.1G
Swap:          7.9G          0B        7.9G
```

It can be seen that the total swap memory available is 7.9G.

2. Disable swap space temporarily.

```console
# swapoff -a
```

3. Check available swap space again.

```console
# free -h
              total        used        free      shared  buff/cache   available
Mem:           7.6G        378M        7.1G        8.5M        136M        7.1G
Swap:            0B          0B          0B
```

The total swap memory available is 0B. The swap space has been disabled.

4. To permanently disable swap space, comment out the line with the value of `swap` in the second column:

```console
# vi /etc/fstab
...
# /dev/mapper/centos-swap swap                    swap    defaults        0 0
...
```

## 2. DolphinDB Deployment

Once the system is configured, you can deploy DolphinDB. DolphinDB provides different deployment options for various business requirements.

### 2.1 Standalone/Single-Server Cluster/Multi-Machine Cluster

This section describes major differences between the different deployment options. 

#### 2.1.1 Standalone vs. Single-Server Cluster Deployment (on a Single Machine) <!-- omit in toc -->

**Standalone deployment** refers to deploying a single node on a single machine. Standalone deployment reduces data transmission between nodes in cases where the configured resources (number of CPU cores, memory capacity, number of hard drives) of the machine handles less traffic and the tasks use less computational resources. It shows slightly better performance than single-server cluster deployment.

**Single-server cluster deployment** refers to deploying multiple nodes on a single machine. Single-machine clusters are commonly used for scenarios involving intensive computing, where the computations are distributed across nodes (processes). It can effectively isolate resources and improve algorithmic efficiency.

In addition, clusters support horizontal scaling, i.e., adding new data nodes online, which increases the maximum load of the entire cluster. High availability is also supported, which enables clusters to have quicker response to a failure event.

So, to deploy on a single machine, cluster deployment is recommended.

#### 2.1.2 Single-Server Cluster vs. Multi-Machine Cluster Deployment (with Multiple Nodes) <!-- omit in toc -->

**Multi-machine cluster deployment** refers to deploying multiple nodes on multiple machines.

Multi-machine deployment can make full use of the computing and storage resources of each node (machine). However, communication between nodes results in additional data transmission over the network. To minimize the network overhead, it is recommended to deploy on an intranet and configure a 10 Gigabit Ethernet.

In addition, assuming that the probability of failure of each machine is the same, for a multi-machine cluster, since the nodes are distributed across multiple machines, there is a higher likelihood of encountering failures compared to a single machine. However, by enabling high availability, the multi-machine cluster can be highly fault tolerant.

#### 2.1.3 Single Machine with Multiple Disks vs. Multi-Machine Cluster Deployment <!-- omit in toc -->

For tasks with high throughput and low computational complexity, a single machine with multiple disks has better performance due to lower network overhead. The multi-machine cluster performs more effectively in tasks with low throughput and high computational complexity.

**Configuration parameters for metadata and redo log**:

- [chunkMetaDir](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/MetaData.html?highlight=chunkmetadir): The folder for the metadata of data chunks on each data node.
    
- [dfsMetaDir](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/MetaData.html?highlight=dfsMetaDir): The directory to save the metadata of the distributed file system on the controller node.
    
- [redoLogDir](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/Log.html?highlight=redologdir#redo-log): The directory of the redo log of OLAP engine.
    
- [TSDBRedoLogDir](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/Log.html?highlight=redologdir#redo-log): The directory of the redo log of TSDB engine.
    

> It is recommended to specify the above configuration parameters to SSDs for better read and write performance.

**Configuration parameters for data entity**:

- [volumes](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/Disk.html?highlight=volumes): The directory of data files. Multiple directories are separated by ',', e.g., /hdd/hdd1/volumes,/hdd/hdd2/volumes,/hdd/hdd3/volumes.
    
- [diskIOConcurrencyLevel](https://dolphindb.cn/cn/help/DatabaseandDistributedComputing/Configuration/Disk.html?highlight=diskioconcurrencylevel): The number of threads for reading and writing to disk. The default is 1. For HDDs, it is recommended to set *diskIOConcurrencyLevel* to the number of volumes configured on the node (specified by the configuration parameter *volumes*).
    

### 2.2 Docker or Non-Docker Environment

Docker is only a lightweight tool for resource isolation, and there is no significant performance difference between running DolphinDB in a Docker and a non-Docker environment. Solution of deployment depends on business needs.

### 2.3 Configuration Parameters for Production Environment

In this section, we introduce how to configure each node of a high availability cluster for metadata and streaming data. Assuming all machines are configured with the same hardware, relative information is given in the table below:

| Machine  | IP              | Note                               |
| -------- | --------------- | ---------------------------------- |
| centos-1 | 175.178.100.3   | 1 controller, 1 agent, 1 data node |
| centos-2 | 119.91.229.229  | 1 controller, 1 agent, 1 data node |
| centos-3 | 175.178.100.213 | 1 controller, 1 agent, 1 data node |

The configuration files *clusters.nodes* and *cluster.cfg* are identical across the 3 machines, while *controller.cfg* and *agent.cfg* vary by server.

> Note that only some important configurations are listed below.

- [**cluster.nodes**](script/deploy_dolphindb_on_new_server/cluster.nodes)

- [**cluster.cfg**](script/deploy_dolphindb_on_new_server/cluster.cfg)

```console
diskIOConcurrencyLevel=0
node1.volumes=/ssd1/dolphindb/volumes/node1,/ssd2/dolphindb/volumes/node1 
node1.redoLogDir=/ssd1/dolphindb/redoLog/node1 
node1.chunkMetaDir=/ssd1/dolphindb/metaDir/chunkMeta/node1 
node1.TSDBRedoLogDir=/ssd1/dolphindb/tsdb/node1/redoLog
chunkCacheEngineMemSize=2
TSDBCacheEngineSize=2
...
```

- [**controller.cfg**](script/deploy_dolphindb_on_new_server/controller.cfg)

```console
localSite=175.178.100.3:8990:controller1
dfsMetaDir=/ssd1/dolphindb/metaDir/dfsMeta/controller1
dfsMetaDir=/ssd1/dolphindb/metaDir/dfsMeta/controller1
dataSync=1
...
```

- [**agent.cfg**](script/deploy_dolphindb_on_new_server/agent.cfg)

```console
localSite=175.178.100.3:8960:agent1
sites=175.178.100.3:8960:agent1:agent,175.178.100.3:8990:controller1:controller,119.91.229.229:8990:controller2:controller,175.178.100.213:8990:controller3:controller
...
```

Refer to the following table for information on configuration parameters above:

<table>
    <thead>
        <tr>
            <th>Configuration Files</th>
            <th>Parameters</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>cluster.cfg</td>
            <td>node1.volumes=/ssd1/dolphindb/volumes/node1,/ssd2/dolphindb/volumes/node1</td>
            <td>Configure multiple SSDs to achieve concurrent reads and writes to improve read and write performance.</td>
        </tr>
        <tr>
            <td>cluster.cfg</td>
            <td>diskIOConcurrencyLevel=0</td>
            <td>For SSDs, it is recommended to set diskIOConcurrencyLevel = 0. For HDDs, it is recommended to set diskIOConcurrencyLevel to the number of volumes configured on the node.</td>
        </tr>
        <tr>
            <td>cluster.cfg</td>
            <td>chunkCacheEngineMemSize=2<br>TSDBCacheEngineSize=2</td>
            <td rowspan=2>If chunkCacheEngineMemSize and TSDBCacheEngineSize are specified in cluster.cfg (i.e., enabling the cache engine), dataSync = 1 must be configured in controller.cfg.</td>
        </tr>
        <tr>
            <td>controller.cfg</td>
            <td>dataSync=1</td>
        </tr>
    </tbody>
</table>

### 2.4 Deployment Procedures

For detailed instructions of deployment procedures, you can refer to the following tutorials.

- [DolphinDB Standalone Deployment](https://github.com/dolphindb/Tutorials_EN/blob/master/standalone_deployment.md)
    
- [DolphinDB ARM Standalone Deployment](https://github.com/dolphindb/Tutorials_EN/blob/master/ARM_standalone_deployment.md)
    
- [DolphinDB Single-Server Cluster Deployment](https://github.com/dolphindb/Tutorials_EN/blob/master/single_machine_cluster_deploy.md)
    
- [DolphinDB Multi-Machine Cluster Deployment](https://github.com/dolphindb/Tutorials_EN/blob/master/multi_machine_cluster_deployment.md)
    
- [Scale out a DolphinDB Cluster](https://github.com/dolphindb/Tutorials_EN/blob/master/cluster_scaleout.md)

### 2.5 Startup Process

Take the high-availability cluster configured in section 2.3 for example, place the corresponding configuration files in *DolphinDB installation folder/clusterDemo/config* on machines centos-1, centos-2, and centos-3 accordingly.

> Note that the startup script uses the relative path, so you need to execute the script under the directory where the script is located.

#### 2.5.1 Start the Controller <!-- omit in toc -->

Execute the following commands on centos-1, centos-2, and centos-3, respectively:

```console
$ cd DolphinDB/clusterDemo/
$ ./startController.sh
```

#### 2.5.2 Start the Agent <!-- omit in toc -->

Execute the following commands on centos-1, centos-2, and centos-3, respectively:

```console
$ cd DolphinDB/clusterDemo/
$ ./startAgent.sh
```

#### 2.5.3 Start the Data Node <!-- omit in toc -->

Navigate to the cluster manager web interface of any controller, e.g., http://175.178.100.3:8990, and you will be redirected to the cluster manager. Select all data nodes and click the start button. For more details on cluster manager web interface, refer to [DolphinDB GUI Manual](https://www.dolphindb.com/gui_help/gui/index.html).

## 3. Appendices

- [cluster.nodes](script/deploy_dolphindb_on_new_server/cluster.nodes)
- [cluster.cfg](script/deploy_dolphindb_on_new_server/cluster.cfg)
- [controller.cfg](script/deploy_dolphindb_on_new_server/controller.cfg)
- [agent.cfg](script/deploy_dolphindb_on_new_server/agent.cfg)
