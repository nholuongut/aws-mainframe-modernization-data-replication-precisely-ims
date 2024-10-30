import aws_cdk.aws_ec2 as ec2
from constructs import Construct
from cdk_nag import NagSuppressions


class VPC(Construct):

    def __init__(
        self,
        scope: Construct,
        id_: str,
    ):
        super().__init__(scope, id_)

        self.vpc = ec2.Vpc(
            self,
            "VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            create_internet_gateway=True,
            max_azs=99,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
            ],
            enable_dns_support=True,
            enable_dns_hostnames=True,
            nat_gateways=0,
        )
        NagSuppressions.add_resource_suppressions(
            self.vpc,
            [
                {
                    "id": "AwsSolutions-VPC7",
                    "reason": "Flow log not enabled since this is Demo code",
                }
            ],
        )

        self.subnet_ids = [subnet.subnet_id for subnet in self.vpc.private_subnets]

        ec2.InterfaceVpcEndpoint(
            self,
            "InterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointService(
                "com.amazonaws.vpce.us-east-1.vpce-svc-0b13484e4196140b5"
            ),
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )
