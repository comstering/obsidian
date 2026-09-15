---
title: Cilium 미관리 Pod 문제
type: article
status: verified
confidential: internal
tags: [kubernetes, cilium, troubleshooting, taint, toleration]
---

# Cilium 미관리 Pod 문제

> Sources: 블로그 "Cilium CNI 설치 후 일부 Pod들이 정상동작하지 않는 문제 해결", 2025-09-02
> Raw: [Cilium 미관리 Pod 트러블슈팅](../../raw/blog/troubleshoot-cilium.md)
> Updated: 2026-09-15

## Overview

Cilium 설치 후 **일부 Pod만** 네트워크 통신이 안 되고 Restart count가 계속 올라갔다.
원인은 taint가 아니라 **taint를 무시하는 toleration** 이었다.

## 증상과 공통점

문제 Pod들의 공통점은 하나였다 — **Cilium DaemonSet Pod보다 먼저 스케줄링된 DaemonSet Pod.**
대표적으로 `ebs-csi-driver`, `istio-cni-node`.

## 원인 — toleration이 taint를 무력화한다

[CNI Chaining 구성](eks-cilium-cni-chaining.md)에서 `node.cilium.io/agent-not-ready` taint를
걸어 Cilium보다 먼저 뜨는 것을 막아뒀는데, 문제 Pod들은 이 spec을 갖고 있었다.

```yaml
tolerations:
  - effect: NoExecute
    operator: Exists
```

**`NoExecute` taint를 전부 무시하고 스케줄링한다**는 뜻이다. 그래서 Cilium이 준비되기 전에
떠버렸고, Cilium이 이 Pod들의 네트워크를 잡지 못했다.

## Cilium이 "관리 중"이라고 판단하는 기준

`CiliumEndpoint` 라는 Custom Resource다. Cilium은 자신이 네트워크를 관리하는 Pod의 정보를
이 리소스로 들고 있다. **CiliumEndpoint에 등록되지 않은 Pod = 미관리(unmanaged) Pod.**

## 해결 — unmanagedPodWatcher

Cilium Operator에 미관리 Pod를 감시해 재시작시키는 옵션이 있다.

```yaml
operator:
  unmanagedPodWatcher:
    restart: true          # 미관리 Pod를 감시하고 재시작
    intervalSeconds: 15    # 감시 간격
  extraArgs:
    - "--pod-restart-selector=app.kubernetes.io/name!=aws-node"
```

여기서 **재시작은 컨테이너 재시작이 아니라 Pod를 완전히 제거하고 새로 스케줄링하는 것**이다.
그래야 새 Pod가 Cilium 네트워크로 잡힌다.

## 반드시 제외해야 하는 것 — aws-node

`--pod-restart-selector` 로 **`aws-node`(VPC CNI DaemonSet)를 감시 대상에서 뺀다.**

aws-node는 Cilium보다 **먼저** 떠서 Pod들의 IPAM과 라우팅을 담당해야 한다.
즉 구조적으로 Cilium의 관리를 받지 않는 게 정상인 Pod다.
이걸 빼지 않으면 watcher가 aws-node를 계속 죽이고, IPAM이 무너진다.

**Chaining 구성에서만 생기는 함정이다.** VPC CNI를 제거하는 구성이라면 aws-node 자체가 없다.

## See Also

- [EKS에서 VPC CNI와 Cilium CNI Chaining](eks-cilium-cni-chaining.md)
