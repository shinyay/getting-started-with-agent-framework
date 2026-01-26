# Demo 2 — Web Search Tool（ツール追加でWeb検索できるようにする）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python#using-built-in-and-hosted-tools
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.hostedwebsearchtool?view=agent-framework-python-latest
```

## ねらい

- **Hosted Web Search（サービス側の検索機能）** をツールとして追加し、エージェントが必要に応じてWeb検索→根拠を材料に回答できるようにする
- Demo 1（モデルに質問して回答）に対し、Demo 2 では **「検索する」能力を追加**する
- 併せて、実運用でハマりやすいポイント（Foundry の Project endpoint / モデルデプロイ名 / Bing 接続 / DNS / Dev Container の env 注入）を最短で回避できる手順にする


## 前提
### 1) Demo 1 を完了している

（Azure CLI ログインや Python 環境ができている前提です）

### 2) Azure AI Foundry Agents の準備（Demo2〜の推奨バックエンド）
Hosted Tools（Web Searchなど）は、サービス側がネイティブでサポートしている必要があります。
このデモセットでは **Azure AI Foundry Agents** を推奨します。

必要な環境変数（どちらも必須）：
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

> 重要: `AZURE_AI_PROJECT_ENDPOINT` は **Foundry Project endpoint** です。
> 例: `https://<account>.services.ai.azure.com/api/projects/<project-name-or-id>`
>
> `https://<resource>.cognitiveservices.azure.com/` のような **Azure AI Services / Azure OpenAI の endpoint は別物**で、Demo 2 では使えません（404 になったり、そもそも接続できません）。

> `AZURE_AI_MODEL_DEPLOYMENT_NAME` は **Foundry プロジェクト側の "Models + endpoints" に表示されるデプロイ名**です。
> Demo 1 の Azure OpenAI のデプロイ名と **同じとは限りません**（ここが一番ハマりやすいポイントです）。

> `AZURE_AI_PROJECT_ENDPOINT` は AI Foundry のプロジェクト詳細から取得します。

### 2.1) Bing 接続（必須: Hosted Web Search）
このデモは **Hosted Web Search** を使います。Azure AI Foundry では Web Search が **Bing 接続（Grounding）** を通して提供されるため、実行時に接続情報がないとツール初期化で失敗します。

`.env` に以下の **どちらか一方** を設定してください。

#### A（推奨）: Grounding with Bing Search
- `BING_CONNECTION_ID`（エイリアス: `BING_PROJECT_CONNECTION_ID`）

値は Foundry プロジェクトに追加した Bing 接続の **project connection ID** です（例: `/subscriptions/.../resourceGroups/.../providers/Microsoft.MachineLearningServices/workspaces/.../connections/...` のようなリソースパス）。

取得の流れ（Foundry portal）:
1. https://ai.azure.com/ を開く
2. 右上のメニューから **Operate** → 左ペイン **Admin**
3. 対象プロジェクトを選択 → **Add connection**
4. Connection type で **Grounding with Bing Search** を選んで接続を作成
5. 作成した接続の **Connection details** から **Project connection ID** をコピー

（公式ドキュメントでは環境変数名が `BING_PROJECT_CONNECTION_ID` になっていますが、このリポジトリのデモコードは `BING_CONNECTION_ID` でも受け取れるようにしています。）

#### B: Bing Custom Search
- `BING_CUSTOM_CONNECTION_ID`（エイリアス: `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID`）
- `BING_CUSTOM_INSTANCE_NAME`（エイリアス: `BING_CUSTOM_SEARCH_INSTANCE_NAME`）

取得方法: Foundry portal の対象プロジェクトで Bing 接続（Grounding または Custom Search）を作成/追加し、接続詳細（ID 等）をコピーして環境変数に設定します。

### 2.2) 環境変数まとめ（最低限これだけ）

| 種別 | 変数 | 必須 | 補足 |
|---|---|---:|---|
| Foundry | `AZURE_AI_PROJECT_ENDPOINT` | ✅ | `https://...services.ai.azure.com/api/projects/...` |
| Foundry | `AZURE_AI_MODEL_DEPLOYMENT_NAME` | ✅ | Foundry の **Models + endpoints** のデプロイ名 |
| Bing (A) | `BING_CONNECTION_ID` | ✅（Aを使う場合） | エイリアス: `BING_PROJECT_CONNECTION_ID` |
| Bing (B) | `BING_CUSTOM_CONNECTION_ID` | ✅（Bを使う場合） | エイリアス: `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID` |
| Bing (B) | `BING_CUSTOM_INSTANCE_NAME` | ✅（Bを使う場合） | エイリアス: `BING_CUSTOM_SEARCH_INSTANCE_NAME` |

### 3) 追加パッケージ（未導入なら）
```bash
pip install agent-framework-azure-ai --pre
```

> このリポジトリの Dev Container は、通常 `requirements.txt` により必要パッケージが入っています。
> （手動で入れる必要があるのは、ローカル環境で実行する場合などです）

### 4) Azure CLI ログイン
```bash
az login --use-device-code
```

> 以降のデモは、既定で **Entra ID（Azure CLI）認証**を使って接続します。

ログイン確認（任意）:
```bash
az account show
```


## 手順

### Step 0. `.env` を準備（推奨）
Dev Container / Codespaces では、`containerEnv` により環境変数が **空文字で注入**されるケースがあります。
その場合、一般的な `.env` 読み込み（dotenv）が「すでに env がある」と判定して **上書きしない**ため、値が空のままになりがちです。

このリポジトリの `src/demo2_web_search.py` は、リポジトリルートの `.env` を明示的に読み込み、
**未設定または空の環境変数だけ補完**する実装になっています。

