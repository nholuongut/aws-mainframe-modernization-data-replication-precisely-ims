import os
import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
from aws_cdk import aws_quicksight as quicksight
from ..backend.redshift import Redshift
from constructs import Construct
from cdk_nag import NagSuppressions


class Quicksight(Construct):

    def __init__(
        self,
        scope: Construct,
        id_: str,
        vpc: ec2.IVpc,
        redshift_cluster: Redshift,
    ):
        super().__init__(scope, id_)

        account_id = cdk.Aws.ACCOUNT_ID

        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        quicksight_ingress = ec2.CfnSecurityGroupIngress(
            self,
            "SecurityGroupIngress",
            ip_protocol="tcp",
            from_port=0,
            to_port=65535,
            cidr_ip="0.0.0.0/0",
            group_id=security_group.security_group_id,
        )
        NagSuppressions.add_resource_suppressions(
            quicksight_ingress,
            [
                {
                    "id": "AwsSolutions-EC23",
                    "reason": "Ingress rule required for accessing Quicksight Dashboard from internet",
                }
            ],
        )

        quicksight_execution_role = iam.Role(
            self,
            "ExecutionRole",
            assumed_by=iam.ServicePrincipal("quicksight.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonRedshiftDataFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSQuickSightDescribeRedshift"
                ),
            ],
            inline_policies={
                "ENIAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ec2:CreateNetworkInterface",
                                "ec2:ModifyNetworkInterfaceAttribute",
                                "ec2:DeleteNetworkInterface",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeSecurityGroups",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
            },
        )
        NagSuppressions.add_resource_suppressions(
            quicksight_execution_role,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed IAM policies are used since this is a Demo application",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wild Card resource is used since VPC access is required",
                },
            ],
        )

        quicksight_vpc = quicksight.CfnVPCConnection(
            self,
            "VPCConnection",
            aws_account_id=account_id,
            name="PreciselyVPC",
            role_arn=quicksight_execution_role.role_arn,
            security_group_ids=[security_group.security_group_id],
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            vpc_connection_id=vpc.vpc_id,
        )

        cluster_master_secret = os.getenv("CREDENTIAL_SECRET")
        quicksight.CfnDataSource(
            self,
            "RedshiftDataSource",
            name="PreciselyRedshiftDataSource",
            type="REDSHIFT",
            data_source_id="precisely_source",
            data_source_parameters=quicksight.CfnDataSource.DataSourceParametersProperty(
                redshift_parameters=quicksight.CfnDataSource.RedshiftParametersProperty(
                    database=redshift_cluster.namespace.attr_namespace_db_name,
                    host=f"{redshift_cluster.workgroup_name}.{account_id}.{cdk.Aws.REGION}"
                    + ".redshift-serverless.amazonaws.com",
                    port=redshift_cluster.port,
                ),
            ),
            credentials=quicksight.CfnDataSource.DataSourceCredentialsProperty(
                credential_pair=quicksight.CfnDataSource.CredentialPairProperty(
                    password=cluster_master_secret,
                    username=redshift_cluster.namespace.attr_namespace_admin_username,
                ),
            ),
            aws_account_id=account_id,
            vpc_connection_properties=quicksight.CfnDataSource.VpcConnectionPropertiesProperty(
                vpc_connection_arn=quicksight_vpc.attr_arn
            ),
        )
