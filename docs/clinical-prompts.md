# A5～A7 提示词与评测

7 份原始提示词保存在 `bench/prompts/`，内容来自本次提供的 txt。程序按题目的 `input.fields` 填充占位符，不把参考答案写入提示词。A7.2 没有提供模板，本次不接入。

| 任务 | 输出字段 | 自动比较 | 待审核内容 |
| --- | --- | --- | --- |
| A5.1 | diagnoses、reason | 每题诊断集合 F1；独立模型评分理由 | 评分调用失败时需重试或人工审核 |
| A5.2 | diagnoses、reason、exclude_reason | 倾向诊断名称集合 | 诊断理由与排除理由 |
| A5.3 | sufficiency、可选 reason | 暂无 | 充足性及不足理由 |
| A6.1 | total、images | 去重总数、逐图数量 | 最终计分规则 |
| A6.2 | diagnoses、reason | 诊断名称集合 | 多图诊断理由 |
| A6.3 | conditions | 暂无 | 补充条件 |
| A7.1 | plans | 暂无 | 治疗计划 |

## 运行

要求 Python 3.10 或更新版本；在项目根目录运行：

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python run.py --task A7.1 --dry-run --limit 1
```

`--dry-run` 不调用模型 API，不写评测结果；它使用明确标为格式示例的模拟回答，不衡量模型医学能力。测试中用临时生成的空白图片检查消息和红框，不需要原始影像。试运行遇到缺图、缺红框或无效回答时会返回非零退出码；下文记录的 A5.1 缺框题会被明确跳过。

A7.1 的题库是纯文字病例，因此试运行不需要图片。其他任务需要先提供题库对应的原始影像：

```powershell
python run.py --task A6.1 --image-root 'D:\你的数据集根目录' --dry-run --limit 1
```

图片根目录下应能直接找到题库路径中的数据集文件夹，例如 `FDTooth-C014/`、`COde-Dataset-C018/`。仓库只记录图片相对路径；本次检查未发现已跟踪的原始图片或影像压缩包，也未发现下载脚本或可直接获取全部影像的说明。默认根目录是项目旁的 `../公开数据集/公开数据集`，本次本地检查该目录不存在。`prepare.py` 只转换 JSON，不下载图片。需要课题组另行提供与题库路径匹配的数据。

准备好影像、模型 API 配置及密钥后，去掉 `--dry-run` 才会实际调用模型，建议先只跑一道题：

```powershell
python run.py --task A7.1 --model-config configs/model-gpt-6-luna.json --limit 1
python run.py --task A6.1 --image-root 'D:\你的数据集根目录' --model-config configs/model-gpt-6-luna.json --limit 1
```

正式调用可能产生 API 费用。模型配置与密钥读取方式沿用原项目，密钥保存在配置指定的文件或环境变量中。以上命令里的数据目录需要替换为实际路径。

`--task` 也可选 A5.1、A5.2、A5.3、A6.2、A6.3。`--task all` 现在包括这 7 个任务；已有名称为 A1-A4 的批处理脚本仍按其原有任务范围工作。

## 输入与答案转换

- 所有 `input.images` 按原顺序发送，使用路径与 `evidence_media` 一一对应，在每张图前注明 M 编号，不把第 1 张固定称为 M01。
- A5.1、A5.2 根据各图的 `diagnosis_bbox` 绘制红框，原图保留，绘制结果写入 `preview/`。缺少坐标时记录输入错误，不自行推断范围。
- A7.1 发送文字病历，允许 `images` 为空；性别、年龄、主诉、病史、检查、诊断和患者偏好按字段填充，未提供的内容明确注明未提供。
- A5.1/A6.2 将参考答案的 `selected_option_ids` 按输入选项转换为中文诊断；A5.2 只把 `favored` 项作为诊断集合参考，不将未标注的选项自动当成已排除。
- A6.1 将 `total_count`/`image_counts` 转为 `total`/`images`，按实际图片发送顺序排列。
- A6.3 将补充条件类别转为提示词要求的中文标签；A7.1 将 `treatment_plans` 转为 `plans`。这些转换供审核展示，不作临床语义等价判分。
- 原始答案保存在结果的 `reference_answer_native`；`reference_answer` 为转换后的展示或比较版本。
- 校验输出字段、类型、诊断是否来自候选列表、逐图计数是否覆盖全部 M 编号，以及 A5.3 理由字段的条件性。格式错误保存在 `parse_error`。

## 分数与审核

诊断选择报告集合完全匹配率及 micro precision/recall/F1；A6.1 报告去重总数完全匹配率、整组逐图计数完全匹配率。无效回答计为相应客观比较未匹配，同时计入 `invalid`。

这些比较保存在 `objective_metrics`。开放回答的待审字段列在 `pending_review_fields` 中，状态为 `pending_review`。A6.1 状态为 `objective_only`。

A5.1 每题总分 100：诊断得分为诊断集合 F1 × 50，理由得分为理由评分（0、1、2）÷ 2 × 50。F1 分别统计真阳性、假阳性、假阴性；模型若有未知诊断选项或格式错误，该题标记无效而不是默认为零分。

实际运行 A5.1 时使用独立的理由评分模型，默认读取 `configs/model-gpt-6-luna.json`，也可通过 `--judge-model-config` 指定另一个配置文件。被测模型与评分模型各自读取自己的配置及 API Key；评分提示词只传递医生参考理由和模型理由，并要求输出 0、1、2 的评分及解释，结果包含评分模型名、原始回答、分数、解释及评分 token 使用量。调用或解析失败时保存 `reason_judge_error`，理由分数及该题总分保持 `null`，可检查错误后重新运行该题；不会默记为 0 分。自动评分需要课题组验证其与专家判断的一致性。

汇总中的 `skipped` 和 `skipped_cases` 单独记录跳过的题，不纳入有效题及总分分母；`fully_scored` / `unscored` 区分已评分和未完成的题。未完成所有已尝试题的评分时，整体 `total_score`、`score_rate` 和 `average_score` 为 `null`；若部分题已完成，另行报告 `scored_total_score`、`scored_total_points` 和 `scored_average_score`。其他 A5～A7 任务尚未确认计分规则，最终分数保持 `null`。

特别是 A5.3：原始标注为 `diagnosis_support: supported/not_supported`，提示词要求判断资料“充足/不足”。不支持某诊断并不意味着资料不足，本实现保留提示词和原始标注，整项交由审核，不作标签互换。

结果 JSONL 的原始模型回答和转换后的回答均保留。可以用下面的命令重新汇总已有结果；该命令不重新调用模型，也不执行人工审核：

```powershell
python evaluate.py 'results/实际结果文件名.jsonl' --task A6.1
```

## 已知题库问题

A5.1 的 `candidate:e1cf8e01197540aea86895416ae5f8a7` 仅有 M02 影像，`evidence_media` 中没有 `diagnosis_bbox`，与提示词要求的红框范围不符。该题暂时记录为跳过；补充有效坐标后会自动恢复处理。其他缺框题仍会明确报错。

自动测试覆盖 352 道题的提示词、模拟输出解析和参考答案转换；使用临时图片验证 351 道题的消息构造和 1 道缺框题的跳过，另测试 A5.1 分数换算及评分接口失败，并抽查原有 14 个任务的首题请求构造和评分。测试不能替代真实模型的评测。
