---
title: Cilium 개요 — eBPF 기반 CNI
type: article
status: verified
confidential: internal
tags: [kubernetes, cilium, ebpf, networking]
---

# Cilium 개요 — eBPF 기반 CNI

> Sources: Cilium Docs; Isovalent Blog
> Raw: [Cilium](../../raw/kubernetes/cilium.md)
> Updated: 2026-09-15

## Overview

Cilium은 eBPF 위에 올라간 CNI로, 컨테이너 간 네트워크 연결과 보안을 함께 처리한다.
eBPF가 Linux 커널 내부에서 실행되기 때문에 **애플리케이션 코드나 컨테이너 구성을 바꾸지 않고도
보안 정책을 적용하고 갱신할 수 있다** — 이것이 기존 방식과 갈라지는 근본 지점이다.

## 기존 방화벽과 다른 점

기존 방화벽은 L3/L4에서 동작한다. 특정 포트에서 도는 프로토콜은 통째로 신뢰하거나 통째로 차단할 뿐,
그 안의 요청을 구분하지 못한다. Cilium은 개별 애플리케이션 프로토콜 요청 단위로 필터링한다.

## Identity 기반 보안

컨테이너 방화벽의 통상적인 방식 — 소스 IP와 대상 포트로 필터링 — 은 컨테이너가 클러스터 어디서든
뜰 때마다 **모든 서버의 방화벽을 조작해야 한다**는 뜻이 된다. 컨테이너가 단시간에 대량으로 뜨는
환경에서 이건 확장성 한계로 직결된다.

Cilium은 IP 대신 **동일 보안 정책을 공유하는 컨테이너 그룹에 보안 ID를 할당**한다.
이 ID가 모든 네트워크 패킷에 실려 수신 노드에서 검증된다. ID 관리는 키-값 저장소로 한다.

외부 서비스 접근처럼 레이블이 통하지 않는 영역에는 기존 CIDR 기반 정책이 수신·송신 양쪽으로 지원된다.

## 네트워킹 모드

플랫 L3 네트워크로 모든 컨테이너를 연결하고, 호스트 범위 할당자를 써서 **호스트 간 조정 없이**
각 호스트가 IP를 할당한다.

| 모드 | 방식 | 언제 |
|---|---|---|
| Overlay | VXLAN·Geneve 캡슐화 (Linux 지원 형식 모두 가능) | 인프라 요구사항이 가장 적다. 호스트 간 IP 연결만 되면 거의 모든 환경에서 동작 |
| Native Routing | Linux 호스트의 일반 라우팅 테이블 사용 | 네트워크가 컨테이너 IP를 라우팅할 수 있어야 한다. 네이티브 IPv6, 클라우드 라우터, 라우팅 데몬 운용 중일 때 |

Native Routing은 기반 인프라 이해가 필요한 고급 사용자용이다.

## Load Balancing

eBPF 해시테이블로 분산 로드밸런싱을 구현해 **kube-proxy를 완전히 대체할 수 있다.**

- **North-South** — XDP(eXpress Data Path)에 연결 가능. 로드밸런싱이 소스 호스트에서 수행되지
  않는 경우 DSR(Direct Server Return)과 Maglev 일관성 해싱 지원
- **East-West** — 커널 소켓 계층에서 바로 서비스→백엔드 변환. 하위 계층의 패킷당 NAT 오버헤드를 피한다

## Bandwidth Management

노드를 떠나는 트래픽에 EDT(Earliest Departure Time) 기반 속도 제한을 eBPF로 건다.
기존 HTB(Hierarchy Token Bucket)·TBF(Token Bucket Filter) 방식 대비 전송 지연을 줄이고
**다중 큐 NIC에서 발생하는 잠금 현상을 피한다.**

## 관측

- 메타데이터를 실은 이벤트 모니터링 — 패킷이 드롭되면 소스·대상 IP만이 아니라 양쪽의 전체 레이블 정보를 함께 보고
- Prometheus로 주요 지표 내보내기
- [Hubble](https://github.com/cilium/hubble/) — Cilium 전용 관측 플랫폼. 서비스 종속성 맵, 운영 모니터링·알림, flow log 기반 가시성

## See Also

- [EKS에서 VPC CNI와 Cilium CNI Chaining](eks-cilium-cni-chaining.md)
- [Cilium 미관리 Pod 문제](cilium-unmanaged-pod.md)
