#!/usr/bin/env python3
import os
import cdk_nag

import aws_cdk as cdk
from cdk_nag import NagSuppressions
from aws_cdk import Aspects

from precisely_replication.precisely_replication_stack import PreciselyReplicationStack


app = cdk.App()

aws_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]
)
appStack = PreciselyReplicationStack(
    app,
    "PreciselyReplicationStack",
    env=aws_env,
)

Aspects.of(appStack).add(cdk_nag.AwsSolutionsChecks())


NagSuppressions.add_stack_suppressions(
    appStack,
    suppressions=[
        {
            "id": "CdkNagValidationFailure",
            "reason": "Access rule for ingress to Precisely Service Endpoint",
        },
    ],
)

app.synth()
