<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockProbe">
</p>

<h1 align="center">DockProbe</h1>

<p align="center">
  <b>軽量なDocker監視ダッシュボード — 異常検知 & Telegram通知</b><br>
  コンテナ1つ。コマンド1つ。完全な可視性。
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <b>日本語</b> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache_2.0-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## DockProbeとは？

DockProbeは、単一コンテナで動作するセルフホスト型Docker監視ダッシュボードです。すべてのコンテナとホストマシンのCPU、メモリ、ネットワーク、ディスクメトリクスをリアルタイムに収集し、クリーンなダークテーマのWeb UIに表示します。

**GPU対応ホスト監視**は、CPU使用率、ホストメモリ、ディスク圧迫、ロードアベレージに加えて、NVIDIA GPUの温度と使用率をリアルタイムチャートで追跡します。MLワークロードやGPU集約型コンテナを実行している場合、DockProbeは別途GPUモニタリングツールをインストールすることなく、完全な可視性を提供します。

問題が発生すると、DockProbeが自動的に検知します。6つの異常検知ルールがCPUスパイク、メモリオーバーフロー、温度警告、ディスク圧迫、予期しない再起動、ネットワークサージを監視します。各アラートには**すぐに実行可能なコマンド付きの推奨対応**が含まれており、何が問題かだけでなく、正確に何をすべきかがわかります。アラートはTelegramに即座に送信され、ユーザーが気づく前に対応できます。

内蔵セキュリティスキャナーが5分ごとに16項目の自動チェックを実行し、コンテナの設定ミス、ネットワークの露出、ホストレベルのセキュリティ強化状態を確認します。

各コンテナにエージェントをインストールする必要はなく、外部データベースも不要で、複雑な設定もありません。Dockerソケットをマウントし、コマンド1つを実行するだけで、`https://localhost:9090`でDocker環境全体を一目で確認できます。外部からアクセスしたい場合は、Cloudflare Tunnelを標準サポートしており、ポートフォワーディングなしで安全なHTTPSアクセスが可能です。

---

## クイックスタート

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

以上です。対話型インストーラーが認証、Telegramアラート、HTTPSを自動設定し、`https://localhost:9090`を開きます。

> **必要要件:** Docker (Compose v2)、Git、OpenSSL

---

## ダッシュボードプレビュー

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="DockProbe ダッシュボード" width="800">
</p>

---

## 主な機能

| カテゴリ | 内容 |
|---------|------|
| **リアルタイムダッシュボード** | ダークテーマWeb UI、10秒自動更新、ソート可能なテーブル、Chart.jsチャート |
| **コンテナ監視** | CPU %、メモリ %、ネットワークI/O、ブロックI/O、再起動回数 |
| **ホスト監視** | CPU/GPU温度・使用率、メモリ使用量、ディスク使用量、ロードアベレージ |
| **異常検知** | 6つのルール＋推奨対応ガイド — CPUスパイク、メモリオーバーフロー、高温、ディスク満杯、再起動、ネットワークスパイク |
| **Telegramアラート** | 即時通知 + アラートタイプ毎30分クールダウン |
| **セキュリティ** | Basic Auth、レート制限 (5回失敗で60秒ロックアウト)、HTTPS |
| **セキュリティスキャナー** | 16項目の自動チェック (コンテナ/ホスト/ネットワーク)、5分間隔スキャン、重大度バッジ |
| **セッション管理** | アクティブ接続追跡、最大接続数設定、リアルタイムIP表示 |
| **パスワード管理** | ダッシュボードUIからユーザー名/パスワード変更 |
| **設定UI** | ダッシュボードから最大接続数をランタイム変更 |
| **接続方式** | 自己署名SSL (デフォルト) またはCloudflare Tunnel (ポート転送不要) |
| **軽量** | Pythonパッケージ4個、単一HTMLファイル、SQLite 7日間保持 |

---

## ダッシュボード構成

| セクション | 詳細 |
|-----------|------|
| セッションバー | ログインユーザー、IP、アクティブ接続数 / 最大制限 |
| ホストカード | CPU温度、GPU温度、CPU/GPU %、ホストメモリ、ディスク %、ロードアベレージ |
| コンテナテーブル | CPU/メモリ/ネットワークでソート可能、異常時に赤色表示 |
| チャート (5つ) | コンテナCPU・メモリ推移、ホストCPU/GPU %、ホスト温度・ロード |
| Dockerディスク | イメージ、ビルドキャッシュ、ボリューム、コンテナRWレイヤー |
| アラート履歴 | 直近24時間（タイムスタンプ付き） |

