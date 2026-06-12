import boto3
from django.conf import settings


def get_dynamo_resource():
    """boto3 DynamoDB resource. endpoint_url points at the local container;
    drop it (and use real creds) to talk to actual AWS DynamoDB."""
    return boto3.resource(
        "dynamodb",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def get_psp_table():
    return get_dynamo_resource().Table(settings.DYNAMODB_TABLE)
