# GitHub Copilot Repository Instructions

## このリポジトリの目的
- Python で Microsoft Agent Framework を使い、AI Agent と Workflows を実装・検証する。
- **推測で書かない**（Agent Framework は更新が速いため、API の正確性を最優先）。
- 「このリポジトリの pinned バージョンで実際に動くこと」を最重要視する。

---

## 正確性（バージョン追従）のルール
- 変更・実装前に必ず依存バージョンを確認する。
  - まず `requirements.txt` / `requirements*.txt` を確認する
  - `pyproject.toml` が存在する場合は併せて確認する
- Agent Framework の API・挙動を説明/実装する際は、**一次情報**で裏取りする。
  - Microsoft Learn の API Reference / User Guide を参照する
  - ただし **docs と pinned 版の差分があり得る**ため、docs の例と食い違う場合は、このリポジトリの実装・用例を優先する
- 不明点/仕様変更が疑われる場合は、推測で実装しない。根拠（docs/リリース情報/実測ログ/既存実装）を示す。

---

## Agent Framework 実装方針（Python / この repo の既定）
- 認証は既定で **Entra ID（Azure CLI credential）** を想定する（`az login` 前提）。
- エージェント作成は、このリポジトリのパターン（例：`AzureAIAgentClient(...).as_agent(...)`）を優先し、API を勝手に置き換えない。
- `run()` / `run_stream()` は async 前提で実装する。
  - CLI/DevUI など UI からは streaming を優先（ただし SDK 差分がある場合は「動く形」を最優先）
- ツールは「小さく・副作用が少ない」単位で実装し、引数の意味が伝わるように型ヒントと説明を付ける。
  - 可能なら `typing.Annotated` と説明（例：Pydantic の Field 等）を活用する

---

## 環境変数 / .env の取り扱い
- Secrets/Keys をコードやログに出さない。
- 利用者が設定できるように、必要なら `.env.example` を更新する（実値は入れない）。
- Dev Container / Codespaces では環境変数が **空文字で注入**される場合があるため、
  - リポジトリルートの `.env` を明示的に読み込み、**未設定または空の環境変数だけ補完**する方式を優先する
  - 既存値を無条件に上書きしない（`VAR=... python ...` の一時上書きを妨げない）

---

## リポジトリ構成（推奨）
- 実装は `src/` 配下に置く。
- “外部に依存する処理”（LLM 呼び出し、MCP、Web検索など）は切り出し、テストや差し替えを容易にする。

---

## 変更提案の出し方（Copilot の振る舞い）
- まず最小の変更で目的を満たす案を出す。
- 大きな改修は、実装に入る前に短く以下を提示する：
  1) 変更理由
  2) 設計案
  3) 影響範囲
  4) テスト計画
- 新規依存を増やす場合は、必要性と代替案（標準ライブラリ/既存依存）を先に説明する。

---

## 変更後の最低限チェック（このリポジトリの現状に合わせる）
- まずは Python の構文チェックを必ず通す：
  - `python3 -m compileall -q src entities`
- 変更対象のデモ/スクリプトがある場合は、該当デモの実行で回帰がないことを確認する。
- lint/type/test の導入提案は歓迎だが、**既存の開発フローに合わせて**最小限に行う（未導入ツールを前提にしない）。