---

## 異常検知ルール

| ルール | 条件 | アクション |
|--------|------|-----------|
| コンテナCPU | >80% 3回連続 (30秒) | Telegram通知 + 赤色ハイライト |
| コンテナメモリ | >90% (limit比) | 即時アラート |
| ホストCPU温度 | >85°C | 即時アラート |
| ホストディスク | >90% 使用 | 即時アラート |
| コンテナ再起動 | restart_count増加 | 即時アラート |
| ネットワークスパイク | RX 10倍急増 + 100MB以上 | 即時アラート |

すべての閾値は環境変数で設定可能です。

各異常には具体的なコマンド付きの**実行可能な推奨対応**が含まれます：

| 異常 | 推奨対応の例 |
|------|-----------|
| CPUスパイク | `docker stats <name>` · `docker restart <name>` · `docker update --cpus=2 <name>` |
| メモリオーバーフロー | `docker stats <name>` · `docker update --memory=2g <name>` |
| 再起動ループ | `docker logs --tail 50 <name>` · `docker inspect <name>` |
| ネットワークスパイク | `docker logs --tail 50 <name>` · DDoSまたは予期しないトラフィックを確認 |
| 高温 | ファン/冷却システムを確認 · `sensors -u` で詳細確認 |
| ディスク満杯 | `docker system prune -f` · `docker builder prune -f` · `docker volume prune` |

---

## セキュリティスキャナー

DockProbeは5分ごとに16項目のセキュリティチェックを自動実行し、重大度バッジ付きの専用ダッシュボードセクションに結果を表示します。

| カテゴリ | チェック項目 |
|---------|------------|
| **コンテナ** (9) | 特権モード、root実行、危険なcapability、Dockerソケットマウント、機密パスマウント、読み取り専用rootfs、AppArmor/Seccomp無効、環境変数内のシークレット、メモリ/CPU制限なし |
| **ネットワーク** (3) | ホストネットワークモード、過剰なポート公開、SSHポート (22) 公開 |
| **ホスト** (4) | Dockerデーモンセキュリティオプション、カーネルASLR、IPフォワーディング、Linux Security Module状態 |

**重大度レベル:**
- 🔴 **重大** — 即座に対応が必要 (例: 特権モード、書き込み可能なDockerソケット)
- 🟡 **警告** — セキュリティ改善を推奨
- 🔵 **情報** — 参考情報
- 🟣 **利用不可** — 環境の制約によりチェック実行不可、有効化手順を表示

> ホストレベルのチェックにはボリュームマウントが必要です (`/proc:/host_proc:ro`, `/sys:/host_sys:ro`)。マウントされていない場合、該当チェックはセットアップ手順付きで**利用不可**と表示されます。

---

## アーキテクチャ

```
┌──────────────────────────────────────────────┐
│  DockProbe Container                         │
│                                              │
│  FastAPI + uvicorn (port 9090)               │
│  ├── collectors/                             │
│  │   ├── containers.py  (aiodocker)          │
│  │   ├── host.py        (/proc, /sys, GPU)   │
│  │   └── images.py      (system df)          │
│  ├── alerting/                               │
│  │   ├── detector.py    (6 ルール + 対応)    │
│  │   └── telegram.py    (httpx)              │
│  ├── security/                               │
│  │   └── scanner.py     (16 checks)          │
│  ├── storage/                                │
│  │   └── db.py          (SQLite WAL)         │
│  └── static/                                 │
│      └── index.html     (Chart.js)           │
│                                              │
│  マウントボリューム:                           │
│    docker.sock (ro), /sys (ro), /proc (ro),  │
│    nvidia-smi (ro), SQLite named volume      │
└──────────────────────────────────────────────┘
```

**依存関係 (4パッケージのみ):**
- `fastapi` — Webフレームワーク
- `uvicorn` — ASGIサーバー
- `aiodocker` — 非同期Docker APIクライアント
- `httpx` — 非同期HTTPクライアント (Telegram API)

---

## 設定

`.env`ファイルですべて設定:

