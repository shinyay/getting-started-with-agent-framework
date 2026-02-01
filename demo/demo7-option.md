# Demo 7 Option: Spec-driven Multi-Agent Workflow (Copilot Agent mode Prompt)

このドキュメントは、`shinyay/getting-started-with-agent-framework` リポジトリで **Spec-driven development** を行うための、**GitHub Copilot Agent mode** 向け指示文章（プロンプト・パケット）です。
目的は、複数エージェント（Constitution → Specify → Plan → Tasks）を **Workflow** として組み、CLI デモと DevUI entity の両方から実行できる形で実装させることです。

## How to use (Success criteria included)

1. Copilot Agent mode を開く
   - 成功条件: Agent mode が使える状態で、リポジトリを開いている

2. 下記「Copilot Agent mode 指示文章」を **そのまま貼り付ける**
   - 成功条件: Copilot が「この repo の既存コードを調べてから進める」前提で理解している

3. 追加で、あなたの今回の開発テーマ（要件）を貼り付ける
   - 成功条件: Copilot が不足情報を質問として列挙し、推測で埋めない

4. （追加要件）CLI デモを「引数なし」で実行した場合、標準入力でアプリ要件を入力できることを確認する
  - 成功条件: 引数なし実行で対話プロンプトが表示され、入力した内容がそのままワークフローの初期プロンプトとして利用される

---

## Copilot Agent mode 指示文章（貼り付け用）

あなたはこのリポジトリ（`shinyay/getting-started-with-agent-framework`）で、`src/demo5_workflow_edges.py` のような複数エージェントのワークフローを、新しく **Spec-driven development 用**に実装します。
ただし今回作るのは「Constitution / Specification / Technical Plan / Task list」の4段階を、マルチエージェントで生成できるワークフローです。CLI デモと DevUI entity の両方を作ってください。

### 1) 絶対に守る制約（重要）

- この repo は `requirements.txt` で **pinned** されています（`--pre` を含む）。
  **API を推測で書かない**こと。ドキュメントの latest と差分があり得るので、必ず **この repo の既存実装（`src/demo*.py`, `entities/**`）を根拠**にする。
- .env の扱いは既存デモ同様にする：
  Dev Container / Codespaces では env が空文字で入ることがあるため、**repo ルートの .env を読み込み、未設定または空文字の env のみ補完**（既存値は上書きしない）。
- Secrets/Keys をコード・ログ・ドキュメントに出さない。
- 変更後は最低限 `python3 -m compileall -q src entities` が通る状態にする。

### 2) 追加するもの（成果物と機能）

#### A. マルチエージェント・ワークフロー（4工程）

順番は固定：
1. **Constitution Agent**（プロジェクト憲法）
2. **Specify Agent**（要件明確化・機能仕様）
3. **Plan Agent**（技術計画・データモデル・設計）
4. **Tasks Agent**（実行可能タスク分割）

#### B. 成果物（Artifacts）は “英語 + 日本語” を必ず生成

成果物はファイルを分けて出力する（混在で読みにくくなるのを避けるため）。
次の 8 ファイルを想定し、各ファイルの必須見出しも固定する：

- `artifacts/constitution.en.md`
- `artifacts/constitution.ja.md`
  必須見出し（英語版）：
  - `## Principles`
  - `## Prohibitions`
  - `## Definition of Done`
  - `## Security & Secrets`
  - `## Output Format Rules`
  日本語版は対応する見出しを日本語で書く。

- `artifacts/spec.en.md`
- `artifacts/spec.ja.md`
  必須見出し（英語版）：
  - `## Goal`
  - `## Scope`
  - `## Requirements`
  - `## Non-Goals`
  - `## Edge Cases`
  - `## Acceptance Criteria`
  日本語版は対応する見出しを日本語で書く。

- `artifacts/plan.en.md`
- `artifacts/plan.ja.md`
  必須見出し（英語版）：
  - `## Approach`
  - `## Files to Change`
  - `## Implementation Steps`
  - `## Data Model`
  - `## Risks`
  - `## Validation`
  日本語版は対応する見出しを日本語で書く。

- `artifacts/tasks.en.md`
- `artifacts/tasks.ja.md`
  必須見出し：`## Task List`（チェックボックス形式）
  ルール：**1タスク=1論理変更**、各タスクに `Files` / `Done when` / `Validate with` を必ず書く（日本語版は日本語で対応項目を記載）。

重要：成果物の内容は、ユーザー入力（後述）に基づいて生成する。足りない情報は「質問」として列挙し、**推測で埋めない**。

#### C. DevUI 対応（必須）

`entities/` に新しい entity を追加し、DevUI から起動できるようにする。
既存の `entities/event_planning_workflow/workflow.py` を手本に、`WorkflowBuilder.register_agent(...)` を使う形式で組み立てること。

DevUI の要件：
- entity の import 時に落ちない（env 未設定でも “一覧表示” は壊さない）
- env が必須な処理は **agent 作成関数の中**で fail-fast にする
- 最終 executor（Tasks）を `output_response=True` にして、DevUI の最終出力が明確に表示されるようにする

#### D. CLI デモ（必須）

