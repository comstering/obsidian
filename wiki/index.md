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
| [중앙 클러스터 하나의 Kiali로 멀티 클러스터 보기](kubernetes/kiali-multi-cluster-central.md) | Kiali는 Prometheus URL을 하나만 받는다. 각 클러스터가 중앙 metrics store로 push하는 구조 | 2026-11-18 |

## identity

Keycloak·IdP 연동, 인증 서버 운영.

| Article | Summary | Updated |
|---------|---------|---------|
| [Keycloak 26.8.2 Admin API audience 검사와 Terraform provider 인증 실패](identity/keycloak-admin-api-audience-check.md) | 26.8.2부터 Admin API가 토큰 aud를 검사해 provider client_credentials 인증이 깨진다 | 2026-11-18 |
| [Keycloak IdP 첫 로그인 시 기존 사용자 자동 연결](identity/keycloak-first-broker-login-auto-link.md) | 기본 first broker login flow 대신 커스텀 flow로 기존 계정에 IdP 자동 연결 | 2026-11-18 |

## aws

AWS CLI·계정 접근 등 AWS 공통 운영.

| Article | Summary | Updated |
|---------|---------|---------|
| [SSL 검사 프록시 환경에서 AWS CLI 인증서 오류](aws/aws-cli-ssl-inspection-proxy.md) | CLI v2는 자체 CA 번들을 써서 프록시 루트 CA를 모른다. AWS_CA_BUNDLE이 현재 셸에 잡혔는지 확인 | 2026-11-18 |

## kafka

MSK 운영, 인증 방식 제약, CDC 파이프라인 트러블슈팅.

| Article | Summary | Updated |
|---------|---------|---------|
| [MSK IAM 인증과 JVM 한정 제약](kafka/msk-iam-authentication.md) | AWS_MSK_IAM은 자바 클래스 기반이라 JVM 클라이언트 전용. DataHub의 python 컴포넌트가 여기서 막혔다 | 2026-09-15 |
| [Kafka 토픽 파티션 수 늘리기](kafka/kafka-partition-increase.md) | kafka-topics.sh --alter 절차와 MSK IAM 인증 시 CLASSPATH 설정 | 2026-09-15 |
| [Debezium MySQL 커넥터 무증상 정지](kafka/debezium-silent-failure.md) | status는 running & healthy인데 CDC도 heartbeat도 멈추는 상태 | 2026-09-15 |
