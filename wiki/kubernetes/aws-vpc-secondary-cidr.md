---
title: EKS Custom Networking — Pod IP 고갈 해결
type: article
status: verified
confidential: internal
tags: [kubernetes, eks, aws, vpc, custom-networking, cgnat, tgw]
---

# EKS Custom Networking — Pod IP 고갈 해결

> Sources: 블로그 "EKS Custom Networking", 2025-07-08; 작업 기록, 2025-06-12; AWS EKS Best Practices
> Raw: [EKS Custom Networking](../../raw/blog/eks-custom-networking.md); [AWS VPC Secondary CIDR 작업 기록](../../raw/kubernetes/aws-vpc-secondary-cidr.md)
> Updated: 2026-09-15

## Overview

VPC CNI는 Pod에 **Node와 같은 Subnet의 IP**를 준다. 장점이 크지만, Subnet IP가 빠르게 마른다.
해결은 **CGNAT 대역을 Secondary CIDR로 붙이고 EKS Custom Networking으로 Pod를 그쪽에 태우는 것**이다.

## 왜 IP가 말랐나 — TGW가 CIDR을 묶는다

여러 팀이 각자 VPC를 쓰고 Transit Gateway로 통신한다.
**TGW가 라우팅하려면 VPC들의 IP 대역이 겹치면 안 된다.** 그래서 대역을 마음대로 못 정하고
관리팀에서 `/21` netmask를 할당받았다.

`/21`을 public·private·db 용도로 쪼개고 나니, EKS Node와 Pod가 쓸 private 대역은
**`/24` subnet 3개** 가 됐다. 약 **760개** 정도의 IP.

VPC CNI는 Node의 Secondary ENI를 Pod에 그대로 할당하므로 이 760개를 빠르게 소모한다.
여기에 MSK, Private ELB까지 같은 대역을 쓰면서 결국
**Pod에 할당할 IP가 없어 스케줄링이 멈추는 사태**까지 갔다.

## 해결 1 — CGNAT 대역을 Secondary CIDR로

AWS VPC는 기존 CIDR에 추가 CIDR을 붙일 수 있고, RFC 1918 사설 대역 외에
**CGNAT 대역인 `100.64.0.0/10`** 을 Secondary CIDR로 허용한다.

이 대역의 값은 **TGW나 VPC Peering을 했을 때 다른 VPC와 대역이 겹치지 않는다**는 점이다.
사실상 내 VPC 내부 전용 대역이 되므로, 앞서 본 TGW 제약을 우회하는 열쇠가 된다.

```hcl
locals {
  custom_networking = {
    vpc_cidr     = "100.64.0.0/17"
    subnet_cidrs = ["100.64.0.0/19", "100.64.32.0/19", "100.64.64.0/19"]
  }
}
```

`/19` 3개로 약 **24,000개** 의 IP를 확보했다. 기존 760개 대비 **약 31배**다.

## 해결 2 — EKS Custom Networking

기본적으로 Pod는 Node와 같은 subnet에서 IP를 받는다. Custom Networking은
**Node의 Secondary ENI를 Node와 다른 Subnet에 할당**해서 Pod를 다른 대역에 태운다.

vpc-cni addon에 설정을 얹는다.

```hcl
configuration_values = jsonencode({
  env = {
    AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG = "true"
    ENI_CONFIG_LABEL_DEF               = "topology.kubernetes.io/zone"
  }
})
```

그리고 AZ별로 `ENIConfig` 리소스를 만들어 어느 subnet을 쓸지 알려준다
(`crd.k8s.amazonaws.com/v1alpha1`). Terraform Kubernetes Provider로 관리하면 이력이 남는다.

결과적으로 Node IP는 `10.x.x.x`, Pod IP는 `100.64.x.x` 로 갈린다.

## 대가 — TGW 통신이 끊긴다

CGNAT 대역이 다른 VPC와 겹치지 않는다는 장점은 뒤집으면
**다른 VPC가 이 대역을 모른다**는 뜻이다.

- outbound rule에 대역을 추가하는 것 자체는 가능하다
- 그러나 **상대 VPC의 routing table에는 `100.64.0.0/10` 대역이 등록되어 있지 않다**
- 요청은 나가지만 **response 응답의 라우팅이 안 된다**

해결은 masquerade(SNAT)다. Pod IP를 Node IP로 바꿔 내보낸다.
이 지점이 CNI 선택과 맞물렸다 — **Cilium을 쓰면 이 처리가 간단하다**는 것이
[CNI Chaining 구성](eks-cilium-cni-chaining.md)을 택한 근거 중 하나였다.
Cilium 없이 가면 DaemonSet을 따로 띄우거나 각 Pod에 init container 작업을 붙여야 한다.

## 확인이 필요한 지점 — CIDR 범위 불일치

> **Status: 확인 필요** (2026-09-15)
> Custom Networking subnet은 `100.64.0.0/19`, `100.64.32.0/19`, `100.64.64.0/19` 3개인데,
> Cilium helm values의 `ipv4NativeRoutingCIDR` 은 `100.64.0.0/18` 로 잡혀 있다.
> `/18` 은 `100.64.63.255` 까지이므로 **세 번째 subnet(`100.64.64.0/19`)이 범위 밖**이다.
>
> `bpf.masquerade: true` 는 `ipv4NativeRoutingCIDR` 대역과 라우팅 테이블의 local rule 대역을
> 제외한 나머지에 SNAT를 건다. 세 번째 subnet은 VPC secondary CIDR(`/17`)의 local rule로
> 덮일 가능성이 크므로 **실제 장애로 이어지지 않았을 수 있다.**
> 다만 두 값이 어긋나 있는 것은 사실이라, 의도한 설정인지 확인이 필요하다.
>
> 근거: `/17`·`/19` 값은 [EKS Custom Networking 포스트](../../raw/blog/eks-custom-networking.md),
> `/18` 값은 [Cilium 설치 포스트](../../raw/blog/install-cilium-eks.md).

## 참고

- https://docs.aws.amazon.com/ko_kr/eks/latest/best-practices/custom-networking.html

## See Also

- [EKS에서 VPC CNI와 Cilium CNI Chaining](eks-cilium-cni-chaining.md)
