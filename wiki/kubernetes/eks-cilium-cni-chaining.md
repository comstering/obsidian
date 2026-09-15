---
title: EKS에서 VPC CNI와 Cilium CNI Chaining
type: article
status: verified
confidential: internal
tags: [kubernetes, eks, cilium, vpc-cni, cni-chaining, networking]
---

# EKS에서 VPC CNI와 Cilium CNI Chaining

> Sources: 블로그 "Cilium CNI 알아보기", 2025-08-31; 블로그 "EKS에 Cilium CNI 설치하기", 2025-09-01; 작업 기록, 2025-05-24
> Raw: [Cilium CNI 알아보기](../../raw/blog/introduce-cilium-cni.md); [EKS에 Cilium CNI 설치하기](../../raw/blog/install-cilium-eks.md); [EKS Cilium 작업 기록](../../raw/kubernetes/eks-cilium.md)
> Updated: 2026-09-15

## Overview

**VPC CNI를 걷어내지 않는다.** CNI Chaining으로 VPC CNI와 Cilium을 함께 돌리고,
둘이 역할을 나눠 갖는다. 제거한 것은 `kube-proxy` 하나뿐이다.

이유는 단순하다. VPC CNI의 핵심 장점 — **Pod가 VPC CIDR 대역의 IP를 직접 받는다** — 을
포기할 이유가 없었다. 이 장점 위에 Cilium의 eBPF 네트워킹을 얹는 구성이다.

> **Status: Outdated** (2026-09-15)
> 2025-05-24 작업 기록에는 `Remove VPC CNI → addon 제거: vpc-cni, kube-proxy` 로 적혀 있다.
> 이는 검토 초기의 계획이었고, 실제로는 chaining으로 방향이 바뀌어 **vpc-cni addon은 유지**됐다.
> 같은 기록에 이미 `cni-chaining-aws-cni` 문서 링크가 달려 있던 것으로 보아,
> 기록 시점에 두 선택지를 함께 보고 있었던 것으로 보인다.

## VPC CNI를 남기는 이유

Pod IP가 VPC CIDR 대역이면 따라오는 것들:

- **NLB → Pod direct** — Node instance를 거치지 않는다. Network hop이 줄어든다
- **RDS·MSK와 direct 통신** — Pod IP에서 바로 붙는다. Node IP를 경유하지 않는다
- **Security Group이 단순해진다** — VPC 내부 대역 규칙을 그대로 쓴다

Cilium만으로 가면 이걸 전부 잃는다. Chaining은 이 장점을 남긴 채 eBPF를 얻는 방법이다.

## 역할 분담

| | 담당 |
|---|---|
| **VPC CNI** | IPAM (Pod IP를 Custom Networking 대역으로 할당), VPC 라우팅 |
| **Cilium** | Service LoadBalancing, NetworkPolicy, 보안, 관측(Hubble) |

VPC 외부(TGW·NAT Gateway)로 나갈 때는 masquerade SNAT로 Pod IP가 Node IP로 변환된다.
안으로 들어올 때는 NLB가 VPC CNI 라우팅을 타고 Pod에 직접 닿는다.

## 필수 설정

### Native routing이어야 한다

Cilium의 네트워킹 모드는 Overlay(캡슐화)와 Native routing 둘인데,
**AWS VPC CNI와 chaining할 때는 Native routing을 써야 한다.**
라우팅 데몬 역할을 VPC CNI가 이미 담당하고 있기 때문이다.

### helm values 핵심

```yaml
cni:
  chainingMode: aws-cni   # AWS CNI와 연결되는 chaining 모드
  exclusive: false        # aws-node DaemonSet도 계속 실행되도록 허용

routingMode: native       # 터널링 비활성화

kubeProxyReplacement: true  # kube-proxy 제거, Cilium이 eBPF로 서비스 처리

# kube-proxy를 삭제할 경우 반드시 필요
k8sServiceHost: {eks-api-endpoint}
k8sServicePort: 443

ipv4NativeRoutingCIDR: "100.64.0.0/18"   # Pod Custom Networking CIDR
```

`exclusive: false` 가 chaining의 스위치다. 이게 없으면 Cilium이 CNI를 독점하려 든다.
`kubeProxyReplacement: true` 로 kube-proxy를 대체하므로 `k8sServiceHost`·`k8sServicePort`가
필수가 된다 — kube-proxy가 없으면 Cilium이 API 서버를 직접 찾아가야 하기 때문이다.

### chaining에서는 못 쓰는 것

```yaml
bpf:
  masquerade: true
#  hostLegacyRouting: false   # cni chaining을 하고 있다면 사용 불가
```

## Node taint — Cilium보다 먼저 뜨는 Pod를 막는다

Cilium Pod가 Running 되기 전에 다른 Pod가 스케줄링되면 그 Pod의 네트워크는 관리되지 않는다.
taint로 막는다.

```hcl
taint {
  key    = "node.cilium.io/agent-not-ready"
  value  = "true"
  effect = "NO_EXECUTE"
}
```

Karpenter NodePool에서는 `startupTaints` 로 같은 키를 건다.

다만 **이 taint를 무시하는 Pod가 있다** (`tolerations: effect: NoExecute, operator: Exists`).
ebs-csi-driver, istio-cni-node 등이 해당한다 — 이 문제와 해결은
[Cilium 미관리 Pod 문제](cilium-unmanaged-pod.md) 참고.

## kube-proxy 제거

Terraform으로 관리한다면 `aws_eks_addon` 에서 kube-proxy 리소스를 지운다.
**vpc-cni addon은 그대로 둔다.**

## 결과 확인

`aws-node` pod(VPC CNI DaemonSet)와 `cilium` pod가 **동시에 Running** 이면 정상이다.
Cilium pod에서 `cilium status` 를 실행하면 AWS CNI와 chaining 상태, Native routing 사용이 보인다.

## See Also

- [Cilium 개요 — eBPF 기반 CNI](cilium-overview.md)
- [Cilium 미관리 Pod 문제](cilium-unmanaged-pod.md)
- [EKS Custom Networking — Pod IP 고갈 해결](aws-vpc-secondary-cidr.md)
