# 🖥️ Wazuh Agent 설치 및 등록 가이드

이 문서는 **Ubuntu 22.04 LTS** 환경에서 **Wazuh Agent 4.13.1**을 설치하고, Wazuh Manager와 연결하는 절차를 설명합니다.  
(※ 다른 배포판은 [공식 문서](https://documentation.wazuh.com/) 참고)

---

## 1. 설치 준비

먼저 GPG 키와 리포지토리를 추가합니다.

```bash
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -
echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
sudo apt-get update
```

---

## 2. Wazuh Agent 설치

서버와 동일한 버전(4.13.1)으로 설치합니다.

```bash
sudo apt-get install wazuh-agent=4.13.1-1
```

설치 확인:

```bash
/var/ossec/bin/wazuh-agentd -V
# → Wazuh v4.13.1 출력되면 정상
```

---

## 3. Agent 설정 수정

Wazuh Server와 연결하기 위해 `ossec.conf`를 수정합니다.

```bash
sudo nano /var/ossec/etc/ossec.conf
```

예시 설정:

```xml
<ossec_config>
  <client>
    <server>
      <address><WAZUH_SERVER_IP></address>
      <port>1514</port>
      <protocol>tcp</protocol>
    </server>
  </client>
</ossec_config>
```

> `<WAZUH_SERVER_IP>` 부분을 실제 매니저 서버 IP로 변경하세요.

---

## 4. Manager에서 Agent 등록

Wazuh Manager 컨테이너에서 다음 명령어 실행:

```bash
docker exec -it single-node-wazuh.manager-1 /var/ossec/bin/manage_agents
```

- `A` → Add agent  
- 이름, 에이전트 IP 입력  
- 키 생성 후 복사  

---

## 5. Agent에 키 등록

엔드포인트 VM에서:

```bash
sudo /var/ossec/bin/manage_agents
```

- `I` → Import key  
- 앞에서 복사한 키 전체 붙여넣기  
- 저장 후 종료

---

## 6. Agent 서비스 실행

```bash
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent
sudo systemctl status wazuh-agent
```

---

## 7. 연결 확인

1. **Dashboard → Agents 메뉴**  
   - 새로 등록한 에이전트가 `Active (●)`로 표시되는지 확인  

2. **Manager 로그 확인**  

```bash
docker logs -n 100 single-node-wazuh.manager-1 | grep agent
```

---

## ✅ 설치 완료

이제 에이전트가 정상적으로 Wazuh Manager와 연결되어 이벤트를 전송합니다.  
추가적으로 osquery, auditd 등을 연동하여 엔드포인트 보안 모니터링을 확장할 수 있습니다.
