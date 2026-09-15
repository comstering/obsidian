---
title: Debezium MySQL 커넥터 무증상 정지
type: article
status: draft
confidential: internal
tags: [kafka, kafka-connect, debezium, cdc, troubleshooting]
---

# Debezium MySQL 커넥터 무증상 정지

> Sources: 작업 기록; Debezium Documentation
> Raw: [Debezium Mysql connector](../../raw/kafka/debezium-mysql-connector.md)
> Updated: 2026-09-15

## Overview

Debezium MySQL 커넥터가 **살아 있다고 보고하면서 실제로는 완전히 멈추는** 상태를 겪었다.
상태 조회만으로는 감지되지 않는 유형이라 별도로 기록해 둔다.

## 증상

- 커넥터의 status는 **running & healthy**
- 그런데 CDC 이벤트가 나오지 않는다
- **heartbeat event 조차 발행되지 않는다** — 완전 정지

## 왜 위험한가

status 기반 헬스체크로는 잡히지 않는다. 커넥터가 스스로 정상이라고 보고하기 때문이다.

heartbeat까지 끊긴다는 점이 진단의 실마리다. **heartbeat 발행 여부를 별도 지표로 감시하면
status만 보는 것보다 먼저 감지할 수 있다** — status는 running인데 heartbeat 토픽에
메시지가 들어오지 않는 구간이 곧 이 상태다.

## 미기록 사항

> **Status: 근거 미비**
> raw 기록에 증상만 있고 원인·재현 조건·해결 방법이 없다. 아래가 비어 있다.
> - 어떤 조건에서 발생했는지 (binlog 위치, 스키마 변경, 네트워크 단절 등)
> - 어떻게 복구했는지 (커넥터 재시작 / task 재시작 / offset 조정)
> - 재발 방지로 무엇을 넣었는지
>
> 다음 인제스트 후보: `raw/incidents/2025-05-28-sendorder-outbox-not-issued.md`
> (메시지 미발행 장애 기록이라 같은 원인일 가능성이 있다)

## 참고

- https://debezium.io/documentation/reference/3.0/connectors/mysql.html
