from aws_cdk import (
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_logs as log,
    aws_s3 as s3,
    Stack,
    CfnOutput,
)
from constructs import Construct


class ECSStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc,
        repo: ecr.Repository,
        image_tag: str,
        bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        airflow_image = ecs.ContainerImage.from_ecr_repository(repo, image_tag)

        ecs_cluster_role = iam.Role(
            self,
            "ecs_role",
            assumed_by=iam.ServicePrincipal("ssm.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ],
        )
        ecs_fix = ecs_cluster_role.node.default_child
        ecs_fix.add_property_override(
            "AssumeRolePolicyDocument.Statement.0.Principal.Service",
            "ssm.amazonaws.com",
        )
        ecs_cluster_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonEC2ContainerServiceforEC2Role"
            )
        )

        cluster = ecs.Cluster(
            self,
            "ecs_cluster",
            cluster_name="cluster",
            vpc=vpc,
        )

        task_def_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["s3:*"],
                    effect=iam.Effect.ALLOW,
                    resources=[f"{bucket.bucket_arn}/*", f"{bucket.bucket_arn}"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "ecs:RunTask",
                        "ecs:DescribeTasks",
                        "ecs:RegisterTaskDefinition",
                        "ecs:DescribeTaskDefinition",
                        "ecs:ListTasks",
                        "ecs:StopTask",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=["iam:PassRole"],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    conditions={
                        "StringLike": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}
                    },
                ),
            ]
        )

        task_def_policy_document_role = iam.Role(
            self,
            "task_def_role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={"ECSTaskDefPolicyDocument": task_def_policy_document},
        )

        managed_secret_manager_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "SecretsManagerReadWrite"
        )
        task_def_policy_document_role.add_managed_policy(managed_secret_manager_policy)

        external_task_def_policy_document_role = iam.Role(
            self,
            "external_ecs_anywhere_role",
            assumed_by=iam.ServicePrincipal("ssm.amazonaws.com"),
        )

        extfix = external_task_def_policy_document_role.node.default_child
        extfix.add_property_override(
            "AssumeRolePolicyDocument.Statement.0.Principal.Service",
            "ssm.amazonaws.com",
        )

        external_managed_SSM_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonSSMManagedInstanceCore"
        )
        external_managed_ECS_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "service-role/AmazonEC2ContainerServiceforEC2Role"
        )
        external_task_def_policy_document_role.add_managed_policy(
            external_managed_SSM_policy
        )
        external_task_def_policy_document_role.add_managed_policy(
            external_managed_ECS_policy
        )

        log_group = log.LogGroup(
            self, "log_group", retention=log.RetentionDays.ONE_MONTH
        )

        # bind-mount the '/data' from the host filesystem
        data_volume = ecs.Volume(host={"source_path": "/data"}, name="data_volume")

        # START task definitions
        christmas_bonus_task_def = ecs.TaskDefinition(
            self,
            "christmas_taskdef",
            family="mwaa-ecs-anywhere-christmas-bonus",
            network_mode=ecs.NetworkMode.HOST,  # use the host's network
            task_role=task_def_policy_document_role,
            volumes=[data_volume],
            memory_mib="512",
            compatibility=ecs.Compatibility.EXTERNAL,  # run on ECS Anywhere hosts
            cpu="256",
        )

        yearly_tax_task_def = ecs.TaskDefinition(
            self,
            "tax_taskdef",
            family="mwaa-ecs-anywhere-yearly-tax",
            network_mode=ecs.NetworkMode.HOST,
            task_role=task_def_policy_document_role,
            volumes=[data_volume],
            memory_mib="512",
            compatibility=ecs.Compatibility.EXTERNAL,
            cpu="256",
        )
        # END task definitions

        # START container definitions
        christmas_bonus_container = ecs.ContainerDefinition(
            self,
            "bonus_container",
            task_definition=christmas_bonus_task_def,
            container_name="christmas_bonus",
            image=airflow_image,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="ecs", log_group=log_group),
            essential=True,
            command=[
                "python3",
                "/app/christmas_bonus.py",
                "--input_file=/data/employee_data.csv",
                "--output_file=/tmp/salary_with_bonus.csv",
                "--s3_bucket=mwaa-ecs-anywhere-bucket",
                "--s3_folder=bonus",
            ],
        )

        yearly_tax_container = ecs.ContainerDefinition(
            self,
            "tax_container",
            task_definition=yearly_tax_task_def,
            container_name="yearly_tax",
            image=airflow_image,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="ecs", log_group=log_group),
            essential=True,
            command=[
                "python3",
                "/app/tax_amount.py",
                "--input_file=/data/employee_data.csv",
                "--output_file=/tmp/tax_amount.csv",
                "--s3_bucket=mwaa-ecs-anywhere-bucket",
                "--s3_folder=tax",
            ],
        )
        # END container definitions

        # START allow containers to access the host filesystem
        christmas_bonus_container.add_mount_points(
            ecs.MountPoint(
                container_path="/data", source_volume="data_volume", read_only=True
            )
        )

        yearly_tax_container.add_mount_points(
            ecs.MountPoint(
                container_path="/data", source_volume="data_volume", read_only=True
            )
        )
        # END allow containers to access the host filesystem

        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
