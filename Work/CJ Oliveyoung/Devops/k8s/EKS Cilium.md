## VPC CNI vs. Cilium CNI
EKS에서는 기본적으로 VPC CNI를 사용한다.
VPC CNI는 iptables 방식의 네트워킹을 사용하는데 이 iptables 방식은 pod수가 늘어나면 늘어날 수록 부하가 증가하면 latency가 지속적으로 증가한다.
- Standard networking vs. Cilium Networking
	![[Pasted image 20250524151234.png]]
- compare eBPF vs. kube-proxy latency
	![[Pasted image 20250524154507.png]]
### iptables vs. eBPF
- iptables
	- 
- eBPF
	- 
### VPC CNI
- Primary ENI + Secondary ENI
	- VPC내 IP를 다이렉트로 사용
	- EC2 Node type마다 가능한 Primary ENI개수와 Secondary ENI개수가 존재
		- EC2 Node의 CPU/Memory 리소스에 상관없이 IP 개수로 인한 Pod 제한 발생
		- IP Prefix를 통해서 해결이 가능하긴 하지만 IP를 미리 예약하는 형태의 방식
		- 
- iptables
	- dasfs
- ELB -> Pod
	- iptables를 통한 통신이 아닌 ELB에서의 direct 통신
### Cilium CNI
- eBPF
- Pod <-> Pod
	- 실질적으로 대부분의 통신은 Pod <-> Pod 통신이 주를 이룸
	- Service를 LoadBalancer, NodePort로 노출하는 것이 아니라 Ingress 혹은 Gateway api를 통해서 ingress Pod or Gateway pod -> Cluster IP Service -> Service Pod로 통신
	- ELB -> Gateway Pod -> Service Pod
## Install Cilium in EKS
### Remove VPC CNI
- Remove addon
	- vpc-cni
	- kube-proxy
- Delete aws-node service & aws-node deployment
	- vpc-cni는 addon만 제거한다고 해서 k8s상에서 삭제되지 않음
	- 직접 k8s에 접속해서 aws-node에 대한 service/deployment를 삭제해줘야됨
### Install Cilium Helm chart
- 




### [How Meltwater migrated from the Amazon VPC CNI plugin to Cilium in K8s](https://www.youtube.com/watch?v=w6S6baRHHu8&list=PLDg_GiBbAx-kDXqDYimwytMLh2kAHyMPd&t=182s)

https://docs.cilium.io/en/stable/installation/cni-chaining-aws-cni/#chaining-aws-cni
https://docs.cilium.io/en/stable/network/concepts/ipam/eni/#ipam-eni