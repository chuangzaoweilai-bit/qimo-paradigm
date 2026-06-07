# 起末范式数据结构

## 目标

起末范式需要从理论进入可运行实现，因此每个容器的产物都必须有明确数据结构。

用户早期构建区块链语义训练容器时，容器 2 生成语料的主体结构可以整理为 `corpus_entry`。

## master state

Master 容器使用 `state.json` 暴露当前阶段和心跳状态。

```json
{
  "train_id": "train1",
  "phase": "heartbeat",
  "status": "running",
  "info": "守护中，任务数=10",
  "timestamp": 1737710400
}
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `train_id` | 当前训练闭环 ID。 |
| `phase` | 当前阶段，例如 `task_generation`、`semantic_check`、`heartbeat`。 |
| `status` | 当前状态，例如 `running`、`success`、`waiting`、`error`。 |
| `info` | 状态说明。 |
| `timestamp` | 写入时间戳。 |

## semantic_entries payload

容器 3 会生成 `semantic_entries.json`，容器 1 读取该文件并写入数据库。

```json
{
  "entries": [
    {
      "unit_id": "train1.blockchain.semantic.001",
      "task_id": "train1.Ownable_38578bd7",
      "contract_name": "Ownable"
    }
  ]
}
```

`entries` 中的每个条目应符合 `semantic_entry` 结构。

## corpus_entry v1

`corpus_entry` 是阶段语料训练容器的核心输出。

它描述某一次训练语料生成任务的来源、阶段、健康检查、模型分工、过去状态、当前动作、推理输入、推理输出和时间。

```python
corpus_entry = {
    "task_id": task_id,
    "type_id": type_id,
    "file": file_ref,
    "contracts_count": 1,
    "stages": ["phase1", "phase2", "phase3"],

    "healthcheck": {
        "brownie_ok": True,
        "proof": f"corpus written at {BROWNIE_CORPUS_FILE}",
        "timestamp": int(time.time())
    },
    "models": {
        "brownie": {
            "name": BROWNIE_MODEL_NAME if risk_model else "none",
            "version": BROWNIE_MODEL_VERSION if risk_model else "none",
            "role": "risk_prefilter_cpu",
            "device": "cpu"
        },
        "qwen_target": {
            "name": "Qwen-14B",
            "role": "semantic_generation_gpu"
        }
    },
    "past": {
        "audit_start": f"理解起始: 训练对象=区块链窗口(epoch={epoch})" if epoch > 0 else f"理解起始: 训练对象=任务文件({contract_file})",
        "checks": {
            "来源是否可用": {"ok": True, "proof": "chain_data 已加载" if chain_data else "文件任务模式"},
            "时效是否最新": {"ok": True, "proof": f"collected_at={chain_data.get('ethereum',{}).get('collected_at')}" if chain_data else "N/A"}
        },
        "interactions_digest": interactions_digest
    },
    "present": {
        "metrics": present_metrics,
        "actions": [
            "compile_check",
            "dependency_verify",
            "path_healthcheck",
            "selector_risk_review",
            "fail_ratio_watch",
            "risk_prefilter_cpu"
        ],
        "security_notes": notes,
        "risk_prefilter": risk_infer,
    },
    "reasoning_input": f"完成任务 {task_id}",
    "reasoning_output": f"起始: 完成任务 {task_id} → 最终答案: 未达成",
    "timestamp": int(time.time())
}
```

## 字段含义

| 字段 | 含义 |
| --- | --- |
| `task_id` | 当前语料任务 ID。可以来自训练轮次，也可以来自具体合约文件。 |
| `type_id` | 任务类型。`epoch_task` 表示阶段轮次任务，`file_task` 表示合约文件任务。 |
| `file` | 当前任务关联的智能合约文件。 |
| `contracts_count` | 当前语料条目覆盖的合约数量。 |
| `stages` | 当前训练任务经过的阶段。 |
| `healthcheck` | 容器 2 对自身产物的健康检查。 |
| `healthcheck.brownie_ok` | Brownie 风险预筛或语料写入链路是否正常。 |
| `healthcheck.proof` | 健康检查证明，例如语料写入路径。 |
| `models` | 当前条目涉及的模型分工。 |
| `models.brownie` | CPU 风险预筛模型。 |
| `models.qwen_target` | 目标语义生成模型。 |
| `past` | 任务进入当前阶段前的历史、来源和交互摘要。 |
| `past.audit_start` | 本次语料任务的理解起始。 |
| `past.checks` | 来源、时效等前置检查。 |
| `past.interactions_digest` | 历史交互摘要。 |
| `present.metrics` | 当前合约或任务的指标观测。 |
| `present.actions` | 当前阶段已经执行的动作。 |
| `present.security_notes` | 安全分析记录。 |
| `present.risk_prefilter` | 风险预筛选结果。 |
| `reasoning_input` | 交给推理结构的输入。 |
| `reasoning_output` | 当前推理结果。未达末时应显式记录未达成。 |
| `timestamp` | 语料条目生成时间。 |

## 起末解释

这个结构已经体现起末范式的雏形。

```text
起：完成某个区块链训练任务
末：该任务生成可用于语义推理的完整语料
当前状态：present
前置状态：past
自检状态：healthcheck
模型分工：models
推理输入：reasoning_input
推理输出：reasoning_output
闭环状态：达成或未达成
```

其中：

```text
reasoning_output = "起始: 完成任务 → 最终答案: 未达成"
```

这说明系统没有把流程执行伪装成成功，而是明确记录“未达成”。

在起末范式中，这不是失败终止，而是回流信号：

```text
未达成 -> 容器 1 核对 -> 生成修正任务或补充任务 -> 容器 2 再生成语料
```

## v1 结构约束

`corpus_entry` 至少应满足：

- 必须有 `task_id`
- 必须有 `type_id`
- 必须有 `stages`
- 必须有 `healthcheck`
- 必须有 `models`
- 必须有 `past`
- 必须有 `present`
- `present` 必须记录当前动作 `actions`
- 必须有 `reasoning_input`
- 必须有 `reasoning_output`
- 必须显式记录达成或未达成状态
- 必须能被容器 3 读取

## v1 闭环含义

优化后的 `corpus_entry` 不再只是“训练语料的一条记录”。

它已经把小结构闭环所需的规则和质检嵌入自身：

```text
healthcheck：证明容器 2 产物路径和风险预筛链路可用
models：声明 CPU 风险预筛和 GPU 语义生成的职责边界
past：记录任务来源、时效检查和历史交互
present：记录当前指标、动作、安全记录和风险预筛
reasoning_output：显式记录达成或未达成
```

这意味着容器 3 在读取语料时，不只是读文本，而是读取一个带有来源、证明、模型职责、当前动作和闭环状态的结构。

## 与三容器闭环的关系

```text
容器 1 输出 task_list
  -> 容器 2 读取 task_list
  -> 容器 2 输出 corpus_entry
  -> 容器 3 读取 corpus_entry
  -> 容器 3 输出 semantic_entry
  -> 容器 1 读取 semantic_entry 核对 task_list
