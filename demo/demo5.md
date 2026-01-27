# Demo 5 — Workflow with edges（2つのエージェントをつないで順序保証）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/agents-in-workflows?pivots=programming-language-python
```

## ねらい
- 1つのプロンプトに全部詰め込むのではなく、**役割別にエージェントを分割**する
- `WorkflowBuilder` と `edge` で **順序保証のあるパイプライン**を組む
- `run_stream()` のイベントを見て「今どのエージェントが仕事しているか」を体感する

---

## 前提（このデモは Azure AI Foundry Agents を推奨）
このデモは、公式サンプルの流れに合わせて **Azure AI Foundry Agents（AzureAIAgentClient）** を使います。

必要な env var：
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

必要パッケージ：
```bash
pip install agent-framework-azure-ai --pre
```

ログイン：
```bash
az login --use-device-code
```

補足（このリポジトリの実装）:
- `src/demo5_workflow_edges.py` を同梱しています（公式サンプルをベースに、デモを動かしやすいよう最小限のガードを追加）
    - リポジトリルート `.env` を明示的に読み込み、**未設定/空の環境変数だけ補完**します（Dev Container / Codespaces の空文字注入対策）
    - `AZURE_AI_PROJECT_ENDPOINT` の DNS 解決を事前チェックして、開始直後に落ちるケースを分かりやすくしています
    - 公式ドキュメントのイベント名と、リポジトリで固定している `agent-framework==1.0.0b260123` のイベント名に差分があるため、
        同梱スクリプト側ではこのバージョンで動くイベントを使っています（挙動は同じく「Writer / Reviewer の出力をストリームで観察」できます）

---

## 手順（公式サンプルの Writer → Reviewer）

### Step 1. スクリプト作成（`src/demo5_workflow_edges.py`）
```bash
mkdir -p src
```

`src/demo5_workflow_edges.py` を次で作成：

```python
import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Any

from agent_framework import AgentResponseUpdateEvent, WorkflowBuilder, WorkflowOutputEvent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

async def create_azure_ai_agent() -> tuple[Callable[..., Awaitable[Any]], Callable[[], Awaitable[None]]]:
    """Azure AI agent を作る factory と、後片付け close() を返す。"""
    stack = AsyncExitStack()
    cred = await stack.enter_async_context(AzureCliCredential())
    client = await stack.enter_async_context(AzureAIAgentClient(credential=cred))

    async def agent(**kwargs: Any) -> Any:
        # client.as_agent(...) は async context として管理されるので enter_async_context する
        return await stack.enter_async_context(client.as_agent(**kwargs))

    async def close() -> None:
        await stack.aclose()

    return agent, close

async def main() -> None:
    agent, close = await create_azure_ai_agent()
    try:
        writer = await agent(
            name="Writer",
            instructions="You are an excellent content writer. You create new content and edit contents based on the feedback.",
        )
        reviewer = await agent(
            name="Reviewer",
            instructions=(
                "You are an excellent content reviewer. "
                "Provide actionable feedback to the writer about the provided content. "
                "Provide the feedback in the most concise manner possible."
            ),
        )

        # Writer -> Reviewer の順で実行される workflow
        workflow = WorkflowBuilder().set_start_executor(writer).add_edge(writer, reviewer).build()

        last_executor_id: str | None = None
        events = workflow.run_stream("Create a slogan for a new electric SUV that is affordable and fun to drive.")

        async for event in events:
            if isinstance(event, AgentResponseUpdateEvent):
                eid = event.executor_id
                if eid != last_executor_id:
                    if last_executor_id is not None:
                        print()
                    print(f"{eid}:", end=" ", flush=True)
                    last_executor_id = eid
                print(event.data, end="", flush=True)

            elif isinstance(event, WorkflowOutputEvent):
                print("\n===== Final output =====")
                print(event.data)

    finally:
        await close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2. 実行
```bash
python3 -u src/demo5_workflow_edges.py
```

期待される挙動:
- 出力中に `Writer:` → `Reviewer:` と切り替わり、**エージェントが順番に動いている**のが分かります
- 最後に reviewer 側の結果（スローガン or フィードバック）が表示されます（環境により文面は変わります）

---

## 技術解説（ワークフロー設計の基本）

### 1) なぜ “分割” が効くのか
- 1つの巨大プロンプトに全工程を書いても、順番通りに進む保証が弱い
- 役割ごとにエージェントを分け、**Edge（接続）で順序を固定**することで
  - “Writer が生成 → Reviewer が評価/改善点提示”
  が安定して再現できる

### 2) `run_stream()` とイベント
- `AgentResponseUpdateEvent`：トークンが流れてくる（途中経過）
- `WorkflowOutputEvent`：最終出力
- `executor_id` を見ると、いまどのエージェントの出力か分かる

補足:
- 公式ドキュメントでは `AgentResponseUpdateEvent` が使われていますが、バージョン差でクラス名が異なる場合があります。
    その場合は、同梱の `src/demo5_workflow_edges.py` をそのまま使うのが確実です。

### 3) `AsyncExitStack` の意味
- Azure CLI credential / AzureAIAgentClient / 作成したエージェント（as_agent）を
  **まとめて確実に後片付け**するためのパターン
- これをやらないと、リソースが残ったり、接続が閉じられない可能性がある

---

## 次のデモへ（DevUI）
Demo 6 では、この “workflow” を **DevUI で可視化**します。  
→ `demo6.md` を開いて続けてください。
