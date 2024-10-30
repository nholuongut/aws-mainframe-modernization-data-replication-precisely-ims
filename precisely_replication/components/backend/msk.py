import os
import json
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_kms as kms
import aws_cdk.aws_secretsmanager as secretsmanager
import aws_cdk.aws_msk as msk
from constructs import Construct
from cdk_nag import NagSuppressions


class MSK(Construct):

    def __init__(
        self,
        scope: Construct,
        id_: str,
        vpc: ec2.IVpc,
        kms: kms.IKey,
    ):
        super().__init__(scope, id_)

        cluster_master_secret = os.getenv("CREDENTIAL_SECRET")
        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        ec2.CfnSecurityGroupIngress(
            self,
            "SecurityGroupIngress",
            ip_protocol="tcp",
            from_port=0,
            to_port=65535,
            cidr_ip=vpc.vpc_cidr_block,
            group_id=security_group.security_group_id,
        )

        count = 0
        subnets_per_az = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, one_per_az=True
        ).subnets
        subnet_list = []
        for subnets in subnets_per_az:
            if not subnets.availability_zone == "us-east-1c":
                subnet_list.append(subnets.subnet_id)
                count += 1
                if count > 2:
                    break

        self.msk_cluster = msk.CfnCluster(
            self,
            "Cluster",
            broker_node_group_info=msk.CfnCluster.BrokerNodeGroupInfoProperty(
                client_subnets=subnet_list,
                instance_type="kafka.t3.small",
                security_groups=[
                    security_group.security_group_id,
                ],
                storage_info=msk.CfnCluster.StorageInfoProperty(
                    ebs_storage_info=msk.CfnCluster.EBSStorageInfoProperty(
                        volume_size=10,
                    ),
                ),
            ),
            cluster_name="PreciselyMskCluster",
            client_authentication=msk.CfnCluster.ClientAuthenticationProperty(
                sasl=msk.CfnCluster.SaslProperty(
                    scram=msk.CfnCluster.ScramProperty(
                        enabled=True,
                    ),
                    iam=msk.CfnCluster.IamProperty(
                        enabled=True,
                    ),
                ),
            ),
            encryption_info=msk.CfnCluster.EncryptionInfoProperty(
                encryption_in_transit=msk.CfnCluster.EncryptionInTransitProperty(
                    client_broker="TLS",
                    in_cluster=True,
                ),
            ),
            enhanced_monitoring="PER_TOPIC_PER_BROKER",
            kafka_version="3.7.x",
            number_of_broker_nodes=len(subnet_list),
        )
        NagSuppressions.add_resource_suppressions(
            self.msk_cluster,
            [
                {
                    "id": "AwsSolutions-MSK6",
                    "reason": "Broker log not enabled since this is Demo code",
                }
            ],
        )

        msk.CfnClusterPolicy(
            self,
            "MskClusterPolicy",
            cluster_arn=self.msk_cluster.attr_arn,
            policy={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": [
                            "kafka:CreateVpcConnection",
                            "kafka:GetBootstrapBrokers",
                            "kafka:DescribeCluster",
                            "kafka:DescribeClusterV2",
                            "kafka-cluster:Connect",
                            "kafka-cluster:DescribeCluster",
                            "kafka-cluster:ReadData",
                            "kafka-cluster:DescribeTopic",
                            "kafka-cluster:WriteData",
                            "kafka-cluster:CreateTopic",
                            "kafka-cluster:AlterGroup",
                            "kafka-cluster:DescribeGroup",
                        ],
                        "Resource": "*",
                    }
                ],
            },
        )

        msk_secret = secretsmanager.CfnSecret(
            self,
            "Secret",
            name="AmazonMSK_Admin_Credentials",
            description="Msk Credential for Precisely Kafka",
            kms_key_id=kms.key_id,
            secret_string=json.dumps(
                {"username": "admin", "password": cluster_master_secret}
            ),
        )
        NagSuppressions.add_resource_suppressions(
            msk_secret,
            [
                {
                    "id": "AwsSolutions-SMG4",
                    "reason": "Secrets rotation not enabled since this is Demo code",
                }
            ],
        )

        msk.CfnBatchScramSecret(
            self,
            "BatchScramSecret",
            cluster_arn=self.msk_cluster.attr_arn,
            secret_arn_list=[msk_secret.attr_id],
        )
