from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_mwaa as mwaa,
    Stack,
)
from constructs import Construct


class MWAAStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dags_bucket: s3.Bucket,
        vpc: ec2.Vpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project = "mwaa"
        name = f"{project}-ecs-anywhere"

        mwaa_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["airflow:PublishMetrics"],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:airflow:{self.region}:{self.account}:environment/{name}"
                    ],
                ),
                iam.PolicyStatement(
                    actions=["s3:ListAllMyBuckets"],
                    effect=iam.Effect.DENY,
                    resources=[
                        f"{dags_bucket.bucket_arn}/*",
                        f"{dags_bucket.bucket_arn}",
                    ],
                ),
                iam.PolicyStatement(
                    actions=["s3:*"],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"{dags_bucket.bucket_arn}/*",
                        f"{dags_bucket.bucket_arn}",
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogStream",
                        "logs:CreateLogGroup",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:GetLogRecord",
                        "logs:GetLogGroupFields",
                        "logs:GetQueryResults",
                        "logs:DescribeLogGroups",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:airflow-{name}-*"
                    ],
                ),
                iam.PolicyStatement(
                    actions=["logs:DescribeLogGroups"],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "sqs:ChangeMessageVisibility",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:GetQueueUrl",
                        "sqs:ReceiveMessage",
                        "sqs:SendMessage",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:sqs:{self.region}:*:airflow-celery-*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "ecs:RunTask",
                        "ecs:DescribeTasks",
                        "ecs:RegisterTaskDefinition",
                        "ecs:DescribeTaskDefinition",
                        "ecs:ListTasks",
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
                iam.PolicyStatement(
                    actions=[
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey*",
                        "kms:Encrypt",
                        "kms:PutKeyPolicy"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"sqs.{self.region}.amazonaws.com",
                                f"s3.{self.region}.amazonaws.com",
                            ]
                        }
                    },
                )
            ]
        )

        mwaa_service_role = iam.Role(
            self,
            "service_role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("airflow.amazonaws.com"),
                iam.ServicePrincipal("airflow-env.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            inline_policies={"CDKmwaaPolicyDocument": mwaa_policy_document},
            path="/service-role/",
        )

        security_group = ec2.SecurityGroup(
            self, id="mwaa_secgp", vpc=vpc, security_group_name=f"{project}-secgp"
        )

        security_group_id = security_group.security_group_id

        security_group.connections.allow_internally(
            ec2.Port.all_traffic(), project.upper()
        )

        network_configuration = mwaa.CfnEnvironment.NetworkConfigurationProperty(
            security_group_ids=[security_group_id],
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        logging_configuration = mwaa.CfnEnvironment.LoggingConfigurationProperty(
            dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
            webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True, log_level="INFO"
            ),
        )

        options = {
            "core.load_default_connections": False,
            "core.load_examples": False,
            "webserver.dag_default_view": "tree",
            "webserver.dag_orientation": "TB",
        }

        managed_airflow = mwaa.CfnEnvironment(
            scope=self,
            id="airflow",
            name=f"{name}",
            airflow_configuration_options={"core.default_timezone": "utc"},
            airflow_version="2.2.2",
            dag_s3_path="dags",
            requirements_s3_path="dags/requirements.txt",
            environment_class="mw1.small",
            execution_role_arn=mwaa_service_role.role_arn,
            logging_configuration=logging_configuration,
            max_workers=1,
            network_configuration=network_configuration,
            source_bucket_arn=dags_bucket.bucket_arn,
            webserver_access_mode="PUBLIC_ONLY",
        )

        managed_airflow.add_override("Properties.AirflowConfigurationOptions", options)
