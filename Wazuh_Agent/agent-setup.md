# Wazuh Agent Setup Guide

## 🧩 개요
이 문서는 `auditd`와 `Wazuh Agent`를 연동하여 엔드포인트에서 발생하는 주요 보안 이벤트를 탐지하고, 이를 매니저로 전송하기 위한 최소 구성 가이드입니다.

---

## 📁 디렉터리 구조

```
Wazuh_Agent/
├── agent-setup.md
├── audit/
│   └── 99-endpoint.rules
└── ossec/
    └── localfile.conf
```

---

## 1️⃣ auditd 설정

### 설치
```bash
# RHEL, CentOS, Amazon Linux
sudo dnf install -y audit
sudo systemctl enable --now auditd

# Ubuntu, Debian
sudo apt update && sudo apt install -y auditd
sudo systemctl enable --now auditd
```

### 룰 설정
`/etc/audit/rules.d/10-endpoint.rules` 파일을 생성하고 아래 내용 추가:

```bash
# /etc/passwd 변경 탐지
-w /etc/passwd -p wa -k passwd_changes

# cron 변경 탐지
-w /var/spool/cron -p wa -k cron_changes
-w /etc/cron.d -p wa -k cron_changes

# wget, curl 실행 탐지
-a exit,always -F arch=b64 -S execve -F exe=/usr/bin/wget -F auid>=1000 -F success=1 -k downloader_exec
-a exit,always -F arch=b64 -S execve -F exe=/usr/bin/curl -F auid>=1000 -F success=1 -k downloader_exec
```

룰 적용:
```bash
sudo augenrules --load
sudo auditctl -l   # 룰 적용 여부 확인
```

---

## 2️⃣ Wazuh Agent 설정

### 설정 파일 추가
`/var/ossec/etc/ossec.conf`에 다음 블록 추가:

```xml
<localfile>
  <log_format>audit</log_format>
  <location>/var/log/audit/audit.log</location>
</localfile>
```

### 재시작
```bash
sudo systemctl restart wazuh-agent
```

### 확인
```bash
sudo tail -f /var/ossec/logs/ossec.log
```

---

## 3️⃣ 테스트 (안전한 방식)

> 실제 `/etc/passwd`는 수정하지 마세요. 테스트용 파일을 사용하세요.

```bash
sudo touch /tmp/passwd_test
sudo auditctl -w /tmp/passwd_test -p wa -k passwd_changes_test
sudo sh -c 'echo "#probe" >> /tmp/passwd_test'
curl --version
```

매니저 측 `alerts.json` 또는 Discord 알림에서 이벤트가 탐지되는지 확인하세요.

---

## 4️⃣ 재부팅 이후에도 룰 유지하기

`/etc/audit/rules.d/` 경로에 룰 파일을 두고 `augenrules`로 로드하면 자동 적용됩니다.

컨테이너 환경일 경우 다음 마운트 권장:
```yaml
volumes:
  - /var/log/audit:/var/log/audit
  - /var/ossec/etc:/var/ossec/etc
  - /var/ossec/logs:/var/ossec/logs
```

---

## 5️⃣ 문제 해결 빠른 점검 명령

| 점검 항목 | 명령어 |
|------------|---------------------------------------------|
| auditd 상태 | `sudo systemctl status auditd` |
| 룰 적용 여부 | `sudo auditctl -l` |
| audit 로그 | `sudo tail -n 50 /var/log/audit/audit.log` |
| agent 로그 | `sudo tail -n 50 /var/ossec/logs/ossec.log` |

---

## ✅ 요약
- **auditd**가 커널 이벤트를 로그화
- **Wazuh Agent**가 해당 로그를 수집 후 매니저로 전송
- **커스텀 룰**로 passwd/cron/wget/curl 탐지
- **테스트 시** 실제 시스템 파일은 수정하지 말 것
