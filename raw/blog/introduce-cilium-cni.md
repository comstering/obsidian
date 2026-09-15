---
type: source
date: 2025-08-31
confidential: public
tags: [blog, kubernetes]
---

# Cilium CNI 알아보기

> Source: https://comstering.github.io/posts/introduce-cilium-cni (본인 블로그, repo: comstering.github.io/posts/introduce-cilium-cni.md)
> Collected: 2026-09-15
> Published: 2025-08-31

<!-- 발행 시점 스냅샷. 블로그 원본이 갱신되면 이 파일은 따라가지 않는다. -->


## What is Cilium CNI?

### What is CNI?

나는 Kubernetes를 EKS로 운영하고 있다. EKS에서는 CNI를 VPC CNI로 제공한다.

CNI란 Cloud Networking Interface의 약자로 k8s와 같은 Container Orchestration System에서 컨테이너 네트워킹을 구성하는 표준 인터페이스이다.

EKS에서 VPC CNI를 이미 제공해주고 있고 잘 사용하고 있는데 왜 갑자기 Cilium CNI를 알아보고 있을까?

### Cilium CNI

Cilium CNI는 CNI 오픈소스 중 하나이다. Cilium CNI의 가장 대표적 특징은 eBPF라는 리눅스 커널 기술을 통해서 Networking을 구성한다는 것이다.

### VPC CNI vs Cilium CNI

VPC CNI와 Cilium CNI의 가장 큰 차이점은 Networking 방식이다. VPC CNI는 iptables라는 기술을 통해서 Networking을 제어하고 Cilium CNI는 eBPF 기술을 통해서 Networking을 제어한다.

