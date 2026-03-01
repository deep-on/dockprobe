<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Docker 컨테이너 모니터링 대시보드 — 이상 탐지 & 텔레그램 알림</b><br>
  컨테이너 하나. 명령어 하나. 완벽한 가시성.
</p>

<p align="center">
  <a href="README.md">English</a> | <b>한국어</b> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## 빠른 시작

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

끝. 대화형 설치가 인증, 텔레그램 알림, HTTPS를 자동 설정합니다. `https://localhost:9090`에 접속하세요.

> **필요 조건:** Docker (Compose v2), Git, OpenSSL

---

## 대시보드 미리보기

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="DockWatch 대시보드" width="800">
</p>

---

## 주요 기능

| 카테고리 | 내용 |
|---------|------|
| **실시간 대시보드** | 다크 테마 웹 UI, 10초 자동 갱신, 정렬 가능한 테이블, Chart.js 차트 |
| **컨테이너 모니터링** | CPU %, 메모리 %, 네트워크 I/O, 블록 I/O, 재시작 횟수 |
| **호스트 모니터링** | CPU/GPU 온도, 디스크 사용량, 로드 평균 |
| **이상 탐지** | 6가지 규칙 — CPU 폭주, 메모리 초과, 고온, 디스크 부족, 재시작, 네트워크 스파이크 |
| **텔레그램 알림** | 즉시 알림 + 알림 유형별 30분 쿨다운 |
| **보안** | Basic Auth, 레이트 리밋 (5회 실패 시 60초 차단), HTTPS |
| **세션 관리** | 접속자 추적, 최대 접속 수 제한, 실시간 IP 표시 |
| **비밀번호 관리** | 대시보드 UI에서 사용자명/비밀번호 변경 |
| **설정 UI** | 대시보드에서 최대 접속 수 실시간 변경 |
| **접속 방식** | 자체 서명 SSL (기본) 또는 Cloudflare Tunnel (포트포워딩 불필요) |
| **경량** | Python 패키지 4개, 단일 HTML 파일, SQLite 7일 보관 |

---

## 대시보드 구성

| 섹션 | 내용 |
|------|------|
| 세션 바 | 로그인 사용자, IP, 활성 접속 수 / 최대 제한 |
| 호스트 카드 | CPU 온도, GPU 온도, 디스크 %, 로드 평균 |
| 컨테이너 테이블 | CPU/메모리/네트워크 기준 정렬, 이상 시 빨간색 표시 |
| 차트 (4개) | 컨테이너 CPU·메모리 추이, 호스트 온도·로드 |
| Docker 디스크 | 이미지, 빌드 캐시, 볼륨, 컨테이너 RW 레이어 |
| 알림 이력 | 최근 24시간 타임스탬프 포함 |

---

## 이상 탐지 규칙

| 규칙 | 조건 | 동작 |
|------|------|------|
| 컨테이너 CPU | >80% 3회 연속 (30초) | 텔레그램 + 대시보드 빨간색 |
| 컨테이너 메모리 | >90% (limit 대비) | 즉시 알림 |
| 호스트 CPU 온도 | >85°C | 즉시 알림 |
| 호스트 디스크 | >90% 사용 | 즉시 알림 |
| 컨테이너 재시작 | restart_count 증가 | 즉시 알림 |
| 네트워크 스파이크 | RX 10배 급증 + 100MB 이상 | 즉시 알림 |

모든 임계값은 환경변수로 조정 가능합니다.

---

## 아키텍처

```
┌─────────────────────────────────────────┐
│  DockWatch Container                    │
│                                         │
│  FastAPI + uvicorn (port 9090)          │
│  ├── collectors/                        │
│  │   ├── containers.py  (aiodocker)     │
│  │   ├── host.py        (/proc, /sys)   │
│  │   └── images.py      (system df)     │
│  ├── alerting/                          │
│  │   ├── detector.py    (상태 머신)      │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite WAL)    │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  마운트 볼륨:                             │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite named volume      │
└─────────────────────────────────────────┘
```

**의존성 (4개만):**
- `fastapi` — 웹 프레임워크
- `uvicorn` — ASGI 서버
- `aiodocker` — 비동기 Docker API 클라이언트
- `httpx` — 비동기 HTTP 클라이언트 (텔레그램 API)

---

## 설정

`.env` 파일로 모든 설정을 관리합니다:

```env
# 인증 (필수)
AUTH_USER=admin
AUTH_PASS=your-password

# 텔레그램 알림 (선택)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# 임계값 (선택, 기본값 표시)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# 최대 접속 수 (선택, 0 = 무제한)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (선택)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## 접속 방식

### 방법 1: 로컬 모드 (자체 서명 SSL) — 기본

```bash
bash install.sh   # 옵션 1 선택
```

`https://localhost:9090` 또는 `https://<서버IP>:9090`으로 접속

### 방법 2: Cloudflare Tunnel (포트포워딩 불필요)

```bash
bash install.sh   # 옵션 2 선택, 터널 토큰 입력
```

공유기 설정 없이 외부 HTTPS 접속 — 정식 인증서 자동 적용

---

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 대시보드 HTML |
| `/api/current` | GET | 최신 스냅샷 (컨테이너 + 호스트 + 이미지 + 이상탐지) |
| `/api/history/{name}?hours=1` | GET | 컨테이너 시계열 데이터 |
| `/api/history/host?hours=1` | GET | 호스트 시계열 데이터 |
| `/api/alerts?hours=24` | GET | 알림 이력 |
| `/api/session` | GET | 현재 사용자, IP, 활성 접속 수 |
| `/api/settings` | GET/POST | 런타임 설정 (max_connections) |
| `/api/change-password` | POST | 사용자명/비밀번호 변경 |
| `/api/health` | GET | 헬스체크 (인증 불필요) |

---

## 보안

- **Basic Auth** — 모든 엔드포인트 인증 필수 (`/api/health` 제외)
- **레이트 리밋** — 로그인 5회 실패 시 IP별 60초 차단
- **HTTPS** — 자체 서명 또는 Cloudflare Tunnel
- **접속 수 제한** — 최대 동시 접속자 설정 가능
- **읽기 전용 마운트** — Docker 소켓, /sys, /proc 모두 read-only
- **제어 기능 없음** — 모니터링 전용, 컨테이너 조작 불가

---

## 수동 설치

설치 스크립트 대신 직접 설정하려면:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# .env 설정
cp .env.example .env
vi .env

# SSL 인증서 생성 (선택)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# 시작
docker compose up -d --build
```

---

## 라이선스

MIT License — [LICENSE](LICENSE) 참조

**귀속 조건:** 수정 및 재배포 시 DeepOn 로고와 "Powered by DeepOn Inc." 문구를 UI에 유지해야 합니다.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  <a href="https://deep-on.com">DeepOn Inc.</a>에서 만들었습니다.
</p>
