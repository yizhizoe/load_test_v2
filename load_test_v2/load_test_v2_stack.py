import os

from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda,
aws_apigateway as apigw,
aws_elasticloadbalancingv2 as elbv2,
aws_ec2 as ec2,
aws_elasticloadbalancingv2_targets as targets,
aws_dynamodb as dynamodb,
aws_iam as iam,
aws_autoscaling as autoscaling,
)
from aws_cdk import Tags

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

class LoadTestDDBStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc = ec2.Vpc(self, "VPC",
            max_azs = 2,
            cidr = "10.10.0.0/16",
            subnet_configuration = [ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC,
                name="Public",
                cidr_mask=24
            )]
        )
        table_1 = dynamodb.Table(self, "table_1",
                                 table_name="table_1",
                                 partition_key=dynamodb.Attribute(name="userid", type=dynamodb.AttributeType.STRING),
                                 billing_mode=dynamodb.BillingMode.PROVISIONED
                                 )

        table_2 = dynamodb.Table(self, "table_2",
                                 table_name="table_2",
                                 partition_key=dynamodb.Attribute(name="userid", type=dynamodb.AttributeType.STRING),
                                 billing_mode=dynamodb.BillingMode.PROVISIONED
                                 )

        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
            cpu_type=ec2.AmazonLinuxCpuType.ARM_64
        )

        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"))

        # Create Autoscaling Group with fixed 2*EC2 hosts
        asg_1 = autoscaling.AutoScalingGroup(self, "asg_1",
                                                vpc=vpc,
                                                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                                instance_type=ec2.InstanceType(instance_type_identifier="c6g.4xlarge"),
                                                machine_image=amzn_linux,
                                                desired_capacity=1,
                                                min_capacity=0,
                                                max_capacity=40,
                                                role=role
                                                )
        Tags.of(asg_1).add("Name","group_table_1")

        asg_2 = autoscaling.AutoScalingGroup(self, "asg_2",
                                                vpc=vpc,
                                                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                                instance_type=ec2.InstanceType(instance_type_identifier="c6g.4xlarge"),
                                                machine_image=amzn_linux,
                                                desired_capacity=1,
                                                min_capacity=0,
                                                max_capacity=40,
                                                role=role
                                                )
        Tags.of(asg_2).add("Name","group_table_2")
