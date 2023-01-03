from aws_cdk import Stack, aws_ec2 as ec2
from constructs import Construct


class VPCStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project = "mwaa"

        self.vpc = ec2.Vpc(
            self,
            id="vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.255.0.0/16"),
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{project}-subnet-public",
                    cidr_mask=24,
                    reserved=False,
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
                ec2.SubnetConfiguration(
                    name=f"{project}-subnet-private",
                    cidr_mask=24,
                    reserved=False,
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )
