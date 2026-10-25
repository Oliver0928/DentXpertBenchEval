# DentXpertBench Evaluation

DentXpertBench-Eval is a lightweight evaluation toolkit for the DentXpertBench oral multimodal benchmark. The current implementation supports A1.1 and A1.3.

## Project Layout

```text
DentXpertBench-Eval/
├── README.md
├── pyproject.toml
├── prepare.py
├── run.py
├── evaluate.py
├── bench/
│   ├── convert.py
│   ├── media.py
│   ├── protocol.py
│   ├── models.py
│   └── metrics/
├── tasks/                      # task specs and task case JSON files
├── configs/
├── tests/
├── data/                       # evaluation run data
└── results/
```

The previous single-task evaluation quickstart is kept in `docs-eval-legacy.md`.

## Quick Start

Dry-run the first two A1.1 cases without calling a model:

```bash
python run.py --task A1.1 --dry-run --limit 2
```

Dry-run A1.3:

```bash
python run.py --task A1.3 --dry-run --limit 2
```

Dry-run every registered task:

```bash
python run.py --task all --dry-run --limit 2
```

在 Windows 下也可以直接双击项目根目录的 `Run-All-A1-A4.cmd`，一次按顺序运行全部 A1-A4 任务。正式运行前可先在 PowerShell 中执行：

```powershell
.\Run-All-A1-A4.ps1 -DryRun -Limit 1
```

脚本默认使用 `configs/model-gpt-6-luna.json`；如需切换模型，可传入 `-ModelConfig configs/model-chatanywhere.json`。

Run an OpenAI-compatible multimodal model:

```bash
python run.py
```

The model, endpoint, and generation settings are configured in a selected JSON profile. The default profile is `configs/model.json`, which uses Sublyx; the API key is read from `D:\Desktop\sublyx.txt` or `SUBLYX_API_KEY`.

To switch manually to the additional `gpt-6-luna` profile:

```bash
python run.py --model-config configs/model-gpt-6-luna.json
```

The Luna profile uses the Sublyx OpenAI-compatible endpoint and key by default. If Luna is provided by another API service, change `base_url`, `api_key_file`, and/or `api_key_env` only in `configs/model-gpt-6-luna.json`; the original profile remains unchanged. Command-line options such as `--temperature` and `--max-tokens` still override profile defaults.

Recompute metrics from saved model answers:

```bash
python evaluate.py results/a1_1_eval_results.jsonl
python evaluate.py results/a1_3_eval_results.jsonl
```

## Defaults

- A1.1 cases: `tasks/A1.1/DentXpertBench-cases-v3.2-A1.1-2026-10-10.json`
- A1.3 cases: `tasks/A1.3/DentXpertBench-cases-v3.2-A1.3-2026-10-11.json`
- Image root: `../公开数据集/公开数据集`
- A1.1 results: `results/a1_1_eval_results.jsonl`
- A1.3 results: `results/a1_3_eval_results.jsonl`

Do not store the API key itself in `configs/model.json`; keep it in the configured key file or environment variable.

