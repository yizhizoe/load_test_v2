from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda,
aws_apigateway as apigw,
aws_elasticloadbalancingv2 as elbv2,
aws_ec2 as ec2,
aws_elasticloadbalancingv2_targets as targets,
)

from constructs import Construct

class LoadTestV2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Defines an AWS Lambda resource
        fast_lambda = aws_lambda.Function(
            self, 'HelloHandlerFast',
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=aws_lambda.Code.from_asset('fast_lambda_func'),
            handler='handler_fast.handler',
        )
        endpoint_config=apigw.EndpointConfiguration(
            types=[apigw.EndpointType.REGIONAL]
        )

        slow_lambda = aws_lambda.Function(
            self, 'HelloHandlerSlow',
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=aws_lambda.Code.from_asset('slow_lambda_func'),
            handler='handler_slow.handler',
        )

        alb_lambda_slow = aws_lambda.Function(
            self, 'AlbHandlerSlow',
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=aws_lambda.Code.from_asset('alb_lambda_slow'),
            handler='handler_slow.handler',
        )

        apigw.LambdaRestApi(
            self, 'fast-api',
            endpoint_configuration=endpoint_config,
            handler=fast_lambda,
        )

        apigw.LambdaRestApi(
            self, 'slow-api',
            endpoint_configuration=endpoint_config,
            handler=slow_lambda,
        )

        #vpc = ec2.Vpc.from_lookup(self,"my_vpc", vpc_id="vpc-371f7453")
        # Create VPC, NAT Gateway
        vpc = ec2.Vpc(self, "VPC",
                      max_azs=2,
                      cidr="10.10.0.0/16",
                      # configuration will create 2 public subnets and 2 private subnets
                      subnet_configuration=[ec2.SubnetConfiguration(
                          subnet_type=ec2.SubnetType.PUBLIC,
                          name="Public",
                          cidr_mask=24
                        )]
                      )

        lb = elbv2.ApplicationLoadBalancer(self, "load_test_lb",
                                           vpc=vpc,
                                           internet_facing=True
                                           )
        listener = lb.add_listener("Listener",
                                   port=80,

                                   # 'open: true' is the default, you can leave it out if you want. Set it
                                   # to 'false' and use `listener.connections` if you want to be selective
                                   # about who can access the load balancer.
                                   open=True
                                   )
        listener.add_targets("lambda_targets",
                             targets=[targets.LambdaTarget(alb_lambda_slow)],

                             # For Lambda Targets, you need to explicitly enable health checks if you
                             # want them.
                             health_check=elbv2.HealthCheck(
                                 enabled=False
                             )
                             )



