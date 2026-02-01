# Agent Framework 学習ガイド（Demo 1〜6：コード読解版）

この `demo/guide.md` は「どう実行するか」よりも、**はじめて Agent Framework を使って開発していく人が、デモコードから何を読み取り、どう応用していくか**に焦点を当てたガイドです。

- “やること” は **コードを読むこと**です（Demo 1〜6 は、概念が段階的に増えるように作られています）
- Agent Framework は更新が速いので、**このリポジトリで pinned されている依存**と **`src/demo*.py` の実装**を正とします

  - pinned 版の確認: `requirements.txt`（例: `agent-framework==1.0.0b260123`）

> Microsoft Learn は “latest” の可能性があります。差分が疑われる場合は、本リポジトリの pinned 版の挙動（`requirements.txt` / `src/` / `entities/`）を優先してください。

---

## どの順で読むべきか（学習の地図）

| Demo | 読み取るテーマ | 主なファイル |
|---:|---|---|
| 1 | 最小のエージェント実行、環境変数/ネットワークの fail-fast、async リソース管理 | `src/demo1_run_agent.py` |
| 2 | Hosted tool（Web Search）の組み込みと “接続情報” の扱い | `src/demo2_web_search.py` |
| 3 | MCP（stdio）= 外部プロセスを tool にする、環境依存/安全性 | `src/demo3_hosted_mcp.py` |
| 4 | 構造化出力（Pydantic）、`response_format` とフォールバック設計 | `src/demo4_structured_output.py` |
| 5 | Workflow によるオーケストレーション、イベント駆動の観測、寿命管理 | `src/demo5_workflow_edges.py` |
| 6 | DevUI のホスト、entity/workflow の発見と UX 設計（import と runtime 検証の分離） | `src/demo6_devui.py`, `entities/**` |

---

## このリポジトリ共通で覚える「型」

### 1) `.env` は **fill-only**（未設定/空のみ補完）

各デモはリポジトリルートの `.env`（`/workspaces/.env`）を明示的に読み込みますが、**既存の環境変数を無条件に上書きしません**。

- Dev Container / Codespaces では env が **空文字で注入**されることがある
- `VAR=... python ...` の一時上書きによるデバッグを邪魔しない

この方針は `AGENTS.md` の「環境変数は未設定/空のみ補完」に一致します。

### 2) `_require_env()` で “不足” を最初に確定する

外部依存（認証、RBAC、ネットワーク、モデル名、接続設定）が多いので、
**SDK を叩く前に「足りないもの」を確定**させ、エラーを読みやすくします。

> 初学者がハマりやすいのは「設定不足なのに SDK が奥の方で落ちて、原因がぼやける」パターンです。

### 3) DNS の事前チェック（Private Link/Private DNS の切り分け）

`AZURE_AI_PROJECT_ENDPOINT` の hostname を `socket.getaddrinfo(...)` で引けるかを先にチェックし、
**ネットワーク問題を早期に特定**します。

### 4) `async with` で credential/client/agent を確実に閉じる

`AzureCliCredential` や `AzureAIAgentClient`、agent インスタンスは **非同期リソース**です。
デモでは `async with`（または `AsyncExitStack`）で寿命管理を徹底しています。

### 5) 「分かる範囲だけ」例外を翻訳する

`ServiceResponseException` などクラウド由来の例外は、原因が典型的なもの（例：モデルデプロイ名）に限り、
**次に何を確認すべきか**が分かるメッセージに変換しています。

### 6) 観測性は optional（OpenTelemetry があれば使う）

OpenTelemetry を必須にせず、入っていれば “agent/tool の動き” が見える形にしています。
「便利だが環境差があるもの」は **任意にする**のがデモとして親切です。

### 7) Ctrl+C を “想定された終了” として扱う（exit code 130）

長時間プロセス（DevUI など）で、ユーザー中断を分かりやすく扱うための慣習です。

---

## Demo 1：最小のエージェント実行（= これ以降の土台）

