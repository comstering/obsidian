## VPC CNI vs. Cilium CNI
EKS에서는 기본적으로 VPC CNI를 사용한다.
VPC CNI는 iptables 방식의 네트워킹을 사용하는데 이 iptables 방식은 pod수가 늘어나면 늘어날 수록 부하가 증가하면 latency가 지속적으로 증가한다.
### iptables vs. eBPF
![[Pasted image 20250524151234.png]]

![[Pasted image 20250524154507.png]]

## Install Cilium in EKS






### [How Meltwater migrated from the Amazon VPC CNI plugin to Cilium in K8s](https://www.youtube.com/watch?v=w6S6baRHHu8&list=PLDg_GiBbAx-kDXqDYimwytMLh2kAHyMPd&t=182s)

https://docs.cilium.io/en/stable/installation/cni-chaining-aws-cni/#chaining-aws-cni
https://docs.cilium.io/en/stable/network/concepts/ipam/eni/#ipam-eni