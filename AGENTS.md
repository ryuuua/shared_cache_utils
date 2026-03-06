# AGENTS.md

## Fast Path (Public Targets)

公開 target は次の3つに固定:
- `env1_a6000`
- `env2_3090`
- `cc21`

設計原則:
- 正本は単一ファイル `targets.yaml`。
- Python 側は Pydantic 型付きローダー兼検証器に徹する。
- `cc21` は「logical access endpoint + capability + queue profile」で扱う。
- `env3` / `env4` の公開互換運用は行わない。

## Workflow Matrix (Usage)

| Mode | Token | `env1_a6000` | `env2_3090` | `cc21` |
| --- | --- | --- | --- | --- |
| no token | なし | 参照/解決/説明のみ | 参照/解決/説明のみ | 参照/解決/説明のみ |
| ref | `ref:<target>` | 参照/解決/説明のみ | 参照/解決/説明のみ | 参照/解決/説明のみ |
| test | `test:<target>` | 承認済み probe/test（Docker 経路のみ） | 承認済み probe/test（Docker 経路のみ） | 承認済み probe/test（`plan_dispatch` + Slurm） |
| exe | `exe:<target>` | ユーザー実行（Docker 強制） | ユーザー実行（Docker 強制） | ユーザー実行（`plan_dispatch` + Slurm 強制） |

## Runtime Context Gate

- token 付きフロー（`ref` / `test` / `exe`）では、実行前に `labenv-hub.open_runtime_context(...)` を必ず呼ぶ。
- 必須入力: `project_id`, `env`, `host`, `permission_tokens`, `mode`。
- 実行 API は `host` と `context_id` の両方を必須とする。
- TTL は `1800` 秒。期限切れは再オープンする。

## Dispatch Rules

| target | Backend | 必須フロー | path scope |
| --- | --- | --- | --- |
| `env1_a6000` | Docker | `docker_run*` / `resolve_and_run`（Docker 実行） | `/home` |
| `env2_3090` | Docker | `docker_run*` / `resolve_and_run`（Docker 実行） | `/home` |
| `cc21` | Slurm | `plan_dispatch` を先行し、`resolve_and_submit_sbatch*` へ接続 | `/work` |

CC21 planner ポリシー:
- `plan_dispatch` の `rationale` は実行前に必ず提示する。
- `queue_profile_override` は expert path 限定。
- 通常経路は planner 強制。
- `sinfo` / `squeue` は短TTL runtime cache（既定60秒）で扱い、repo tracked YAML に混ぜない。

## Hard Constraints

- Local Mac から env 実ホストへ直接 `ssh` しない。headnode 経由（MCP / ProxyJump）を使う。
- `cc21dev0` と `cc21dev1` は同一扱いで、論理 host `cc21` に正規化する。
- `cc21` compute I/O は `/work` を使う。
- GPU 実行は `--gres=gpu:<N>` を要求する。
- `cc21` の GPU capability は `singularity exec --nv` 必須。非GPU capability では `--nv` 禁止。

## Trigger Tokens (Execution / Automation)

### Execution permission tokens
- `ref:<target>`
- `test:<target>`
- `exe:<target>`

`<target>` は `env1_a6000` / `env2_3090` / `cc21` を使用する。

組み合わせルール:
- 同一 target で `ref + test` は許可。
- 同一 target で `exe` と他 mode の併用は不可。

### Sandbox automation tokens
- `MCP_SANDBOX_SYNC`
- `MCP_SANDBOX_STOP_SMOKE`
- `MCP_SANDBOX_DEV`
- `MCP_SANDBOX_EXP`
- `MCP_SANDBOX_ANALYZE`
- `MCP_SANDBOX_LOOP`

### Emergency stop
- `STOP <job_id>`
- `STOPRUN <run_id>`

### External RAM context switch
- `@RAM`
- `@todoist`

### Ollama offload tokens
- `@REPORT`
- `@SUMMARY`
- `@INDEX`
- `@SEARCH`

### Agentic trigger profile tokens
- `mx:dev`
- `mx:loop`
- `mx:sync`
- `mx:local`
- `mx:coop`
- `headnode`
- `cc21`
- `local`

## Canonical Sources

- Policy: `/Users/ryua/code/labenv_config/.mcp/policy.yaml`
- Token validator: `/Users/ryua/code/labenv_config/scripts/validate_env_tokens.py`
- Detailed rules: `/Users/ryua/code/labenv_config/docs/AGENTS_DETAILS.md`
- Exec usage: `/Users/ryua/code/labenv_config/docs/EXEC_MCP.md`

## Quick Checks

- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>"`
- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>" --env cc21 --execution-kind exec_compute`

## Repo Entrypoints

- Trigger dispatch: `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token <TOKEN>`
- Sandbox automation: `bash /Users/ryua/code/mcp_sandbox/scripts/factory_auto.sh --token <TOKEN> --repo-id shared_cache_utils --repo-name shared_cache_utils --branch "$(git rev-parse --abbrev-ref HEAD)"`

## Tool Policy

- `web.image_query` は使用禁止。
- 画像が必要な場合は `web.search_query` を使い、画像掲載ページURLを提示する。
