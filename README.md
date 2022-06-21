# Load test API Gateway and Lambda
## Test approach
The test client will be based on AWS solution of [Distributed Load Testing](https://www.amazonaws.cn/en/solutions/distributed-load-testing/) 
The test will be against API Gateway+Lambda or ALB+ Lambda.
## Test resources
The CDK stack LoadTestV2Stack in this repo is to set up
- API Gateway REST API integrated with fast lambda function (simple hello world python lambda function)
- API Gateway REST API integrated with slow lambda (hello world function with 1 second sleep)
- VPC and ALB target with slow lambda function

1. In account A where the concurrency has raised,
```
git clone https://github.com/yizhizoe/load_test_v2.git
cd load_test_v2
cdk bootstrap --profile <account A>
cdk deploy LoadTestV2Stack --profile <account A>
```
2. In account B for load test client, follow the [guide of distributed load testing solution](https://s3.cn-north-1.amazonaws.com.cn/aws-dam-prod/china/Solutions/distributed_load_testing/distributed-load-testing-platform-deployment-guide.pdf) and deploy the client. 
3. (optional) Prewarm ALB of step 1.

# Load test DynamoDB
## Test approach
The load test for DynamoDB is based on [YCSB workload generator for DynamoDB](https://github.com/brianfrankcooper/YCSB/tree/master/dynamodb). With multiple clients running the YCSB workload generator in parallel, this can load test with very high read/write capacity for DynamoDB. 

The repo provides CDK script to create 2 EC2 autoscaling group with desired number of EC2 instances and run load test using AWS Systems Manager Run Command. The 2 EC2 autoscaling group can load test 2 tables respectively at the same time.

## Test Resources

The CDK stack LoadTestV2Stack in this repo is to set up
- DynamoDB table named 'table_1' and 'table_2'
- VPC
- 2 Auto Scaling Group of c6g.4xlarge tagged with 'group_table_1' and 'group_table_2' respectively

To be cost efficient, the ASG will be initiated with 1 instance only to verify access. You can scale manually by changing the 'desired capacity' in load testing. 


## Prerequisite
 - S3 bucket for YCSB package and shared configuration file
 - AKSK to DynamoDB table with R/W privilege

## User Guide
0. As YCSB package is pretty large, it's recommended to download to local path.
1. Clone the repo.
```
export AWS_PROFILE=<profile>
git clone https://github.com/yizhizoe/load_test_v2.git
cd load_test_v2
```
2. Edit the user_data/install_ycsb.sh with the bucket name and AKSK and save the file.
```
#!/bin/bash
yum install -y java-1.8.0-devel
cd /tmp/
aws s3 cp s3://<bucket>/ycsb-0.17.0.tar.gz /tmp/ --region cn-northwest-1
tar xfvz ycsb-0.17.0.tar.gz
cd ycsb-0.17.0
mkdir conf
aws s3 cp s3://<bucket>/table_1.properties /tmp/ycsb-0.17.0/conf/ --region cn-northwest-1
aws s3 cp s3://<bucket>/table_2.properties /tmp/ycsb-0.17.0/conf/ --region cn-northwest-1
touch /tmp/ycsb-0.17.0/conf/AWSCredentials.properties
echo "accessKey = <accessKey>
secretKey = <secretKey>" >> /tmp/ycsb-0.17.0/conf/AWSCredentials.properties
```
3. Upload the package and deploy the CDK stack
```
aws s3 cp <download path>/ycsb-0.17.0.tar.gz s3://<s3_bucket>/ 
aws s3 cp conf/table_1.properties s3://<s3_bucket>/ 
aws s3 cp conf/table_2.properties s3://<s3_bucket>/ 
cdk bootstrap 
cdk deploy LoadTestDDBStack 
```
4. In Systems Manager, verify that the instances in ASG are listed in 'Managed Instances'.
5. Update 'Provisioned capacity' of DynamoDB table. This can take some time if the desired capacity is very high.
6. Scale the ASG to desired number of instances by changing the 'desired capacity'.
7. Load test write capacity on table_1 with load command on group_table_1 clients.

```
aws ssm send-command --document-name "AWS-RunShellScript" --document-version "1" --targets '[{"Key":"tag:Name","Values":["group_table_1"]}]' --parameters '{"workingDirectory":[""],"executionTimeout":["3600"],"commands":["#!/bin/bash","cd /tmp/ycsb-0.17.0/","start=`date +\"%s\"`","for (( i=0; i<6; i++ ))","do"," {"," bin/ycsb load dynamodb -P workloads/workloada -P conf/table_1.properties -threads 64 -p recordcount=5000000 -load"," } &","done","wait","end=`date +\"%s\"`","echo \"time: \" `expr $end - $start`"]}' --timeout-seconds 1800 --max-concurrency "100%" --max-errors "0" --cloud-watch-output-config '{"CloudWatchOutputEnabled":true}'
```
8. Load test read capacity on table_1 using group_table_1 clients.
```
aws ssm send-command --document-name "AWS-RunShellScript" --document-version "1" --targets '[{"Key":"tag:Name","Values":["group_table_1"]}]' --parameters '{"commands":["#!/bin/bash","cd /tmp/ycsb-0.17.0/","start=`date +\"%s\"`","for (( i=0; i<5; i++ ))","do"," {"," bin/ycsb run dynamodb -P workloads/workloadc -P conf/table_1.properties -threads 64 -p recordcount=2000000 -p operationcount=3000000"," } &","done","wait","end=`date +\"%s\"`","echo \"time: \" `expr $end - $start`"],"workingDirectory":[""],"executionTimeout":["3600"]}' --timeout-seconds 1800 --max-concurrency "100%" --max-errors "0" --cloud-watch-output-config '{"CloudWatchOutputEnabled":true}'
```
9. You can run similar load test on table_2 in parallel using group_table_2 clients.

### Monitoring
1. The Run Command output log can be found in CloudWatch log group /aws/ssm/AWS-RunShellScript
2. The DynamoDB table Consumed Write Capacity and Read Capacity can be found in DynamoDB table's 'Monitor' tab.