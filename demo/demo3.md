# Demo 3 — MCP Stdio Tool（sequential-thinking をローカルで起動）

Scott の demo03 と同じ狙いで、**stdio MCP server** をツールとして追加し、
LLM がツール（sequential-thinking）を使いながら段階的に計画を立てる様子を観察します。

## ねらい
- `MCPStdioTool` を追加して **ローカル MCP server（sequential-thinking）** を起動する
- “MCP（Model Context Protocol）で標準化されたツール” を **Foundry Agents から呼ぶ**感覚を掴む
- OTel span（任意）で「agent / tool が呼ばれた」痕跡を見える化する（Scott 風）

---

## 前提
- Demo 2 まで完了している（Azure AI Foundry Agents の env vars 設定済み）
- `agent-framework-azure-ai` がインストール済み
- `az login` 済み

追加:
- `node` / `npx` が利用できること
  - この dev container では通常プリインストールされています

> このデモでは Foundry ポータルでの「Hosted tool 追加」は不要です。
> `MCPStdioTool` がローカルで `npx ...` を起動します。

> このデモは **Azure AI Foundry Agents** をバックエンドとして実行します。
> `AZURE_AI_PROJECT_ENDPOINT` は `https://...services.ai.azure.com/api/projects/...` の形式（Foundry Project endpoint）である必要があります。

---

## 手順

### Step 0. `.env` の確認（推奨）
Demo 2 と同様、Dev Container / Codespaces では環境変数が **空文字で注入**されることがあります。
このリポジトリの `src/demo3_hosted_mcp.py` は、リポジトリルート `.env` を明示的に読み込み、**未設定または空の環境変数だけ補完**します。

最低限、以下が入っていることを確認してください：

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"
```

> Demo 3 は Bing connection を使いません。

### Step 1. スクリプトを確認（`src/demo3_hosted_mcp.py`）
このリポジトリには `src/demo3_hosted_mcp.py` が同梱されています。

主なポイント:
- Agent Framework の推奨パターンに合わせて `AzureAIAgentClient(...).as_agent(...)` を使用
- Tools:
  - `MCPStdioTool(name="sequential-thinking", command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"])`

補足:
- Scott のコードでは `client.create_agent(...)` ですが、このリポジトリで pinned している SDK では `as_agent(...)` が現行 API なので、それに合わせています
- `npx` は初回実行時にパッケージ取得が入るので、最初だけ少し時間がかかる場合があります

### Step 2. 実行
```bash
python3 src/demo3_hosted_mcp.py
```

### Step 3. 期待される出力
以下のように、Scott と同じ「イベント計画」が出力されます。

- client/agent/run の進行ログ
- tool 呼び出しが入った場合（OTel が有効なら）`[TOOL] ... tool=...` のログ
- 最後に、ホリデーパーティーの計画（候補、タイムライン、役割分担、予算観点など）がまとまって出力

---

## MCP が動作しているかの判断基準（重要）

### 1) いちばん確実: Foundry の Run traces / 実行トレースで確認
Foundry 側のトレースで **tool 呼び出しが記録されている**ことを確認するのが確実です。

### 2) 簡易: OTel span ログ（任意）
このデモは OpenTelemetry が利用可能な環境では、agent/tool span を簡易に 1 行で出力します。
`[TOOL] ... tool=sequential-thinking` が見えれば「ツールが呼ばれた」ことが分かります。

---

## 技術解説（MCP / MCPStdioTool を理解する）

### 1) MCP（Model Context Protocol）とは？
- “LLMが外部のツール/データソースを使う” ときの **標準化プロトコル**
- ざっくり言うと
  - **MCP Server**：ツール（機能）とリソース（データ）を公開する
  - **MCP Client / Tool**：エージェント側がサーバーに接続して利用する

### 2) MCPStdioTool は何が嬉しい？
- MCP server を **ローカルプロセスとして起動**し、stdio で通信するスタイル
- Foundry ポータルでのツール追加や接続設定に依存しにくく、手元で再現しやすい

注意:
- ローカルでプロセスを起動するため、実行環境のポリシー（外部コマンド実行の可否）に依存します
- `npx -y ...` は外部パッケージ取得を伴うため、ネットワーク制限があると失敗する場合があります

### 3) sequential-thinking（段階的推論の外部化）
- いきなり回答を書かせるのではなく、ツール側に「考える手順」を委譲して、
  その結果を使って最終回答を組み立てるパターンを体験できます

---

## うまくいかない時のチェック

### `npx` が見つからない
- Node.js をインストールする（この dev container では通常不要）

Debian / Ubuntu 系の環境であれば、以下で導入できます：

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

### `npx` が失敗する（ネットワーク制限など）
- 実行環境から npm registry に到達できるか
- Proxy が必要な環境では npm の proxy 設定が必要な場合があります

追加チェック（DNS）:
- `AZURE_AI_PROJECT_ENDPOINT` のホスト名（例: `*.services.ai.azure.com`）が実行環境から DNS 解決できないと、このデモは開始時点で停止します
  - エラー例: `Cannot resolve AZURE_AI_PROJECT_ENDPOINT host via DNS`
  - 対応: Private networking / DNS の構成を見直す、または DNS 解決できるネットワークから実行する
  - 暫定対応として `/etc/hosts` で固定する方法もありますが、IP 変更の可能性があるため恒久対策には非推奨です

### “ツールが使えない” エラー
- ローカルコマンド実行が許可されているか（企業端末/CI の制限など）
- `npx` が起動できているか（上のログでエラーが出ていないか）

---

## 次のデモへ
Demo 4 では、`response_format` を使って **構造化出力**を取り出します。
→ `demo4.md` を開いて続けてください。