Networking 제어에는 k8s의 Service Network, [NetworkPolicy](https://kubernetes.io/ko/docs/concepts/services-networking/network-policies/)에 대한 방식이 iptables를 이용하느냐 eBPF를 이용하느냐의 차이를 포함한다.

#### kube-proxy

k8s에서 Networking을 Pod <-> Pod형태로 직접하지 않는다. Service라는 Resource를 이용해서 통신한다. Service에서 트래픽을 받으면 Service에 연결된 Pod에 적절히 라우팅을 해준다. 이 라우팅에 대한 iptables의 정보를 kube-proxy가 업데이트해준다.

#### Network Policy

Network policy는 Container Networking에서 각 컨테이너별 네트워크 정책을 설정하여 네트워크 보안관리를 하는 Resource다. NetworkPolicy에는 각 Network Layer별로 설정할 수 있으며 L3/L4부터 L7까지 정책 설정이 가능하다.

#### iptables vs. eBPf

![compare-networking](/images/posts/contents/introduce-cilium-cni/compare-networking.png)

이 그림은 VPC CNI에서 사용하는 iptables 방식과 Cilium CNI의 eBPF의 차이를 잘 보여준다.

iptables의 networking을 보면 검사하는 단계가 매우 많다. 특히, iptables의 routing은 Service와 Pod가 늘어나면 늘어날 수록 늘어난다. iptables에 등록된 라우팅을 전체 검사하는 O(N)의 시간복잡도를 가지게 된다. 여기에 NetworkPolicy에 해당하는 규칙 검사까지 진행하게 되면 Network 속도는 더 느려질 수 밖에 없다.

kube-proxy 역시 이런 iptables의 규칙을 업데이트하는 형태로 Service, Pod의 Routing 및 Load Balancing을 진행한다.

![eBPF-linux-kernal](/images/posts/contents/introduce-cilium-cni/eBPF-linux-kernal.png)

eBPF는 완전히 Linux Kernel 내장되어 있으며 eBPF Maps를 사용한다. 이 Maps는 말 그대로 Map 자료형을 생각하면 된다. Map 자료형은 Key, Value 형태로 구성되어 있으며 O(1)의 시간복잡도를 가진다. O(N)의 시간복잡도를 가지는 iptables와 비교해서 Service, Pod의 개수, NetworkPolicy 개수가 늘어나도 Network 속도가 기하급수적으로 늘어나지는 않는다.

또한 iptables를 사용하지 않기 때문에 iptables를 update하는 kube-proxy를 사용하지 않고 Cilium 자체에서 Routing과 LoadBalancing을 담당할 수 있다.
https://docs.cilium.io/en/stable/overview/intro/#load-balancing

#### Network Latency

![compare-latency-service](/images/posts/contents/introduce-cilium-cni/compare-latency-service.png)

eBPF와 kube-proxy의 Service 개수에 따른 Network Latency이다. 개수가 적을 때는 큰 차이를 보이지 않고 오히려 kube-proxy가 더 빠를 수도 있지만 서비스의 개수가 늘어나면 늘어날 수록 kube-proxy의 latency는 증가하는 반면 eBPF는 거의 동일한 결과를 보여주고 있다.

#### Cilium Feature

Cilium CNI를 고려한 가장 큰 이유는 Networking 방식인 iptables vs. eBPF의 차이로 인해 고려 중이었다. 또한 Cilium의 다양한 기능들도 이유에 포함되었다.

- Overlay Networking: 캡슐화 기반 가상 네트워크
- Network monitoring: Hubble을 통해서 네트워크 모니터링 가능
- Multi Cluster(Cluster Mesh): 하나의 k8s Cluster 내의 네트워크만이 아니라 Multi cluster간의 네트워크 통신을 손쉽게 관리할 수 있게 해준다.
- IPAM: Cilium이 직접 Pod의 IP 할당을 담당하여 VPC 및 Subnet의 IP 부족 문제를 해결할 수 있다. -> 이건 이전 포스팅의 [EKS Custom Networking](https://comstering.github.io/posts/eks-custom-networking)이 있어서 큰 메리트는 없었다.

## How to set Cilium in EKS?

Cilium CNI를 적용하겠다라고 의사결정을 한 이후 가장 큰 문제점은 EKS에 어떻게 적용하는 가였다. EKS에서는 이미 VPC CNI가 기본 설정이고 이 VPC CNI를 제거하는 순간 EKS내의 네트워크는 전부 마비가 된다. 또한 VPC CNI의 가장 큰 장점인 Pod의 IP가 VPC CIDR 내의 IP로 할당되어 AWS Resource와 direct 통신을 할 수 있는 장점도 없어지게 된다.

### Support Cilium

![eks-alternate-cni](/images/posts/contents/introduce-cilium-cni/eks-alternate-cni.png)

AWS [EKS 문서](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/alternate-cni-plugins.html)에서 VPC CNI외에 사용할 수 있는 CNI가 명시되어 있다. 여기에는 Cilium이 포함되어 있다.

이 문서대로라면 EKS의 VPC CNI를 대체제로 Cilium CNI를 사용할 수 있다는 뜻이 된다.

### Cilium CNI Chaining

Cilium CNI와 VPC CNI의 차이가 있고 당연히 VPC CNI가 가지고 있는 장점이 있다. 이러한 장점을 전부 버리면서 Cilium으로 넘어가야하는지는 물음표였다. 특히 VPC CNI의 Pod ENI IP 할당을 VPC CIDR Block으로 할당하여 VPC의 라우팅 테이블을 그대로 사용하면 LoadBalancer <-> Pod와의 통신이 Node를 거치지 않고 Direct로 된다는 점, 당연하게 RDS, MSK 등 VPC 내에 설치된 인스턴스들과 Node를 거치지 않고 Pod IP에서 direct도 통신한다는 점에서 Cilium을 사용하는 네트워크 통신보다 더 빠른 Network Latency를 가질 것 같았다.

그러던 중 Cilium CNI 문서에서 [CNI Chaining](https://docs.cilium.io/en/stable/installation/cni-chaining/)이라는 문서를 확인했다. [AWS VPC CNI plugin 문서](https://docs.cilium.io/en/stable/installation/cni-chaining-aws-cni/)에서 VPC CNi와 Cilium CNI가 함께 사용하는 내용을 보여주었다.

![aws-cni-chaining-1](/images/posts/contents/introduce-cilium-cni/aws-cni-chaining-1.png)
![aws-cni-chaining-2](/images/posts/contents/introduce-cilium-cni/aws-cni-chaining-2.png)

두 이미지는 AWS VPC CNI와 Cilium을 Chaining 했을 때 각 CNI가 어떤 역할을 담당하는지 설명해주고 있다.

이것을 토대로 내 VPC에서 EKS Custom Networking을 적용한 Networking을 도식화하면 아래와 같은 결과가 나온다.

![networking-structure](/images/posts/contents/introduce-cilium-cni/networking-structure.png)

VPC CNI는 IPAM을 담당하여 Pod의 IP를 EKS Custom Networking 대역으로 할당한다.

VPC 외부로 통신하는 TGW, NAT Gateway로 통신할 때는 masquerade SNAT가 되어 Pod IP는 Node IP로 변환되어 통신한다.

외부에서 트래픽을 받을 때는 NLB 통해서 통신하게 되는데 이때 NLB와 Pod간 통신은 VPC CNI의 라우팅을 통해서 Node를 거치지 않고 Direct로 Pod와 통신하게 된다. 마찬가지로 Pod가 내부에 배포되어 있는 RDS, MSK 등과 통신하게 될 때는 Node IP를 통하지 않고 direct로 Pod IP와 통신하게 된다.

나머지 Kubernetes Networking은 전부 Cilium CNI가 담당하여 LoadBalancing, Security 등을 처리한다.

## Finished

Cilium CNI에 대해서 간단히 알아보고 내 EKS에 VPC CNI와 어떻게 잘 연결하여 사용할 수 있을지 알아보았다. 다음 포스팅에서는 위 내용을 토대로 내 EKS에 Cilium CNI를 설치하는 과정을 포스팅해보겠다.
