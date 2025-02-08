"""Client for DynamoDB and S3."""

import boto3
import uuid
from typing import Any

DEFAULT_REGION_NAME = 'us-east-1'
DEFAULT_DYNAMO_TABLE_NAME = 'Similar-Images-Meta'
DEFAULT_S3_BUCKET_NAME = 'similar-images-data'
DEFAULT_PROJECT_NAME = 'unit_tests'


class DBClient:

    def __init__(
            self,
            dynamo: Any | None = None,
            s3: Any | None = None,
            region_name: str = DEFAULT_REGION_NAME,
            dynamo_table_name: str = DEFAULT_DYNAMO_TABLE_NAME,
            s3_bucket_name: str = DEFAULT_S3_BUCKET_NAME,
            project_name: str = DEFAULT_PROJECT_NAME):
        self.dynamo = dynamo if dynamo else boto3.client('dynamodb', region_name=region_name)
        self.s3 = s3 if s3 else boto3.client('s3', region_name=region_name)
        self.dynamo_table_name = dynamo_table_name
        self.s3_bucket_name = s3_bucket_name
        self.project_name = project_name

    def upload(self, file_path: str, origin_url: str) -> str:
        image_id = str(uuid.uuid4())
        self.s3.upload_file(
            file_path,
            self.s3_bucket_name,
            image_id,
        )
        s3_url = f'https://{self.s3_bucket_name}.s3.amazonaws.com/{image_id}'
        item = {
            'projectName': {'S': self.project_name},
            'imageUrl': {'S': origin_url},
            's3Url': {'S': s3_url},
            's3Key': {'S': image_id},
        }
        res = self.dynamo.put_item(
            TableName=self.dynamo_table_name,
            Item=item,
        )
        print(res)
        return s3_url, image_id

    def download(self, file_path: str, origin_url: str) -> dict:
        response = self.dynamo.get_item(
            TableName=self.dynamo_table_name,
            Key={
                'projectName': {'S': self.project_name},
                'imageUrl': {'S': origin_url},
            }
        )
        print(response)
        s3_key = response['Item']['s3Key']['S']
        self.s3.download_file(
            self.s3_bucket_name,
            s3_key,
            file_path,
        )
        return response['Item']
