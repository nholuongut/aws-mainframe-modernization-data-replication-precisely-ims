from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_kms as kms,
)
from .components.network.vpc import VPC
from .components.backend.msk import MSK
from .components.backend.redshift import Redshift
from .components.backend.ec2_iam import EC2_IAM
from .components.frontend.quicksight import Quicksight
from constructs import Construct


class PreciselyReplicationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        kms_key = kms.Key(
            self,
            "PreciselyKMSKey",
            description="Symmetric key for Msk secret",
            enable_key_rotation=True,
            pending_window=Duration.days(7),
            removal_policy=RemovalPolicy.DESTROY,
        )

        network = VPC(self, "PreciselyNetwork")

        MSK(
            self,
            "PreciselyMSK",
            vpc=network.vpc,
            kms=kms_key,
        )

        redshift = Redshift(
            self,
            "PreciselyRedshift",
            vpc=network.vpc,
            subnet_ids=network.subnet_ids,
            kms=kms_key,
        )

        EC2_IAM(
            self,
            "PreciselyEC2IAM",
        )

        Quicksight(
            self,
            "PreciselyQuickSight",
            vpc=network.vpc,
            redshift_cluster=redshift,
        ).node.add_dependency(redshift)