対象: `src/demo1_run_agent.py`

このファイルは「とにかく最短で動かす」だけでなく、クラウド連携で必ず踏む **“失敗しやすい地雷” を先に片付ける**ための、
共通テンプレート（fail-fast + 寿命管理 + 観測性）の最小形です。

### このファイルの読み順（迷子にならないルート）

1. `.env` 読み込み（fill-only）
   - `dotenv_values(...)` でリポジトリルートの `.env` を読み、`os.environ` に **未設定/空だけ**補完
2. `_require_env(...)`
   - 必須設定が無い場合に **その場で止める**（原因を手前で確定）
3. `_check_project_endpoint_dns()`
   - Azure AI Foundry project endpoint の host を **DNS 解決できるか**を “接続前に” 判定
4. （任意）OpenTelemetry の初期化
   - import できる環境なら span を 1 行ログで観測（できなければスキップ）
5. `main()`
   - `async with` で credential / agent の寿命を閉じ、`agent.run()` → `result.text`

### 1) `.env` は fill-only：Dev Container/Codespaces の「空文字 env」対策

`_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"` により、リポジトリルートの `.env` を読み込みます。

ここで重要なのは、`.env` の値で **無条件に上書きしない**ことです。

- Dev Container / Codespaces では env が **空文字で注入**されることがある（「変数はあるが中身が空」）
- デバッグ時に `VAR=... python ...` のような **一時上書き**を邪魔しない

実装としても、既存値が `None`（未設定）または `strip()` して空のときだけ `.env` の値で補完しています。

### 2) `_require_env(name)`：不足を “奥で落とさず” 手前で確定する

`_require_env(...)` は単なる入力チェックではなく、**失敗を早く・読みやすくする**ための関数です。

Demo 1 では最低限として、次を必須扱いにしています。

