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
    - （任意）`AZURE_OPENAI_API_VERSION`（指定が必要な環境のみ）
  - （必要なら）`AZURE_OPENAI_API_KEY`
- `pydantic` がインストール済み（Dev Container 前提ならOK）

補足:
- 多くの Azure OpenAI リソースでは **API key が無効**（key-based auth disabled）な場合があります。
    このリポジトリでは既定で **Entra ID（Azure CLI credential）** を使う実装にしています。
    - 既定: `az login` が必要
        - API key を強制したい場合: `AZURE_OPENAI_AUTH=api_key` を設定

（推奨）
- まずは Demo 4 実行前に、以下を満たしているか確認してください
    - `az login` 済み（Entra ID 既定で動かす場合）
    - `.env`（リポジトリルート）に必要な値が入っている

---

## 手順

### Step 1. 構造（スキーマ）を Pydantic で定義する
このリポジトリには `src/demo4_structured_output.py` が同梱されています。
（必要なら自分で編集して拡張できます）

以下は **概念が分かりやすい最小例** です。実運用向けの堅牢化（`.env` 明示ロード、空文字注入対策、DNSチェック、フォールバック等）は、同梱の `src/demo4_structured_output.py` を参照してください。

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

実装上のポイント（同梱スクリプト側）:
- リポジトリルート `.env` を明示的に読み込み、**未設定/空の環境変数だけ補完**します
    - Dev Container / Codespaces で env が空文字注入される問題への対策
- `response.value` が `None` の場合でも、`response.text` が JSON なら Pydantic で復元するフォールバックを入れています
    - バックエンド/バージョン差で「非ストリーミング時だけ value に入らない」ケースがあるため

（補足）
- 同梱スクリプトは **非ストリーミング/ストリーミングの両方**を実行し、どちらでも `PersonInfo` を取り出せることを確認できるようにしています。

### Step 2. 実行
```bash
python3 -u src/demo4_structured_output.py
```

### Step 3. 期待される出力例
環境により出力の細部は変わりますが、概ね以下のようになります。

- 非ストリーミングは `response.value` が入らない場合があり、その場合は同梱スクリプトが `response.text`（JSON）から復元して表示します
- ストリーミングは最終的に `final_response.value`（Pydantic）として取れるのが “王道” です

例:

```text
[non-stream] name=John Smith, age=35, occupation=Software engineer
[stream]     name=John Smith, age=35, occupation=Software engineer
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

### 非ストリーミングで `response.value` が `None` になる
発生条件は環境差（バックエンド/バージョン差）に依存しますが、以下のパターンがあり得ます。

- `response.text` には JSON が返っているのに、`response.value`（Pydantic）に詰め替えられない

対応:
- **同梱の `src/demo4_structured_output.py` はフォールバック実装済み**です（`response.text` が JSON なら `PersonInfo.model_validate_json(...)` で復元）
- 自作コードの場合も、`response.value is None` のときに `response.text` をログし、JSONならパースするのが安全です

### 構造化出力が効かない
- すべてのエージェント種類/バックエンドが対応しているとは限りません
- まずは Demo 4 のコードを **そのまま**動かし、動いた後に拡張しましょう

### DNS 解決に失敗して開始前に止まる
実行環境から `AZURE_OPENAI_ENDPOINT` のホストが DNS 解決できないと、開始時点で停止します。

- エラー例: `Cannot resolve AZURE_OPENAI_ENDPOINT host via DNS`
- 対応: Private networking / DNS の構成を見直す、または DNS 解決できるネットワークから実行する

補足:
- 「ホスト環境では引けるのに、Dev Container の中だけ引けない」ことがあります。その場合はコンテナ側の DNS 設定（Corporate DNS / Private Link / Dev Container の network 設定）を疑ってください。
- `/etc/hosts` に固定する回避策もありますが、IP 変更で壊れるので恒久策にはなりません（手元検証の“最後の手段”としてのみ推奨）。

---

## 次のデモへ
Demo 5 では、処理を2つのエージェントに分解して **Workflow + Edge** で順序保証のあるパイプラインを作ります。
→ `demo5.md` を開いて続けてください。
