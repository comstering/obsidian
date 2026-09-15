---
type: source
date: 2025-07-08
confidential: public
tags: [blog, kubernetes]
---

# EKS Custom Networking

> Source: https://comstering.github.io/posts/eks-custom-networking (본인 블로그, repo: comstering.github.io/posts/eks-custom-networking.md)
> Collected: 2026-09-15
> Published: 2025-07-08

<!-- 발행 시점 스냅샷. 블로그 원본이 갱신되면 이 파일은 따라가지 않는다. -->


## VPC CNI

### VPC CNI의 Pod IP 할당

![not-custom-network](/images/posts/contents/eks-custom-networking/not-custom-network.png)

Pod의 IP를 보면 VPC의 Subnet IP를 그대로 할당받는 것을 볼 수 있다. 이건 VPC CNI의 Pod CNI 할당 방식인데 바로 Node의 Secondary ENI를 그대로 Pod에 할당해서 VPC의 IP 대역을 그대로 Pod가 사용한다.

### ENI IP의 장점

VPC CNI의 이런 ENI IP 할당하는 방식에는 큰 장점이 있다.

1. Security Group 설정

   VPC CNI는 VPC 대역의 IP를 그대로 사용한다. 그래서 EKS의 Pod 외의 RDS, Redis 등 AWS Resource를 VPC에 Provision했을 때 Security group 설정을 VPC 내부 대역으로 그대로 사용할 수 있어서 Pod가 자체 IP를 갖는 것 보다 훨씬 간단한 rule을 지정할 수 있다.

2. IP direct connect

   Pod가 VPC의 내부 IP를 그대로 할당받아서 사용하다 보니 Pod간 통신 뿐 아니라 VPC내에 Provisioning 되어 있는 다른 리소스들과도 IP를 통해서 VPC 라우팅 테이블로 바로 direct 통신이 가능하다. 대표적인 예로 AWS Elastic Load Balancer가 Node instance를 거치지 않고 Pod로 바로 direct 통신이 가능해서 Network hop이 줄어드는 효과를 가져올 수도 있다.

## Subnet에 Pod가 할당받을 IP가 부족하다고?

위의 이런 VPC CNI의 ENI를 활용한 CNI 방법은 많은 장점을 주지만 여러 단점들을 주기도 한다. 이번 포스팅에서는 그 중 Subnet에 할당할 수 있는 IP가 부족해지는 문제와 해결법을 확인해보려고 한다.

### 여러 VPC 간의 Networking

개인 Side Project나 규모가 작은 프로젝트성 네트워크 구성에서는 거의 일어나지 않는 일이다. 실제로 나도 이것 때문에 문제가 될거라고는 생각하지 못했던 내용이기도 하다.

우리는 VPC를 하나만 쓰는게 아니라 여러 팀에서 각자 VPC를 생성해서 서비스를 운영하고 있다. 여기서 여러 팀들이 서로의 서비스와 통신해야되기 때문에 Transit Gateway를 통해서 서로간의 VPC가 통신한다.

![tgw-networking](/images/posts/contents/eks-custom-networking/tgw-networking.png)

### VPC CIDR 대역을 자유롭게 설정하지 못하는 제한이 있어요

TGW는 가운데에서 서로 다른 VPC의 네트워크를 처리해줘야한다. 이때 TGW가 각 VPC에 대해서 라우팅을 진행해줘야되기 때문에 VPC들의 IP 대역은 서로 겹치면 안된다.

그래서 우리도 IP를 VPC에 마음대로 할당할 수 없는 상태였고 관리팀에서 `/21` netmask의 크기로 VPC CIDR block을 할당해주었다.

/21 netmask가 작아보이진 않지만 우리 입장해서는 해당 VPC 대역에 public subnet, private subnet, db subnet 등 용도와 public, private 영역에 맞춰 구분을 해야되었고 최종적으로 EKS Node 및 Pod, 그리고 MSK, Private ELB 등 Application에 관련된 private 대역은 netmask /24 대역의 subnet 3개를 사용하게 되었다.

