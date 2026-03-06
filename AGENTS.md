# AGENTS.md

## Control Plane Boundary

- `mcp_sandbox` / codex-factory は `sandboxN` の orchestration を担当する。
- `labenv_config` は `env1_a6000` / `env2_3090` / `cc21` の execution bridge を担当する。
- `sandboxN` と `env*` は別物であり、同一視しない。
- `sandboxN` は host selector、`mx:*` は workflow selector として組み合わせる。

## Recommended Entrypoints

- `python3 /Users/ryua/code/mcp_sandbox/scripts/execute_user_intent.py --repo-root /Users/ryua/code/shared_cache_utils "sandbox1 mx:coop で進めて"`
- `python3 /Users/ryua/code/mcp_sandbox/scripts/execute_message_only.py "sandbox mx:loop を shared_cache_utils で回して"`
- `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token mx:loop`

## Public Sandbox Workflow Tokens

公開 trigger token は `mx:*` 系のみを使う。`MCP_SANDBOX_*` は内部実装トークンであり、通常のユーザープロンプトには入れない。

| Token | Alias | Route | Purpose |
| --- | --- | --- | --- |
| `mx:dev` | - | `sandbox` | Agentic DEV autopilot on sandbox1 profile |
| `mx:loop` | - | `sandbox` | Agentic EXP/ANALYZE loop on sandbox2 profile |
| `mx:local` | - | `outside` | Run an end-to-end local agentic development cycle with codex exec |
| `mx:exp` | `mxexp` | `sandbox` | One-shot experiment execution on sandbox2 |
| `mx:analyze` | `mxanalyze` | `sandbox` | Analyze experiment outputs and summarize metrics on sandbox2 |
| `mx:smoke` | `mxsmoke` | `sandbox` | Stop/smoke safety check on sandbox1 |
| `mx:sync` | `mxsync` | `sandbox` | Sync headnode mirror branch to selected sandbox host(s) |
| `mx:devflow` | `mxdevflow` | `pipeline` | Development workflow (sync -> local -> sandbox dev -> analyze) |
| `mx:expflow` | `mxexpflow` | `pipeline` | Experiment workflow (sync -> experiment -> analyze) |
| `mx:verify` | `mxverify` | `pipeline` | Verification workflow (sync -> analyze -> stop/smoke) |
| `mx:coop` | `mxcoop` | `pipeline` | Cooperative DEV and LOOP on sandbox1/sandbox2 |
| `mx:full` | `mxfull` | `pipeline` | Full cycle across development, experiment, and verification workflows |

## Host Selectors

- 利用可能な selector: `sandbox`, `sandbox1`, `sandbox2`, `sandboxN`
- `sandbox` のみなら default host group に委ねる。
- `sandboxN` を併記すると、その host を優先して配分する。
- 将来 `config/sandboxes.yaml` に host を追加した場合も `sandboxN` 命名で同じ規約を使う。

## Labenv Execution Tokens

- `ref:<target>`
- `test:<target>`
- `exe:<target>`

`<target>` は `env1_a6000`, `env2_3090`, `cc21` を使う。

組み合わせルール:
- 同一 target で `ref + test` は許可。
- 同一 target で `exe` と他 mode の併用は不可。

## Operational Tokens

- Emergency stop: `STOP <job_id>`, `STOPRUN <run_id>`
- External RAM: `@RAM`, `@todoist`
- Ollama offload: `@REPORT`, `@SUMMARY`, `@INDEX`, `@SEARCH`

## Internal Sandbox Tokens

以下は `factory_auto.sh` / `codex-factory` 内部で使う。公開 trigger token としては扱わない。

- `MCP_SANDBOX_SYNC`
- `MCP_SANDBOX_STOP_SMOKE`
- `MCP_SANDBOX_DEV`
- `MCP_SANDBOX_EXP`
- `MCP_SANDBOX_ANALYZE`
- `MCP_SANDBOX_LOOP`

## Canonical Sources

- Sandbox inventory: `/Users/ryua/code/mcp_sandbox/config/sandboxes.yaml`
- Trigger defaults: `/Users/ryua/code/mcp_sandbox/scripts/trigger_profile_lib.py`
- Dispatch entrypoint: `/Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py`
- Intent entrypoint: `/Users/ryua/code/mcp_sandbox/scripts/execute_user_intent.py`
- Labenv policy: `/Users/ryua/code/labenv_config/.mcp/policy.yaml`
- Labenv validator: `/Users/ryua/code/labenv_config/scripts/validate_env_tokens.py`

## Quick Checks

- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>"`
- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>" --env cc21 --execution-kind exec_compute`
- `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token mx:coop --dry-run`

## Tool Policy

- `web.image_query` は使用禁止。
- 画像が必要な場合は `web.search_query` を使い、画像掲載ページ URL を提示する。
