#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import signal
import requests
from typing import Optional, Dict, Any, Iterable

# ===== 설정 =====
ALERT_FILE = os.environ.get("WAZUH_ALERT_FILE", "/var/ossec/logs/alerts/alerts.json")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "https://discord.com/api/webhooks/여기에_새웹훅")
MIN_LEVEL = int(os.environ.get("MIN_LEVEL", "7"))  # 이 레벨 이상만 전송
# 특정 룰만 보낼 때 (예: "100100"); 비우면 전체 허용
MATCH_RULE_IDS = set(filter(None, os.environ.get("MATCH_RULE_IDS", "").split(",")))
# 특정 그룹만 보낼 때 (예: "privilege_escalation,syscheck_file"); 비우면 전체 허용
MATCH_GROUPS = set(filter(None, os.environ.get("MATCH_GROUPS", "").split(",")))
SEND_INTERVAL = float(os.environ.get("SEND_INTERVAL", "0.1"))  # 전송 사이 텀(초)

# 상태(중복 방지)
last_sent_id: Optional[str] = None
running = True


def graceful_exit(signum, frame):
    global running
    running = False

for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, graceful_exit)


def fits_filters(alert: Dict[str, Any]) -> bool:
    """레벨/룰ID/그룹 필터 검사"""
    rule = alert.get("rule", {}) or {}
    level = int(rule.get("level", 0) or 0)
    if level < MIN_LEVEL:
        return False

    if MATCH_RULE_IDS:
        rid = str(rule.get("id", ""))
        if rid not in MATCH_RULE_IDS:
            return False

    if MATCH_GROUPS:
        groups: Iterable[str] = rule.get("groups", []) or []
        if not any(g in MATCH_GROUPS for g in groups):
            return False

    return True


def format_message(alert: Dict[str, Any]) -> str:
    """디스코드 텍스트 메시지 생성(2000자 제한 대응)"""
    rule = alert.get("rule", {}) or {}
    agent = (alert.get("agent", {}) or {}).get("name", "unknown")
    ts = alert.get("timestamp", "no-time")
    desc = str(rule.get("description", "no-desc"))
    rid = str(rule.get("id", "no-id"))
    level = int(rule.get("level", 0) or 0)

    tag = "[CRITICAL]" if level >= 12 else "[HIGH]" if level >= 8 else "[MEDIUM]" if level >= 5 else "[INFO]"
    lines = [
        f"{tag}",
        f"• Time: {ts}",
        f"• Agent: {agent}",
        f"• Rule: {rid}",
        f"• Level: {level}",
        f"• Desc: {desc}",
    ]
    msg = "\n".join(lines)
    # 디스코드 2000자 제한 안전 여유
    return msg[:1900]


def send_discord(msg: str) -> None:
    """디스코드로 전송. 429(레이트리밋) 처리 포함."""
    if not WEBHOOK or not WEBHOOK.startswith("https://"):
        raise RuntimeError("WEBHOOK 미설정 또는 형식 오류")

    payload = {"content": msg}
    while True:
        r = requests.post(WEBHOOK, json=payload, timeout=10)
        if r.status_code == 204 or r.status_code == 200:
            return
        if r.status_code == 429:
            retry = r.json().get("retry_after", 1)
            time.sleep(float(retry) / 1000.0 if retry > 5 else 1.0)
            continue
        # 기타 에러는 짧은 대기 후 한 번 더 시도, 그래도 실패면 로그 출력
        if 500 <= r.status_code < 600:
            time.sleep(1.0)
            continue
        raise RuntimeError(f"Discord send failed: {r.status_code} {r.text[:200]}")


def tail_follow(path: str):
    """alerts.json tail (파일 로테이션 대응: inode 바뀌면 자동 reopen)"""
    global running
    # 파일이 생길 때까지 대기
    while running and not os.path.exists(path):
        time.sleep(0.5)

    f = open(path, "r", encoding="utf-8", errors="replace")
    f.seek(0, os.SEEK_END)
    st_ino = os.fstat(f.fileno()).st_ino

    try:
        while running:
            line = f.readline()
            if line:
                yield line
                continue

            # 로테이션 감지: inode 변경 시 reopen
            try:
                cur_ino = os.stat(path).st_ino
            except FileNotFoundError:
                cur_ino = None

            if cur_ino and cur_ino != st_ino:
                try:
                    f.close()
                except Exception:
                    pass
                f = open(path, "r", encoding="utf-8", errors="replace")
                st_ino = os.fstat(f.fileno()).st_ino
                f.seek(0, os.SEEK_END)
            time.sleep(0.2)
    finally:
        try:
            f.close()
        except Exception:
            pass


def main():
    global last_sent_id
    print(f"[+] Forwarder start. file={ALERT_FILE}, min_level={MIN_LEVEL}, rule_ids={','.join(MATCH_RULE_IDS) or '-'}, groups={','.join(MATCH_GROUPS) or '-'}")

    for line in tail_follow(ALERT_FILE):
        try:
            alert = json.loads(line)
        except Exception:
            continue

        # 중복 방지: 같은 id면 건너뜀
        aid = str(alert.get("id", ""))
        if last_sent_id is not None and aid == last_sent_id:
            continue

        if not fits_filters(alert):
            last_sent_id = aid
            continue

        msg = format_message(alert)
        try:
            send_discord(msg)
            print(f"[sent] id={aid} rule={alert.get('rule',{}).get('id')} level={alert.get('rule',{}).get('level')} agent={(alert.get('agent',{}) or {}).get('name')}")
        except Exception as e:
            print(f"[error] send failed: {e}")
        finally:
            last_sent_id = aid
            time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