リポジトリルート（`/workspaces`）に `.env` を作り、少なくとも次を入れてください（例）：

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"

# A: Grounding with Bing Search（推奨）
BING_CONNECTION_ID="/subscriptions/.../resourceGroups/.../providers/Microsoft.MachineLearningServices/workspaces/.../connections/..."

# （Bを使う場合は A ではなくこちら）
# BING_CUSTOM_CONNECTION_ID="..."
# BING_CUSTOM_INSTANCE_NAME="..."
```

> `.env` は **コミットしない**でください（Secrets を含み得ます）。

### Step 1. スクリプトを確認（`src/demo2_web_search.py`）
このリポジトリには `src/demo2_web_search.py` が同梱されています。
主なポイントは次のとおりです：

- リポジトリルートの `.env` を明示的に読み込み（空/未設定だけ補完）
- `AZURE_AI_PROJECT_ENDPOINT` / `AZURE_AI_MODEL_DEPLOYMENT_NAME` を必須チェック
- `AZURE_AI_PROJECT_ENDPOINT` のホスト名を DNS 解決できるか事前チェック（環境側の DNS/Private Link 問題を早期に可視化）
- Bing 接続を必須チェック（`BING_CONNECTION_ID` など）
- Agent Framework の API 差分に合わせ、`AzureAIAgentClient(...).as_agent(...)` を利用

（ドキュメント上の `create_agent(...)` 例と異なる場合がありますが、**このリポジトリのコードが正**です）

### Step 2. 実行
```bash
python3 src/demo2_web_search.py
```

### Step 3. 期待される出力
環境が正しく揃っていれば、エラーなく完走し、ターミナルに次のような形式で回答が出ます：

- 「最近のAIニュース」をいくつか列挙
- 概要（要約）
- （モデルによっては）参照したWeb情報を根拠として言及

※出力内容は日々変動します（検索結果に依存）。


## 技術解説（ここがポイント）

### 1) ツールは「モデルの行動範囲を広げる拡張点」
  - **必要に応じてツールを呼び出す → 結果を材料に回答する**
  という “行動” が可能になります

### 2) HostedWebSearchTool は「サービス側でWeb検索を実行」

- 「ローカルでスクレイピングする」ではなく、**Foundry 側が提供する Hosted Tool** を呼び出します
- そのため、ツール利用可否は **Foundry プロジェクトの設定（Bing 接続など）**と、アカウントの構成（ネットワーク、権限）に依存します

### 3) 重要：ツールの対応可否は “バックエンド次第”
公式ドキュメントでも、**ツールのサポートはサービスプロバイダーにより異なる**と明記されています。
もし動かない場合は以下を確認：


## うまくいかない時のチェック

### まず最初に見るべき例外
`src/demo2_web_search.py` は、設定不足を早めに検知して分かりやすく落とすようにしています。
まずは例外メッセージ（特に「どの env が足りないか」「DNS が引けないか」）を確認してください。

### `AZURE_AI_PROJECT_ENDPOINT` が未設定
```bash
echo $AZURE_AI_PROJECT_ENDPOINT
```
空なら設定漏れです。

#### 形式が違う（404 になった / そもそも別サービス）
`AZURE_AI_PROJECT_ENDPOINT` は **Foundry Project endpoint** です。

- ✅ 例: `https://<account>.services.ai.azure.com/api/projects/<project-id>`
- ❌ 例: `https://<resource>.cognitiveservices.azure.com/`（Azure AI Services / Azure OpenAI の endpoint）

### `Temporary failure in name resolution` / `Name or service not known` (DNS)
`AZURE_AI_PROJECT_ENDPOINT` のホスト名（例: `...services.ai.azure.com`）を、この実行環境から DNS 解決できていない状態です。

確認ポイント:
- 値のコピーミスがないか（Foundry の Project overview から再コピーする）
- Foundry プロジェクト/アカウントが **Private networking / Private DNS** 構成になっていないか
    - その場合、この Dev Container / Codespaces 側では名前解決できず、実行できません
    - private DNS が使えるネットワーク（社内NW/VPN等）で実行するか、public なプロジェクト構成で試してください

### `Hosted web search requires a Bing connection`（Bing 接続不足）
Hosted Web Search は Bing 接続が必須です。

- A（推奨）: `BING_CONNECTION_ID`（または `BING_PROJECT_CONNECTION_ID`）
- B: `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`

値は「Bing の API Key」ではなく、**Foundry プロジェクトに追加した接続の Project connection ID（リソースパス）**です。

### `Failed to resolve model info for: ...`（モデルデプロイ名不一致）
`AZURE_AI_MODEL_DEPLOYMENT_NAME` が Foundry プロジェクトで解決できていません。

チェック観点:
- Foundry portal → 対象プロジェクト → **Models + endpoints** で、デプロイ名が存在するか
- Demo 1 の Azure OpenAI デプロイ名と混同していないか（**別物**なことが多い）

### 権限不足

Foundry プロジェクトに対して、実行ユーザー（`az login` したアカウント）が権限不足の場合に失敗します。
チーム/管理者に以下を確認してください：

- 対象 Foundry プロジェクト（または背後の workspace）へのアクセス権
- Bing 接続（Grounding）の利用権限

（環境によりエラーメッセージが変わるため、ここは「まずはエラー全文を読む」が正攻法です）


## 次のデモへ
Demo 3 では **Hosted MCP Tool** を追加し、Microsoft Learn MCP を使ってドキュメント参照を強化します。
→ `demo3.md` を開いて続けてください。
