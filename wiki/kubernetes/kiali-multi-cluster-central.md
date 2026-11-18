---
title: 중앙 클러스터 하나의 Kiali로 멀티 클러스터 보기
type: article
status: draft
confidential: public
tags: [kubernetes, istio, kiali, observability, prometheus, multi-cluster]
---

# 중앙 클러스터 하나의 Kiali로 멀티 클러스터 보기

> Sources: Claude Code 세션 요약, 2026-11-17
> Raw: [세션 요약 2026-11-17](../../raw/sessions/2026-11-17.md)
> Updated: 2026-11-18

## Overview

Kiali는 multi-cluster를 지원하므로 중앙(internal) 클러스터에 Kiali 하나만 두고 여러 클러스터의
Istio mesh를 한 화면에서 볼 수 있다. 핵심 제약은 **Kiali가 Prometheus 주소를 하나만 받는다**는 것이다.
그래서 각 클러스터의 Prometheus를 열어 Kiali가 가져가는 구조가 아니라,
**각 클러스터가 중앙 metrics store로 push하고 Kiali는 그 하나만 조회**하는 구조가 된다.

## Kiali가 정보를 가져오는 두 경로

| 정보 | 출처 | 중앙화 방법 |
|---|---|---|
| 토폴로지 그래프, 트래픽 지표 | Prometheus API (PromQL) | 중앙 metrics store(Mimir 또는 VictoriaMetrics)를 Kiali의 Prometheus URL로 지정 |
| 리소스·설정 (Workload, VirtualService, AuthorizationPolicy 등) | 각 클러스터의 Kubernetes API | Kiali에 원격 클러스터 접근 권한을 준다 |

Kiali는 지표를 직접 수집하지 않는다. 화면을 열 때마다 `external_services.prometheus.url` 하나에
PromQL을 보낸다. 클러스터별 Prometheus 주소를 여러 개 넣을 수 없으므로,
모든 클러스터의 Istio 지표를 한곳에서 조회할 수 있는 PromQL 엔드포인트가 먼저 있어야 한다.

## 설계 판단

- DevOps만 보는 대시보드라 Kiali는 중앙 하나로 충분하다고 봤다 (당시 내 판단)
- 클러스터 간 지표가 섞이므로 각 클러스터 지표에 cluster 식별 label이 붙어 있어야 구분된다

> **Status: 근거 미비**
> 세션 요약에만 근거한다. 바로 위 cluster label 항목은 일반 원칙이며 기록에는 없다.
> 레포에서 "먼저 고쳐야 할 설정"을 하나 찾았다는 언급이 있으나 기록이 잘려 무엇인지 남아 있지 않다.

## See Also

- [Istio service mesh에서 JWT 인증 처리](istio-jwt-authentication.md)
