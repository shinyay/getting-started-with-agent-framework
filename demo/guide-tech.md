# Agent Framework 学習ガイド（技術説明）

## セッションが本当に言いたいこと

この回は単に「エージェントを作る方法」ではなく、**PoC的なエージェント遊びを、運用できる“業務システム”に引き上げるための設計原則**を提示しています。イベント説明自体も「A2A互換エージェント設計」「MCPツールによるセキュアなオーケストレーション」「エンタープライズ品質でのビルド/デプロイ/スケール」を明確に掲げています。([Microsoft Developer][1])

この前提に立つと、後半デモの並び（単体→ツール→MCP→構造化→ワークフロー→A2A）が、単なる段階学習ではなく、

> **“LLMの不確実性を、工学的に扱える形に落とす”**
> ＝「契約（スキーマ）」「境界（プロトコル）」「観測（トレース）」「継続（状態）」で囲う

というストーリーになっているのが見えてきます。

---

## Microsoft Agent Frameworkをどう位置づけるべきか

**Microsoft Agent Framework**は、.NET / Python対応のOSSの開発キットで、Semantic KernelとAutoGenの考え方を統合しつつ、ワークフローや状態管理などを強化した“次世代の統合基盤”として説明されています。([Microsoft Learn][2])
ドキュメント上も、機能を大きく **AI agents** と **Workflows** に分けています：

* **AI agents**：入力を受け、意思決定し、ツールやMCPサーバーを呼び、応答する
* **Workflows**：複数エージェント/関数をグラフで繋ぎ、型安全なルーティング、ネスト、チェックポイント、Human-in-the-loopの要求/応答などを扱う ([Microsoft Learn][2])

そして重要なのは、「なぜ別枠で Workflows があるのか」です。ここに**設計思想の核心**があります。

---

## 深掘り：本番運用に必要な概念を“4つの設計軸”に落とす

あなたが既にまとめている「標準プロトコル / 観測可能性 / 長期実行 / 状態 / アイデンティティ」を、私は次の4軸で捉えると腹落ちが速いと思います。

### 1) 境界：どこまでを“エージェントに任せてよい”のか

エージェントは賢いですが、**システム境界を越える瞬間（外部データアクセス、外部API、他エージェント呼び出し）が最も危険**です。
Agent Frameworkは、MCPやA2Aのような標準プロトコルを採用して「境界」を明示的にし、さらに“第三者サーバー/第三者エージェントと連携するならデータ境界や保持ポリシーは自分で責任を持て”という注意喚起までドキュメントに書いています。([Microsoft Learn][2])

> 洞察：**“境界が明示されている設計”は、AIの賢さより重要**
> 事故の大半は推論ミスより「境界越え（漏洩・誤操作・権限逸脱）」で起きます。
> MCP/A2Aは、まさに境界をプロトコルとして固定する試みです。

### 2) 契約：LLM出力を“プログラムが扱える形”にする

本番でのLLMは「テキスト生成器」ではなく、**下流の自動処理を駆動する“非決定的コンポーネント”**です。
この非決定性を受け止める最短ルートが **Structured Output（スキーマ）**。Agent Frameworkでは、.NET側は型からJSON Schemaを生成してresponse formatに指定でき、Python側はPydanticモデルを指定して構造化出力を得られることが具体例で示されています。([Microsoft Learn][3])

> 洞察：構造化出力は「便利機能」ではなく、**エージェントを“自動化部品”に変える変換器**
> “自然文→自動化”をやるなら、最終的に必要なのは文章ではなく **契約されたデータ**です。
> ここを押さえると、デモ4が“急に堅くなる”理由が説明できます。

### 3) 継続：時間をまたぐ（長期実行・中断・再開・監査）

業務は「一回の応答」で終わりません。承認待ち、外部システム待ち、夜間バッチ、段階的な合意…
そのために Workflows は **チェックポイント**を提供し、スーパーステップの終わりで状態を保存し、後から復元して再開できる設計になっています。([Microsoft Learn][4])
これは、単なる“便利な保存”ではなく、**「エージェントをプロセスとして運用する」ための最低条件**です。

> 洞察：長期実行の本質は「待つ」ではなく、**“中断可能性”と“再開可能性”**
> 人が介入する/外部依存がある、の時点で必ず止まります。
> 止まっても壊れない設計（チェックポイント、状態管理、再試行、冪等性）が主戦場になります。

### 4) 観測と統制：エージェントを“デバッグ可能な対象”にする

