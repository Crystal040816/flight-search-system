# Hadoop 从节点安全关闭与恢复手册

## 1. 适用范围

本手册适用于 `node1`、`node2`、`node3`、`node4`。每台从节点运行：

- HDFS DataNode
- YARN NodeManager

`node-master` 同时运行 NameNode、ResourceManager、Hive 和 MySQL，不属于本手册的从节点关机范围。所有数据操作必须在 `hadoop` 用户下完成。

短期关机、夜间关机或虚拟机维护不需要执行 decommission。decommission 会触发副本迁移，只适用于节点长期下线或永久移除。

## 2. 关机前置条件

在 `node-master` 执行以下只读检查：

```bash
export JAVA_HOME=/opt/jdk1.8.0_311
export HADOOP_HOME=/opt/hadoop-3.4.3
export HADOOP_CONF_DIR=/opt/hadoop-3.4.3/etc/hadoop
export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

echo "===== Active YARN applications ====="
yarn application -list -appStates SUBMITTED,ACCEPTED,RUNNING

echo "===== HDFS safe mode ====="
hdfs dfsadmin -safemode get

echo "===== HDFS health ====="
hdfs fsck /

echo "===== Current nodes ====="
yarn node -list -all
hdfs dfsadmin -report | grep -E '^(Live datanodes|Dead datanodes|Name:)'
```

只有在以下条件全部满足时才能继续：

- 活动 YARN 应用数为 0。
- HDFS 安全模式为 `OFF`。
- `hdfs fsck /` 显示文件系统 `HEALTHY`。
- Missing blocks 和 Corrupt blocks 均为 0。

如果存在写入任务、缺失块或损坏块，停止关机流程并先处理异常。

## 3. 安全关闭单台从节点

以 `node4` 为例，通过 Xshell 直接登录 `node4`，执行：

```bash
export JAVA_HOME=/opt/jdk1.8.0_311
export HADOOP_HOME=/opt/hadoop-3.4.3
export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

echo "===== Before stop ====="
"$JAVA_HOME/bin/jps" -l | grep -E 'DataNode|NodeManager' || true

echo "===== Stop NodeManager ====="
yarn --daemon stop nodemanager

echo "===== Stop DataNode ====="
hdfs --daemon stop datanode

sleep 5

echo "===== After stop ====="
if "$JAVA_HOME/bin/jps" -l | grep -E 'DataNode|NodeManager'; then
    echo "ERROR: Hadoop worker process is still running"
    exit 1
else
    echo "DataNode and NodeManager are stopped"
fi

sync
```

确认两个进程均已停止后，再执行操作系统关机：

```bash
sudo shutdown -h now
```

输入当前 Linux 用户的 sudo 密码。SSH 随后断开属于正常现象。

不要把 `set -e` 写入交互式登录 Shell；命令异常时可能直接退出 SSH。不要使用 `kill -9`，除非正常停止反复失败且已经检查日志。

## 4. 从 node-master 远程关闭单台节点

远程 sudo 必须分配 TTY，否则会出现 `a terminal is required to read the password`：

```bash
ssh -t node4 'sudo shutdown -h now'
```

该命令只负责操作系统关机。仍应先按第 3 节停止 NodeManager 和 DataNode。

## 5. 安全关闭 node1-4

如果只关闭四台从节点而保持 `node-master` 运行，不要执行 `stop-dfs.sh` 或 `stop-yarn.sh`，因为这两个脚本还会停止 NameNode 和 ResourceManager。

按 `node1`、`node2`、`node3`、`node4` 顺序逐台执行第 3 节。不要并行关机，以便在每台节点停止后确认结果。

也可以在 `node-master` 逐台停止工作进程：

```bash
for host in node1 node2 node3 node4; do
    echo "===== stopping Hadoop services on $host ====="
    ssh -o ConnectTimeout=5 "$host" '
        export JAVA_HOME=/opt/jdk1.8.0_311
        export HADOOP_HOME=/opt/hadoop-3.4.3
        export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"
        yarn --daemon stop nodemanager || true
        hdfs --daemon stop datanode || true
        sleep 5
        "$JAVA_HOME/bin/jps" -l | grep -E "DataNode|NodeManager" || true
    '
done
```

确认工作进程全部停止后，使用带 TTY 的命令逐台关机：

```bash
ssh -t node1 'sudo shutdown -h now'
ssh -t node2 'sudo shutdown -h now'
ssh -t node3 'sudo shutdown -h now'
ssh -t node4 'sudo shutdown -h now'
```

每条命令完成并断开后再执行下一条。不要把 sudo 密码写入脚本，也不要使用 `sudo -S` 从明文管道传入密码。

四台从节点全部关闭后，`node-master` 上的 HDFS/YARN 页面会显示从节点丢失，这是预期状态。此时不要运行 Spark、Hive 写入或 HDFS 修复命令。

## 6. 完整集群关机的区别

如果 `node-master` 也要关闭，顺序为：

1. 确认没有活动任务。
2. 停止 HiveServer2。
3. 停止 Hive Metastore。
4. 在 `node-master` 执行 `stop-yarn.sh`。
5. 执行 `stop-dfs.sh`。
6. 确认 Hadoop Java 进程退出。
7. 关闭 `node1-4`。
8. 停止 MySQL，并最后关闭 `node-master`。

完整集群关机时可以使用 `stop-yarn.sh` 和 `stop-dfs.sh`，因为此时主节点服务也应停止。

## 7. 节点恢复

单台节点重新开机后登录该节点：

```bash
export JAVA_HOME=/opt/jdk1.8.0_311
export HADOOP_HOME=/opt/hadoop-3.4.3
export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

hdfs --daemon start datanode
yarn --daemon start nodemanager

sleep 10
"$JAVA_HOME/bin/jps" -l | grep -E 'DataNode|NodeManager'
```

然后在 `node-master` 验证：

```bash
yarn node -list -all
hdfs dfsadmin -report | grep -E '^(Live datanodes|Dead datanodes|Name:)'
hdfs fsck /
```

恢复标准为目标 NodeManager 显示 `RUNNING`、DataNode 显示 `Live`，并且 HDFS 仍为 `HEALTHY`。

## 8. 禁止操作

- 不要格式化 NameNode 或 DataNode。
- 不要删除 `dfs.datanode.data.dir` 下的块目录。
- 不要把虚拟机关机当作 DataNode 正常停止方式。
- 不要为短期关机执行 decommission。
- 不要在仍有 Spark/YARN 任务时停止节点。
- 不要通过并行脚本同时向四台机器发送带密码的 sudo 命令。
- 不要在 HDFS 副本缺失或损坏时继续关闭节点。
