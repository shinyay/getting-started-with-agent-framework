# Demo 1 — Getting Started（最初のエージェントを作って実行する）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.azure.azureopenaichatclient?view=agent-framework-python-latest
```

## ねらい（このデモでできるようになること）
- Agent Framework（Python）で **エージェントを1つ作って実行**できる
- Azure OpenAI をバックエンドとして使い、`agent.run()` の結果を取得できる
- 「エージェント＝LLM + 指示（Instructions） + 実行API」という最小単位を体感する

---

## 前提条件（ここが揃っていれば、あとはコピペで動く）
### A. 実行環境
- **Dev Containers / GitHub Codespaces**（推奨）
  - Codespaces の場合：リポジトリを開いて **“Create codespace”** するだけでOK
  - ローカル Dev Containers の場合：VS Code で「Reopen in Container」

> Dev Container を使わない場合でも、Python 3.10+ と `pip` があれば実行できます。

### B. Azure OpenAI の準備（1回だけ）
1. Azure OpenAI リソースを作成
2. Chat completions 用の **モデルデプロイ**を作成（例：`gpt-4o-mini` など）
3. 実行ユーザーにロール付与  
   - `Cognitive Services OpenAI User` または `Cognitive Services OpenAI Contributor`

### C. 必要な環境変数（どちらかで設定）
- 方法1：Codespaces の **Secrets**（推奨：鍵が漏れない）
- 方法2：Dev Container 内で `export` する
- 方法3：`.env`（※コミット禁止。`.env.example` を用意する）

最低限：
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`

任意（APIキー認証する場合）：
- `AZURE_OPENAI_API_KEY`

例：
```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="<your-deployment-name>"
# export AZURE_OPENAI_API_KEY="<your-api-key>"   # 必要な場合のみ
```

---

## 手順（Step-by-step）

### Step 1. 依存関係をインストール
Dev Container が前提なら、多くの場合すでに入っています。入っていなければ以下を実行：

```bash
pip install agent-framework --pre
```

### Step 2. Azure CLI でログイン（AzureCliCredential を使う場合）
**Codespaces / コンテナ内で**実行してください。

```bash
az login
```

> Codespaces ではブラウザを開けない場合があるので、`--use-device-code` が便利です。  
> `az login --use-device-code`

### Step 3. 最小コードを作成（`src/demo1_run_agent.py`）
作業ディレクトリ直下で：

```bash
mkdir -p src
```

次の内容で `src/demo1_run_agent.py` を作成します。

```python
import asyncio
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

agent = AzureOpenAIChatClient(credential=AzureCliCredential()).as_agent(
    instructions="You are good at telling jokes.",
    name="Joker",
)

async def main():
    result = await agent.run("Tell me a joke about a pirate.")
    print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4. 実行
```bash
python src/demo1_run_agent.py
```

期待する動き：
- “Joker” エージェントがジョークを返す
- エラーなく `result.text` が表示される

---

## 技術解説（このデモで起きていること）

### 1) `AzureOpenAIChatClient` は「推論バックエンドへの接続」
- Azure OpenAI への接続情報（endpoint / deployment）を **環境変数や .env** から読み取れる
- 認証は
  - `AzureCliCredential()`（Azure CLI でログインしたアカウント）
  - もしくは `AZURE_OPENAI_API_KEY`（APIキー）
  のどちらかで成立します

### 2) `as_agent(...)` は「クライアントをエージェント化」する糖衣構文
- “クライアント” に “指示（instructions）” と “名前（name）” を付けて
- `run()` / `run_stream()` を持つ **Agent** として使えるようにする

### 3) `run()` は「1ターン実行」
- 1つの入力に対して1つの結果を返す
- ストリーミングしたい場合は `run_stream()` を使う（以降のデモで登場）

---

## トラブルシューティング

### よくある1：認証エラー（401/403）
- `az login` がコンテナ内でできているか
- 対象 Azure OpenAI リソースにロール付与できているか
- サブスクリプションが違う場合は `az account set` で合わせる

### よくある2：デプロイメント名が違う
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` が **デプロイ名**と一致しているか再確認
- “モデル名” と “デプロイ名” は別物です

### よくある3：endpoint が違う
- `https://<resource>.openai.azure.com` の形式になっているか
- 末尾スラッシュがあっても多くの場合動きますが、統一すると安心です

---

## 次のデモへ
Demo 2 では、エージェントに **ツール（Web Search）** を追加します。  
→ `demo2.md` を開いて続けてください。
