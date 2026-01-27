# Demo 3 — Hosted MCP Tool（Microsoft Learn MCP をツールとして追加）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python#using-built-in-and-hosted-tools
```

## ねらい
- `HostedMCPTool` を追加して **Microsoft Learn MCP** に接続する
- “MCP（Model Context Protocol）で標準化された外部ツール” を使う感覚を掴む
- 可能なら、**複数ツールを連続呼び出し（sequential tool calls）**する挙動を観察する

補足（このデモで確認したいこと）:
- 「ドキュメント（Microsoft Learn）→追加確認（Web検索）」のように、**目的ごとにツールを使い分ける**感覚
- MCP は “Web検索” と違い、**公式ドキュメントソースに寄せた検索・取得**がしやすい（はず）

---

## 前提
- Demo 2 まで完了している（Azure AI Foundry Agents の env vars 設定済み）
- `agent-framework-azure-ai` がインストール済み
- `az login` 済み

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

# Demo 3 は sequential tool calls 観察のため Web Search も併用します
# （そのため Bing connection が必要です。値は Project connection ID です）
BING_CONNECTION_ID="/subscriptions/.../resourceGroups/.../providers/Microsoft.MachineLearningServices/workspaces/.../connections/..."
```

> MCP 単体で試したい場合は、`src/demo3_hosted_mcp.py` から Web Search を外してください。

### Step 1. スクリプトを確認（`src/demo3_hosted_mcp.py`）
このリポジトリには `src/demo3_hosted_mcp.py` が同梱されています。

主なポイント:
- Agent Framework の推奨パターンに合わせて `AzureAIAgentClient(...).as_agent(...)` を使用
- Tools:
  - `HostedMCPTool(name="Microsoft Learn MCP", url="https://learn.microsoft.com/api/mcp")`
  - `HostedWebSearchTool(...)`（sequential tool calls 観察用）
- MCP が使えない/不安定な環境でもデモが止まらないように、
  **MCP が失敗したら Web Search のみで続行するフォールバック**を入れています

### Step 2. 実行
```bash
python3 src/demo3_hosted_mcp.py
```

### Step 3. 期待される出力
環境によって挙動が分かれます。

1) MCP が利用できる場合
- 「MCP（Microsoft Learn）で公式手順を見つける」→「Web検索でUI変更などを確認」→「手順+CLI例」の順で出力されます

2) MCP が不安定/利用不可の場合
- `(Note) Microsoft Learn MCP tool call did not produce a usable response...` の表示後
- Web Search のみで公式情報を探し、手順+CLI例を出力します

> `https://learn.microsoft.com/api/mcp` は API エンドポイントで、ブラウザ等で GET すると 405 になることがあります。
> それ自体は異常ではありません（MCP クライアントとしての呼び出しを前提としたエンドポイントです）。

---

## 技術解説（MCP / HostedMCPTool を理解する）

### 1) MCP（Model Context Protocol）とは？
- “LLMが外部のツール/データソースを使う” ときの **標準化プロトコル**
- ざっくり言うと
  - **MCP Server**：ツール（機能）とリソース（データ）を公開する
  - **MCP Client / Tool**：エージェント側がサーバーに接続して利用する

### 2) HostedMCPTool は何が嬉しい？
- MCP への接続とツール呼び出しを “サービス側” が管理するスタイル
- エージェントに `tools=[HostedMCPTool(...)]` と追加するだけで、LLMが必要に応じて MCP を呼べる

補足:
- Hosted Tools は「どのツールが使えるか」「どのドメインに到達できるか」が **バックエンド/環境/権限**に左右されます
- Demo 2 の Web Search と同様、動かない場合は **まずエラーメッセージ全文**を確認してください

### 3) sequential tool calls（連続ツール呼び出し）
- ひとつの質問に対し
  - 「まずドキュメントを調べる」→「次に別の確認をする」
  というように、複数のツールを連続で呼ぶ可能性があります
- ただし **実際に連続呼び出しが起きるかはプロンプトとモデル判断次第**です
  → 上の `prompt` のように「手順を分けて明示する」と起きやすくなります

補足（観察のコツ）:
- “まず MCP を使え” のように優先順位を明示し、次に “Web Search で確認せよ” と続ける
- それでもモデルがツールを呼ばない/呼べない場合は、バックエンド側が未対応の可能性があります

---

## うまくいかない時のチェック

### MCP の URL が誤っている
- `https://learn.microsoft.com/api/mcp` が指定されているか

### MCP が空応答 / "Sorry, something went wrong" になる
環境（バックエンド/リージョン/ネットワーク制約/プレビュー機能の有効化状況）によって、Hosted MCP Tool が安定して動かないことがあります。

このリポジトリの `src/demo3_hosted_mcp.py` は、デモ継続のため **Web Search のみ**にフォールバックします。
まずは以下を確認してください：

- Foundry 側で Hosted Tools が利用可能か（権限・機能・リージョン）
- 実行環境が外部エンドポイントに到達できるか（特に Private networking）

### “ツールが使えない” エラー
- Demo2 と同様、バックエンド側で Hosted Tools が利用可能か確認（権限/リージョン/機能）

---

## 次のデモへ
Demo 4 では、`response_format` を使って **構造化出力**を取り出します。
→ `demo4.md` を開いて続けてください。
