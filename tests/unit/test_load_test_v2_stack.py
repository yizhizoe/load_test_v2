import aws_cdk as core
import aws_cdk.assertions as assertions

from load_test_v2.load_test_v2_stack import LoadTestV2Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in load_test_v2/load_test_v2_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LoadTestV2Stack(app, "load-test-v2")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