`src/` に新しいデモを追加する（ファイル名は `demo7_spec_driven_workflow.py` など、既存命名に合わせる）。
`src/demo5_workflow_edges.py` のパターンを踏襲すること：

- `AzureCliCredential` + `AzureAIAgentClient(...).as_agent(...)`
- `AsyncExitStack` で credential/client/agent をまとめて寿命管理
- `workflow.run_stream(prompt)` を使い、イベントを型で分岐して進捗表示
- **工程ごとの結果は “executor_id ごと” に回収**し、最後にまとめて表示する
  （最終出力イベントはフォールバックとして扱う）

追加要件（対話入力）：
- CLI デモは **引数なしで実行した場合**、標準入力（stdin）で「どのようなアプリケーションを作りたいか」を入力できること。
- その stdin 入力（複数行可）を、Spec-driven workflow の **初期プロンプト（project/context/requirements/constraints を含む要求文）**として使用し、Constitution → Specify → Plan → Tasks を回すこと。
- 実装上の注意：
  - 対話モードは `sys.stdin.isatty()` のときのみ有効にし、パイプや CI でハングしないようにする。
  - 何も入力されなかった場合は、分かりやすいエラーで fail-fast する。
  - 引数でプロンプトを渡した場合（例：`--prompt` / `--file` など）は、stdin の問い合わせは行わない。

### 3) エージェントの役割（Instruction の要求）

各エージェントに渡す instructions は次を満たす：

- **Constitution Agent**
  - 目的：このプロジェクトの判断基準（原則、禁止事項、DoD、セキュリティ、出力規約）を定義
  - 出力：`constitution.*.md` のみ
  - 不明点は「Open Questions」として列挙し、決め打ちしない

- **Specify Agent**
  - 目的：ユーザー要求を “実装可能な仕様” に落とす（受け入れ基準を具体化）
  - 出力：`spec.*.md`
  - 仕様で外部 SDK/API に触れる場合は、この repo の pinned 実装を根拠にする

- **Plan Agent**
  - 目的：仕様から技術計画を作る（変更ファイル、データモデル、実装手順、リスク、検証）
  - 出力：`plan.*.md`
  - “この repo で動くパターン” を前提に計画を書く（src と entities）

- **Tasks Agent**
  - 目的：PR に落ちる粒度のタスクへ分解（チェック可能な完了条件）
  - 出力：`tasks.*.md`

### 4) ツール・外部依存の方針（今回のデフォルト）

- まずは **Web Search は使わない**（Bing connection 等の環境依存を増やさないため）。
- MCP（`npx`）も **必須にはしない**。必要なら後から Plan Agent のみに付与する提案は可。
- つまり今回のデフォルトは「Foundry Agents + 4エージェント + workflow edges + artifacts 生成」に集中する。

### 5) 環境変数（Foundry Agents 前提）

最低限必要：
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

既存デモに合わせて：
- .env を repo ルートから読み込み（未設定/空の env のみ補完）
- 可能なら `AZURE_AI_PROJECT_ENDPOINT` の DNS 解決チェックを入れ、Private DNS の切り分けができるエラーメッセージにする
  （ただし DevUI import 時ではなく、実行時にチェック）

### 6) ワークフローの I/O（ユーザー入力）

ワークフローの入力（プロンプト）は、最低限以下を受け取れるようにする：

- Project: `<project name>`
- Context: `<background>`
- Requirements: `<what to build>`
- Constraints: `<languages, frameworks, runtime, non-functional>`
- Repo constraints: “pinned agent-framework; no guessing APIs; compileall required”

追加要件（入力経路）：
- CLI デモは「引数なし」の場合、上記入力を **stdin から対話的に受け取る**。
- 可能なら、ユーザーが入力しやすいように次のいずれかを採用する：
  - 1つの自由記述テキスト（後段で agent が項目化）
  - または、Project/Context/Requirements/Constraints を順に聞く簡易ウィザード

入力が不足している場合は、Constitution/Specify で質問リストを出し、その質問を成果物に含めること。

### 7) 完了条件（Acceptance）

- CLI デモが起動し、4工程が順に実行される（env が揃っている前提）
- CLI デモを引数なしで実行した場合、stdin 入力 → workflow 実行に進む（TTY のみで対話、非TTYはハングしない）
- DevUI entity が import でき、DevUI の一覧に表示される（env 未設定でも落ちない）
- `artifacts/*.md` が英語・日本語で出揃い、必須見出しを満たす
- `python3 -m compileall -q src entities` が通る

### 8) 作業の進め方（Copilot への要求）

- まず `requirements.txt` と既存ファイル（`src/demo5_workflow_edges.py`, `entities/event_planning_workflow/workflow.py`, `src/demo6_devui.py`）を根拠に API を確認してから実装に入ること。
- `WorkflowBuilder` は pinned 差分がある可能性があるため、既存デモ同様に互換性を考慮する（例：kwargs が合わない場合のフォールバック）。
- 余計なリファクタや依存追加はしない（最小変更）。

---

## Optional: Input template (paste after the instructions)

Project:
- Name:
- Audience:
- Timeline:

Context:
- Background:
- Existing system / repo constraints:

Requirements:
- Must-have:
- Nice-to-have:

Constraints:
- Language/runtime:
- Deployment:
- Security/compliance:

Open questions:
- (If any)
