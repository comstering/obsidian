---
title: MSK IAM 인증과 JVM 한정 제약
type: article
status: verified
confidential: internal
tags: [kafka, msk, aws, authentication, iam]
---

# MSK IAM 인증과 JVM 한정 제약

> Sources: 작업 기록, 2025-05-29; DataHub 구축 기록
> Raw: [AWS MSK increase partitions](../../raw/kafka/aws-msk-increase-partitions.md); [datahub kafka](../../raw/kafka/datahub-kafka.md)
> Updated: 2026-09-15

## Overview

MSK의 `AWS_MSK_IAM` 인증은 편리하지만 **JVM 기반 클라이언트에서만 쓸 수 있다.**
설정값이 자바 클래스명(`IAMLoginModule`, `IAMClientCallbackHandler`)을 직접 가리키기 때문이다.
이 제약은 문서를 읽을 때보다 **파이썬 컴포넌트를 붙일 때 갑자기 드러난다.**

## 클라이언트 설정

`client.properties` 에 네 줄을 넣는다.

```properties
security.protocol=SASL_SSL
sasl.mechanism=AWS_MSK_IAM
sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
sasl.client.callback.handler.class=software.amazon.msk.auth.iam.IAMClientCallbackHandler
```

그리고 인증 라이브러리를 받아 CLASSPATH에 올린다.

```bash
wget https://github.com/aws/aws-msk-iam-auth/releases/download/v2.3.2/aws-msk-iam-auth-2.3.2-all.jar
```

`sasl.jaas.config` 와 `sasl.client.callback.handler.class` 값이 전부 자바 클래스 경로다.
**여기가 JVM 종속이 생기는 지점이다.**

## 실제로 막힌 사례 — DataHub

DataHub를 MSK에 붙이려 할 때 컴포넌트별로 결과가 갈렸다.

| 컴포넌트 | 기반 | AWS_MSK_IAM |
|---|---|---|
| front-end, gms, mae, mce | java / spring | 가능 |
| **datahub-actions** | **python** | **불가** |

GMS에서 ingestion을 할 때 `datahub-actions` 를 쓰는데, 이게 파이썬 기반이라
`AWS_MSK_IAM` 인증이 안 된다. **`SASL_SSL` / `SCRAM` 방식만 가능하다.**

즉 클러스터 하나에 인증 방식 두 가지를 열어야 하거나, 파이썬 컴포넌트 때문에
전체를 SCRAM으로 내려야 하는 선택이 생긴다.

## 당시 결정 — 임시 우회

DataHub prerequisites의 kafka chart를 써서 **k8s에 kafka를 임시 배포**하는 쪽을 택했다.
MSK를 쓸지 k8s 배포본을 계속 쓸지는 **미결로 남겨둔 상태**다.

> **Status: 미결** (2026-09-15)
> 최종적으로 MSK로 갔는지, k8s kafka로 굳었는지가 raw에 기록되지 않았다.
> 이 판단이 확정되면 이 절을 갱신해야 한다.

## See Also

- [Kafka 토픽 파티션 수 늘리기](kafka-partition-increase.md)
