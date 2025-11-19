# rotation_lambda.py
import json
import boto3
import logging
import pymysql
import secrets
import string
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sm = boto3.client('secretsmanager')
# If you prefer a region explicitly:
# sm = boto3.client('secretsmanager', region_name='ap-south-1')

def lambda_handler(event, context):
    secret_arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']  # createSecret | setSecret | testSecret | finishSecret
    logger.info("Rotation invoked for %s, step=%s", secret_arn, step)

    if step == "createSecret":
        create_secret(secret_arn, token)
    elif step == "setSecret":
        set_secret(secret_arn, token)
    elif step == "testSecret":
        test_secret(secret_arn, token)
    elif step == "finishSecret":
        finish_secret(secret_arn, token)
    else:
        raise ValueError("Unknown step " + step)

def create_secret(secret_arn, token):
    meta = sm.describe_secret(SecretId=secret_arn)
    versions = meta.get('VersionIdsToStages', {})
    # If this token already has AWSPENDING, do nothing.
    if token in versions and 'AWSPENDING' in versions[token]:
        logger.info("createSecret: AWSPENDING already exists for token")
        return

    # Get current secret to copy other fields
    current = sm.get_secret_value(SecretId=secret_arn)
    current_json = json.loads(current['SecretString'])

    # Generate a new password
    new_password = generate_password(24)

    pending = current_json.copy()
    pending['password'] = new_password

    sm.put_secret_value(
        SecretId=secret_arn,
        ClientRequestToken=token,
        SecretString=json.dumps(pending),
        VersionStages=['AWSPENDING']
    )
    logger.info("createSecret: created AWSPENDING secret version")

def set_secret(secret_arn, token):
    # Get AWSPENDING secret value
    pending = sm.get_secret_value(SecretId=secret_arn, VersionId=token)
    pending_json = json.loads(pending['SecretString'])

    # Get current (to obtain admin/superuser creds)
    current = sm.get_secret_value(SecretId=secret_arn)
    current_json = json.loads(current['SecretString'])

    host = pending_json['host']
    port = int(pending_json.get('port', 3306))
    dbname = pending_json.get('dbname')
    username = pending_json['username']
    new_password = pending_json['password']

    # Use superuser credentials (either stored as separate keys or fallback to current username/password)
    admin_user = current_json.get('superuser') or current_json.get('username')
    admin_pass = current_json.get('superuser_password') or current_json.get('password')

    logger.info("setSecret: connecting to DB %s@%s:%s as admin %s", dbname, host, port, admin_user)

    conn = pymysql.connect(host=host, user=admin_user, password=admin_pass, port=port, database=dbname, connect_timeout=10)
    try:
        with conn.cursor() as cur:
            # Use ALTER USER for modern MySQL, fallback handled by DB privileges
            try:
                cur.execute(f"ALTER USER %s@'%%' IDENTIFIED BY %s;", (username, new_password))
            except pymysql.MySQLError as e:
                # Some MySQL versions or privileges may require different statements
                logger.warning("ALTER USER failed: %s - trying SET PASSWORD fallback", str(e))
                cur.execute(f"SET PASSWORD FOR %s@'%' = PASSWORD(%s);", (username, new_password))
        conn.commit()
    finally:
        conn.close()
    logger.info("setSecret: DB password updated for user %s", username)

def test_secret(secret_arn, token):
    # Validate AWSPENDING credentials can connect
    pending = sm.get_secret_value(SecretId=secret_arn, VersionId=token)
    pending_json = json.loads(pending['SecretString'])

    host = pending_json['host']
    port = int(pending_json.get('port', 3306))
    dbname = pending_json.get('dbname')
    username = pending_json['username']
    password = pending_json['password']

    logger.info("testSecret: trying to connect as %s@%s", username, host)
    conn = pymysql.connect(host=host, user=username, password=password, port=port, database=dbname, connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            res = cur.fetchone()
            if not res:
                raise Exception("testSecret: test query failed")
    finally:
        conn.close()
    logger.info("testSecret: AWSPENDING credentials validated")

def finish_secret(secret_arn, token):
    # Mark the pending version as AWSCURRENT
    sm.update_secret_version_stage(
        SecretId=secret_arn,
        VersionStage="AWSCURRENT",
        MoveToVersionId=token
    )
    logger.info("finishSecret: moved AWSPENDING to AWSCURRENT")

def generate_password(length=20):
    alphabet = string.ascii_letters + string.digits + "!@#%^&*-_"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