LLMはブラックボックス寄りなので、本番運用では **「何が起きたかを説明できる」ことが信頼の前提**です。
Agent FrameworkはOpenTelemetryでトレースを出せることを前提にしており、チュートリアルでも「対話がログ/エクスポートされる」ようにOtelを有効化する方法が示されています。([Microsoft Learn][5])
さらに DevUI は、エージェント/ワークフローを視覚的にデバッグ・反復するためのサンプルアプリで、OpenAI互換APIも持ちます。ただし明確に「運用環境向けではない」と書かれています。([Microsoft Learn][6])
DevUIのトレース機能は、Agent Frameworkが吐いたOpenTelemetryスパンを集めて表示するだけで、独自スパンを作るわけではない、という点もポイントです。([Microsoft Learn][7])

> 洞察：AI運用の競争力は“プロンプト”より**観測と統制（コントロールプレーン）**に出る
> 良いエージェントは「賢い」より「追跡できる」「止められる」「再現できる」「改善サイクルが回る」。

---

## 核心の深掘り：MCPは何を解決しているのか

MCP（Model Context Protocol）は、LLMアプリと外部ツール/データソースを繋ぐための**オープンプロトコル**で、JSON-RPC 2.0で **Host / Client / Server** の三者が通信します。([Model Context Protocol][8])
さらに、LSP（Language Server Protocol）のように「エコシステム全体での拡張」を標準化したい、という思想が明記されています。([Model Context Protocol][8])

### MCPの“本質的価値”はツール連携ではなく「責任分界」

MCPが大事なのは「ツールを呼べる」からではなく、**責任の境界と同意フローを設計に埋め込める**からです。
仕様は、ユーザー同意・データプライバシー・ツール安全性・サンプリング制御などを“原則”として強く打ち出し、Hostが同意と制御を担うことを求めています。([Model Context Protocol][8])

> 洞察：MCPは「ツール市場」ではなく、**“境界を守るための標準化”**
> 企業利用で怖いのは「どんなツールがあるか」ではなく、
> 「どのデータが」「どこへ」「誰の同意で」流れるか。
> MCPはここを“プロトコル要件”として言語化しているのが強い。

### Agent FrameworkでのMCP：実装上のポイント

Agent FrameworkはMCPサーバーとの統合をサポートし、.NET版は公式MCP C# SDKと併用して、MCPツール一覧取得→AIFunction化→関数呼び出しとして利用、という流れがガイドで示されています。([Microsoft Learn][9])
ここで登壇で刺さるポイントは：

* **MCPサーバーが“ツール実装の独立単位”になる**（別言語・別チームで作ってもよい）
* エージェント側は「そのツールを関数として扱う」だけでよい
* 境界（ローカル/リモート、権限、同意）をHost側で管理できる ([Model Context Protocol][8])

---

## 核心の深掘り：A2Aは何を解決しているのか

A2A（Agent-to-Agent）は、Agent Framework側のドキュメントでも「標準化された通信」「エージェントカードによる検出」「長時間プロセス（タスク）」「クロスフレームワーク相互運用」を支える、と明示されています。([Microsoft Learn][10])

A2A公式ドキュメントでは、A2Aが **Google 発で、現在は Linux Foundation に寄贈された“オープン標準”だと説明され、MCPと補完関係にあることも明記されています。([a2a-protocol.org][11])

### A2Aの価値：内部を共有せずに協業できる

A2Aの良さは「複数エージェント」それ自体ではなく、**別チーム/別ベンダーが作ったエージェントを、内部実装を明かさずに合成できる**点です。([a2a-protocol.org][11])
これは企業の現実（組織境界、知財、責任、監査）に合っています。

> 洞察：A2Aは“マルチエージェント”ではなく、**“マルチ組織エージェント”**のためのプロトコル
> つまり技術というより、組織論・契約論を前に進める仕掛けです。
> ここを言語化できると、A2Aデモの説得力が上がります。

### Agent FrameworkでA2Aを語るときの要点

* Agent Frameworkには、ASP.NET CoreでA2Aエンドポイントとしてエージェントを公開する統合が用意され、AgentCardも構成できる、という説明がドキュメントにあります。([Microsoft Learn][10])
* そして実運用で最大の論点は認証です。Foundry側のA2A認証ドキュメントには、**プロジェクトのマネージドID**での認証、あるいは **OAuth identity passthrough**（ユーザーがサインインして同意→そのユーザーの資格情報でA2A先へ接続）の説明が具体的にあります。([Microsoft Learn][12])

