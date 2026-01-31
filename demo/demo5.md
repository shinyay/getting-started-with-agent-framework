# Demo 5 — Multi-agent Workflow（Event Planning Workflow）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/agents-in-workflows?pivots=programming-language-python
```

Scott の demo05 と同じ狙いで、**複数の専門エージェントを workflow（edge）で直列につなぎ**、
イベント計画を “分業→統合” するデモです。

## ねらい
- 役割（専門性）ごとにエージェントを分割し、**Edge で順序を固定**して安定したパイプラインを作る
- Hosted tools（Web Search / Code Interpreter）と MCP tool（sequential-thinking）を、ワークフローの中で使う
- （任意）OTel span を 1 行で出して「agent/tool が呼ばれた」を観察する

このデモのワークフローは次の順です：

1. `coordinator`（全体設計 + sequential-thinking）
2. `venue`（会場候補の調査：Hosted Web Search）
3. `catering`（ケータリング案の調査：Hosted Web Search）
4. `budget_analyst`（概算と配分：Hosted Code Interpreter）
5. `booking`（最終統合：markdown でプラン出力）

---

## 前提

### 共通（Foundry Agents）
- Demo 2 まで完了（Foundry の env vars 設定済み）
- `agent-framework-azure-ai` がインストール済み
- `az login` 済み（このデモは既定で AzureCliCredential を利用）

必要な env var：

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"
```

### 追加（このデモ固有）

#### 1) sequential-thinking（MCP stdio）
- `node` / `npx` が使えること（`MCPStdioTool` がローカルで `npx ...` を起動します）

#### 2) Hosted Web Search（Bing connection）
このデモは会場/ケータリングで Web 検索を行うため、Bing grounding の接続 ID が必要です。

次のどちらかを設定してください：

- `BING_CONNECTION_ID`（または `BING_PROJECT_CONNECTION_ID`）
- もしくは Custom Search の場合は
  - `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`
  - （または `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID` + `BING_CUSTOM_SEARCH_INSTANCE_NAME`）

> `src/demo5_workflow_edges.py` はリポジトリルート `.env` を明示ロードし、未設定/空の env var だけ補完します（Dev Container / Codespaces の空文字注入対策）。

---

## 手順

### Step 1. `.env` の確認（推奨）
最低限、以下が必要です：

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `BING_CONNECTION_ID`（または同等の Bing 接続設定）

### Step 2. ログイン（Entra ID）

```bash
az login --use-device-code
```

### Step 3. 実行

```bash
python3 -u src/demo5_workflow_edges.py
```

（任意）Scott 風に実行後に一時停止したい場合：

```bash
DEMO_PAUSE=1 python3 -u src/demo5_workflow_edges.py
```

期待される挙動：

- `Running workflow...` の後に `Workflow Result:` が表示される
- 出力は複数ステップ（専門家ごとの結果）として並ぶ
- （OTel が有効な環境では）`[TOOL] ... tool=...` / `[AGENT] ...` のようなログが混ざる

---

## 技術メモ（Scott との寄せポイント）

- Scott の demo05 は「イベント計画を *複数専門家* に分業させ、最後に booking が統合する」流れ
- このリポジトリの pinned SDK では `create_agent(...)` ではなく `AzureAIAgentClient(...).as_agent(...)` を使うのが安全なため、同等のストーリーを `as_agent` ベースで実装しています

---

## うまくいかない時のチェック

### `npx` が見つからない
- Node.js を導入してください（dev container では通常不要）

### Bing connection が無い
- `BING_CONNECTION_ID`（または `BING_PROJECT_CONNECTION_ID`）を設定してください

### 403 / Forbidden
- `az login` 済みか
- Foundry の Project / Hub に実行ユーザーの RBAC が付与されているか

### Failed to resolve model info
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` が Foundry の **Models + endpoints のデプロイ名**になっているか

### DNS 解決に失敗して開始前に止まる
- Private networking / private DNS を疑ってください
  - 同梱スクリプトは DNS を事前チェックして分かりやすいエラーにしています

---

## 次のデモへ（DevUI）
Demo 6 では、この “Event Planning Workflow” を **DevUI で可視化**します。
→ `demo6.md` を開いて続けてください。
