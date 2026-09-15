# Knowledge Base Index

<!-- 에이전트 진입점. 인제스트할 때마다 갱신된다. 손으로 쓰지 않는다. -->

## kubernetes

EKS 운영, CNI 선택과 전환, service mesh 기반 인증.

| Article | Summary | Updated |
|---------|---------|---------|
| [Cilium 개요 — eBPF 기반 CNI](kubernetes/cilium-overview.md) | eBPF 기반 CNI의 identity 보안·네트워킹 모드·로드밸런싱·관측 정리 | 2026-09-15 |
| [EKS에서 VPC CNI와 Cilium CNI Chaining](kubernetes/eks-cilium-cni-chaining.md) | VPC CNI를 유지한 채 Cilium을 얹는 chaining 구성. 제거한 건 kube-proxy뿐 | 2026-09-15 |
| [Cilium 미관리 Pod 문제](kubernetes/cilium-unmanaged-pod.md) | taint를 무시하는 toleration 때문에 생긴 unmanaged Pod와 unmanagedPodWatcher 해결 | 2026-09-15 |
| [EKS Custom Networking — Pod IP 고갈 해결](kubernetes/aws-vpc-secondary-cidr.md) | CGNAT 대역 Secondary CIDR로 IP 760개를 24,000개로. 대가는 TGW 응답 라우팅 단절 | 2026-09-15 |
| [Istio service mesh에서 JWT 인증 처리](kubernetes/istio-jwt-authentication.md) | RequestAuthentication + AuthorizationPolicy 조합으로 경로별 JWT 검증 | 2026-09-15 |

## kafka

MSK 운영, 인증 방식 제약, CDC 파이프라인 트러블슈팅.

| Article | Summary | Updated |
|---------|---------|---------|
| [MSK IAM 인증과 JVM 한정 제약](kafka/msk-iam-authentication.md) | AWS_MSK_IAM은 자바 클래스 기반이라 JVM 클라이언트 전용. DataHub의 python 컴포넌트가 여기서 막혔다 | 2026-09-15 |
| [Kafka 토픽 파티션 수 늘리기](kafka/kafka-partition-increase.md) | kafka-topics.sh --alter 절차와 MSK IAM 인증 시 CLASSPATH 설정 | 2026-09-15 |
| [Debezium MySQL 커넥터 무증상 정지](kafka/debezium-silent-failure.md) | status는 running & healthy인데 CDC도 heartbeat도 멈추는 상태 | 2026-09-15 |
