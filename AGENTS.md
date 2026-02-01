# AGENTS.md

このファイルは、本リポジトリを GitHub Copilot Agent mode / coding agent などの **自律実行を伴うエージェント**で扱う際の、作業規約（安全性・正確性・再現性）を定義します。

## このリポジトリでのゴール
- Python で Microsoft Agent Framework（+ Azure AI Foundry Agents）を使い、AI Agent と Workflows を **安全かつ再現可能**に実装・検証する。
- 重要: **API は推測しない**。必ず「このリポジトリで固定しているバージョン」と一次情報（必要に応じて）に基づいて実装する。

---

## まず最初に確認するもの（順序が重要）
1. `requirements.txt` / `requirements*.txt`
   - agent-framework* の **pinned バージョン**を確認する（この repo は pinned 前提で運用する）。
2. `README.md` と `demo/*.md`
   - 実行手順、環境変数、想定される失敗（DNS/権限/接続）を確認する。
3. `src/demo*.py` と `entities/**`
   - **この repo で実際に動いている用例**を優先する（docs と差分が出る可能性がある）。

---

## 実行環境の前提
- OS/環境: Dev Container / Codespaces を想定（Linux）。
- Python: 3.11+ を想定（実際のバージョンは dev container の設定に従う）。
- 認証: 既定で **Entra ID + Azure CLI credential** を使う（`az login` 前提）。

---

## Agent Framework 実装の既定パターン（この repo のルール）
- エージェント生成は、原則として次の形を優先する：
  - `AzureAIAgentClient(...).as_agent(...)`
- クライアント/credential は **async リソース**として扱い、必ず `async with` でクローズを保証する：
  - `azure.identity.aio.AzureCliCredential`
  - `agent_framework.azure.AzureAIAgentClient`
- 逐次表示が必要な UI/CLI では `run_stream()` を優先する。
  - ストリーミングのイベント形状は SDK の差分で変わり得るため、完了イベントの収集や最終出力フォールバックなど **壊れにくい表示経路**を用意する。

---

## 環境変数 / .env の運用（必須）
- Secrets/Keys をコード・ログ・ドキュメントに貼らない。
- Dev Container / Codespaces では環境変数が **空文字で注入**される場合があるため、スクリプト側は次を既定とする：
  - リポジトリルートの `.env` を **明示的に読み込み**
  - **未設定または空の環境変数だけ** `.env` から補完（既存値は上書きしない）
- 必須環境変数が欠ける場合は、早い段階で `RuntimeError` などで **分かりやすく fail-fast** する。

---

## 外部依存（ネットワーク/ツール）と失敗時の設計
- 外部依存は「失敗するもの」として扱い、利用者が次に取る行動が分かるエラーメッセージを提供する。
- 代表例:
  - Foundry endpoint の DNS 解決失敗（private networking / private DNS の可能性）
  - モデルデプロイ名の不一致（`AZURE_AI_MODEL_DEPLOYMENT_NAME`）
  - Hosted Web Search の Bing connection 未設定
  - MCP ツール用の `npx` が実行環境に無い/ネットワーク制限

---

## ドキュメントの正確性（更新運用）
- Agent Framework の API 名/シグネチャ/動作を docs に書く場合:
  - Microsoft Learn の一次情報を参照し、URL を併記する。
  - ただし **docs と pinned 版の差分があり得る**ため、差分が疑われる場合は本 repo の動作（用例コード）を優先し、注記を残す。

---

## 変更の作法（自律実行のガードレール）
- まず最小の変更で目的を満たす。不要なリファクタ・整形・依存追加を避ける。
- 大きい改修は、実装前に短く以下を提示してから着手する：
  1) 変更理由
  2) 設計案
  3) 影響範囲
  4) テスト/検証計画
- 新規依存を増やす場合は、必要性と代替案（標準ライブラリ/既存依存）を先に説明する。

---

## 最低限の検証（この repo の現状に合わせる）
- Python の構文チェックを必ず通す：
  - `python3 -m compileall -q src entities`
- 変更対象のデモがある場合は、該当スクリプトを実行して回帰がないことを確認する。
