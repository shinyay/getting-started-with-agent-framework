# Demo 3 — Hosted MCP Tool（Microsoft Learn MCP をツールとして追加）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python#using-built-in-and-hosted-tools
```

## ねらい
- `HostedMCPTool` を追加して **Microsoft Learn MCP** に接続する
- “MCP（Model Context Protocol）で標準化された外部ツール” を使う感覚を掴む
- 可能なら、**複数ツールを連続呼び出し（sequential tool calls）**する挙動を観察する

---

## 前提
- Demo 2 まで完了している（Azure AI Foundry Agents の env vars 設定済み）
- `agent-framework-azure-ai` がインストール済み
- `az login` 済み

---

## 手順

### Step 1. MCP ツールを追加したエージェントを作る（`src/demo3_hosted_mcp.py`）

`src/demo3_hosted_mcp.py` を次で作成：

```python
import asyncio
from agent_framework import HostedMCPTool, HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

MSLEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"

async def main():
    async with AzureCliCredential() as cred:
        chat_client = AzureAIAgentClient(credential=cred)

        agent = chat_client.create_agent(
            name="DocAssistant",
            instructions=(
                "You are a documentation assistant. "
                "Prefer official docs, and cite the source section titles you used."
            ),
            tools=[
                # Demo2 の Web Search も併用（連続呼び出し観察用）
                HostedWebSearchTool(
                    additional_properties={"user_location": {"city": "Tokyo", "country": "JP"}}
                ),
                HostedMCPTool(
                    name="Microsoft Learn MCP",
                    url=MSLEARN_MCP_URL,
                ),
            ],
        )

        prompt = (
            "I want to create an Azure Storage account.
"
            "1) Use Microsoft Learn MCP to find the official steps.
"
            "2) Then use Web Search to confirm any recent UI changes.
"
            "3) Output: numbered steps + a short Azure CLI example.
"
        )

        result = await agent.run(prompt)
        print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2. 実行
```bash
python src/demo3_hosted_mcp.py
```

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

### 3) sequential tool calls（連続ツール呼び出し）
- ひとつの質問に対し
  - 「まずドキュメントを調べる」→「次に別の確認をする」
  というように、複数のツールを連続で呼ぶ可能性があります
- ただし **実際に連続呼び出しが起きるかはプロンプトとモデル判断次第**です  
  → 上の `prompt` のように「手順を分けて明示する」と起きやすくなります

---

## うまくいかない時のチェック

### MCP の URL が誤っている
- `https://learn.microsoft.com/api/mcp` が指定されているか

### “ツールが使えない” エラー
- Demo2 と同様、バックエンド側で Hosted Tools が利用可能か確認（権限/リージョン/機能）

---

## 次のデモへ
Demo 4 では、`response_format` を使って **構造化出力**を取り出します。  
→ `demo4.md` を開いて続けてください。
