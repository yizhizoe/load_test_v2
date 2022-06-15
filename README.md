# Test approach
The test client will be based on AWS solution of [Distributed Load Testing](https://www.amazonaws.cn/en/solutions/distributed-load-testing/) 
The test will be against API Gateway+Lambda or ALB+ Lambda.
## Test resources
The CDK in this repo is to set up
- API Gateway REST API integrated with fast lambda function (simple hello world python lambda function)
- API Gateway REST API integrated with slow lambda (hello world function with 1 second sleep)
- VPC and ALB target with slow lambda function

1. In account A where the concurrency has raised,
```
git clone https://github.com/yizhizoe/load_test_v2.git
cd load_test_v2
cdk bootstrap --profile <account A>
cdk deploy --profile <account A>
```
2. In account B for load test client, follow the [guide of distributed load testing solution](https://s3.cn-north-1.amazonaws.com.cn/aws-dam-prod/china/Solutions/distributed_load_testing/distributed-load-testing-platform-deployment-guide.pdf) and deploy the client. 
3. (optional) Prewarm ALB of step 1.

