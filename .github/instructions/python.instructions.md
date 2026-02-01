---
applyTo: "**/*.py"
---

# Python path-specific instructions

このワークスペースの Python 実装（主に `src/` と `entities/`）に対して、Copilot が一貫した品質・実行性・再現性を保つための指針です。

## コード品質 / 書き方
- 公開 API（他モジュールから import される関数/クラス）は **型ヒント必須**（少なくとも引数と戻り値）。
  - 例：`-> None` / `-> str` / `-> dict[str, str]` などを省略しない
- 非同期 I/O（Agent Framework の `run`/`run_stream`、Azure credential/client など）は **`async`/`await` を崩さない**。
  - `azure.identity.aio.AzureCliCredential` は `async with` を使う
  - `AzureAIAgentClient` / `agent` も `async with` でクローズを保証する
- 例外は握りつぶさない。
  - ただし、外部依存（Foundry / Bing / MCP / DNS / npx 等）の失敗は **利用者が次の一手を取れる**ように、`RuntimeError` などで「何を確認すべきか」を添えて fail-fast する
  - 元例外は `raise ... from ex` で保持する

## このリポジトリでの「実行できる」実装規約（重要）
- 依存は pinned されている前提で書く（`requirements.txt` を確認）。
- Agent 生成は原則として **`AzureAIAgentClient(...).as_agent(...)`** を優先し、API を推測で置き換えない。
  - docs の例と差がある場合は、まずリポジトリ内の用例（`src/demo*.py`）に揃える
- スクリプトは基本 `async def main() -> None:` + `if __name__ == "__main__": asyncio.run(main())` の形にする。

## .env / 環境変数の取り扱い（Dev Container / Codespaces 対策）
- Secrets/Keys をコードやログに出さない。
- Dev Container / Codespaces では環境変数が **空文字で注入**されることがあるため、次を推奨：
  - リポジトリルートの `.env` を **明示的に読み込み**
  - **未設定または空の環境変数だけ** `.env` から補完（既存値は上書きしない）
- 実装はこの repo の既存パターン（`dotenv_values` + fill-only）に揃える。

## 外部依存の境界（I/O の隔離）
- ツール/統合は「小さく・境界が明確」にする。
  - 外部 API / HTTP / MCP / subprocess / FS などは、呼び出し箇所を局所化する
  - 例：DNS 事前チェック、`npx` の存在チェック、Bing 接続設定の組み立ては小さな関数に切り出す
- 新規依存の追加は控えめに。
  - 追加が必要なら、代替（標準ライブラリ/既存依存）と比較して理由を示す

## Structured output（必要な場合）
- UI / Workflow で扱う結果は、可能なら **構造化**する。
  - `pydantic.BaseModel` を使い、`response_format=<Model>` で受ける
- 実行環境差で `response.value` が空になる可能性がある場合は、`response.text` から復元するフォールバックを検討する（既存デモの実装に合わせる）。

## Streaming
- 逐次表示が必要な UI/CLI では `run_stream()` を優先する。
- ストリーミングの結果表示は SDK のイベント形状差分があり得るため、
  - 完了イベントの収集やフォールバック（最終出力）など、壊れにくい表示経路を用意する

## テスト指針（導入する場合）
- 外部呼び出し（Azure/Foundry/MCP/HTTP）はモック可能な層に閉じ込める。
- “プロンプトの変化” はユニットテストの厳密一致ではなく、評価/ゴールデンテスト（スナップショット等）で扱う。
  - ただし、この repo にテスト基盤が無い場合は、まずは導入方針を相談してから追加する

## 最低限のチェック
- 変更後は少なくとも Python の構文チェックを通す：
  - `python3 -m compileall -q src entities`
