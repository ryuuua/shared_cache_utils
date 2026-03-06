# AGENTS.md

## Fast Path (Public Targets)

公開 target は次の3つに固定:
- `env1_a6000`
- `env2_3090`
- `cc21`

設計原則:
- 正本は単一ファイル `targets.yaml`。
- Python 側は Pydantic 型付きローダー兼検証器に徹する。
- `cc21` は `logical access endpoint + capability + queue_profile` で扱う。
- `headnode` は `targets.yaml.infrastructure_hosts` で管理する bastion であり、公開 target ではない。
- 公開 target は上記3つのみを使い、旧 split-target 運用はしない。

## Workflow Matrix (Usage)

| Mode | Token | `env1_a6000` | `env2_3090` | `cc21` |
| --- | --- | --- | --- | --- |
| no token | なし | 参照/解決/説明のみ | 参照/解決/説明のみ | 参照/解決/説明のみ |
| ref | `ref:<target>` | 参照/解決/説明のみ | 参照/解決/説明のみ | 参照/解決/説明のみ |
| test | `test:<target>` | 承認済み probe/test（Docker 経路） | 承認済み probe/test（Docker 経路） | 承認済み probe/test（`plan_dispatch` + Slurm） |
| exe | `exe:<target>` | ユーザー実行（Docker 強制） | ユーザー実行（Docker 強制） | ユーザー実行（`plan_dispatch` + Slurm 強制） |

## Runtime Context Gate

- token 付きフロー（`ref` / `test` / `exe`）では、実行前に `labenv-hub.open_runtime_context(...)` を必ず呼ぶ。
- 必須入力: `project_id`, `env`, `host`, `permission_tokens`, `mode`。
- 実行 API は `host` と `context_id` の両方を必須とする。
- Runtime context TTL は `1800` 秒。期限切れ時は再オープンする。
- `host_env_mismatch` は拒否。`cc21dev0` / `cc21dev1` は論理 host `cc21` に正規化する。
- `headnode` / `local` は topology anchor であり、execution target としては扱わない。

## Dispatch Matrix

| Target | Backend | Required Flow | Path Scope |
| --- | --- | --- | --- |
| `env1_a6000` | Docker | `docker_run*` を優先（ユーザー実行は Docker 強制） | `/home` |
| `env2_3090` | Docker | `docker_run*` を優先（ユーザー実行は Docker 強制） | `/home` |
| `cc21` | Slurm | `plan_dispatch` -> `resolve_and_submit_sbatch*` / `submit_sbatch*` | `/work` |

CC21 planner ポリシー:
- `plan_dispatch` の `rationale` は実行前に必ず提示する。
- 通常経路は planner 強制。`queue_profile_override` は expert path 限定。
- live 状態（`sinfo` / `squeue`）は短 TTL runtime cache で扱い、repo tracked YAML に混在させない。

## labenv_config Public Tokens

### Execution permission tokens
- `ref:<target>`
- `test:<target>`
- `exe:<target>`

`<target>` は `env1_a6000` / `env2_3090` / `cc21` を使う。

組み合わせルール:
- 同一 target で `ref + test` は許可。
- 同一 target で `exe` と他 mode の併用は不可。

`labenv_config` の公開 execution contract は上記の `ref` / `test` / `exe` です。
`mcp_sandbox` 連携トークンは下記に分離して載せますが、別レイヤのトークンとして扱います。

## mcp_sandbox Integration Tokens

### Public workflow tokens (`mx:*`)

| Token | Alias | Route | Purpose |
| --- | --- | --- | --- |
| `mx:dev` | `mxdev` | `sandbox` | Development single-pass on sandbox1 |
| `mx:loop` | `mxloop` | `sandbox` | Iterative EXP/ANALYZE loop on sandbox2 |
| `mx:local` | `mxlocal` | `outside` | Local codex exec cycle |
| `mx:exp` | `mxexp` | `sandbox` | One-shot experiment on sandbox2 |
| `mx:analyze` | `mxanalyze` | `sandbox` | Analyze/summarize experiment outputs |
| `mx:smoke` | `mxsmoke` | `sandbox` | Stop/smoke safety check |
| `mx:sync` | `mxsync` | `sandbox` | Sync mirror branch to sandbox hosts |
| `mx:devflow` | `mxdevflow` | `pipeline` | sync -> local -> dev -> analyze |
| `mx:expflow` | `mxexpflow` | `pipeline` | sync -> exp -> analyze |
| `mx:verify` | `mxverify` | `pipeline` | sync -> analyze -> smoke |
| `mx:coop` | `mxcoop` | `pipeline` | Cooperative DEV + LOOP |
| `mx:full` | `mxfull` | `pipeline` | Full development/experiment/verify cycle |

### Host/context selectors
- `sandbox`, `sandbox1`, `sandbox2`, `sandboxN`
- `headnode`, `cc21`, `local`

selector メモ:
- `headnode` は bastion/topology anchor。
- 単体の `cc21` は selector、`ref:cc21` / `test:cc21` / `exe:cc21` は execution target token。

### Internal sandbox tokens (implementation-only)
- `MCP_SANDBOX_SYNC`
- `MCP_SANDBOX_STOP_SMOKE`
- `MCP_SANDBOX_DEV`
- `MCP_SANDBOX_EXP`
- `MCP_SANDBOX_ANALYZE`
- `MCP_SANDBOX_LOOP`

### Emergency stop tokens
- `STOP <job_id>`
- `STOPRUN <run_id>`

### External context / offload tokens
- External RAM: `@RAM`, `@todoist`
- Ollama offload: `@REPORT`, `@SUMMARY`, `@INDEX`, `@SEARCH`

## Canonical Sources

- Policy: `/Users/ryua/code/labenv_config/.mcp/policy.yaml`
- Token validator: `/Users/ryua/code/labenv_config/scripts/validate_env_tokens.py`
- Detailed rules: `/Users/ryua/code/labenv_config/docs/AGENTS_DETAILS.md`
- Exec usage: `/Users/ryua/code/labenv_config/docs/EXEC_MCP.md`

## Quick Checks

- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>"`
- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>" --env cc21 --execution-kind exec_compute`
- `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token mx:coop --dry-run`

## Repo Entrypoints

- Intent entrypoint: `python3 /Users/ryua/code/mcp_sandbox/scripts/execute_user_intent.py --repo-root /Users/ryua/code/shared_cache_utils "sandbox1 mx:coop で進めて"`
- Message-only entrypoint: `python3 /Users/ryua/code/mcp_sandbox/scripts/execute_message_only.py "sandbox mx:loop を shared_cache_utils で回して"`
- Trigger dispatch: `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token <TOKEN>`

## Tool Policy

- `web.image_query` は使用禁止。
- 画像が必要な場合は `web.search_query` を使い、画像掲載ページ URL を提示する。