> 洞察：A2Aの“難しさ”は通信ではなく **Identityの継承**
> 「この呼び出しは誰の権限で？」を曖昧にすると、監査も責任も破綻します。
> identity passthrough は、ここを正面から解こうとしている構造です。([Microsoft Learn][12])

---

## あなたの登壇で“深い洞察”として刺さるまとめ方

最後に、セッション全体を一言でまとめるなら私はこう言います：

### 洞察1：Agent Frameworkは「賢さ」より「運用できる不確実性」を売っている

LLMが賢いのは前提。その上で、

* スキーマで縛る（契約）([Microsoft Learn][3])
* チェックポイントで継続する（時間）([Microsoft Learn][4])
* OTelで追跡する（観測）([Microsoft Learn][5])
* MCP/A2Aで境界を固定する（責任分界）([Model Context Protocol][8])
  という**ソフトウェア工学の武器**で、エージェントを“プロダクト”に変える話です。([Microsoft Learn][2])

### 洞察2：Workflowsは「マルチエージェントのため」ではなく「業務のため」

Workflowsは“賢い会話”を増幅する装置ではなく、**業務プロセスに必要な制御**（型安全・分岐・並列・外部統合・Human-in-the-loop・チェックポイント）を与えるものです。([Microsoft Learn][13])
この捉え方にすると、「なぜコードファーストなのか」の論拠が一段強くなります（GUIで業務の制御を全部表現すると破綻しやすい）。

### 洞察3：標準プロトコルは“エージェントのインターネット化”を起こす

* MCPは「ツールの標準接続」([Model Context Protocol][8])
* A2Aは「エージェント同士の標準通信」([Microsoft Learn][10])
  この2つが揃うと、エージェントは“アプリの内部部品”から、**ネットワーク上で交換可能なサービス**に変わります。
  これが本当に起きると、組織内で「経理エージェント」「購買エージェント」「法務エージェント」をA2Aで公開し、必要なときだけ呼ぶ、という **エージェントのマイクロサービス化**が現実味を帯びます。

---

## 追加の注意点（あなたのデモで事故りやすい所）

あなたが同じセッションをする場合、ここを“落とし穴”として言及するとプロっぽさが出ます。

* **DevUIは開発用サンプルであり運用向けではない**（誤解されやすい）([Microsoft Learn][6])
* **Web検索/グラウンディング系ツールはデータ境界と規約が絡む**
  FoundryのWeb検索ツール（プレビュー）は、SLAなしで運用非推奨、Bing検索/カスタム検索を使うこと、そしてDPAが適用されない/地理的・コンプライアンス境界外にデータ転送が起き得る、などが明記されています。([Microsoft Learn][14])
  → “最新情報が取れる”の裏側には、必ず**契約・規約・データ越境**がある。

---

[1]: https://developer.microsoft.com/en-us/reactor/events/26581/ "Advanced Multi-Agent Orchestration with SWE Agents and  Microsoft Agent Framework | Microsoft Reactor"
[2]: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview "Introduction to Microsoft Agent Framework | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output "Producing Structured Output with agents | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints "Microsoft Agent Framework Workflows - Checkpoints | Microsoft Learn"
[5]: https://learn.microsoft.com/ja-jp/agent-framework/tutorials/agents/enable-observability "エージェントの可観測性の有効化 | Microsoft Learn"
[6]: https://learn.microsoft.com/ja-jp/agent-framework/user-guide/devui/ "DevUI の概要 | Microsoft Learn"
[7]: https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/tracing "DevUI Tracing & Observability | Microsoft Learn"
[8]: https://modelcontextprotocol.io/specification/2025-11-25 "Specification - Model Context Protocol"
[9]: https://learn.microsoft.com/ja-jp/agent-framework/user-guide/model-context-protocol/using-mcp-tools "MCP ツールの使用 | Microsoft Learn"
[10]: https://learn.microsoft.com/ja-jp/agent-framework/user-guide/hosting/agent-to-agent-integration "A2A 統合 | Microsoft Learn"
[11]: https://a2a-protocol.org/latest/ "A2A Protocol"
[12]: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-to-agent-authentication?view=foundry "Agent2Agent (A2A) authentication - Microsoft Foundry | Microsoft Learn"
[13]: https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/overview "Microsoft Agent Framework Workflows | Microsoft Learn"
[14]: https://learn.microsoft.com/ja-jp/azure/ai-foundry/agents/how-to/tools/web-search?view=foundry "Foundry Agent Service で Web 検索ツールを使用する - Microsoft Foundry | Microsoft Learn"
