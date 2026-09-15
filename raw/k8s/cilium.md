
## What is Cilium
Cilium은 Docker 및 Kubernetes와 같은 Linux 컨테이너 관리 플랫폼을 사용하여 배포된 애플리케이션 서비스 간의 네트워크 연결을 투명하게 보호하기 위한 오픈 소스 소프트웨어입니다.

Cilium의 기반에는 eBPF라는 새로운 Linux 커널 기술이 있습니다. eBPF는 Linux 커널 내부에서 실행되므로 애플리케이션 코드나 컨테이너 구성을 변경하지 않고도 Cilium 보안 정책을 적용하고 업데이트할 수 있습니다.

## 주요 기능
### Protect and secure APIs transparently
기존 방화벽은 Layer 3과 Layer4에서 동작
특정 포트에서 실행하는 프로토콜은 완전히 신회되거나 완전히 차단 가능
개별 애플리케이션 프로토콜 요청을 필터링하는 기능 제공
### Secure service to service communication based on identities
최신 분산 애플리케이션은 애플리케이션 컨테이너와 같은 기술을 활용하여 배포의 민첩성을 높이고 필요에 따라 확장할 수 있습니다. 이로 인해 단시간에 많은 수의 애플리케이션 컨테이너가 실행됩니다. 일반적인 컨테이너 방화벽은 소스 IP 주소와 대상 포트를 필터링하여 워크로드를 보호합니다. 이러한 개념은 클러스터 내 어디에서든 컨테이너가 시작될 때마다 모든 서버의 방화벽을 조작해야 한다는 것을 의미합니다.
이러한 확장성 제한 상황을 방지하기 위해 Cilium은 동일한 보안 정책을 공유하는 애플리케이션 컨테이너 그룹에 보안 ID를 할당합니다. 이 ID는 애플리케이션 컨테이너에서 전송되는 모든 네트워크 패킷과 연결되어 수신 노드에서 ID의 유효성을 검사할 수 있습니다. 보안 ID 관리는 키-값 저장소를 사용하여 수행됩니다.
### Secure access to and from external services
레이블 기반 보안은 클러스터 내부 접근 제어에 적합한 도구입니다. 외부 서비스 접속을 보호하기 위해 수신 및 송신 모두에 기존 CIDR 기반 보안 정책이 지원됩니다. 이를 통해 애플리케이션 컨테이너 접속을 특정 IP 범위로 제한할 수 있습니다.
### Simple Networking
여러 클러스터에 걸쳐 확장 가능한 간단한 플랫 레이어 3 네트워크가 모든 애플리케이션 컨테이너를 연결합니다. 호스트 범위 할당자를 사용하여 IP 할당을 간소화합니다. 즉, 각 호스트는 호스트 간 조정 없이 IP를 할당할 수 있습니다.
- Overlay: 모든 호스트에 걸쳐 있는 캡슐화 기반 가상 네트워크입니다. 현재 VXLAN과 Geneve가 기본으로 내장되어 있지만, Linux에서 지원하는 모든 캡슐화 형식을 활성화할 수 있습니다.
	이 모드를 사용해야 하는 경우: 이 모드는 최소한의 인프라 및 통합 요구 사항을 갖습니다. 호스트 간 IP 연결만 요구되므로 거의 모든 네트워크 인프라에서 작동하며, 이는 일반적으로 이미 제공됩니다.
- Native Networking: Linux 호스트의 일반 라우팅 테이블을 사용합니다. 네트워크는 애플리케이션 컨테이너의 IP 주소를 라우팅할 수 있어야 합니다.
	이 모드를 사용해야 하는 경우: 이 모드는 고급 사용자를 위한 것이며, 기본 네트워크 인프라에 대한 이해가 필요합니다. 이 모드는 다음과 같은 경우에 적합합니다.
	- 네이티브 IPv6 네트워크
	- 클라우드 네트워크 라우터와 함께
	- 이미 라우팅 데몬을 실행 중이라면
### Load Balancing
Cilium은 애플리케이션 컨테이너 간 트래픽과 외부 서비스 트래픽에 대한 분산 로드 밸런싱을 구현하며, kube-proxy와 같은 구성 요소를 완전히 대체할 수 있습니다. 로드 밸런싱은 효율적인 해시테이블을 사용하여 eBPF로 구현되어 거의 무제한적인 확장을 지원합니다.

남북형 부하 분산(For north-south type load balancing)의 경우, Cilium의 eBPF 구현은 최대 성능을 위해 최적화되어 있으며, XDP(eXpress Data Path)에 연결할 수 있으며, 부하 분산 작업이 소스 호스트에서 수행되지 않는 경우 DSR(Direct Server Return)과 Maglev 일관성 해싱을 지원합니다.

동서 유형의 부하 분산(For east-west type load balancing)의 경우, Cilium은 Linux 커널의 소켓 계층에서 바로 효율적인 서비스-백엔드 변환을 수행합니다(예: TCP 연결 시). 이를 통해 하위 계층에서 패킷당 NAT 작업 오버헤드를 피할 수 있습니다.
### Bandwidth Management
Cilium은 노드를 떠나는 컨테이너 트래픽에 대해 효율적인 EDT(Earliest Departure Time) 기반 속도 제한과 eBPF를 통해 대역폭 관리를 구현합니다. 이를 통해 애플리케이션의 전송 지연 시간을 크게 줄이고 대역폭 CNI 플러그인에 사용되는 HTB(Hierarchy Token Bucket) 또는 TBF(Token Bucket Filter)와 같은 기존 방식과 비교하여 다중 큐 NIC에 의한 잠금 현상을 방지할 수 있습니다.
### Monitoring and Troubleshooting
가시성을 확보하고 문제를 해결하는 능력은 모든 분산 시스템 운영에 필수적입니다. `tcpdump`및 `ping`와 같은 도구를 애용하는 법을 배웠고, 이러한 도구들은 앞으로도 항상 저희 마음속에 특별한 자리를 차지할 것입니다. 저희는 문제 해결을 위한 더 나은 도구를 제공하기 위해 노력하고 있습니다. 여기에는 다음과 같은 도구가 포함됩니다.

- 메타데이터를 활용한 이벤트 모니터링: 패킷이 삭제되면 해당 도구는 패킷의 소스 및 대상 IP만 보고하는 것이 아니라, 보낸 사람과 받는 사람의 전체 레이블 정보를 비롯한 여러 정보를 제공합니다.
    
- Prometheus를 통한 지표 내보내기: 주요 지표는 기존 대시보드와 통합하기 위해 Prometheus를 통해 내보내집니다.
    
- [Hubble](https://github.com/cilium/hubble/) : Cilium을 위해 특별히 제작된 관측 플랫폼입니다. 서비스 종속성 맵, 운영 모니터링 및 알림, 그리고 흐름 로그를 기반으로 한 애플리케이션 및 보안 가시성을 제공합니다.








### Reference
https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/
https://isovalent.com/blog/post/why-replace-iptables-with-ebpf/

### Conference
https://www.youtube.com/watch?v=hmx4rP7EwV0