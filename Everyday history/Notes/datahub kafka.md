front-end, gms, mae, mce는 모두 java, spring 기반 서비스라서 SASL_SSL, AWS_MSK_IAM 인증방식 가능...

문제는 datahub-actions인데
GMS에서 ingestion을 할 때 datahub-actions를 사용
datahub-actions를 python 기반 프로그램
AWS_MSK_IAM 인증 불가

SASL_SSL/SCRAM 인증방식만 가능


### Solution
일단 datahub prerequisites의 kafka chart를 이용해서 k8s chart에 임시 kafka 배포

추후 MSK를 사용할 지 kafka를 k8s에 배포한 것으로 사용할지 확인