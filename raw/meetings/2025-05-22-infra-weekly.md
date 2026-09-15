
## EKS Control Plane Loggin
- ISMS 인터뷰할 때 Lens를 통한 접근에 대해서 문의가 들어왔음(from. 여인보님)
	- lens나 이런 걸로 pod에 접근, control plane에 접근하는 것에 대한 로깅이 필요한데 어떻게 해야되는가
		- AWS Guard duty를 사용하면 됨
		- EKS에 Gurad duty addons가 존재하고 해당 addons를 추가하면 자동적으로 control plane 및 dataplane에 대한 로깅 완료


## Document DB Global cluster
- DNS 등록을 통한 최단시간 downtime
		1. Route53에 endpoint 추가
		2. seoul region cluster endpoint 적용
		3. Document DB Switch over
		4. Writer DB 변경되는 down time 시간 동안 Route53에 endpoint virginia로 변경
		5. TTL은 0으로 설정

### Snowflake PrivateLink 현재 불가
https://docs.snowflake.com/ko/user-guide/intro-editions#overview-of-editions
Business Critical Edition 이상이 되어야 가능
현재는 Enterprise 사용중

