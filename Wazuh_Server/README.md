# 🧩 Wazuh Server — Auditd 기반 엔드포인트 탐지 환경

이 저장소는 **Wazuh + auditd 기반 엔드포인트 보안 탐지 서버 구성**을 예시로 보여주는 프로젝트입니다.  
커스텀 룰을 통해 **권한 상승, 지속성 확보, 외부 연결 시도(curl/wget)** 등의 행위를 탐지하고, Discord Webhook으로 실시간 알림을 전송하도록 구성되어 있습니다.

---

## 📁 디렉터리 구조

```
📂 Wazuh_Server
 ├── 📁 docs/                     → 내부 탐지 흐름 및 아키텍처 설명
 │    └── README.md
 ├── 📁 logs/                     → 탐지 이벤트 샘플(alert.json)
 │    └── README.md
 │    └── downloader_exec_alert.json
 │    └── persistence_alert.json
 │    └── privilege_escalation_alert.json
 ├── docker-compose.yml           → Wazuh 서버 컨테이너 실행 설정
 ├── local_rules.xml              → 사용자 정의 탐지 룰 (auditd 기반)
 ├── ossec.conf                   → Wazuh 매니저 설정 파일
 ├── wazuh_discord.py             → Discord Webhook 연동 스크립트
 └── README.md                    → 현재 파일
```

---

## ⚙️ 주요 기능 요약

| 기능 | 설명 |
|------|------|
| **Auditd 연동** | 시스템 콜 수준의 이벤트(audit.log)를 수집하여 보안 이벤트 탐지 |
| **Custom Rule 매칭** | `/etc/passwd`, `crontab`, `curl/wget` 등의 행위를 탐지 |
| **Alerts 관리** | `alerts.json` 파일로 탐지 결과 저장 |
| **Discord 알림 연동** | Python 스크립트를 통한 실시간 알림 전송 |
| **Docker 기반 실행** | Wazuh Manager 환경을 컨테이너로 간편히 실행 가능 |

---

## 🧱 탐지 시나리오 (Custom Rules)

| Rule ID | 탐지 시나리오 | Audit Key | 심각도 |
|----------|----------------|------------|--------|
| `100100` | `/etc/passwd` 변경 시도 (권한 상승) | `passwd_changes` | 🔴 Critical |
| `100200` | `crontab` 추가/변경 감지 (지속성 확보) | `cron_changes` | 🟠 High |
| `100300` | `curl` 또는 `wget` 실행 감지 (다운로더 행위) | `downloader_exec` | 🟡 Medium |

---

## 🔗 주요 파일 설명

### 🧩 `ossec.conf`
- Wazuh 매니저 전체 설정 파일.
- 주요 섹션:
  - `<alerts>`: 로그 알림 레벨 설정  
  - `<integration>`: Discord 연동 설정 (Webhook, Rule ID 필터 등)
  - `<ruleset>`: 사용자 정의 룰 디렉터리 포함

### 🧱 `local_rules.xml`
- Auditd 로그(`audit.log`)를 기반으로 탐지하는 사용자 정의 룰 파일.
- 예시 룰:
  ```xml
  <rule id="100100" level="12">
    <if_group>audit</if_group>
    <match>passwd_changes</match>
    <description>Priv-Esc: /etc/passwd modified</description>
    <group>privilege_escalation,</group>
  </rule>
  ```

### 🐍 `wazuh_discord.py`
- `alerts.json` 파일을 감시하면서 새 탐지 이벤트 발생 시 Discord로 전송.
- Webhook URL은 `.env`로 분리해 보관 권장.

### 🐳 `docker-compose.yml`
- Wazuh Manager 컨테이너 구성 정의.
- 필요한 경우 `volumes:` 섹션을 수정해 설정 및 로그를 호스트에 영구 저장 가능.

---

## 🧠 탐지 흐름 요약

```
[auditd] → [Wazuh Agent] → [Wazuh Manager] → [alerts.json] → [Discord Webhook]
```

1. `auditd`가 시스템 이벤트 기록  
2. `Wazuh Agent`가 `audit.log`를 수집 후 Manager로 전송  
3. `analysisd`가 룰 매칭 후 alert 생성  
4. `integrator` 또는 `wazuh_discord.py`가 Discord로 전송

---

## 🚀 실행 방법 (요약)

```bash
# 1️⃣ 컨테이너 실행
docker-compose up -d

# 2️⃣ 설정 파일 반영 후 재시작
docker exec -it wazuh.manager /var/ossec/bin/wazuh-control restart

# 3️⃣ Discord Webhook 동작 테스트
python3 wazuh_discord.py
```

---

## 🧾 참고 자료
- [Wazuh 공식 문서](https://documentation.wazuh.com/)
- [Linux Auditd Rules Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/security_hardening/using-auditd-to-monitor-file-access-security-hardening)
- [Discord Webhook API](https://discord.com/developers/docs/resources/webhook)

---

> 📘 **작성자 노트**  
> 이 서버 구성은 포트폴리오용 예시로, 민감정보(Webhook, 내부 IP 등)는 모두 마스킹 후 공개를 권장합니다.