### Subnet의 IP 부족

netmask /24 대역은 할당 가능한 ip가 수학적으로는 256개이고 3개의 subnet이 있으니 대충 760개 정도의 IP를 사용 가능했다. 하지만 VPC CNI의 Pod IP 할당 방식은 이 Subnet의 IP를 빠른 시간에 다 소모시키기 시작했다.

Pod가 사용하는 IP의 개수는 생각보다 더 많았고 Subnet에는 점점 Pod가 할당 받을 IP가 부족해졌다. 거기에 MSK와 같은 Private Network에 Provisioning한 리소스들과 Private ELB의 IP 사용까지 더해져 EKS에서 Pod에 할당할 수 있는 IP가 더이상 없다는 Error Event와 함께 Pod들이 Scheduling 되지 못하는 사태까지 벌어졌다.

## How to Fix?

### VPC Secondary CIDR

AWS VPC에는 기존 VPC를 생성할 때 정해놨던 CIDR 대역에 추가로 CIDR 대역을 더 추가할 수 있다.

- [VPC IPv4 CIDR Block](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/vpc-cidr-blocks.html#add-cidr-block-restrictions)
- [VPC CIDR Block 추가](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/add-ipv4-cidr.html)

#### CGNAT 대역

AWS VPC에서는 자신이 할당한 10.0.0.0/x와 같은 CIDR block 대역말고 추가적인 대역을 기존 VPC에 Secondary CIDR Block으로 추가할 수 있게 해준다.

바로 [CGNAT 대역](https://www.purevpn.com/kr/blog/what-is-cgnat/)인 100.64.0.0/10 대역이다. 기존 VPC에 할당할 수 있는 CIDR 대역인 [RFC 1918](http://www.faqs.org/rfcs/rfc1918.html) 대역말고 추가로 VPC에 할당 할 수 있는 CIDR block 대역이다.

이 대역은 일반적인 사설 IP 대역과는 다른 IP 대역으로 TGW나 VPC Peering을 했을 때 다른 VPC와 대역이 겹치지 않는다. 즉, 내 VPC 내부에서만 사용되는 CIDR 대역인 것이다.

### EKS Custom Networking

EKS에서는 [Custom Networking](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/cni-custom-network.html)이라는 기능을 지원한다.

EKS에서 pod는 기본적으로 Node와 동일한 subnet에서 ip를 할당 받는다. 그 이유는 Pod의 CNI를 Node의 Secondary ENI를 통해서 할당하기 때문이다.

Custom Networking은 Node의 Secondary ENI를 Node와 다른 Subnet에 할당하여 Pod의 CNI를 Node와 다른 Subnet으로 할당하는 방법이다.

![custom-networking](/images/posts/contents/eks-custom-networking/custom-networking.png)

_출처: [AWS Documentation](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/cni-custom-network.html)_

### 해결방법

위에서 말한 CGNAT 대역의 VPC Secondary CIDR과 EKS Custom Networking을 사용하면 IP 부족문제를 해결할 수 있게 된다.

1. Secondary CIDR로 CGNAT 대역에서 큰 netmask로 생성
2. EKS Custom Networking의 대상 Subnet을 해당 CGNAT 대역의 Subnet으로 설정

## Go to Fix!

### VPC Secondary CIDR & Subnet

먼저 VPC Secondary CIDR과 해당 CIDR Block에 Subnet을 추가한다.

```hcl

locals {
  custom_networking = {
    vpc_cidr = "100.64.0.0/17"
    subnet_cidrs = ["100.64.0.0/19", "100.64.32.0/19", "100.64.64.0/19"]
  }
}

resource "aws_vpc_ipv4_cidr_block_association" "pod_custom_networking" {
  vpc_id     = aws_vpc.main.id
  cidr_block = locals.custom_networking.vpc_cidr
}

resource "aws_subnet" "pod_custom_networking" {
  vpc_id = aws_vpc.main.id
  count  = length(locals.custom_networking.subnet_cidrs)

  cidr_block        = locals.custom_networking.subnet_cidrs[count.index]
  availability_zone = local.az[count.index % var.availability_zone_count]

  tags = {
    Name = "${var.name.vpc}-${var.name.pod_custom_networking_subnet}-${format("%02s", count.index)}-${local.az[count.index % var.availability_zone_count]}"
  }

  depends_on = [aws_vpc_ipv4_cidr_block_association.pod_custom_networking]
}
```

### EKS VPC CNI Addon Advanced Configuration

VPC CNI addon에서 EKS Custom Networking을 사용할 수 있도록 config를 추가한다.

```hcl
resource "aws_eks_addon" "vpc_cni" {
  cluster_name  = aws_eks_cluster.main.name
  addon_name    = "vpc-cni"
  addon_version = "v1.19.5-eksbuild.3"

  // 아래 config 추가
  configuration_values = jsonencode({
    env = {
      AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG = "true"
      ENI_CONFIG_LABEL_DEF               = "topology.kubernetes.io/zone"
    }
  })
}
```

### EKS ENI Config 설정 (using kubernetes provider)

이제 VPC CNI 설정이 다 마쳐졌으면 새 Pod들이 Node와 같은 subnet이 아닌 새로 추가된 subnet으로 Scheduling될 수 있도록 ENIConfig를 추가해줘야한다.

일반적인 kubectl 명령어로 local에서 바로 적용할 수도 있지만 subnet id나 subnet의 AZ를 사용해야되고 코드로써 해당 적용 내용의 이력을 남기기 위해서 Terraform에서 Kubernetes Provider를 추가했다.

#### Kubernetes Provider

```hcl
data "aws_eks_cluster" "main" {
  name = aws_eks_cluster.main.name
}

data "aws_eks_cluster_auth" "main" {
  name = aws_eks_cluster.main.name
}

# If use terraform cloud
# You need eks access entry add terraform cloud role
provider "kubernetes" {
  host                   = data.aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}
```

#### ENIConfig

```hcl
data "aws_subnet" "pod_custom_networking" {
  count = length(locals.custom_networking.subnet_cidrs)
  id    = aws_subnet.pod_custom_networking[count.index].id
}

resource "kubernetes_manifest" "eni_config" {
  count = length(locals.custom_networking.subnet_cidrs)
  manifest = {
    apiVersion = "crd.k8s.amazonaws.com/v1alpha1"
    kind       = "ENIConfig"
    metadata = {
      name = "${data.aws_subnet.pod_custom_networking[count.index].availability_zone}"
    }
    spec = {
      securityGroups = [
        aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
      ]
      subnet = "${data.aws_subnet.pod_custom_networking[count.index].id}"
    }
  }
}
```

## Result

node ip는 10.x.x.x 대역인 것에 대비해서 Pod의 IP는 100.64.x.x 대역인 것을 확인할 수 있다.

![custom-networking-result](/images/posts/contents/eks-custom-networking/custom-networking-result.png)

나는 대역을 netmask /19 대역으로 3개 설정했다. 대충 24,000개의 IP를 사용할 수 있게 된 것이다. 기존 760개 정도 할당 가능했던 IP개수와 비교하면 약 31배 정도 더 많아진 양이다. 계속 Pod 수가 늘고 서비스가 많아지면 해당 대역의 IP가 부족해질 수도 있겠지만 그러면 다시 또 새로운 CIDR Block을 추가해서 100.64.x.x 대역을 추가하면 된다.

이 방법을 통해서 관리팀에게 추가 IP를 할당해달라고 요청을 하지 않고도 Pod의 IP 부족 문제를 해결하였다.

### Reference

- [VPC CIDR Block](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/vpc-cidr-blocks.html)
- [EKS Custom Networking](https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/cni-custom-network.html)
- [EKS Best Practice Custom Networking](https://docs.aws.amazon.com/ko_kr/eks/latest/best-practices/custom-networking.html)
