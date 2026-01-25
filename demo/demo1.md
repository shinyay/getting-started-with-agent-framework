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

#### 補足：Microsoft Foundry 側の構成（どこで何を作る？）
このデモで必要なのは「Azure OpenAI リソース」と「モデルのデプロイ（= Deployment）」です。

- **Azure portal**
  - Azure OpenAI リソース（課金・ネットワーク・IAM の“器”）を作成
  - `Keys and Endpoint`（or `Keys & Endpoint`）で **Endpoint** を確認
- **Microsoft Foundry (ai.azure.com)**
  - 上で作った Azure OpenAI リソースを選んで
  - **Deployments（または Models + endpoints）** から **モデルをデプロイ**
  - ここで入力した **Deployment name** が、コードで使う `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` になります

> Foundry のドキュメントは「Foundry (classic) / Foundry (new)」で UI が少し違います。
> Learn の作成手順は Foundry (classic) 前提のことが多いので、画面に *New Foundry toggle* が出る場合は注意してください。

### C. 必要な環境変数（どちらかで設定）
- 方法1：Codespaces の **Secrets**（推奨：鍵が漏れない）
- 方法2：Dev Container 内で `export` する
- 方法3：`.env`（※コミット禁止。`.env.example` を用意する）

最低限：
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`

任意（APIキー認証する場合）：
- `AZURE_OPENAI_API_KEY`

#### Endpoint / Deployment 名の注意点（ハマりどころ）
- **Deployment 名 ≠ モデル名**
  - Azure OpenAI は API 呼び出し時に常に **deployment 名**が必要です（Foundry/Portal で付けた名前）。
- Endpoint はポータルに表示されるものをそのまま使う
  - Learn の例では `https://<resource>.openai.azure.com` がよく出ます。
  - 環境によっては `https://<resource>.cognitiveservices.azure.com/` の形式で表示されることもあります。
  - いずれにせよ「HTTPS の URL」で、あなたのリソースを指していれば OK です（このリポジトリでもその形で動作確認しました）。

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

#### このデモで実際に使った認証方式（重要）
Azure OpenAI リソースによっては **Key based authentication が無効**になっており、API キーで呼ぶと 403 になります：

- `AuthenticationTypeDisabled: Key based authentication is disabled for this resource.`

その場合は **Microsoft Entra ID（= Azure CLI ログイン）**で呼び出す必要があります。
このリポジトリの `src/demo1_run_agent.py` は、デフォルトで Entra ID 認証を優先するようにしてあります。

### Step 3. コードを作成（`src/demo1_run_agent.py`）
作業ディレクトリ直下で：

```bash
mkdir -p src
```

次の内容で `src/demo1_run_agent.py` を作成します。

```python
import asyncio
import os
from pathlib import Path

from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv


# Load env vars from the repository root `.env` (method 3).
# NOTE: In Dev Containers, vars may be injected as empty strings via `containerEnv`.
#       We set override=True so `.env` can populate real values.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)


def _make_agent():
  """Create an Agent using either API key auth or Azure CLI auth.

  Default: Entra ID (Azure CLI) auth.
  - Set AZURE_OPENAI_AUTH=api_key to force API key auth.
  """

  auth_mode = (os.getenv("AZURE_OPENAI_AUTH") or "").strip().lower()
  api_key = os.getenv("AZURE_OPENAI_API_KEY")

  if auth_mode == "api_key":
    if not api_key:
      raise RuntimeError(
        "AZURE_OPENAI_AUTH=api_key is set but AZURE_OPENAI_API_KEY is empty."
      )
    from azure.core.credentials import AzureKeyCredential

    credential = AzureKeyCredential(api_key)
    client = AzureOpenAIChatClient(credential=credential, api_key=api_key)
  else:
    from azure.identity import AzureCliCredential

    credential = AzureCliCredential()
    # Force Entra ID mode (ignore any key picked from env/.env)
    client = AzureOpenAIChatClient(credential=credential, api_key="")

  return client.as_agent(
    instructions="You are good at telling jokes.",
    name="Joker",
  )


agent = _make_agent()


async def main():
  result = await agent.run("Tell me a joke about a pirate.")
  print(result.text)


if __name__ == "__main__":
  asyncio.run(main())
```

