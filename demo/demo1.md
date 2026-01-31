# Demo 1 — Getting Started（最初の Foundry Agent を作って実行する）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
```

## ねらい（このデモでできるようになること）
- Agent Framework（Python）で **エージェントを1つ作って実行**できる
- Azure AI Foundry Agents（`AzureAIAgentClient`）をバックエンドとして使い、`agent.run()` の結果を取得できる
- 「エージェント＝LLM + 指示（Instructions） + 実行API」という最小単位を体感する

補足:
- 以降の Demo 2/3/5 も同じバックエンド（Foundry Agents）で積み上げます
- Azure OpenAI 直結（`AzureOpenAIChatClient`）は別のバックエンドです（このリポジトリでは Demo 4/6 で扱っています）

---

## 前提条件（ここが揃っていれば、あとはコピペで動く）
### A. 実行環境
- **Dev Containers / GitHub Codespaces**（推奨）
  - Codespaces の場合：リポジトリを開いて **“Create codespace”** するだけでOK
  - ローカル Dev Containers の場合：VS Code で「Reopen in Container」

> Dev Container を使わない場合でも、Python 3.10+ と `pip` があれば実行できます。

### B. Azure AI Foundry Agents の準備（1回だけ）
この Demo 1 は **Azure AI Foundry Project** をバックエンドにします。

1. Azure AI Foundry で Hub / Project を用意（既存でOK）
2. Project の **Models + endpoints** でモデルをデプロイ（例：`gpt-4o-mini` など）
3. 実行ユーザー（`az login` するアカウント）に、Project / Hub 上で Agents を実行できる RBAC を付与

このデモで必要なのは主に次の2つです：
- **Project endpoint**（`AZURE_AI_PROJECT_ENDPOINT`）
- **Model deployment name**（`AZURE_AI_MODEL_DEPLOYMENT_NAME`）

### C. 必要な環境変数（どちらかで設定）
- 方法1：Codespaces の **Secrets**（推奨：鍵が漏れない）
- 方法2：Dev Container 内で `export` する
- 方法3：`.env`（※コミット禁止。`.env.example` を用意する）

最低限（必須）：
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

例：
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

ハマりどころ：
- `AZURE_AI_PROJECT_ENDPOINT` は **Foundry Project endpoint**（`https://...services.ai.azure.com/api/projects/...`）です。
  - Azure OpenAI や Azure AI Services の endpoint（`...cognitiveservices.azure.com`）とは別物です
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` は **Foundry プロジェクト側のデプロイ名**です（“モデル名”ではありません）

---

## 手順（Step-by-step）

### Step 1. 依存関係をインストール
Dev Container が前提なら、多くの場合すでに入っています。入っていなければ以下を実行：

```bash
pip install agent-framework-azure-ai --pre
```

### Step 2. Azure CLI でログイン（Entra ID 認証）
**Codespaces / コンテナ内で**実行してください。

```bash
az login
```

> Codespaces ではブラウザを開けない場合があるので、`--use-device-code` が便利です。
> `az login --use-device-code`

#### このデモで実際に使う認証方式（重要）
このデモは **Microsoft Entra ID（= Azure CLI credential）** を使います。
そのため、`az login` が必須です。

### Step 3. スクリプトを確認（`src/demo1_run_agent.py`）
このリポジトリには `src/demo1_run_agent.py` が同梱されています。
（手作業で作る必要はありません）

（補足）
- 公式ドキュメントでは `create_agent(...)` の例が出ることがありますが、
  このリポジトリは固定バージョン（`agent-framework==1.0.0b260123`）に合わせて `as_agent(...)` を使っています。

#### このリポジトリで入れている “ハマり対策”
- Dev Container / Codespaces の環境で、環境変数が **空文字**で注入されることがあります。
  その場合、dotenv の一般的な読み込みだと値が埋まらず失敗しがちです。
- その対策として、`src/demo1_run_agent.py` は **リポジトリルート `.env` を明示ロードし、未設定/空の env var だけ補完**します。

### Step 4. 実行
```bash
python3 -u src/demo1_run_agent.py
```

期待する動き：
- `venue_specialist` がイベント計画（会場/候補/要点など）を提案する
- エラーなく `result.text` が表示される

---

## 技術解説（このデモで起きていること）

### 1) 構成の全体像（Foundry / ローカルコード）
このデモは、ざっくり言うと次の 3 層です。

1. **Azure AI Foundry 側**
  - Project（Hub/Project）
  - Models + endpoints のモデルデプロイ
2. **環境変数（`.env` / Secrets / export）**
  - `AZURE_AI_PROJECT_ENDPOINT`
  - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
  - 認証情報（Entra ID: `az login`）
3. **アプリコード（`src/demo1_run_agent.py`）**
  - `AzureAIAgentClient` を作り、`as_agent()` で Agent 化して、`run()` を呼ぶ

### 2) `AzureAIAgentClient` は「Foundry Agents に接続するクライアント」
`AzureAIAgentClient` は Azure AI Foundry Project 上の Agents 実行に接続するためのクライアントです。
このデモでは環境変数で Project / Model を指定して、実行時に `agent.run()` を呼びます。

### 3) 観測（OpenTelemetry / OTel）
このデモのスクリプトは、環境に OpenTelemetry が入っている場合、
Agent 実行や Tool 呼び出しを **短い1行ログ**で表示します（デモ中の観測用）。

### 4) `run()` は「1ターン実行」
`run()` は 1 回の入力（ユーザー発話）に対して 1 回の推論を行い、結果を `ChatResponse` として返します。
`result.text` は「テキストとして読める最終結果」です。

#### 参考：ストリーミング版（`run_stream()`）
Learn のチュートリアルにもある通り、ストリーミングしたい場合は `run_stream()` が使えます：

```python
async def main():
  async for update in agent.run_stream("Tell me a joke about a pirate."):
    if update.text:
      print(update.text, end="", flush=True)
  print()
```

---

## トラブルシューティング

### よくある1：認証エラー（401/403）
- `az login` がコンテナ内でできているか
- 対象 Azure OpenAI リソースにロール付与できているか
- サブスクリプションが違う場合は `az account set` で合わせる

### よくある2：`AZURE_AI_PROJECT_ENDPOINT` が違う / 404
`AZURE_AI_PROJECT_ENDPOINT` は **Foundry Project endpoint** です。

- ✅ 例: `https://<account>.services.ai.azure.com/api/projects/<project-id>`
- ❌ 例: `https://<resource>.cognitiveservices.azure.com/`（Azure OpenAI / Azure AI Services の endpoint）

### よくある3：`Failed to resolve model info`（デプロイ名が違う）
`AZURE_AI_MODEL_DEPLOYMENT_NAME` が Foundry プロジェクトで解決できていません。

チェック:
- Foundry portal → 対象プロジェクト → **Models + endpoints** にデプロイ名が存在するか

### よくある4：DNS 解決に失敗して開始前に止まる
`AZURE_AI_PROJECT_ENDPOINT` のホストが、この実行環境から DNS 解決できない状態です。

- 対応: Private networking / private DNS 構成を見直す、または DNS 解決できるネットワークから実行する

---

## 次のデモへ
Demo 2 では、エージェントに **ツール（Hosted Web Search）** を追加します。
→ `demo2.md` を開いて続けてください。
