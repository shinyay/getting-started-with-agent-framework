# Demo 4 — Structured Output（response_format で型付き出力を得る）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
```

## ねらい
- Pydantic モデルを定義し、`response_format=<Model>` を指定して実行する
- 出力を `response.value`（= Pydanticインスタンス）として安全に扱えるようにする
- 「テキスト生成」から「構造化データ抽出」へ一歩進む

---

## 前提
- Demo 1（Azure OpenAI エンドポイント＆デプロイ設定）が完了している
- 次の env var が設定済み：
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
  - （必要なら）`AZURE_OPENAI_API_KEY`
- `pydantic` がインストール済み（Dev Container 前提ならOK）

---

## 手順

### Step 1. 構造（スキーマ）を Pydantic で定義する
`src/demo4_structured_output.py` を作成します。

```bash
mkdir -p src
```

```python
import asyncio
from pydantic import BaseModel
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from agent_framework import AgentResponse

class PersonInfo(BaseModel):
    """Information about a person."""
    name: str | None = None
    age: int | None = None
    occupation: str | None = None

agent = AzureOpenAIChatClient(credential=AzureCliCredential()).as_agent(
    name="HelpfulAssistant",
    instructions="You are a helpful assistant that extracts person information from text.",
)

async def main():
    query = "Please provide information about John Smith, who is a 35-year-old software engineer."

    # 1) 非ストリーミング（最初はこれが分かりやすい）
    response = await agent.run(query, response_format=PersonInfo)

    if response.value:
        person = response.value
        print(f"Name: {person.name}, Age: {person.age}, Occupation: {person.occupation}")
    else:
        print("No structured data found in response")

    # 2) ストリーミングで構造化出力を取る場合（上級）
    # streaming_updates = agent.run_stream(query, response_format=PersonInfo)
    # final_response = await AgentResponse.from_agent_response_generator(
    #     streaming_updates,
    #     output_format_type=PersonInfo,
    # )
    # if final_response.value:
    #     person = final_response.value
    #     print(f"[stream] Name: {person.name}, Age: {person.age}, Occupation: {person.occupation}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2. 実行
```bash
python src/demo4_structured_output.py
```

---

## 技術解説（ここが本質）

### 1) `response_format` は “出力の形” を契約にする
- ただの JSON 文字列ではなく
- **指定したスキーマ（Pydanticモデル）に合う形で出力**するようモデルに要求します

### 2) `response.value` が “型安全な結果”
- 成功すれば、`response.value` に **Pydanticインスタンス**が入る
- 失敗時は `None` になり得るので、必ず if でチェックする

### 3) ストリーミング時の注意
- ストリーミングは “断片” が届くので、最後にまとめて解釈する必要があります
- `AgentResponse.from_agent_response_generator(...)` は、そのためのヘルパーです

---

## よくある落とし穴

### 構造化出力が効かない
- すべてのエージェント種類/バックエンドが対応しているとは限りません
- まずは Demo 4 のコードを **そのまま**動かし、動いた後に拡張しましょう

---

## 次のデモへ
Demo 5 では、処理を2つのエージェントに分解して **Workflow + Edge** で順序保証のあるパイプラインを作ります。  
→ `demo5.md` を開いて続けてください。
