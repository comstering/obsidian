# Wiki Log

<!-- Format: ## [YYYY-MM-DD] <action> | <subject>. Actions: ingest / query / lint. Append-only. -->

## [2026-09-15] setup | KB 구조 전환

- karpathy-llm-wiki 스킬 설치 (`.agents/skills/`)
- 기존 47개 노트를 `raw/` 로 이관, frontmatter 부여, 위키링크 kebab-case 보정
- `raw/` 불변 규칙은 이 시점부터 적용
- `Private/` 는 파이프라인 범위 밖으로 제외

## [2026-09-15] ingest | Cilium 개요 — eBPF 기반 CNI
- Disposition: New
- Raw: raw/kubernetes/cilium.md

## [2026-09-15] ingest | EKS VPC CNI → Cilium 전환
- Disposition: New
- Raw: raw/kubernetes/eks-cilium.md

## [2026-09-15] ingest | AWS VPC Secondary CIDR과 TGW 라우팅 문제
- Disposition: New
- Raw: raw/kubernetes/aws-vpc-secondary-cidr.md
- Updated: EKS VPC CNI → Cilium 전환 (Secondary CIDR/TGW 건을 Cilium 선택 근거로 교차 참조 추가)

## [2026-09-15] ingest | Istio service mesh에서 JWT 인증 처리
- Disposition: New
- Raw: raw/kubernetes/istio-l7-network-policy.md
- Core finding: RequestAuthentication 단독으로는 토큰 없는 요청이 통과한다. 경로를 잠그는 건 AuthorizationPolicy

## [2026-09-15] ingest | no material: raw/kubernetes/eks.md
- Disposition: No material

## [2026-09-15] lint | 9 issues found, 5 auto-fixed
- 4건 자동수정: article에 H1 제목 누락 → Raw 필드 인식 실패 (파서는 H1 직후 blockquote만 메타데이터로 인정)
- 1건 자동수정: 편집자 주석을 본문 blockquote로 작성 → 스크립트가 인용문으로 보고 근거 요구
- 4건 미해결: frontmatter `updated:` 가 fidelity suspect로 잡힘. 파서가 preamble을 body에 합치기 때문.
  구조적 충돌이라 방침 결정 필요

## [2026-09-15] lint | 4 issues found, 4 auto-fixed
- frontmatter에서 `updated` 제거로 결정. 문서 최신성은 index.md의 Updated 컬럼이 담당
- CLAUDE.md에 H1 필수 규칙, frontmatter 날짜·숫자 금지 규칙 추가
- 결과: 0 fidelity suspect, 0 evidence error

## [2026-09-15] ingest | MSK IAM 인증과 JVM 한정 제약
- Disposition: New
- Raw: raw/kafka/aws-msk-increase-partitions.md; raw/kafka/datahub-kafka.md
- Core finding: AWS_MSK_IAM 설정값이 자바 클래스 경로라 JVM 클라이언트 전용. python 기반 datahub-actions가 이 때문에 SCRAM만 가능

## [2026-09-15] ingest | Kafka 토픽 파티션 수 늘리기
- Disposition: New
- Raw: raw/kafka/aws-msk-increase-partitions.md

## [2026-09-15] ingest | Debezium MySQL 커넥터 무증상 정지
- Disposition: New
- Raw: raw/kafka/debezium-mysql-connector.md
- Core finding: status는 running & healthy인데 heartbeat까지 끊긴다. status 헬스체크로 감지 불가

## [2026-09-15] ingest | no material: raw/kafka/aws-msk.md
- Disposition: No material

## [2026-09-15] ingest | no material: raw/kafka/kafka-connect.md
- Disposition: No material

## [2026-09-15] ingest | no material: raw/kafka/parallel-consumer.md
- Disposition: No material

## [2026-09-15] ingest | 블로그 포스트 5건을 raw/blog/ 스냅샷으로 편입
- Disposition: New
- Raw: raw/blog/introduce-cilium-cni.md; raw/blog/install-cilium-eks.md; raw/blog/troubleshoot-cilium.md; raw/blog/eks-custom-networking.md; raw/blog/custom-networking-karpenter-eni-troubleshooting.md
- 블로그가 vault raw보다 완성도가 높아 역방향 편입. 앞으로는 wiki -> post 정방향

## [2026-09-15] ingest | EKS에서 VPC CNI와 Cilium CNI Chaining
- Disposition: New; Disputed
- Raw: raw/blog/introduce-cilium-cni.md; raw/blog/install-cilium-eks.md
- Core finding: VPC CNI를 제거하지 않는다. chaining으로 병행하고 kube-proxy만 제거
- Updated: eks-cni-migration 폐기 (제목·내용이 사실과 달라 eks-cilium-cni-chaining으로 대체, Status: Outdated 블록으로 이전 계획 보존)
- Updated: EKS Custom Networking (블로그 근거로 전면 재작성, CIDR 범위 불일치 발견)
- Updated: Cilium 개요 (See Also 갱신)

## [2026-09-15] ingest | Cilium 미관리 Pod 문제
- Disposition: New
- Raw: raw/blog/troubleshoot-cilium.md
- Core finding: aws-node를 unmanagedPodWatcher 대상에서 반드시 제외해야 한다. chaining 구성에서만 생기는 함정

## [2026-09-15] post | draft: Istio로 JWT 인증을 Service Mesh에서 처리하기
- 출력: ~/Side/comstering.github.io/posts/istio-jwt-authentication.md
- 원본: wiki/kubernetes/istio-jwt-authentication.md
- 내부 호스트명·realm·리소스명을 placeholder로 치환 (confidential: internal -> public)
