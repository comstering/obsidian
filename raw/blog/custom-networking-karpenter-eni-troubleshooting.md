---
type: source
date: 2025-07-10
confidential: public
tags: [blog, kubernetes]
---

# Custom network Kapenter ENI troubleshooting

> Source: https://comstering.github.io/posts/custom-networking-karpenter-eni-troubleshooting (본인 블로그, repo: comstering.github.io/posts/custom-networking-karpenter-eni-troubleshooting.md)
> Collected: 2026-09-15
> Published: 2025-07-10

<!-- 발행 시점 스냅샷. 블로그 원본이 갱신되면 이 파일은 따라가지 않는다. -->


## Karpenter Node에 할당가능한 Pod보다 더 많은 Node가 Scheduling 되고 있어요

열심히 Custom Networking을 설정하고 Pod를 모니터링하고 있었는데 이상한 현상이 발생했다.

![pod-not-scheduled](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/pod-not-scheduled.png)

Pod가 ContainerCreating 상태에서 더이상 다음 단계로 진행이 되지 않고 멈춰서 실행이 안되고 있던 것이다.

그래서 Pod가 왜 실행이 안되고 있는지 Pod Event를 확인해봤다.

### Failed to assign an IP address to container

![pod-schedule-failed-event](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/pod-schedule-failed-event.png)

Event를 보면 Pod에 aws-cni에서 IP를 더이상 할당할 수 없다는 오류가 나오고 있었다.

이미 Custom Networking으로 Pod의 IP 여유공간을 충분하다 못해 넘치게 설정한 내 입장에서는 도저히 이해할 수 없는 상황이었다.

그래서 문제를 찾던 도중 이런 상황이 eks node-group의 Node에서는 발생하지 않고 Karpenter에서 만든 Node에서만 발생한다는 사실을 알았다.

## Node가 할당 가능한 IP 개수

Karpenter로 뜬 Node 하나의 스펙을 확인해봤다.

![node-spec](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/node-spec.png)

현재 Node는 t4g.medium type의 instance가 띄워진 상태였고 EC2 스펙에서 EC2의 할당 가능한 ENI개수를 확인해봤다.

### EC2 Network Spec

![ec2-network-spec](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/ec2-network-spec.png)

t4g.large와 t4g.medium의 network interface를 확인해본 결과 각각 3개의 network interface가 존재하지만 network interface당 할당 가능한 IP가 12개, 6개로 되어 있었다.

계산상으로만 하면 t4g.large는 36개의 IP를, t4g.medium은 18개의 ip를 할당할 수 있다.

여기서 Node가 자체 IP를 가져야하기 때문에 Node IP 1개를 제외하면 각각 t4g.large는 35개, t4g.medium은 17개의 IP를 Pod에 할당할 수 있다.

### Custom Networking으로 Pod에 할당 가능한 IP 개수가 줄어들었다.

그런데 EKS console 상에서 custom networking이 설정된 default node group의 EC2인 t4g.large에 35개의 Pod 할당이 아닌 24개의 Pod가 할당가능하다고 표시되어 있었다.

![t4g.large-pod-cound](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/t4g.large-pod-cound.png)

#### Custom Networking의 할당 가능한 Pod 개수

Custom Netoworking이 적용되지 않은 기존 EC2 Node의 Pod에 할당 가능한 IP 개수 계산은 아래와 같다.

```
(ENI count) * (IP addr per interface) - 1
```

ENI개수에서 할당 가능한 IP 개수를 곱하고 Node가 가져가야할 IP 한개를 제외한 나머지 IP들을 모두 사용할 수 있다.

하지만 Custom Networking을 사용하는 순간 사용가능한 IP 개수가 완전히 바뀌게 된다.

ENI 1개를 제외하고 나머지 ENI의 IP 할당 개수 만큼 사용할 수 있다.

