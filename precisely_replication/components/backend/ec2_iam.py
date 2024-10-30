import aws_cdk.aws_iam as iam
from constructs import Construct
from cdk_nag import NagSuppressions


class EC2_IAM(Construct):

    def __init__(
        self,
        scope: Construct,
        id_: str,
    ):
        super().__init__(scope, id_)

        self.ec2_role = iam.Role(
            self,
            "PreciselyEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonMSKFullAccess"),
            ],
        )
        NagSuppressions.add_resource_suppressions(
            self.ec2_role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed IAM policies are used since this is a Demo application",
                }
            ],
        )
