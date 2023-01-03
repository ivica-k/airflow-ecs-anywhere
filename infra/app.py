#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.bucket import BucketStack
from stacks.vpc import VPCStack
from stacks.mwaa import MWAAStack
from stacks.ecr import ECRStack
from stacks.ecs import ECSStack

env = cdk.Environment(account="932785857088", region="eu-central-1")

app = cdk.App()

bucket_stack = BucketStack(app, "BucketStack", env=env)
ecr_stack = ECRStack(app, "ECRStack", env=env)
vpc_stack = VPCStack(app, "VPCStack", env=env)
mwaa_stack = MWAAStack(
    app, "MWAAStack", env=env, vpc=vpc_stack.vpc, dags_bucket=bucket_stack.dags_bucket
)
ECSStack(
    app,
    "ECSStack",
    env=env,
    vpc=vpc_stack.vpc,
    repo=ecr_stack.repo,
    bucket=bucket_stack.dags_bucket,
    image_tag="latest",
)

app.synth()
