# Example Logs — Wazuh / auditd 탐지 샘플

이 디렉터리에는 포트폴리오용으로 보관하는 **샘플 탐지 로그**가 들어 있습니다.
각 파일은 실제 탐지 이벤트를 포함하고, 재현 방법과 마스킹 기준도 함께 제공하고 있습니다.

## 포함된 파일
| 파일명 | Rule ID | 설명 |
|---|---:|---|
| `privilege_escalation_alert.json` | 100100 | **권한 상승** — `/etc/passwd` 수정 시도 감지 (Priv-Esc) |
| `persistence_alert.json` | 100200 | **지속성 확보** — 사용자/시스템 crontab 변경 감지 (cron_changes) |
| `downloader_alert.json` | 100300 | **다운로더 실행** — `wget`/`curl` 실행 감지 (downloader_exec) |

---

## 파일별 상세 설명

### 1) `privilege_escalation_alert.json` (Rule 100100)
- **무엇을 보여주는가**: 에이전트에서 `/etc/passwd` 파일에 접근(수정 또는 시도)할 때 발생한 audit 이벤트가 Wazuh에서 룰(100100)로 매칭되어 생성된 alert 예시.
- **중요 필드**: `timestamp`, `rule.id`, `rule.description`, `agent`, `data.audit.command`, `data.audit.exe`, `data.audit.key`
- **마스킹**: 에이전트명, IP, PID/PPID, 사용자명(auid), cwd 등 식별 가능한 값은 `REDACTED_*`로 대체.
- **재현(안전한 테스트)**:
  ```bash
  # 에이전트에서(일반 사용자 세션)
  sudo auditctl -w /etc/passwd -p wa -k passwd_changes
  # 권장 대안: 테스트 전용 파일 사용
  sudo auditctl -w /tmp/passwd_test -p wa -k passwd_changes
  sudo sh -c 'echo "#probe" >> /tmp/passwd_test'
  ```
  > 실제 `/etc/passwd` 수정은 시스템에 치명적일 수 있으니, 위 예시는 **테스트 전용 파일**(`/tmp/passwd_test`)로 먼저 확인하길 권장.

---

### 2) `persistence_alert.json` (Rule 100200)
- **무엇을 보여주는가**: crontab(시스템 또는 사용자) 수정 시 audit 로그에 `key=cron_changes`로 기록되고 Wazuh가 룰(100200)을 통해 alert을 생성한 예시.
- **중요 필드**: `data.audit.command` (예: `crontab`), `data.audit.exe`, `data.audit.key`, `data.audit.file`(CREATE/DELETE 등)
- **마스킹**: 파일 경로, 사용자명, PID 등은 `REDACTED_*`로 처리.
- **재현(권장 안전 방법)**:
  ```bash
  # 시스템 crontab에 안전한 항목을 추가
  echo '* * * * * root /bin/true #cron_probe' | sudo tee -a /etc/crontab
  # 또는 사용자 crontab 테스트
  ( crontab -l 2>/dev/null; echo '*/5 * * * * /bin/true #cron_probe' ) | crontab -
  ```

---

### 3) `downloader_alert.json` (Rule 100300)
- **무엇을 보여주는가**: 사용자가 `wget` 또는 `curl`을 실행했을 때 auditd가 `downloader_exec` 키로 기록하고 Wazuh가 룰(100300)로 매칭해 생성된 alert 예시.
- **중요 필드**: `data.audit.command` (`curl` / `wget`), `data.audit.exe`, `data.audit.execve` (argv), `data.audit.key`
- **마스킹**: 사용자명, 홈 디렉터리, PID 등은 `REDACTED_*`로 처리.
- **재현(권장 안전 방법)**:
  ```bash
  # 일반 사용자 세션에서 실행
  curl --version
  # 또는
  wget --version
  # 그 후 매니저에서 alerts.json에 항목이 생성되는지 확인
  ```

---

## 마스킹 기준
- `agent.name`, `agent.ip` 등 식별 가능한 모든 값은 `REDACTED_*`로 대체합니다.
- `cwd`, `file.name`, `pid`, `ppid`, `auid` 등 시스템 식별값은 제거 또는 `REDACTED` 처리합니다.
- 목적은 "탐지 컨텍스트(무엇이 감지됐는지)"를 보여주되, "사용자/호스트 식별" 정보는 공개하지 않는 것입니다.

---