```

因此，`corpus_entry` 是容器 2 和容器 3 之间的闭环接口。

## corpus_entry results variant

另一种优化后的 `corpus_entry` 会把当前阶段的所有执行结果聚合到 `results` 中。

这种结构更适合表达“编译成功、部署失败、风险较高、需要生成新验证逻辑”这类复合状态。

```json
{
  "task_id": "train1.BaseCoin_922763f1",
  "type_id": "misc",
  "file": "/app/output/tasks/922763f1efa3f0726977198362816858b818b4206b21057e75e26709bd63c6f9/spec/BaseCoin.sol",
  "contracts_count": 1,
  "stages": ["phase1", "phase2", "phase3"],
  "results": {
    "compile_result": {
      "status": "success",
      "solc_version": "0.8.20",
      "abi_snippet": "...",
      "binary_snippet": "..."
    },
    "deploy_result": {
      "status": "fail",
      "error": "gas_limit_exceeded"
    },
    "risk_prefilter": {
      "level": "high",
      "label": 1
    },
    "interactions_digest": {
      "selectors": ["0x095ea7b3"],
      "fail_ratio": 0.12,
      "tx_count": 50
    },
    "present_metrics": {
      "ethereum": {
        "daily_tx": 10000,
        "gas_avg_gwei": 15
      }
    },
    "security_notes": ["失败交易比例偏高", "关注高频函数选择器的风险"],
    "actions": ["compile_check", "deploy_testnet", "risk_prefilter_cpu"],
    "multi_verification": [
      {
        "combo": "compile_success + deploy_fail",
        "result": "需要创新验证逻辑",
        "innovation": "为[部署失败]生成新的验证逻辑"
      },
      {
        "combo": "deploy_fail + risk_high",
        "result": "风险确认 -> 创新探索",
        "innovation": "为[高风险合约]生成新的路径"
      }
    ]
  },
  "reasoning_input": "完成任务 train1.BaseCoin_922763f1",
  "reasoning_output": "起始: 完成任务 train1.BaseCoin_922763f1 -> 最终答案: 未达成",
  "timestamp": 1737710400
}
```

### results 字段含义

| 字段 | 含义 |
| --- | --- |
| `compile_result` | 合约编译结果，包括状态、编译器版本、ABI 与字节码片段。 |
| `deploy_result` | 测试部署结果。失败时必须记录错误。 |
| `risk_prefilter` | CPU 风险预筛结果。 |
| `interactions_digest` | 交易选择器、失败比例、交易数量等交互摘要。 |
| `present_metrics` | 当前链上或环境指标。 |
| `security_notes` | 安全观察记录。 |
| `actions` | 当前阶段实际执行过的动作。 |
| `multi_verification` | 多条件组合验证结果，以及由失败或风险触发的新验证逻辑。 |

`results variant` 中的 `type_id` 可以存在，也可以省略。省略时，容器 3 可以从 `task_id`、`file` 或上游任务清单中推断任务类型。

编译结果也不要求每次都保存 ABI 或字节码片段。最小闭环只要求：

```text
compile_result.status
deploy_result.status
risk_prefilter.level
multi_verification
reasoning_output
```

因为这些字段已经足够判断哪些小结构闭环、哪些小结构未闭环。

### 多重验证的起末意义

`multi_verification` 是这个结构最关键的部分。

它不是传统补丁，而是把复合状态转化成新的验证逻辑或达末路径。

例如：

```text
compile_success + deploy_fail
```

说明编译已经闭环，但部署结构没有闭环。系统不能把“编译成功”当成整体成功，而必须为“部署失败”生成新的验证逻辑。

再例如：

```text
deploy_fail + risk_high
```

说明部署失败与高风险同时出现。系统不能跳过这个组合，而必须把它转化为新的探索路径。

这符合起末范式的结构闭环原则：

```text
复合状态 -> 多重验证 -> 发现未闭环小结构 -> 生成新验证逻辑或新路径
```

### 与 v1 的关系

`corpus_entry v1` 更强调 `healthcheck`、`models`、`past`、`present` 的分区。

`results variant` 更强调执行结果聚合和多重验证。

两者可以并存：

```text
v1：适合表达来源、模型职责、过去状态和当前动作。
results variant：适合表达编译、部署、风险、交互和多重验证结果。
```

后续实现可以把二者统一为一个更完整的 `corpus_entry v2`。

## semantic_entry v1

`semantic_entry` 是容器 3 的核心输出。

它把容器 2 生成的语料推理成可被容器 1 反向核对的语义条目。

```json
{
  "unit_id": "train1.blockchain.semantic.001",
  "contract_name": "Ownable",
  "source_file": "/app/contracts/access/Ownable.sol",
  "task_id": "train1.Ownable_38578bd7",
  "phase": "phase1",
  "type_id": "access",
  "content": {
    "function": "transferOwnership",
    "visibility": "public",
    "modifier": "onlyOwner",
    "description": "允许当前合约所有者将所有权转移给新的地址。",
    "semantic_tags": ["ownership", "access_control", "security"],
    "code_snippet": "function transferOwnership(address newOwner) public onlyOwner { ... }"
  },
  "timestamp": 1719820000,
  "trace": "train1-master"
}
```

## semantic_entry 字段含义

| 字段 | 含义 |
| --- | --- |
| `unit_id` | 唯一语义条目标识。通常包含训练容器、领域和序号。 |
| `contract_name` | 合约名称。 |
| `source_file` | 源码路径。 |
| `task_id` | 对应任务 ID，用于回连容器 1 的任务清单。 |
| `phase` | 训练阶段，例如 `phase1`、`phase2`、`phase3`。 |
| `type_id` | 任务类型，例如 `access`、`proxy`、`token_erc20`。 |
| `content` | 具体语义内容。 |
| `content.function` | 函数名称。 |
| `content.visibility` | 函数可见性。 |
| `content.modifier` | 函数修饰符。 |
| `content.description` | 自然语言语义描述。 |
| `content.semantic_tags` | 语义标签。 |
| `content.code_snippet` | 相关代码片段。 |
| `timestamp` | 写入时间戳。 |
| `trace` | 来源标记，表示由哪个容器或训练链路写入。 |

## semantic_entry 的起末意义

`semantic_entry` 是“完整区块链语义”这个末端的组成单元。

它不是普通摘要，而是一个可追踪、可核对、可回流的语义条目。

```text
容器 1 生成任务 task_id
容器 2 生成 corpus_entry
容器 3 生成 semantic_entry
容器 1 读取 semantic_entry.task_id 核对任务是否执行
```

其中 `task_id` 是闭环关键字段。

如果 `semantic_entry.task_id` 无法对应容器 1 的任务清单，容器 1 就不能确认该语义条目完成了原始任务。

因此，`semantic_entry` 必须能证明：

```text
这个语义来自哪个任务
这个语义覆盖哪个合约
这个语义属于哪个阶段
这个语义描述了哪个代码结构
这个语义能否回到任务清单接受核对
```

## semantic_entry v1 结构约束

`semantic_entry` 至少应满足：

- 必须有 `unit_id`
- 必须有 `task_id`
- 必须有 `contract_name`
- 必须有 `source_file`
- 必须有 `phase`
- 必须有 `type_id`
- 必须有 `content`
- `content` 必须至少包含一个语义对象，例如函数、描述、标签或代码片段
- 必须有 `timestamp`
- 必须有 `trace`
- 必须能被容器 1 读取并核对
