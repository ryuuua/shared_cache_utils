# AGENTS.md

## Fast Path (Unified)

| Mode | Allowed | Denied |
| --- | --- | --- |
| no token | reference/resolve/explain/static checks | any real execution |
| `refenvN` | same as no token (env-scoped) | any real execution |
| `testenvN` | approved test/probe execution | arbitrary user execution |
| `exeenvN` | user-requested execution | none beyond environment constraints |

### Source of Truth
- Policy: `/Users/ryua/code/labenv_config/.mcp/policy.yaml`
- Validator: `/Users/ryua/code/labenv_config/scripts/validate_env_tokens.py`
- Detailed rules: `/Users/ryua/code/labenv_config/docs/AGENTS_DETAILS.md`

### Execution Rule
- `execution_kind=none`: token not required.
- `execution_kind=exec_login|exec_compute`: env token required (`testenvN` or `exeenvN`).
- Missing token for execution must fail with `execution_token_required`.

### MCP Usage
1. Call `server_info` once per MCP server at session start and cache the result.
2. Prefer composite tools (`resolve_and_run`, `resolve_and_submit_sbatch`).
3. For runtime facts, prefer `verify_runtime_facts` (light first, compute only when needed).

### Repo Note
- Any execution must target a `project_id` registered in `/Users/ryua/code/labenv_config/projects.yaml`.

### Quick Checks
- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>"`
- `python3 /Users/ryua/code/labenv_config/scripts/validate_env_tokens.py "<message>" --env env3 --execution-kind exec_compute`

## MCP_SANDBOX_TRIGGER

If user input contains one of these tokens, run codex-factory automation via mcp_sandbox:
- MCP_SANDBOX_SYNC
- MCP_SANDBOX_STOP_SMOKE
- MCP_SANDBOX_DEV
- MCP_SANDBOX_EXP
- MCP_SANDBOX_ANALYZE
- MCP_SANDBOX_LOOP

Execution command template:
```bash
bash /Users/ryua/code/mcp_sandbox/scripts/factory_auto.sh \
  --token <TOKEN> \
  --repo-id shared_cache_utils \
  --repo-name shared_cache_utils \
  --branch "$(git rev-parse --abbrev-ref HEAD)"
```

STOP-first override:
- \'STOP <job_id>\' -> `python3 /Users/ryua/code/mcp_sandbox/scripts/kill_switch.py --mcp-url http://127.0.0.1:18177/mcp --target job --id <job_id> --mode kill`
- \'STOPRUN <run_id>\' -> `python3 /Users/ryua/code/mcp_sandbox/scripts/kill_switch.py --mcp-url http://127.0.0.1:18177/mcp --target run --id <run_id> --mode kill`

Use codex_factory MCP for orchestration; do not use labenv_* tools for job/run/fleet control.

## EXTERNAL RAM WORKFLOW (Context Switch)

ユーザー入力にコマンドトークン `@RAM` または `@todoist` が含まれている場合、複数ツールの逐次呼び出しは行わず、**必ず `workflow_external_ram` を1回だけ**呼び出して退避すること。

1. **コンテキスト抽出**
- Context: 中断理由、現在状態、失敗内容など。
- Next Action: 次の具体的な着手項目。
2. **マクロ退避実行**
- `workflow_external_ram(repo_name, context, next_action, todoist_project_id?)` を1回だけ実行する。
- `repo_name` は必ず `owner/repo` 形式。
- `todoist_project_id` を省略した場合は Inbox（またはTodoist既定）に作成される。
3. **内部で同時実行される処理**
- GitHub Issue の起票（`[RAM] <next_action>`）
- Todoist タスク登録（Issueリンク付き）
- `codex_dashboard/<repo>_dashboard.md` の `## 中断ログ` へ追記（`prepend_to_heading`）
4. **ユーザー通知**
- ツール戻り値の `github_issue` / `todoist_task` / `dashboard_updated` を使って完了報告する。

使い方例:
- `行き詰まったので一旦寝ます。 @RAM [Context: 依存解決で404] -> [Next Action: private registry設定を確認]`

## OLLAMA LOCAL RAG & REPORT WORKFLOW

強力なローカルLLM（Ollama）への処理のオフロードを行うためのトークン一覧です。このトークンが含まれていた場合、長文の読み込みや要約推論はエージェント自身で行わず、速やかにMCPサーバーのローカル処理へ投げてトークン消費を抑止してください。

### `@REPORT`
フォルダ配下の `.md` を再帰的に集約し、ローカルLLMでレポート生成して保存したい場合のトリガー。
1. `ollama_generate_report` を利用する。
2. `source_directory`（入力ディレクトリ）、`target_file`（保存先）、`prompt`（指示）を渡す。
3. 出力は Vault に直接保存される。

### `@SUMMARY`
フォルダ配下の `.md` を再帰的に集約し、その場で要約結果だけを返したい場合のトリガー。
1. `ollama_summarize_directory` を利用する。
2. `directory_path` と `prompt` を渡す。

### `@INDEX`
VaultのローカルRAG用ベクトルキャッシュの再構築を行うトリガートークン。
1. `ollama_rebuild_index` ツールを利用する。
2. `target_directory` 指定時は対象配下のみ差分更新し、対象外キャッシュは保持する。
3. 未指定時は Vault 全体を再計算する。

### `@SEARCH`
ローカルのベクトルキャッシュに対し、意味的な関連でノートを検索するRAGトークン。
1. `ollama_semantic_search` ツールを利用する。
2. ユーザーの意図を汲んだ `query` と、必要な取得数 `top_k` (デフォルト5) を渡す。
3. 返却された結果（パスとプレビュー）を使って、エージェントがユーザーに的確に回答する。

使い方例:
- `@REPORT Codex Notes/CEBRA-NLP-gen2 の今週の進捗をレポート化して`
- `@INDEX を実行して`
- `@SEARCH PCAエラー回避策`

## Token Reference (Execution / Sandbox)

### Execution permission tokens
- `refenvN`: 読み取り・解決・静的確認のみ（実行不可）
- `testenvN`: 承認済みテスト/プローブ実行のみ
- `exeenvN`: ユーザー依頼の実行を許可
- 同一環境では `refenvN` と `testenvN` の併用を許可
- 同一環境で `exeenvN` と他モードの併用は不可

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

## Tool Policy

- `web.image_query` はこのリポジトリでは使用禁止。
- 画像が必要な場合は `web.search_query` を使って画像掲載ページURLを提示する。

<!-- AGENTIC_TRIGGER_TOKENS:BEGIN -->
## Agentic Trigger Tokens

このrepoでは `.mcp/trigger_profiles.yaml` のトリガー定義を使います。
以下のトークンをユーザー入力に含めると、`dispatch_repo_trigger.py` で実行できます。

- `mx:dev`
- `mx:loop`
- `mx:local`
- `headnode`
- `cc21`
- `local`

実行例:
- `python3 /Users/ryua/code/mcp_sandbox/scripts/dispatch_repo_trigger.py --repo-root /Users/ryua/code/shared_cache_utils --token <TOKEN>`
<!-- AGENTIC_TRIGGER_TOKENS:END -->
