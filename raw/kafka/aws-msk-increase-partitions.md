
### Using Apache kafka native tool

1. [apache kafka download](https://kafka.apache.org/downloads)
2. (if using AWS SASL_SSL/IAM Authentication)
	1. Create `client.properteis`
	   ```properties
	   security.protocol=SASL_SSL
	sasl.mechanism=AWS_MSK_IAM
	sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
	sasl.client.callback.handler.class=software.amazon.msk.auth.iam.IAMClientCallbackHandler

	2. downdload aws msk auth
		```bash
		wget https://github.com/aws/aws-msk-iam-auth/releases/download/v2.3.2/aws-msk-iam-auth-2.3.2-all.jar
1. Increase number of partition
	```bash
	./bin/kafka-topics.sh \
  --bootstrap-server {broker-endpoint} \
  --alter \
  --topic my-topic \
  --partitions 12 \
  --command-config client.properties
  // if using aws-msk-auth
  CLASSPATH=aws-msk-iam-auth-2.3.2-all.jar ./bin/kafka-topics.sh \
  --bootstrap-server b-1.my-msk-cluster.abcde.c2.kafka.amazonaws.com:9098 \
  --alter \
  --topic my-topic \
  --partitions 12 \
  --command-config client.properties
