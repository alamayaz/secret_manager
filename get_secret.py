import boto3
import base64
import json
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name='ap-south-1'):
    client = boto3.client('secretsmanager', region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise
    if 'SecretString' in response:
        secret = response['SecretString']
    else:
        secret = base64.b64decode(response['SecretBinary'])
    return json.loads(secret)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret", required=True, help="SecretId or ARN")
    parser.add_argument("--region", default="ap-south-1")
    args = parser.parse_args()
    secret = get_secret(args.secret, args.region)
    print(json.dumps(secret, indent=2))