```
(ENI count - 1) * (IP addr per interface)

tg4.medium의 경우
기존: 3 * 6 - 1(Node 자체 IP) = 17
custom network: (3-1) * 6 = 12
```

이렇게 사용가능한 IP가 줄어드는 이유는 EC2 Node의 IP와 Pod의 IP가 완전히 서로 다른 대역을 사용하기 때문이다.

![custom-networking](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/custom-networking.png)

_출처: [AWS Documentation](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/cni-custom-network.html)_

그림에서 보이듯이 Node는 10.0.0.0/24 대역을 사용하는 반면, Pod는 100.64.0.0/16 대역을 사용한다.

ENI에서 할당하는 IP는 ENI가 속한 Subnet IP 대역의 IP로만 할당이 가능하다. 이 부분에서 Pod에 할당 가능한 IP 개수가 줄어들게 되는 것이다.

Node는 10.0.0.0/24 대역의 IP를 사용해야하기 때문에 ENI 하나를 사용해서 10.0.0.0/24 대역에 IP를 할당 받는다. 그리고 남은 ENI를 사용해서 Custom Networking을 사용할 IP 대역으로 ENI에 IP를 할당한다. 그래서 ENI 1개를 빼고 나머지 ENI에 대해서 곱한 개수만이 Pod의 IP로 할당 가능하다.

## Karpenter는 이 사실을 모른다!

eks의 node group node는 vpc-cni addon과 eks 자체 managed를 통해서 자동적으로 할당 가능한 IP를 알고 그 이상으로 Pod를 Scheduling하지 않는다.

하지만 Karpenter의 Node는 EKS에서 Managed되고 있는 Node가 아니라 Karpenter가 직접 Managed하고 있는 Node이다. 그래서 현재 EC2의 ENI 개수가 몇개인지, 할당 가능한 IP 개수가 변경되었는지도 모르고 기존의 IP할당 가능한 개수만큼의 Pod를 Node에 할당할 수 있다고 판단한다.

그래서 Node에서는 할당할 수 있는 IP가 없는데 Pod는 계속 Scheduling되려고 하는데 Karpenter는 아직 Node에 Pod가 할당할 수 있다고 판단하여 추가 Node를 생성하지 않는 것이다.

### How to Fix?

그래서 Custom Networking을 적용했을 때는 EC2의 ENI 1개를 사용할 수 없다는 걸 Karpenter에게 알려줘서 Node에 Scheduling될 수 있는 Pod의 개수를 조정해주어야한다.

### Karpenter 추가 설정

#### ReservedENIs

Karpenter 공식문서에서 이미 이 내용에 대해서 명시해주고 있다.

![karpenter-docs-note](/images/posts/contents/custom-networking-karpenter-eni-troubleshooting/karpenter-docs-note.png)

내용은 간단하다. Karpenter Node에 ENI 1개를 예약된 ENI로 등록하여 사용하지 않게 설정하면 된다. 기존 Karpenter values에서 아래의 값만 추가하면 된다.

```yaml
# Karpenter values.yaml
## 중략...
settings:
  clusterName: ${EKS_CLUSTER_NAME}
  interruptionQueue: Karpenter-${EKS_CLUSTER_NAME}-SpotInterruptionQueue
  reservedENIs: "1" # 여기 추가
  # 설정하지 않으면 default가 0, custom networking으로 1개의 eni를 사용할 수 없으므로 1을 입력하여 ENI 1개가 예약된 상태여서 사용할 수 없다고 명시
```

## Fixed

기존에 이미 생성된 Node들은 변경된 설정을 인식하지 못해서 이전 설정 그대로 남아있다. 그래서 반드시 Node의 Drain, Delete를 통해서 새 Node를 생성하고 기존 Karpenter Node를 제거하여 ReservedENIs를 인식한 새 Node가 Pod를 실행하도록 해야한다.

### Reference

- [Karpenter Settings](https://karpenter.sh/docs/reference/settings/)
