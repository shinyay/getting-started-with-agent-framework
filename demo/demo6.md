# Demo 6 — DevUI（ワークフローを可視化・デバッグする）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference
```

## ねらい
- DevUI を起動し、**ワークフローの実行をUIで観察**する
- “どのステップがいつ動いたか / 入出力が何か” を目で追えるようにする
- 必要なら OpenAI互換API（`/v1/*`）でプログラムから叩けることを理解する

> DevUI は開発用のサンプルアプリであり、本番用途ではありません。

---

## 前提
- Demo 5 まで完了している
- `agent-framework-devui` がインストール済み（未導入なら以下）
```bash
pip install agent-framework-devui --pre
pip install openai
```

---

## 進め方（2パターン）
DevUI は **(A) ディレクトリ検出（CLI）** と **(B) プログラム登録（serve）** の2つがあります。  
このハンズオンでは **A（CLI）** を推奨します（再現性が高い）。

---

# A) ディレクトリ検出（CLI）で workflow を表示する（推奨）

## Step A-1. entities ディレクトリを作る
```bash
mkdir -p entities/ai_genius_workflow
```

## Step A-2. workflow を “export” する `__init__.py` を作る
DevUI は、各エンティティ配下の `__init__.py` が **`agent` または `workflow` 変数を export**している必要があります。

`entities/ai_genius_workflow/__init__.py` を作成：

```python
# entities/ai_genius_workflow/__init__.py
from .workflow import workflow
```

## Step A-3. workflow 実装ファイルを作る（`workflow.py`）
ここでは Demo5 の概念（Writer → Reviewer）を DevUI で扱いやすい形にします。

> 注意：Demo5 のコードは “スクリプト” 形式でした。DevUI 用には “import された時点で workflow 変数が存在する” 必要があります。

`entities/ai_genius_workflow/workflow.py` を作成：

```python
# entities/ai_genius_workflow/workflow.py
from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

# Azure OpenAI の env var（Demo1）を使う
writer = AzureOpenAIChatClient(credential=AzureCliCredential()).as_agent(
    name="Writer",
    instructions="You are an excellent content writer. Generate a short draft based on the request.",
)

reviewer = AzureOpenAIChatClient(credential=AzureCliCredential()).as_agent(
    name="Reviewer",
    instructions="You are an excellent reviewer. Give concise, actionable feedback.",
)

workflow = WorkflowBuilder().set_start_executor(writer).add_edge(writer, reviewer).build()
```

> ここでは DevUI での動作安定を優先して、バックエンドを Azure OpenAI（Demo1）に寄せています。  
> Demo5 の Azure AI Foundry Agents 版を可視化したい場合は、まず CLI で DevUI が workflow を検出できる形に落とすのがコツです。

## Step A-4. DevUI を起動
```bash
devui ./entities --host 0.0.0.0 --port 8080
```

- UI: `http://localhost:8080`
- API: `http://localhost:8080/v1/*`（OpenAI互換）

Codespaces の場合：
- ポート `8080` を “Forward / Open in Browser” します

---

## Step A-5. UI で workflow を実行
1. サイドバーで `ai_genius_workflow` を選ぶ
2. “Configure & Run” を押す
3. 入力に以下を貼る：
   - `Create a slogan for a new electric SUV that is affordable and fun to drive.`
4. 実行中、Writer → Reviewer の順にハイライト/ログが更新されるはずです

---

# B) OpenAI 互換APIで DevUI を叩く（オプション）

DevUI は `http://localhost:8080/v1` を基準URLに、OpenAI互換の Responses API を提供します。

例（Python）：
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")

resp = client.responses.create(
    metadata={"entity_id": "ai_genius_workflow"},
    input="Create a slogan for a new electric SUV that is affordable and fun to drive."
)

print(resp.output[0].content[0].text)
```

---

## トラブルシューティング

### entity が検出されない
- `entities/<name>/__init__.py` が存在するか
- `__init__.py` が `workflow` 変数を export しているか
- 文法エラーがないか
- `devui` に渡したパス直下にディレクトリがあるか

### 環境変数が読み込まれていない
- `.env` の場所が正しいか（entities直下 or 各entity直下）
- `--reload` を付けて再読み込みできる

---

## 次にやること（発展）
- `--tracing` を付けて OpenTelemetry トレースを有効化し、ツール呼び出し/実行フローをさらに追う
- Demo2/3 のツール（Web Search / MCP）を workflow 内エージェントへ組み込み、より “現実の業務” に近づける
