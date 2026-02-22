import boto3
from smolagents import tool


@tool
def create_boto_client(service_name: str) -> object:
    """
    Create a boto3 client with a specified AWS profile.

    Args:
        service_name: The AWS service name (e.g., 's3', 'ec2', 'dynamodb')

    Returns:
        A boto3 client for the specified service
    """
    session = boto3.Session(profile_name="notisphere")
    return session.client(service_name)
