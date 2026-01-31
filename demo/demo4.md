# Demo 4 — Structured Output（response_format で型付き出力を得る）

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
```

## ねらい
- Pydantic モデルを定義し、`response_format=<Model>` を指定して実行する
- 出力を `response.value`（= Pydanticインスタンス）として安全に扱えるようにする
- Demo 2 のストーリー（venue 探し）を引き継ぎ、**Web Search で集めた情報を構造化して出す**

---

## 前提
- Demo 2 まで完了している（Azure AI Foundry Agents の env vars 設定済み）
- `pydantic` がインストール済み（Dev Container 前提ならOK）
- `az login` 済み

追加で必要な env var:
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

このデモは Web Search を使うため、Bing connection も必要です（Demo 2 と同じ）：
- `BING_CONNECTION_ID`（または `BING_PROJECT_CONNECTION_ID`）
    - もしくは `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`

（推奨）
- まずは Demo 4 実行前に、以下を満たしているか確認してください
    - `az login` 済み（Entra ID 既定で動かす場合）
    - `.env`（リポジトリルート）に必要な値が入っている

---

## 手順

### Step 1. 構造（スキーマ）を Pydantic で定義する
このリポジトリには `src/demo4_structured_output.py` が同梱されています。
（必要なら自分で編集して拡張できます）

以下は **概念が分かりやすい最小例** です。
実運用向けの堅牢化（`.env` 明示ロード、空文字注入対策、DNSチェック、`response.value` が空の時のフォールバック等）は、同梱の `src/demo4_structured_output.py` を参照してください。

```python
from pydantic import BaseModel

class VenueInfoModel(BaseModel):
    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0

class VenueOptionsModel(BaseModel):
    options: list[VenueInfoModel]

# 実際の demo では、Azure AI Foundry Agents + HostedWebSearchTool を使って
# "venue を探して" という質問を投げ、その結果を response_format=VenueOptionsModel で受け取ります。
```

実装上のポイント（同梱スクリプト側）:
- リポジトリルート `.env` を明示的に読み込み、**未設定/空の環境変数だけ補完**します
    - Dev Container / Codespaces で env が空文字注入される問題への対策
- `response.value` が `None` の場合でも、`response.text` が JSON なら Pydantic で復元するフォールバックを入れています
    - バックエンド/バージョン差で「非ストリーミング時だけ value に入らない」ケースがあるため

補足:
- 公式/サンプルコードでは `client.create_agent(...)` の例が出ることがありますが、このリポジトリで pinned している SDK では `as_agent(...)` が現行 API のため、それに合わせています

（補足）
- 同梱スクリプトは **非ストリーミング/ストリーミングの両方**を実行し、どちらでも `PersonInfo` を取り出せることを確認できるようにしています。

### Step 2. 実行
```bash
python3 -u src/demo4_structured_output.py
```

### Step 3. 期待される出力例
Venue 候補が複数件、構造化されたフィールド（title/address/description/...）で出力されます。

- `response.value` が埋まれば、そのまま Pydantic として表示
- `response.value` が空でも、`response.text` が JSON なら復元して表示（フォールバック）

---

## 技術解説（ここが本質）

### 1) `response_format` は “出力の形” を契約にする
- ただの JSON 文字列ではなく
- **指定したスキーマ（Pydanticモデル）に合う形で出力**するようモデルに要求します

### 2) `response.value` が “型安全な結果”
- 成功すれば、`response.value` に **Pydanticインスタンス**が入る
- 失敗時は `None` になり得るので、必ず if でチェックする

### 3) ストリーミング時の注意
このデモではまず **非ストリーミング** で「構造化が取れる」を見せます。
ストリーミングと組み合わせるのは上級編として Demo 5/6 の観察と合わせてやるのが分かりやすいです。

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
実行環境から `AZURE_AI_PROJECT_ENDPOINT` のホストが DNS 解決できないと、開始時点で停止します。

- エラー例: `Cannot resolve AZURE_AI_PROJECT_ENDPOINT host via DNS`
- 対応: Private networking / DNS の構成を見直す、または DNS 解決できるネットワークから実行する

補足:
- 「ホスト環境では引けるのに、Dev Container の中だけ引けない」ことがあります。その場合はコンテナ側の DNS 設定（Corporate DNS / Private Link / Dev Container の network 設定）を疑ってください。
- `/etc/hosts` に固定する回避策もありますが、IP 変更で壊れるので恒久策にはなりません（手元検証の“最後の手段”としてのみ推奨）。

---

## 次のデモへ
Demo 5 では、処理を2つのエージェントに分解して **Workflow + Edge** で順序保証のあるパイプラインを作ります。
→ `demo5.md` を開いて続けてください。
