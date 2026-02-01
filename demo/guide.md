# Agent Framework 学習ガイド（Demo 1〜6：コード読解版）

この `demo/guide.md` は「どう実行するか」よりも、**はじめて Agent Framework を使って開発していく人が、デモコードから何を読み取り、どう応用していくか**に焦点を当てたガイドです。

- “やること” は **コードを読むこと**です（Demo 1〜6 は、概念が段階的に増えるように作られています）
- Agent Framework は更新が速いので、**このリポジトリで pinned されている依存**と **`src/demo*.py` の実装**を正とします

  - pinned 版の確認: `requirements.txt`（例: `agent-framework==1.0.0b260123`）

> Microsoft Learn は “latest” の可能性があります。差分が疑われる場合は、本リポジトリの pinned 版の挙動（`requirements.txt` / `src/` / `entities/`）を優先してください。

---

## どの順で読むべきか（学習の地図）

| Demo | 読み取るテーマ | 主なファイル |
|---:|---|---|
| 1 | 最小のエージェント実行、環境変数/ネットワークの fail-fast、async リソース管理 | `src/demo1_run_agent.py` |
| 2 | Hosted tool（Web Search）の組み込みと “接続情報” の扱い | `src/demo2_web_search.py` |
| 3 | MCP（stdio）= 外部プロセスを tool にする、環境依存/安全性 | `src/demo3_hosted_mcp.py` |
| 4 | 構造化出力（Pydantic）、`response_format` とフォールバック設計 | `src/demo4_structured_output.py` |
| 5 | Workflow によるオーケストレーション、イベント駆動の観測、寿命管理 | `src/demo5_workflow_edges.py` |
| 6 | DevUI のホスト、entity/workflow の発見と UX 設計（import と runtime 検証の分離） | `src/demo6_devui.py`, `entities/**` |

---

## このリポジトリ共通で覚える「型」

### 1) `.env` は **fill-only**（未設定/空のみ補完）

各デモはリポジトリルートの `.env`（`/workspaces/.env`）を明示的に読み込みますが、**既存の環境変数を無条件に上書きしません**。

- Dev Container / Codespaces では env が **空文字で注入**されることがある
- `VAR=... python ...` の一時上書きによるデバッグを邪魔しない

この方針は `AGENTS.md` の「環境変数は未設定/空のみ補完」に一致します。

### 2) `_require_env()` で “不足” を最初に確定する

外部依存（認証、RBAC、ネットワーク、モデル名、接続設定）が多いので、
**SDK を叩く前に「足りないもの」を確定**させ、エラーを読みやすくします。

> 初学者がハマりやすいのは「設定不足なのに SDK が奥の方で落ちて、原因がぼやける」パターンです。

### 3) DNS の事前チェック（Private Link/Private DNS の切り分け）

`AZURE_AI_PROJECT_ENDPOINT` の hostname を `socket.getaddrinfo(...)` で引けるかを先にチェックし、
**ネットワーク問題を早期に特定**します。

### 4) `async with` で credential/client/agent を確実に閉じる

`AzureCliCredential` や `AzureAIAgentClient`、agent インスタンスは **非同期リソース**です。
デモでは `async with`（または `AsyncExitStack`）で寿命管理を徹底しています。

### 5) 「分かる範囲だけ」例外を翻訳する

`ServiceResponseException` などクラウド由来の例外は、原因が典型的なもの（例：モデルデプロイ名）に限り、
**次に何を確認すべきか**が分かるメッセージに変換しています。

### 6) 観測性は optional（OpenTelemetry があれば使う）

OpenTelemetry を必須にせず、入っていれば “agent/tool の動き” が見える形にしています。
「便利だが環境差があるもの」は **任意にする**のがデモとして親切です。

### 7) Ctrl+C を “想定された終了” として扱う（exit code 130）

長時間プロセス（DevUI など）で、ユーザー中断を分かりやすく扱うための慣習です。

---

## Demo 1：最小のエージェント実行（= これ以降の土台）

対象: `src/demo1_run_agent.py`

### このデモで読むべきポイント

- `.env` fill-only：Dev Container/Codespaces の “空文字 env” を踏まえた設計
- `_require_env(...)`：必須設定を fail-fast
- `_check_project_endpoint_dns()`：ネットワーク問題の切り分け
- `AzureCliCredential` + `AzureAIAgentClient(...).as_agent(...)`：この repo の基本形
- `agent.run(...)` と `result.text`：まずは最小の戻り値で学習コストを下げる

### 応用の観点（開発での読み替え）

- 「ツールを追加したい」→ Demo 2/3
- 「出力をプログラムで扱いたい」→ Demo 4
- 「複数工程に分割したい」→ Demo 5

---

## Demo 2：Hosted Web Search（ツールを “設計要素” として扱う）

対象: `src/demo2_web_search.py`

### このデモで読むべきポイント

- `tools=[HostedWebSearchTool(...)]`：tool は “関数呼び出し” ではなく **エージェントに付与する能力**
- `_get_bing_tool_properties()`：接続情報の組み立て（env 名の揺れを吸収）
- `additional_properties`：ツール実行の文脈（例：`user_location`）を渡す
- `ServiceResponseException` の翻訳：特に `Failed to resolve model info` のメッセージ改善

### 初学者がハマる点（なぜこの設計？）

- “Bing の API キー” ではなく、Foundry 側の **project connection** が必要になる
- 接続情報は環境差が出やすいので、コード側で揺れを吸収している

