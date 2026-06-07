# 容器 1：Master 闭环控制器

## 定位

容器 1 是多容器语义训练闭环中的 Master 控制器。

它不是普通任务启动脚本，而是负责维持整个闭环的起点、任务索引、语义回流和状态心跳。

它的职责可以概括为：

```text
生成任务清单
监控任务索引
等待语义条目
读取语义条目
写入数据库
核对闭环状态
持续心跳守护
```

## 起末定义

```text
起：我要获得完整的区块链语义
末：完整区块链语义条目被生成、读取、入库，并能回连任务清单
中间：任务生成、语料训练、语义推理、语义回流、Master 核对
```

## 关键文件

```text
/app/output/state.json
/app/output/task_list_phase1.json
/app/output/task_list_phase2.json
/app/output/task_list_phase3.json
/app/output/tasks_index.json
/app/output/tasks_index_copy.json
/app/output/semantic_entries.json
```

## 核心流程

### 1. 首次启动自检

Master 容器通过数据库 `train_tasks_index` 判断是否第一次启动。

```text
train_tasks_index 为空 -> 第一次启动
train_tasks_index 不为空 -> 非第一次启动
数据库不可达 -> 待机模式
```

如果数据库不可达，系统不会伪装成功，而是写入错误状态并进入待机。

### 2. 合约可见性检查

Master 会检查合约目录是否可见：

```text
/app/openzeppelin-contracts/contracts
/app/contracts
```

如果没有发现 `.sol` 文件，任务生成不会继续执行。

这体现了小结构闭环：

```text
合约不可见 -> 任务生成结构未闭环 -> 不生成伪任务
```

### 3. 任务清单生成

如果任务清单不存在，Master 会调用任务生成器：

```text
/mnt/train_space1/task_generator.py
```

如果宿主机路径不可见，则改用容器内路径：

```text
/app/task_generator.py
```

任务生成成功的判定不是脚本跑完，而是：

```text
任务生成器返回成功
tasks_index.json 存在
tasks_index.json 中 tasks 数量大于 0
```

### 4. 语义条目读取

Master 会读取：

```text
/app/output/semantic_entries.json
```

如果文件不存在或 `entries` 为空，状态进入 `waiting`，而不是失败伪成功。

如果有语义条目，Master 会为每条语义生成：

```text
unit_id = {TRAIN_ID}.blockchain.semantic.{i}
trace = {TRAIN_ID}-master
```

然后写入数据库表：

```text
semantics_container1
```

## 状态文件

Master 使用 `state.json` 暴露当前闭环状态：

```json
{
  "train_id": "train1",
  "phase": "heartbeat",
  "status": "running",
  "info": "守护中，任务数=10",
  "timestamp": 1737710400
}
```

其中 `status` 可以是：

```text
running
success
waiting
error
```

## 守护循环

Master 不会执行一次就退出。

它会持续循环：

```text
检查任务索引
任务索引为空时尝试重建
读取语义条目
更新心跳
导出任务索引副本
等待 5 秒
继续循环
```

这说明容器 1 不是一次性启动器，而是闭环守护器。

## 起末范式意义

Master 容器体现了几个关键原则：

```text
没有任务索引 -> 不允许训练闭环伪成功
合约不可见 -> 不生成无来源任务
语义条目缺失 -> 状态进入 waiting
语义条目存在 -> 写库并带 trace
任务索引为空 -> 自动尝试再生成
```

它不是靠补丁维持运行，而是把自检、等待、回流、写库和心跳内嵌到结构本身。

## 与三容器闭环的关系

```text
容器 1：生成 tasks_index.json
容器 2：读取任务清单，生成 corpus_entry
容器 3：读取 corpus_entry，生成 semantic_entries.json
容器 1：读取 semantic_entries.json，写库并核对闭环
```

因此，容器 1 是闭环的起点，也是闭环的回流验证端。

