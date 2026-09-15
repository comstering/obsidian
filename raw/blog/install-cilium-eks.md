---
type: source
date: 2025-09-01
confidential: public
tags: [blog, kubernetes]
---

# EKS에 Cilium CNI 설치하기 (with CNI Chaining AWS VPC CNI Plugin)

> Source: https://comstering.github.io/posts/install-cilium-eks (본인 블로그, repo: comstering.github.io/posts/install-cilium-eks.md)
> Collected: 2026-09-15
> Published: 2025-09-01

<!-- 발행 시점 스냅샷. 블로그 원본이 갱신되면 이 파일은 따라가지 않는다. -->


## Cilium CNI

### Networking Mode

Cilium에는 Networking Mode가 2가지로 구분된다.

- Overlay: 캡슐화 기반 가상 네트워크
- Native routing: Linux Host의 라우팅 테이블을 사용

### AWS VPC CNI Chaining

AWS VPC CNI와 Chaining을 할 때는 위 두 모드 중에서 Native routing mode를 사용해야한다.

Native Routing에능 아래와 같은 내용이 적혀있다.

When to use this mode: This mode is for advanced users and requires some awareness of the underlying networking infrastructure. This mode works well with:

- Native IPv6 networks
- In conjunction with cloud network routers
- If you are already running routing daemons

AWS VPC CNI를 사용하면 routing daemon을 AWS VPC CNI가 담당하기 때문에 overlay mode가 아닌 Native routing mode로 네트워킹을 선택해야한다.

## Install Cilium CNI in EKS

### helm values

```yaml
# Kube-Proxy를 삭제할 경우 반드시 필요
k8sServiceHost: { eks-api-endpoint }
k8sServicePort: 443

cluster:
  name: { cluster name }
  id: 1

# CNI 설정: VPC CNI와 chaining 모드로 사용
cni:
  chainingMode: aws-cni # AWS CNI와 연결되는 chaining 모드 사용
  exclusive: false # aws-node DaemonSet도 계속 실행되도록 허용

# Cilium 설정: ENI 기반 라우팅을 사용하여 VPC와 통합
routingMode: native # 네이티브 라우팅 모드를 사용하여 터널링을 비활성화합니다.

# Masquerade (SNAT) 설정: 필요한 경우에만 eBPF를 사용하여 SNAT 수행
bpf:
  masquerade: true # 활성화를 하면 ipv4NativeRoutingCIDR values에 해당하는 대역과 native Route Table에서 local로 보내는 Rule이 있는 대역 제외 모든 대역에 대해 eBPF를 활용한 SNAT 활성화
#  # 이 설정은 cni chaining을 하고 있다면 사용 불가
#  hostLegacyRouting: false   # host network에서 발생하는 트래픽에 대해 legacy routing(iptables)를 사용하지 않도록 설정, eBPF를 사용하여 처리

# bpf.masquerade 설정: eBPF 기반 SNAT 활성화(NodePort 활설화 필수)
nodePort:
  enabled: true # NodePort 서비스에 대한 eBPF 기반 처리 활성화

# Cilium 설정: eBPF 소켓 로드 밸런싱
socketLB:
  enabled: true # Cilium의 eBPF 소켓 로드 밸런싱 기능 활성화
  hostNamespaceOnly: true # 호스트 네임스페이스에만 적용하도록 설정 for integration istio (https://docs.cilium.io/en/latest/network/servicemesh/istio/)
  tracing: true # eBPF 소켓 로드 밸런싱 트레이싱 활성화 (디버깅 용도)

# Cilium 설정: 호스트 방화벽
hostFirewall:
  enabled: true # 호스트 방화벽 기능 활성화

# Cilium 설정: 엔드포인트 라우팅
endpointRoutes:
  enabled: true # Cilium 엔드포인트 라우팅 활성화 (Pod 간 통신을 위한 라우팅)

# egress gateway 기능
egressGateway:
  enabled: true # 특정 목적지에만 SNAT을 적용하고 싶을 때 true

# Cilum 설정: Pod ip 대역
ipv4NativeRoutingCIDR: "100.64.0.0/18" # Pod Custom Networking CIDR 설정

# Cilium 설정: IP Masquerade Agent
ipMasqAgent:
  enabled: true
  config:
    nonMasqueradeCIDRs:
      - 10.0.0.0/16

# kube-proxy 대체: 완전히 제거하고 Cilium이 eBPF로 서비스 처리를 담당
kubeProxyReplacement: true # iptables와 kube-proxy 완전히 제거

# Cilium 설정: istio와의 통합
envoy:
  enabled: false # Istio와의 통합을 위해 Envoy를 사용하지 않도록 설정 (Istio가 자체적으로 Envoy를 관리)

# Cilium resources 설정
resources:
  requests:
    cpu: 100m
    memory: 512Mi
  limits:
    memory: 512Mi

# Hubble (가시성/관측 도구) 설정
hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: true

# Prometheus 모니터링 (선택)
prometheus:
  enabled: true
  serviceMonitor:
    enabled: true

# 디버깅 로깅 수준 (선택)
debug:
  enabled: true
```

