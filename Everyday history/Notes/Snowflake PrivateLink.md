
## Context
현재 snowflake와의 통신을 NAT Gateway을 통해서 public network로 통신 중
보안상의 이유 + snowflake 특성상 많은 양의 네트워크트래픽 처리

이 이유로 비용감소와 보안상의 이유로 VPC Snowflake 통신을 내부망 통신을 하도록 변경해야됨

Snowflake의 경우 AWS PrivateLink를 통한 Private 통신을 지원하고 있음

### 현재 적용 불가
Business edition price에서만 적용 가능
https://docs.snowflake.com/ko/user-guide/admin-security-privatelink#enabling-aws-privatelink
여기에 나온 select SYSTEM$AUTHORIZE_PRIVATELINK ( '<aws_id>' , '<federated_token>' ); 함수가 business edition이상 부터 사용 가능