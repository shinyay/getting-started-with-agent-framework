---
applyTo: "**/*.md"
---

# Documentation path-specific instructions

このリポジトリの Markdown（`README.md` / `demo/*.md` / 将来の `docs/**` など）に対して、
**正確性**と**更新運用**を最優先にするためのルールです。

## 1) 一次情報の裏取りと引用（最重要）
- Agent Framework の **API 名 / シグネチャ / 戻り値 / イベント名 / 例外 / 動作** を記述する場合は、必ず一次情報に当たる。
  - 原則: Microsoft Learn の該当ページ（API reference / user guide）
  - 併記: **参照 URL**（可能ならセクション見出しも）
- docs が「概念説明」だけで API 仕様が曖昧な場合は、以下も根拠として扱ってよい：
  - このリポジトリ内の実装・用例（`src/demo*.py` / `entities/**`）
  - `requirements.txt` の pinned バージョン（例: `agent-framework==...`）

## 2) pinned バージョンと “latest” の扱い
- このリポジトリは `requirements.txt` で agent-framework* を **pinned** している。
  - 記述は **原則 pinned 版で動くもの**を基準にする。
- Microsoft Learn の参照が “latest” の場合は、本文中に次を明記する：
  - 「このページは latest の可能性がある」
  - 「本リポジトリの pinned 版では差分が出る可能性がある」
  - 差分が疑われる場合は、**本リポジトリのコード側の挙動**を優先し、必要なら注記する

## 3) 手順書の書き方（再現性）
- 手順は **コマンド単位**で書く（1ステップ=1目的）。
- 各ステップに必ず **成功条件**を付ける：
  - 期待出力の例、またはチェック方法（例: `/health` が 200、特定ログが出る、など）
- 失敗時の分岐を “よくある落とし穴” として明示する（ネットワーク/DNS/権限/未設定env等）。

## 4) 環境変数と Secrets の記述
- secrets/keys を docs に貼らない。
- env var は「名前」「用途」「例（プレースホルダー）」を記載する。
- Dev Container / Codespaces では **空文字 env 注入**があり得るため、
  - `.env` を明示ロードし、未設定/空のみ補完する運用（本 repo の実装方針）を前提に書く。

## 5) 変化に強い書き方（メンテ運用）
- 固定しやすい事実（pinned version / ファイルパス / env var 名）と、変動しやすい事実（ポータル UI / 実行結果の内容）を分けて書く。
- 変動しやすい箇所には「例」「参考」と明記し、断定を避ける。
- 「このドキュメントが古くなったらまず見る場所」を入れる：
  - `requirements.txt`（pinned version）
  - `src/demo*.py`（動く用例）

## 6) 禁止事項
- 裏取りのない API 仕様を断定しない。
- “たぶん/おそらく” を根拠なしに放置しない（根拠を付けるか、記述を取り下げる）。
