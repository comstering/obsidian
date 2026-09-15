---
type: source
date: 2025-09-02
confidential: public
tags: [blog, kubernetes]
---

# Cilium CNI 설치 후 일부 Pod들이 정상동작하지 않는 문제 해결

> Source: https://comstering.github.io/posts/troubleshoot-cilium (본인 블로그, repo: comstering.github.io/posts/troubleshoot-cilium.md)
> Collected: 2026-09-15
> Published: 2025-09-02

<!-- 발행 시점 스냅샷. 블로그 원본이 갱신되면 이 파일은 따라가지 않는다. -->


## Cilium CNI 설치 이후 발생한 Networking Error

Cilium CNI를 설치하고 나서 문제가 발생했다. 몇몇 Pod들에서 정상적으로 통신이 네트워크 통신이 안되고 있던 것이다.

그래서 Pod들의 Restart 횟수는 점점 올라왔고 해당 Pod는 정상적으로 동작하지 않고 있었다.

이러한 Pod들의 공통점이 1가지가 보였다. 바로 Cilium CNI DaemonSet Pod가 Scheduling되기 전에 Scheduled된 DaemonSet Pod들에서 이런 현상이 보였다.

### Taint and Toleration

이 문제는 내가 위에서 설정한 taint의 설정이 제대로 적용이 안되고 있다는 부분에 초점을 잡았다.

대표적으로 몇몇 Pod들을 살펴보면 ebs-csi-driver, istio-cni-node(추후 포스팅할 istio 관련 pod이다)들에서 발생했다.

이 Pod들에는 공통적인 spec이 있다.

```yaml
tolerations:
  - effect: NoExecute
    operator: Exists
```

이 toleration 옵션은 taint를 무시하는 옵션이다. 이전 포스팅에서 나는 Cilium Pod가 실행되기 전에 다른 Pod들이 scheduling될 수 없도록 taint 설정을 걸어놨다. 하지만 이 eks-cis-driver DamonSet과 istio-cni-node DaemonSet에는 이 toleration이 설정되어 있었다.

이 toleration이 의미하는 건 간단하다. NoExecute라는 taint는 무시하고 Pod를 scheduling 한다는 것이다.

## Troubleshooting(How to Fix?)

### Cilium Operator

Cilium을 설치할 때 cilium operator라는 component가 함께 설치된다.

이 Cilium Operator는 Cilium을 사용하는데 함께 필요한 operation을 처리해주는 역할을 한다.

### UnmanagedPodWatcher

Cilium Operator에는 unmanagedWatcher라는 옵션이 있다. 이름에서 알 수 있듯 Cilium이 Managed(관리)하지 않는 Pod를 찾는 역할을 한다.

#### Cilium Endpoint

그렇다면 Cilium이 Managed하고 있는 Pod의 기준은 무엇으로 판단할까? 바로 `Cilium Endpoint`라는 Custom Resource를 통해서 판단한다.

Cilium은 자신이 Network록 관리하고 있는 Pod들에 대한 정보를 Cilium Endpoint라는 Resource를 통해서 관리한다.

![cilium-endpoint-resources](/images/posts/contents/troubleshoot-cilium/cilium-endpoint-resources.png)

이렇게 Cilium Endpoint로 등록되어 있지 않는 Pod들은 Cilium이 관리하고 있지 않는 Pod로 판단한다.

#### Unmanaged Pod Restart

Unmanaged의 대표적인 경우는 Cilium Pod가 Running되어서 Network를 관리할 수 있는 상태가 되기 전에 먼저 Pod가 Scheduled되어 Cilium이 해당 Pod의 Network를 관리하지 못하는 경우이다.

바로 지금 내가 겪고 있는 문제이다.

Cilium Operator에서는 이러한 Unmanaged Pod를 종료시키고 재시작하여 Cilium Network로 관리될 수 있도록 하는 옵션을 제공해주고 있다.

#### Don't restart aws-node pod(VPC CNI DaemonSet)

여기서 주의해야할 점이 VPC CNI DaemonSet인 aws-node pod이다. 이 pod는 Cilium보다 먼저 Node에 생성되고 Pod들의 IPAM, Routing을 관리해주어야한다.

즉, 이 Pod는 예외로 Cilium의 관리를 받지 않는 Pod가 되어야한다는 것이다.

#### Add Cilium Operator Values in values.yaml

```yaml
# cilium values.yaml

# 중략...
# Cilium 설정: Unmanaged Pod Restart
operator:
  unmanagedPodWatcher:
    restart: true # Cilium이 관리하지 않는 Pod를 감시하고 재시작하도록 설정
    intervalSeconds: 15 # 감시 간격 설정 (초 단위)
  extraArgs:
    - "--pod-restart-selector=app.kubernetes.io/name!=aws-node" # VPC CNI인 aws-node를 제외한 모든 Pod에 대해 재시작 감시 설정
```

cilium operator의 unmanagedPodWatcher에 대한 설정을 한다.

UnmanagedWatcher에 대상이 되면 restart를 할 수 있도록 true로 설정하고 extraArgs를 통해서 aws-node는 UnmanagedWatcher 대상에서 제외한다.

## Result

이 설정을 통해서 Cilium이 관리하지 않는 Pod들은 강제로 재시작이 되도록 설정하였다.

여기서 Pod의 재시작이란 Pod가 그대로 남아있고 Restart count가 증가하는 Container의 재시작이 아니라 Pod를 완전히 제거하고 새로운 Pod를 Scheduling하고 실행하는 것을 의미한다.