- `AZURE_AI_PROJECT_ENDPOINT`（Azure AI Foundry project endpoint）
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`（Azure AI Foundry project のモデルデプロイ名）

SDK を叩いた後で “なんとなく落ちる” よりも、SDK を叩く前に「足りないもの」を確定させた方が、
初学者の調査コストが圧倒的に下がります。

### 3) `_check_project_endpoint_dns()`：ネットワーク問題を “認証より前” に切り分ける

`AZURE_AI_PROJECT_ENDPOINT` を URL として解析し、`socket.getaddrinfo(host, 443)` で **DNS 解決だけ**を確認します。
つまり、このチェックは TCP/HTTPS の疎通ではなく、次を早期に切り分けるためのものです。

- endpoint が URL として変（host が取れない）
- private networking / private DNS な endpoint を、名前解決できない環境から叩いている

クラウド開発でありがちな「RBAC？認証？SDK？…」と疑う前に、まず **“DNS できていない”** を確定できるのが効きます。

### 4) `async with` が “この repo の基本形” になっている理由

`AzureCliCredential`（aio 版）や agent は **非同期リソース**として扱い、`async with` で確実に閉じます。

- `async with AzureCliCredential() as cred:`
- `async with AzureAIAgentClient(credential=cred).as_agent(...) as agent:`

デモは短くても、後続（workflow / DevUI）ほど「閉じ忘れ」や「例外時の後始末」が効いてきます。

> 補足: `AzureCliCredential` は “Azure CLI のログイン状態” を前提にするため、未ログイン/権限不足だとここから先で失敗します。

### 5) `agent.run(...)` と `result.text`：最初は “文字列で理解する” のが正解

Demo 1 は返答を構造化せず、`result.text` を表示して最小の成功体験を作ります。

- まず「返ってくる」体験で学習コストを下げる
- 次に「文字列だと扱いづらい」へ気づける → Demo 4（Structured Output）へ自然につながる

### 6) 観測性は optional：OpenTelemetry があれば 1 行ログで動きが見える

冒頭で `configure_otel_providers` を `try/except` しているのは、デモとして重要な配慮です。

- OpenTelemetry が入っていない環境でも動く（必須にしない）
- 入っていれば `_DemoSpanExporter` が agent/tool らしい span だけを拾い、読みやすい 1 行ログで出します

### 応用の観点（開発での読み替え）

- 「ツールを追加したい」→ Demo 2/3
- 「出力をプログラムで扱いたい」→ Demo 4
- 「複数工程に分割したい」→ Demo 5

---

## Demo 2：Hosted Web Search（ツールを “設計要素” として扱う）

対象: `src/demo2_web_search.py`

このファイルは Demo 1 の土台（fill-only `.env` / `_require_env` / DNS preflight / `async with`）を引き継ぎつつ、
**Hosted tool を “エージェントの能力として付与する”**ときに、どこでハマり、どう設計すると調査が楽になるかを見せるデモです。

### このファイルの読み順（迷子にならないルート）

1. `.env` 読み込み（fill-only）
   - Demo 1 と同じ。未設定/空だけ `.env` から補完
2. `_require_env(...)` と `_check_project_endpoint_dns()`
   - Azure AI Foundry project endpoint の前提を手前で確定（DNS まで含めて切り分け）
3. `_get_bing_tool_properties()`
   - Hosted Web Search 用の **接続情報（Bing grounding / Custom Search）**を env から組み立てる
4. `HostedWebSearchTool(additional_properties=...)`
   - user_location + Bing connection 情報を tool に渡す
5. `try/except ServiceResponseException`
   - 典型的な失敗（モデル解決失敗）を “次に見るべき場所” が分かるメッセージに翻訳する

### 1) `_get_bing_tool_properties()`：env 名の揺れを吸収して「接続の前提」を固定する

Hosted Web Search は “Bing を叩く” というより、Azure AI Foundry の hosted web search（Bing grounding）を使うため、
**Azure AI Foundry プロジェクトに作成した connection（project connection ID）**が必要です。

このデモでは `_get_bing_tool_properties()` が、環境変数の表記揺れを吸収します。

- ライブラリ側が参照しがちな env 名（エラーメッセージ由来）
  - `BING_CONNECTION_ID`
  - `BING_CUSTOM_CONNECTION_ID`
  - `BING_CUSTOM_INSTANCE_NAME`
- Azure AI Foundry ドキュメントや UI で目にしがちな env 名
  - `BING_PROJECT_CONNECTION_ID`
  - `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID`
  - `BING_CUSTOM_SEARCH_INSTANCE_NAME`

さらに、ユースケースを 2 系統に分けて「どちらを設定すべきか」をコードで明確化しています。

- Standard（Bing grounding）
  - `connection_id` だけで成立（`{"connection_id": ...}` を返す）
- Custom Bing Search
  - `custom_connection_id` と `custom_instance_name` の **両方**が必要

> 重要: ここが “API キー” ではない点が初学者の罠です。
> 必要なのは Azure AI Foundry portal 上で作った connection の ID（project connection）です。

### 2) `additional_properties`：tool 実行の “文脈” と “接続” を同じ場所で渡す

tool の設定は `HostedWebSearchTool(additional_properties={...})` に集約されています。

- `user_location`：検索結果のローカライズの文脈（例: Seattle / US）
- `**bing_props`：`_get_bing_tool_properties()` が返す connection 情報

この形にしておくと、
「検索精度を上げたい（= 文脈を足す）」と「接続を直したい（= connection を直す）」を
**同じ設定ブロックで追跡**でき、初学者でも変更点を見失いにくくなります。

### 3) `ServiceResponseException` の翻訳：モデル解決失敗を “最短で直せる” メッセージにする

`agent.run(...)` の呼び出しは `try/except ServiceResponseException` で包まれており、
特に `"Failed to resolve model info"` を含む場合は `RuntimeError` に翻訳しています。

ここで伝えたい設計意図は次の 2 つです。

1. **典型的な失敗は、読み手が次に取る行動まで提示する**
   - Azure AI Foundry portal の `Models + endpoints` を確認する、など
2. “デプロイ名の混同” を明確に注意する
   - `AZURE_AI_MODEL_DEPLOYMENT_NAME` は **Azure AI Foundry プロジェクトのモデルデプロイ名**
   - Azure OpenAI の deployment name（別プロジェクト・別 SDK で使うことがある）と混同しやすい

> 補足: 例外メッセージ内で `AZURE_AI_MODEL_DEPLOYMENT_NAME` の現在値を表示しています。
> これは secret というより “設定値の取り違え” の特定が目的ですが、ログに残したくない運用の場合は注意してください。

### 応用の観点（開発での読み替え）

- 「tool を複数付けたい／外部プロセスも使いたい」→ Demo 3（MCP）
- 「検索結果を構造化して UI/DB に入れたい」→ Demo 4（Structured Output）

---

## Demo 3：Hosted MCP（stdio で外部プロセスを tool にする）

対象: `src/demo3_hosted_mcp.py`

このファイルは Demo 2 までの “Azure AI Foundry Agents を安全に動かす土台” を維持しつつ、
tool の実体を **Python 関数ではなく「ローカルの外部プロセス」**にしたときに必要な考え方（依存の切り分け / 失敗の早期化 / 境界の意識）を学ぶデモです。

### このファイルの読み順（迷子にならないルート）

1. `.env` 読み込み（fill-only）
   - ここまでは Demo 1/2 と同じ
2. `_require_env(...)` と `_check_project_endpoint_dns()`
   - Azure AI Foundry 側の前提（endpoint / model deployment / DNS）を先に確定
3. `_require_command("npx")`
   - MCP サーバ起動に必要なローカル依存（Node.js / npx）を fail-fast
4. `MCPStdioTool(...)` の定義
   - tool の実体（= 外部プロセス）をどう起動し、どう安全側に寄せるか
5. `client.as_agent(..., tools=[...])` → `agent.run(...)`
   - agent に「能力」として tool を付与し、実行する
6. `try/except ServiceResponseException`
   - モデル解決失敗など、クラウド側の典型エラーを読みやすくする

### 1) `_require_command("npx")`：外部依存を “接続前” に切り分ける

`_require_command` は `shutil.which(cmd)` で PATH を確認し、`npx` が無い場合に分かりやすく止めます。

Demo 3 のポイントは「Azure AI Foundry に繋がるか」以前に、
**ローカル環境に依存する失敗（Node/npx 不在）**があり得る点です。

この check を入れておくと、失敗時に原因が

- Azure（認証/RBAC/モデル名）
- ネットワーク（DNS/Private Link）
- ローカル（Node/npx/パッケージ取得）

のどこかを素早く特定できます。

### 2) `MCPStdioTool(...)`：tool が “外部プロセス” になると境界が増える

Demo 3 の tool は次の構成です。

- `command="npx"`
- `args=["-y", "@modelcontextprotocol/server-sequential-thinking"]`
- `name="sequential-thinking"`
- `load_prompts=False`

ここで重要なのは、tool の呼び出しが Python の関数呼び出しではなく、
**標準入出力（stdio）越しに外部プロセスと会話する**形になることです。

つまり、失敗モードが増えます。

- `npx` が見つからない（PATH）
- 外部パッケージ取得ができない（ネットワーク制限）
- 外部プロセスが起動しても想定のプロトコルで応答しない

このデモは、そういった “環境要因” を前提に、
デモとして最低限の guard（`_require_command`）を入れています。

### 3) `args=["-y", ...]`：対話プロンプトで止まらない（CI/DevContainer 向け）

`npx` は状況によって確認プロンプトが出ることがあるため、
`-y` を付けて **非対話で確実に動く**ように寄せています。

（デモは “動くこと” が最優先なので、こういうオプションは地味に大事です。）

### 4) `load_prompts=False`：挙動を固定して “説明可能性” を上げる

`load_prompts=False` は、外部ツール側が持つ prompt を自動ロードしない設定です。

デモとしては次の意味を持ちます。

- 環境やツール実装の差で agent の挙動が揺れにくい
- 「このデモのプロンプトはここに書いてある」と説明しやすい
- tool 連携の挙動を **安全側（予測可能側）**に寄せられる

### 5) tool の “使わせ方” は instructions にも現れる

`instructions` に
「sequential-thinking tool で段取りを作ってから回答する」
旨が書かれており、単に tool を渡すだけでなく **使い方の意図**まで指定しています。

Hosted tool / MCP tool は「付ければ勝手に良くなる」ではなく、
**いつ・何のために使うか**を instructions で設計するのがコツです。

### 6) `ServiceResponseException` の翻訳：クラウド側の失敗を “最短で直せる” メッセージにする

`agent.run(...)` の呼び出しは `try/except ServiceResponseException` で包まれており、
`"Failed to resolve model info"` を含む場合は `RuntimeError` に翻訳しています（Demo 2 と同じ発想）。

MCP 連携のデモは「ローカルで落ちる」ことが目立ちますが、
実際には **モデルデプロイ名や権限**のようなクラウド側の失敗も普通に起こるため、
両方の失敗モードを “読み手が次の一手を打てる形” に揃えるのがポイントです。

### 7) セキュリティ視点（初心者向けに最低限）

MCP（外部プロセス起動）は、設計上どうしても境界が増えます。

- サプライチェーン（どのパッケージを実行しているか）
- 実行権限（ローカルで何ができるか）
- 入出力境界（stdio 経由でどんなデータを渡すか）

デモ段階から「どのコマンドを許すか」「どの tool を本番で許すか」を意識しておくと、
後で workflow / DevUI に広げたときに破綻しにくくなります。

---

## Demo 4：Structured Output（Pydantic で “アプリ向けデータ” にする）

対象: `src/demo4_structured_output.py`

このデモは Demo 1〜3 の延長（fail-fast / tool / 例外翻訳）に、
**「LLM の出力を “アプリで扱えるデータ構造” に落とす」**という現実的な要件を足したものです。

> Demo 1 では `result.text` をまず見せて “動く体験” を作り、
> Demo 4 で「そのままだとアプリに入れづらい」を “型” で解決する流れになっています。

### このファイルの読み順（迷子にならないルート）

1. `VenueInfoModel` / `VenueOptionsModel`（Pydantic スキーマ）
   - 何を「構造化」したいのか（= アプリ要件）を定義
2. `HostedWebSearchTool(... additional_properties=...)`
   - 情報収集の手段（Web Search）を agent に付与
3. `client.as_agent(... instructions=...)`
   - 「ツールをどう使い、どう返すか」を *自然言語で設計* する
4. `agent.run(..., response_format=VenueOptionsModel)`
   - “文字列ではなくモデル” として受け取る本体
5. `response.value` → フォールバック（`response.text` → `model_validate_json`）
   - バージョン差・バックエンド差に壊れにくい受け取り方

### 1) スキーマ設計：LLM の出力を「保存/表示できる形」に固定する

`VenueInfoModel` と `VenueOptionsModel` が、このデモの中心です。

- `VenueInfoModel` は 1 会場ぶんの情報
  - `title`, `description`, `services`, `address` は `str | None`
    - Web 由来の情報は欠けることがあるので、最初から “欠ける前提” の型にしている
  - `estimated_cost_per_person: float = 0.0`
    - 数値として扱いたい項目を float に固定し、未取得時のデフォルトを与えている
- `VenueOptionsModel` は会場候補の配列
  - `options: list[VenueInfoModel]`

この作りの狙いは、「LLM が何を返すべきか」を *文面だけ* に頼らず、
**スキーマで “出力の形” を規定**することです。

> 実務では、この “出力の形” がそのまま DB のカラムや UI の表示項目になります。
> だから先にスキーマを置くと、後続の実装（保存/検証/差分比較）が圧倒的に楽になります。

### 2) tool 設定：検索の文脈（user_location）と接続（Bing connection）をまとめて渡す

Demo 2 と同様に Hosted Web Search を使いますが、Demo 4 の文脈は
「検索して終わり」ではなく「検索して *構造化データとして返す*」です。

このデモでは tool の設定を次に集約しています。

- `additional_properties` に
  - `user_location`（検索のローカライズ文脈）
  - `bing_props`（接続情報。`_get_bing_tool_properties()` の戻り）

ポイントは、**構造化出力の話をしていても “接続と検索文脈” は引き続き重要**ということです。
検索がブレると、出力をスキーマにしても中身がブレます。

### 3) instructions：スキーマだけでなく「返し方の姿勢」も固定する

`client.as_agent(...)` の `instructions` は短いですが、意図は明確です。

- web search を使って候補を探す
- **提供された schema に一致する構造化データだけ**を返す

`response_format` があるとはいえ、LLM は “つい説明文を足す” ことがあります。
このデモは、instructions で先に
「自然言語の長文ではなく、構造データだけ返してね」
を釘刺ししておく、という設計を見せています。

### 4) `response_format=VenueOptionsModel`：受け取りが「文字列」から「モデル」になる

`agent.run(...)` で次のように呼び出しています。

- `response_format=VenueOptionsModel`

ここが Demo 4 の主役です。
成功すると、戻り値 `response` の中に **Pydantic モデルとしての結果**が入ります。

コード上はまず `getattr(response, "value", None)` を見に行き、
`venue_options.options` をループして表示します。

この書き方の良い点:

- アプリ側は `option.estimated_cost_per_person` のように **型付きデータ**として扱える
- 後工程（並び替え/フィルタ/保存）を Python の通常のコードで書ける

### 5) フォールバック：`.value` が無い/取れない場合に `.text` から復元する

このデモは “壊れにくさ” の作り方が丁寧です。

1. まず `response.value` を試す
2. 無ければ `response.text` を見に行く
3. `text` が JSON っぽい（`{...}`）なら `VenueOptionsModel.model_validate_json(text)` を試す

コードにもコメントがありますが、環境やバージョン差で
「構造化のはずなのに `.value` が空で、`.text` に JSON が入る」
ケースがあり得ます。

このフォールバックが伝えているのは、次の実務的な姿勢です。

- **“SDK が常に理想形で返す” と決め打ちしない**
- ただし、何でも握りつぶすのではなく
  - 取れたら表示
  - 取れなければ “何が取れなかったか” を表示（`No structured data found...`）
 という順で、デバッグ可能性を残す

> 応用するときは、ここに「JSON ではない」「schema に合わない」場合の
> リトライや、プロンプトの修正（例："Return JSON only" の強化）を足すこともできます。

### 6) 典型的な失敗モード：モデル解決失敗を “最短で直せる” メッセージにする

`agent.run(...)` は `try/except ServiceResponseException` で包まれており、
`"Failed to resolve model info"` を含む場合に `RuntimeError` へ翻訳しています（Demo 2/3 と同じ発想）。

Structured Output の話をしていても、現場で多いのはまずここです。

- `AZURE_AI_MODEL_DEPLOYMENT_NAME` が Foundry project の “モデルデプロイ名” と一致していない
- `AZURE_AI_PROJECT_ENDPOINT` が違う project を指している

このデモはエラーに現在値を添えることで、
「どこを直すべきか」を短時間で特定しやすくしています。

### セキュリティ/信頼境界の注意（初心者向けに最低限）

Web Search を入れると、入力（検索結果）が外部由来になります。
Structured Output は出力の形を縛れますが、
**中身の正しさ（真偽）まで保証するものではありません**。

- “もっともらしいが誤った住所/価格” が混ざる前提で、確認・出典・再検証の設計が必要
- 本番では
  - URL/出典の格納
  - 価格/住所の検証
  - tool の結果テキストをそのままプロンプトへ入れる際の注入（指示混入）対策
 も検討対象になります

### 応用の観点（開発での読み替え）

- 「UI や DB に入れるデータが欲しい」→ このデモのスキーマ設計 + `response_format` が基本形
- 「複数工程で構造データを受け渡したい」→ Demo 5（Workflow）の各ステップ出力を同様にモデル化する


---

## Demo 5：Workflow（“会話”から “実行フロー” へ）

対象: `src/demo5_workflow_edges.py`

### このデモで読むべきポイント

- `AsyncExitStack` による寿命管理：
  - 複数 agent を作るほど `async with` のネストが辛くなる → まとめて管理する
- 役割分割（coordinator/venue/...）：
  - 工程と責任を分け、ツールも最小限に付与する（最小権限の感覚）
- `WorkflowBuilder` と edge：
  - “次に誰を走らせるか” を **宣言的に**定義する
- `run_stream()` とイベント処理：
  - token を垂れ流さず、executor 切り替えで進捗を把握する
- `_print_result_item()`：
  - イベント payload の揺れを吸収する “表示層” を用意する

### pinned 差分への配慮（初心者が真似すべき姿勢）

`WorkflowBuilder(**kwargs)` が通らない可能性に備えて `try/except TypeError` でフォールバックしています。
「beta/pinned を前提にするなら、互換性ガードはコストに見合う」ことが読み取れます。

---

## Demo 6：DevUI（開発体験を良くするコード設計）

対象: `src/demo6_devui.py` と `entities/**`

### このデモで読むべきポイント

- `sys.path` の調整：
  - `python src/...` 直実行で import が壊れやすい問題を回避
- `serve(entities=[workflow], ...)`：
  - DevUI は “entity（workflow/agent）” を渡すと UI をホストできる
- 起動前のポートチェック：
  - 初学者が迷いにくいエラーにする（UX をコードで作る）
- entity 側の設計（重要）：
  - DevUI は import して entity を列挙するため、**できれば import 時に落とさず**、実行時に必要条件を検証する
  - この方針の具体例: `entities/event_planning_workflow/workflow.py` は `_validate_environment()` を “実行時” に呼びます

### entities のバリエーション（DevUI で何が動くかを読む）

`entities/**` には複数の workflow entity が入っています。DevUI では **どの entity を開くか**で前提が変わるので、
まず各 entity が「どのクライアント（Azure AI Foundry / Azure OpenAI）を使っているか」を確認します。

- `entities/event_planning_workflow/workflow.py`
  - `AzureAIAgentClient`（Azure AI Foundry Agents）を使用
  - env 検証は `_validate_environment()` に集約（DevUI の “一覧表示” を邪魔しない）
- `entities/ai_genius_workflow/workflow.py`
  - `AzureOpenAIChatClient`（Azure OpenAI）を使用
  - env の必須化が import 時点で走るため、未設定だと DevUI 起動時に落ち得ます（改善余地）

> DevUI は「まず起動して一覧が見える」こと自体が開発体験の核なので、
> import と runtime requirements を分ける設計は、デモ以上に実務で効きます。

---

## つまずいたときに “コードで” どこを見るか

- 設定不足（env）：各 demo の `_require_env(...)`
- ネットワーク/DNS：`_check_project_endpoint_dns()`
- モデル名：例外の `Failed to resolve model info` 翻訳箇所（Demo 2/3/4/5）
- 権限：403/Forbidden の翻訳箇所（特に Demo 5）
- ローカル依存：`_require_command("npx")`（Demo 3/5）
- DevUI：ポート事前チェックと `DEMO_NO_OPEN` の分岐（Demo 6）

---

## 参考（Microsoft Learn）

※以下は “latest” の可能性があるため、挙動が異なる場合は本リポジトリ（pinned）を優先してください。

- Run agent（Python）
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- Agent tools（built-in / hosted tools）
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python
- Structured output
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
- DevUI
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference
