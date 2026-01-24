# Demo 2 — Web Search Tool（ツール追加でWeb検索できるようにする）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python#using-built-in-and-hosted-tools
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.hostedwebsearchtool?view=agent-framework-python-latest
```

## ねらい
- エージェントに `tools` を追加し、**Web検索を使った回答**ができるようにする
- “ツール呼び出し” の基本（モデルが必要に応じてツールを選択する）を体感する

---

## 前提
### 1) Demo 1 を完了している
- Dev Container / Codespaces が起動している
- `agent-framework` がインストール済み（未導入なら `pip install agent-framework --pre`）

### 2) Azure AI Foundry Agents の準備（Demo2〜の推奨バックエンド）
Hosted Tools（Web Searchなど）は、サービス側がネイティブでサポートしている必要があります。  
このデモセットでは **Azure AI Foundry Agents** を推奨します。

必要な環境変数：
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

> `AZURE_AI_PROJECT_ENDPOINT` は AI Foundry のプロジェクト詳細から取得します。

### 3) 追加パッケージ（未導入なら）
```bash
pip install agent-framework-azure-ai --pre
```

### 4) Azure CLI ログイン
```bash
az login --use-device-code
```

---

## 手順

### Step 1. Web Search を使うエージェントを作る（`src/demo2_web_search.py`）
```bash
mkdir -p src
```

`src/demo2_web_search.py` を次で作成：

```python
import asyncio
from agent_framework import HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

async def main():
    # Azure AI Foundry Agents を chat client として利用
    async with AzureCliCredential() as cred:
        chat_client = AzureAIAgentClient(credential=cred)

        agent = chat_client.create_agent(
            name="WebSearchAssistant",
            instructions="You are a helpful assistant with web search capabilities.",
            tools=[
                HostedWebSearchTool(
                    additional_properties={
                        "user_location": {"city": "Tokyo", "country": "JP"}
                    }
                )
            ],
        )

        result = await agent.run("What are the latest news about AI?")
        print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2. 実行
```bash
python src/demo2_web_search.py
```

---

## 技術解説（ここがポイント）

### 1) ツールは「モデルの行動範囲を広げる拡張点」
- 通常のエージェントは “テキスト生成” が中心
- ツールを与えると
  - **必要に応じてツールを呼び出す → 結果を材料に回答する**
  という “行動” が可能になります

### 2) HostedWebSearchTool は「サービス側でWeb検索を実行」
- ツール呼び出しの実体は、（サービスが対応していれば）サービス側で実行されます
- `additional_properties.user_location` は検索の地域文脈（天気やローカルニュース）に効きやすい

### 3) 重要：ツールの対応可否は “バックエンド次第”
公式ドキュメントでも、**ツールのサポートはサービスプロバイダーにより異なる**と明記されています。  
もし動かない場合は以下を確認：
- Azure AI Foundry 側で Web Search が許可/利用可能な状態か
- プロジェクト設定やリージョン制約、利用可能なモデル/機能

---

## うまくいかない時のチェック

### `AZURE_AI_PROJECT_ENDPOINT` が未設定
```bash
echo $AZURE_AI_PROJECT_ENDPOINT
```
空なら設定漏れです。

### 権限不足
- Foundry プロジェクト/リソースにアクセス権があるか
- `az account show` が意図したテナント/サブスクか

---

## 次のデモへ
Demo 3 では **Hosted MCP Tool** を追加し、Microsoft Learn MCP を使ってドキュメント参照を強化します。  
→ `demo3.md` を開いて続けてください。
