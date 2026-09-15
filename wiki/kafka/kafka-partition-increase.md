---
title: Kafka 토픽 파티션 수 늘리기
type: article
status: verified
confidential: internal
tags: [kafka, msk, aws, operations]
---

# Kafka 토픽 파티션 수 늘리기

> Sources: 작업 기록, 2025-05-29; Apache Kafka
> Raw: [AWS MSK increase partitions](../../raw/kafka/aws-msk-increase-partitions.md)
> Updated: 2026-09-15

## Overview

Apache Kafka native tool(`kafka-topics.sh`)로 처리한다. MSK에서는 IAM 인증을 붙이느라
`--command-config` 와 CLASSPATH가 추가로 필요하다는 점만 다르다.

## 준비

1. [Apache Kafka를 내려받는다](https://kafka.apache.org/downloads) — 번들에 `kafka-topics.sh` 가 들어 있다
2. MSK에서 SASL_SSL/IAM을 쓴다면 `client.properties` 와 인증 jar를 준비한다
   → [MSK IAM 인증과 JVM 한정 제약](msk-iam-authentication.md)

## 실행

일반 Kafka:

```bash
./bin/kafka-topics.sh \
  --bootstrap-server {broker-endpoint} \
  --alter \
  --topic my-topic \
  --partitions 12 \
  --command-config client.properties
```

MSK IAM 인증을 쓸 때는 CLASSPATH에 인증 jar를 올려서 실행한다:

```bash
CLASSPATH=aws-msk-iam-auth-2.3.2-all.jar ./bin/kafka-topics.sh \
  --bootstrap-server b-1.my-msk-cluster.abcde.c2.kafka.amazonaws.com:9098 \
  --alter \
  --topic my-topic \
  --partitions 12 \
  --command-config client.properties
```

IAM 인증 브로커는 포트 **9098** 을 쓴다.

## 짚어둘 것

`--partitions` 는 **늘리는 것만 된다.** 줄이려면 토픽을 다시 만들어야 한다.

파티션을 늘리면 **키 기반 파티셔닝의 대상 파티션이 바뀐다.** 같은 키가 이전과 다른
파티션으로 가게 되므로, 키 단위 순서를 전제한 컨슈머가 있다면 영향을 받는다.

> **Status: 근거 미비**
> 위 두 문단은 Kafka의 일반적 성질이며 raw 작업 기록에는 없다.
> 당시 이 영향을 검토했는지, 대상 토픽에 키 순서 의존이 있었는지는 기록되지 않았다.

## See Also

- [MSK IAM 인증과 JVM 한정 제약](msk-iam-authentication.md)
