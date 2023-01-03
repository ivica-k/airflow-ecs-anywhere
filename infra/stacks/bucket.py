import aws_cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    Stack,
)
from constructs import Construct


class BucketStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project = "mwaa"

        self.dags_bucket = s3.Bucket(
            self,
            "bucket_dags",
            bucket_name=f"{project}-ecs-anywhere-bucket",
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        s3deploy.BucketDeployment(
            self,
            "deployment_dags",
            sources=[s3deploy.Source.asset("./dags")],
            destination_bucket=self.dags_bucket,
            destination_key_prefix="dags",
            prune=False,
            retain_on_delete=False,
        )

        aws_cdk.CfnOutput(self, "BucketName", value=self.dags_bucket.bucket_name)
