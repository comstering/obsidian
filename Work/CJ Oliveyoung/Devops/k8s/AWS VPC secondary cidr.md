
https://docs.aws.amazon.com/ko_kr/eks/latest/best-practices/custom-networking.html


https://yongho1037.notion.site/Amazon-EKS-Custom-Network-c0eb5c5a04304d228c2d2b4d90db166c


Secondary cidr을 추가하면 자동으로 routing table에 secondary cidr이 등록됨

![[Pasted image 20250612171358.png]]


![[스크린샷 2025-06-12 오후 3.14.12.png]]


문제점
Pod IP가 100.64.0.0/10 대역일 경우 TGW를 통한 다른 VPC와의 통신이 불가
outbond rule에 추가는 가능하지만 다른 VPC의 Routing table에는 100.64.0.0/10 대역에 대해서 등록이 안되어 있기 때문에 response 응답 라우팅이 안됨.


masquerade를 통해서 SNAT 설정필요
-> 이것 때문에 Cilium을 사용하는게 처리하기 편할 것 같음
Cilium을 사용하지 않을 경우 DaemonSet을 추가하거나 각 Pod에 init container관련 작업을 추가로 해줘야함