#### なぜ「最小コード」より少し長いの？（このリポジトリでの実運用ハマり対策）
上のコードは Learn の最小例（`AzureOpenAIChatClient(credential=AzureCliCredential()).as_agent(...)`）をベースにしつつ、
このリポジトリの Dev Container / `.env` 運用で現実に発生したハマりどころを吸収しています：

1) **`.env` が読まれない / endpoint が空になる問題**
- Dev Container 設定によって、環境変数が **未設定ではなく空文字**で注入されることがあります。
- `python-dotenv` はデフォルトだと既存の環境変数を上書きしないため、`.env` の値が反映されず
  `AZURE_OPENAI_ENDPOINT` が空のまま → 設定バリデーションで落ちます。
- その対策として `load_dotenv(..., override=True)` を使っています。

2) **Key-based auth 無効リソースで 403 になる問題**
- `.env` に `AZURE_OPENAI_API_KEY` が入っていると、クライアントが key を拾って key 認証を試みるケースがあります。
- リソース側で key 認証が無効だと `AuthenticationTypeDisabled` で 403。
- その対策として、Entra ID を使う分岐では `api_key=""` を明示して **key 認証を抑止**しています。

### Step 4. 実行
```bash
python src/demo1_run_agent.py
```

期待する動き：
- “Joker” エージェントがジョークを返す
- エラーなく `result.text` が表示される

---

## 技術解説（このデモで起きていること）

### 1) 構成の全体像（Foundry / Azure OpenAI / ローカルコード）
このデモは、ざっくり言うと次の 3 層です。

1. **Microsoft Foundry / Azure portal 側**
  - Azure OpenAI リソース（エンドポイント、IAM、ネットワーク）
  - モデルデプロイ（Deployment name）
2. **環境変数（`.env` / Secrets / export）**
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
  - 認証情報（Entra ID なら `az login`、API キーなら `AZURE_OPENAI_API_KEY`）
3. **アプリコード（`src/demo1_run_agent.py`）**
  - `AzureOpenAIChatClient` を作り、`as_agent()` で Agent 化して、`run()` を呼ぶ

### 2) `AzureOpenAIChatClient` は「推論バックエンドへの接続」
`AzureOpenAIChatClient` は Azure OpenAI の Chat Completions に対してリクエストを投げるためのクライアントです。
Learn / API リファレンスでも、次の値を環境変数または `.env` から受け取れることが明記されています：

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
- （任意）`AZURE_OPENAI_API_KEY`

そして認証は大きく 2 つです：

- **Microsoft Entra ID（推奨 / 組織設定で必須になりがち）**
  - `AzureCliCredential()`（= コンテナ内で `az login` したユーザー）
  - リソースに `Cognitive Services OpenAI User` などの RBAC が必要
- **API キー（リソース側で許可されている場合のみ）**
  - `AZURE_OPENAI_API_KEY`
  - リソースで key-based authentication が無効だと 403

### 3) `as_agent(...)` は「クライアントをエージェント化」
`as_agent(instructions=..., name=...)` で、
「LLM に接続するクライアント」に対して「人格（instructions）」と「識別子（name）」を付け、
`run()` / `run_stream()` を持つ Agent として扱えるようにしています。

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

#### 403: AuthenticationTypeDisabled（APIキーが無効）
症状：

- `AuthenticationTypeDisabled: Key based authentication is disabled for this resource.`

意味：

- その Azure OpenAI リソースは **API キー認証を受け付けません**（Entra ID が必要）。

対処：

- `az login` を行い、Entra ID で呼び出す
- RBAC（`Cognitive Services OpenAI User` など）を確認

### よくある2：デプロイメント名が違う
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` が **デプロイ名**と一致しているか再確認
- “モデル名” と “デプロイ名” は別物です

### よくある3：endpoint が違う
-- ポータル（Azure portal）に表示される Endpoint をコピーして使う
-- 末尾スラッシュがあっても多くの場合動きますが、統一すると安心です

#### 起動直後に設定バリデーションで落ちる（endpoint が空）
症状：

- `endpoint: Input should be a valid URL, input is empty`

主因：

- `.env` の値が読めていない、または Dev Container が空文字の環境変数を注入して上書きしている

対処：

- `.env` がリポジトリルート（`/workspaces/.env`）にあるか確認
- `python-dotenv` で `override=True` を使って `.env` を優先する（このリポジトリの実装は対応済み）

---

## 次のデモへ
Demo 2 では、エージェントに **ツール（Web Search）** を追加します。
→ `demo2.md` を開いて続けてください。