내가 설정한 helm values는 위와 같다. 이미 AWS VPC CNI가 배포되어 있는 상태이기 때문에 위 helm values를 통해서 Cilium CNI를 helm install해서 배포했다.

```bash
# Cilium repo add
helm repo add cilium https://helm.cilium.io/
# helm repo update
helm repo update
# Cilium Install
helm upgrade --install cilium cilium/cilium -f values.yaml -n kube-system
```

### Node taint 설정

Cilium을 설치하면서 networking은 Cilium이 담당하게 된다. 즉, Cilium Pod가 정상적으로 Running되기 전에는 Node에 다른 Pod들이 설치되거나 실행되면 안되다.

그래서 이러한 설정을 해주기 위해 taint를 설정한다.

#### default node group

```
resource "aws_eks_node_group" "default_node_group" {
  # 중략

  # cilium cni가 실행되기 전에 다른 pod들이 scheduling 되지 않도록 한다.
  taint {
    key    = "node.cilium.io/agent-not-ready"
    value  = "true"
    effect = "NO_EXECUTE"
  }
}
```

#### karpenter nodepool

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: { { .Values.nodePool.name } }
spec:
  template:
    # 중략
    spec:
      startupTaints:
        - key: node.cilium.io/agent-not-ready
          value: "true"
          effect: NoExecute
      # 중략
```

### Remove kube-proxy

Cilium을 이용해서 kube-proxy를 대체하고 있기 때문에 EKS의 kube-proxy addon을 제거했다.

나는 terraform으로 관리하고 있었기 때문에 eks addon에서 kube-proxy만 제거했다.

```
resource "aws_eks_addon" "kube_proxy" {
  cluster_name  = aws_eks_cluster.main.name
  addon_name    = "kube-proxy"
  addon_version = "v1.33.0-eksbuild.2"
}
```

이 부분을 제거했다.

### Result

![installed-cilium](/images/posts/contents/install-cilium-eks/installed-cilium.png)

AWS VPC CNI의 DaemonSet이 aws-node pod와 Cilium CNI의 DaemonSet이 Cilium pod가 동시에 실행되서 정상적으로 동작중인 것을 볼 수 있다.

![cilium-status](/images/posts/contents/install-cilium-eks/cilium-status.png)

Cilium pod에 접속해서 cilium status 명령어를 실행해보면 AWS CNI와 chaining이 정상적으로 되어 있고 라우팅이 Native routing을 사용하는 것을 볼 수 있다.

#### Hubble monitor

hubble UI를 통해서 k8s의 namespace별 network를 볼 수 있다.

![hubble-ui](/images/posts/contents/install-cilium-eks/hubble-ui.png)

hubble ui를 보면 어떤 components들 간에 네트워크 통신을 하고 있는지 ingress, egress, ip, port, identity까지 확인할 수 있다.