> 補足: `AZURE_AI_MODEL_DEPLOYMENT_NAME` は **Foundry プロジェクトのモデルデプロイ名**です。
> デモ内のエラーメッセージでは（過去の例に由来して）Azure OpenAI のデプロイ名に言及することがありますが、
> 要点は「**別の場所で使っている“デプロイ名”と混同しない**」です。

---

## Demo 3：Hosted MCP（stdio で外部プロセスを tool にする）

対象: `src/demo3_hosted_mcp.py`

### このデモで読むべきポイント

- `_require_command("npx")`：外部依存を fail-fast（PATH/Node の切り分け）
- `MCPStdioTool(...)`：tool の実体が **ローカルの外部プロセス**になる
- `args=["-y", "@modelcontextprotocol/server-sequential-thinking"]`：対話プロンプトで止まらない配慮
- `load_prompts=False`：挙動を固定化して予測可能性を上げる（説明可能な安全側の選択）

### セキュリティ視点（初心者向けに最低限）

- 外部プロセス起動はサプライチェーン/権限境界の話になり得る
- デモ段階から「どのコマンドを許すか」は意識しておくと後で楽

---

## Demo 4：Structured Output（Pydantic で “アプリ向けデータ” にする）

対象: `src/demo4_structured_output.py`

### このデモで読むべきポイント

- Pydantic モデル（`VenueInfoModel`, `VenueOptionsModel`）：
  - 欲しいデータ（= アプリ要件）を **スキーマに落とす**
- `agent.run(..., response_format=VenueOptionsModel)`：
  - 返答を “文字列” ではなく “構造化データ” として受け取る試み
- フォールバック：
  - `response.value` が取れない場合に備えて `response.text` から復元する

### なぜフォールバックが必要？

Agent Framework / バックエンドや pinned バージョン差分で、
「`.value` が常に埋まる」とは限りません。
このデモは **壊れやすい部分にフォールバック層を入れる**という実務的な判断を見せています。

---

## Demo 5：Workflow（“会話”から “実行フロー” へ）

対象: `src/demo5_workflow_edges.py`

### このデモで読むべきポイント

- `AsyncExitStack` による寿命管理：
  - 複数 agent を作るほど `async with` のネストが辛くなる → まとめて管理する
- 役割分割（coordinator/venue/...）：
  - 工程と責任を分け、ツールも最小限に付与する（最小権限の感覚）
- `WorkflowBuilder` と edge：
  - “次に誰を走らせるか” を **宣言的に**定義する
- `run_stream()` とイベント処理：
  - token を垂れ流さず、executor 切り替えで進捗を把握する
- `_print_result_item()`：
  - イベント payload の揺れを吸収する “表示層” を用意する

### pinned 差分への配慮（初心者が真似すべき姿勢）

`WorkflowBuilder(**kwargs)` が通らない可能性に備えて `try/except TypeError` でフォールバックしています。
「beta/pinned を前提にするなら、互換性ガードはコストに見合う」ことが読み取れます。

---

## Demo 6：DevUI（開発体験を良くするコード設計）

対象: `src/demo6_devui.py` と `entities/**`

### このデモで読むべきポイント

- `sys.path` の調整：
  - `python src/...` 直実行で import が壊れやすい問題を回避
- `serve(entities=[workflow], ...)`：
  - DevUI は “entity（workflow/agent）” を渡すと UI をホストできる
- 起動前のポートチェック：
  - 初学者が迷いにくいエラーにする（UX をコードで作る）
- entity 側の設計（重要）：
  - DevUI は import して entity を列挙するため、**できれば import 時に落とさず**、実行時に必要条件を検証する
  - この方針の具体例: `entities/event_planning_workflow/workflow.py` は `_validate_environment()` を “実行時” に呼びます

### entities のバリエーション（DevUI で何が動くかを読む）

`entities/**` には複数の workflow entity が入っています。DevUI では **どの entity を開くか**で前提が変わるので、
まず各 entity が「どのクライアント（Foundry / Azure OpenAI）を使っているか」を確認します。

- `entities/event_planning_workflow/workflow.py`
  - `AzureAIAgentClient`（Foundry Agents）を使用
  - env 検証は `_validate_environment()` に集約（DevUI の “一覧表示” を邪魔しない）
- `entities/ai_genius_workflow/workflow.py`
  - `AzureOpenAIChatClient`（Azure OpenAI）を使用
  - env の必須化が import 時点で走るため、未設定だと DevUI 起動時に落ち得ます（改善余地）

> DevUI は「まず起動して一覧が見える」こと自体が開発体験の核なので、
> import と runtime requirements を分ける設計は、デモ以上に実務で効きます。

---

## つまずいたときに “コードで” どこを見るか

- 設定不足（env）：各 demo の `_require_env(...)`
- ネットワーク/DNS：`_check_project_endpoint_dns()`
- モデル名：例外の `Failed to resolve model info` 翻訳箇所（Demo 2/3/4/5）
- 権限：403/Forbidden の翻訳箇所（特に Demo 5）
- ローカル依存：`_require_command("npx")`（Demo 3/5）
- DevUI：ポート事前チェックと `DEMO_NO_OPEN` の分岐（Demo 6）

---

## 参考（Microsoft Learn）

※以下は “latest” の可能性があるため、挙動が異なる場合は本リポジトリ（pinned）を優先してください。

- Run agent（Python）
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- Agent tools（built-in / hosted tools）
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python
- Structured output
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
- DevUI
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference
