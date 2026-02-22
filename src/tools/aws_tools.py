import boto3
from smolagents import tool

from src.config import get_config


class CreateBotoClientTool:
    def __init__(self, profile: str | None) -> None:
        self.profile = profile

    def create_boto_client(self, service_name: str) -> object:
        """
        Create a boto3 client with a specified AWS profile.

        Args:
            service_name: The AWS service name (e.g., 's3', 'ec2', 'dynamodb')

        Returns:
            A boto3 client for the specified service
        """
        if self.profile:
            session = boto3.Session(profile_name=self.profile)
        else:
            session = boto3.Session()
        return session.client(service_name)

    def as_tool(self) -> tool:
        return tool(self.create_boto_client)


def create_boto_client_tool() -> tool:
    config = get_config()
    aws_profile = config.aws_profile
    return CreateBotoClientTool(aws_profile).as_tool()
