import os
import aws_cdk.aws_redshiftserverless as redshift
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_kms as kms
from constructs import Construct
from cdk_nag import NagSuppressions


class Redshift(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        vpc: ec2.IVpc,
        subnet_ids: list[str],
        kms: kms.IKey,
    ):
        super().__init__(scope, id_)

        redshift_role = iam.Role(
            self,
            "PreciselyRedshiftRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonMSKFullAccess"),
            ],
        )
        NagSuppressions.add_resource_suppressions(
            redshift_role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed IAM policies are used since this is a Demo application",
                }
            ],
        )

        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        self.port = 5439

        ec2.CfnSecurityGroupIngress(
            self,
            "SecurityGroupIngress",
            ip_protocol="tcp",
            from_port=self.port,
            to_port=self.port,
            cidr_ip=vpc.vpc_cidr_block,
            group_id=security_group.security_group_id,
        )

        cluster_master_secret = os.getenv("CREDENTIAL_SECRET")
        self.namespace = redshift.CfnNamespace(
            self,
            "Namespace",
            namespace_name="precisely-namespace",
            admin_username="admin",
            admin_user_password=cluster_master_secret,
            db_name="precisely",
            default_iam_role_arn=redshift_role.role_arn,
            iam_roles=[redshift_role.role_arn],
            kms_key_id=kms.key_id,
            manage_admin_password=False,
        )

        self.workgroup_name = "precisely-workgroup"
        self.workgroup = redshift.CfnWorkgroup(
            self,
            "Workgroup",
            workgroup_name=self.workgroup_name,
            base_capacity=128,
            config_parameters=[
                redshift.CfnWorkgroup.ConfigParameterProperty(
                    parameter_key="enable_user_activity_logging",
                    parameter_value="true",
                )
            ],
            port=self.port,
            subnet_ids=subnet_ids,
            security_group_ids=[security_group.security_group_id],
            namespace_name=self.namespace.namespace_name,
        ).add_dependency(self.namespace)
