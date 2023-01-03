from aws_cdk import aws_ecr as ecr, Stack, RemovalPolicy, CfnOutput
from constructs import Construct


class ECRStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repo = ecr.Repository(
            self,
            "repo",
            image_scan_on_push=False,
            repository_name="mwaa-ecs-anywhere-repo",
            removal_policy=RemovalPolicy.DESTROY,
        )

        CfnOutput(self, "RepoName", value=self.repo.repository_name)

    def ecr_data(self):
        return self.repo
