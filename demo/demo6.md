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
- Scott demo06 と同じく `serve()` で **workflow を直接登録**して表示する

> DevUI は開発用のサンプルアプリであり、本番用途ではありません。

---

## 前提
- Demo 5 まで完了している（Foundry Agents + Bing + npx が動く状態）
- `agent-framework-devui` がインストール済み

必要な env var（Demo 5 と同じ）:

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `BING_CONNECTION_ID`（または `BING_PROJECT_CONNECTION_ID`）

追加:
- `npx` が使えること（coordinator が sequential-thinking MCP を起動）

補足:
- DevUI はローカル開発向けのサンプルアプリです（本番用途ではありません）
- Codespaces / Dev Container の場合はポートフォワードが必要です（後述）

---

## 進め方（Scott 寄せ: `serve()` を使う）
Scott demo06 と同じく、`serve(entities=[workflow], auto_open=True)` で workflow を登録して DevUI を起動します。

---

# A) `serve()` で DevUI を起動する（推奨: Scott と同じ）

このリポジトリには、Scott の demo06 と同じ "Event Planning Workflow" を DevUI で見られるように、
次のファイルを用意しています：

- `src/demo6_devui.py`（DevUI 起動スクリプト）
- `entities/event_planning_workflow/`（DevUI entity: workflow を export）

## Step A-1. 実行

```bash
python3 -u src/demo6_devui.py
```

もし `address already in use`（ポートが使用中）になった場合は、次のどちらかで解決できます。

- 既に起動している DevUI（または別プロセス）を停止する
- もしくは別ポートで起動する（例: `DEVUI_PORT=8082`）

起動すると DevUI が `http://localhost:8081` で待ち受けます（推奨）。

Codespaces / Dev Container の場合:
- ポート `8081` を Forward してください

補足:
- ブラウザ自動起動が不要/失敗する環境では、次のように無効化できます。

```bash
DEMO_NO_OPEN=1 python3 -u src/demo6_devui.py
```

## Step A-2. UI で workflow を実行
1. DevUI を開く（`http://localhost:8081`）
2. Entities 一覧から "Event Planning Workflow" を選ぶ
3. 入力に以下を貼って実行:
    - `Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle`
4. 実行中、coordinator → venue → catering → budget_analyst → booking の順で動くのを観察

---

## DevUI の状態確認 / 停止方法

### 状態確認（まずはここ）

#### 1) Ports パネルで確認（Dev Container / Codespaces 推奨）
- VS Code の下部タブ **PORTS** を開く
- `8081` の行があり、Running Process に `python3 -u src/demo6_devui.py` が見えていれば起動中です

#### 2) /health で確認（いちばん確実）
コンテナ内で以下が `{"status":"healthy"...}` を返せば起動中です。

```bash
curl -fsS http://localhost:8081/health
```

#### 3) どのプロセスが listen しているか確認（Linux/Dev Container）

```bash
ss -ltnp | grep ':8081'
```

### 停止方法

#### 1) foreground 実行なら Ctrl+C
ターミナルで `python3 -u src/demo6_devui.py` を実行している場合は、そのターミナルで `Ctrl+C` が一番安全です。

#### 2) PID を指定して停止
`ss -ltnp | grep ':8081'` で見えた pid を停止します。

```bash
kill <PID>
```

#### 3) 見つけてまとめて停止（最終手段）
DevUI の起動プロセスだけをまとめて止めたい場合:

```bash
pkill -f 'src/demo6_devui.py'
```

> 注意: `pkill -f` は一致したプロセスを停止します。誤爆が怖い場合は PID 指定の `kill` を使ってください。

# B) ディレクトリ検出（CLI）で起動する（オプション）

既存の DevUI CLI で entity を検出したい場合は、次でも起動できます：

```bash
devui ./entities --host 0.0.0.0 --port 8081 --no-open
```

この場合は `entities/` 配下の entity（例: `event_planning_workflow`）が一覧に出ます。

---

# C) OpenAI 互換APIで DevUI を叩く（オプション）

DevUI は `http://localhost:8081/v1` を基準URLに、OpenAI互換の Responses API を提供します。

例（Python）：
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8081/v1", api_key="not-needed")

resp = client.responses.create(
    metadata={"entity_id": "event_planning_workflow"},
    input="Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
)

print(resp.output[0].content[0].text)
```

補足:
- DevUI の base URL は `http://localhost:8081/v1` です
- `metadata={"entity_id": "ai_genius_workflow"}` の `entity_id` は、`/v1/entities` で見える ID と一致します

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

補足:
- DevUI は公式仕様として `.env` を自動ロードできます（entities ルート / entity 配下）
- 一方このリポジトリでは、既存デモ（Demo1〜）の流れに合わせて **リポジトリルート `.env`** を参照する実装も併用しています
    - どちらか一方に揃えるのが理想ですが、ハンズオンの再現性を優先しています

### DNS 解決に失敗して開始前に止まる（Azure OpenAI）
`AZURE_OPENAI_ENDPOINT` のホストが Dev Container 内から DNS 解決できないと起動時/実行時に失敗します。

- エラー例: `Cannot resolve AZURE_OPENAI_ENDPOINT host via DNS`
- 対応: Private networking / private DNS 構成を見直す、または DNS 解決できるネットワークから実行する

---

## 次にやること（発展）
- `--tracing` を付けて OpenTelemetry トレースを有効化し、ツール呼び出し/実行フローをさらに追う
- Demo2/3 のツール（Web Search / MCP）を workflow 内エージェントへ組み込み、より “現実の業務” に近づける

参考:
- DevUI は Agent Framework が出す OpenTelemetry span を収集・表示します（DevUI 自身が span を作るわけではありません）