```env
# 認証 (必須)
AUTH_USER=admin
AUTH_PASS=your-password

# Telegramアラート (任意)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# 閾値 (任意、デフォルト値表示)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# 接続制限 (任意、0 = 無制限)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (任意)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## 接続方式

### 方法1: ローカルネットワーク (自己署名SSL) — デフォルト

```bash
bash install.sh   # オプション1を選択
```

`https://localhost:9090` または `https://<サーバーIP>:9090` でアクセス

同じネットワーク内の他のデバイスからアクセスするには、サーバーのLAN IP（例: `https://192.168.1.100:9090`）を使用します。必要に応じて:
- ファイアウォールでポートを許可: `sudo ufw allow 9090/tcp`
- ブラウザで自己署名証明書の警告を承認

> **ブラウザの警告が表示される理由:** DockProbeはインストール時に生成された自己署名SSL証明書を使用します。信頼された認証局（CA）が発行したものではないため、ブラウザが「この接続はプライベートではありません」という警告を表示します。これは正常な動作です —「詳細設定」→「サイトへ進む」をクリックしてください。この警告をなくすには、信頼されたTLS証明書を自動提供するCloudflare Tunnel（方法3）をご利用ください。

### 方法2: ポートフォワーディングによるリモートアクセス

Cloudflareなしで外部からアクセスするには:

1. ルーターでポート9090をサーバーのLAN IPに転送
2. `https://<グローバルIP>:9090` でアクセス
3. グローバルIPが変わる場合はDDNSサービス（No-IP、DuckDNS等）を利用

> **注意:** ポートが直接公開されます。Basic Auth + HTTPSはデフォルトで有効ですが、セキュリティのためCloudflare Tunnel（方法3）を推奨します。

### 方法3: Cloudflare Tunnel (リモートアクセス推奨)

ポート転送不要、ファイアウォール変更不要、正式なTLS証明書 — どこからでも最も簡単で安全にアクセスする方法です。

```bash
bash install.sh   # オプション2を選択、トンネルトークンを入力
```

**セットアップ手順:**
1. [Cloudflare Zero Trust](https://one.dash.cloudflare.com)で無料アカウントを作成
2. **Networks** > **Tunnels** > **Create a tunnel** に移動
3. トンネル名を設定（例: `dockprobe`）してトンネルトークンをコピー
4. `bash install.sh` を実行してCloudflare Tunnelオプションを選択
5. トークンを入力
6. Cloudflareダッシュボードで**Public Hostname**を `http://localhost:9090` に設定
7. `https://your-domain.com` で正式なTLS証明書付きでアクセス

---

## APIエンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/` | GET | ダッシュボードHTML |
| `/api/current` | GET | 最新スナップショット (コンテナ + ホスト + イメージ + 異常) |
| `/api/history/{name}?hours=1` | GET | コンテナ時系列データ |
| `/api/history/host?hours=1` | GET | ホスト時系列データ |
| `/api/alerts?hours=24` | GET | アラート履歴 |
| `/api/session` | GET | 現在のユーザー、IP、アクティブ接続数 |
| `/api/settings` | GET/POST | ランタイム設定 (max_connections) |
| `/api/change-password` | POST | ユーザー名/パスワード変更 |
| `/api/health` | GET | ヘルスチェック (認証不要) |

---

## セキュリティ

- **Basic Auth** — 全エンドポイントで認証必須 (`/api/health` を除く)
- **レート制限** — ログイン5回失敗でIPごとに60秒ロックアウト
- **HTTPS** — 自己署名またはCloudflare Tunnel
- **接続数制限** — 最大同時接続ユーザー設定可能
- **読み取り専用マウント** — Docker socket、/sys、/proc すべてread-only
- **制御機能なし** — 監視専用、コンテナ操作不可

---

## 手動セットアップ

インストールスクリプトの代わりに手動設定する場合:

```bash
git clone https://github.com/deep-on/dockprobe.git
cd dockprobe

# .env 設定
cp .env.example .env
vi .env

# SSL証明書生成 (任意)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockprobe"

# 起動
docker compose up -d --build
```

---

## ライセンス

Apache License 2.0 — [LICENSE](LICENSE) を参照

**帰属条件:** 修正・再配布版にはDeepOnロゴと「Powered by DeepOn Inc.」の表記をUIに保持する必要があります。

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  <a href="https://deep-on.com">DeepOn Inc.</a> が開発
</p>
