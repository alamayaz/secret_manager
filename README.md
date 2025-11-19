🔐 AWS Secrets Manager – Automatic Secret Rotation (with Lambda)

This project demonstrates secure storage, automatic rotation, and programmatic retrieval of database credentials using AWS Secrets Manager and a custom Rotation Lambda.

It includes:

✔ Storing DB credentials in Secrets Manager
✔ Creating an IAM Role for rotation
✔ Implementing a rotation Lambda (rotation_lambda.py)
✔ Packaging Lambda with dependencies
✔ Enabling automatic secret rotation
✔ Retrieving the rotated secret with Python (get_secret.py)
✔ A full step-by-step deployment & demo guide

🏗️ Project Architecture
+------------------+            +-----------------------+
| Application Code |   fetch    |  AWS Secrets Manager  |
|  (get_secret.py) | ---------> |  (Stores secret)      |
+------------------+            +----------+------------+
                                            |
                                            | triggers rotation
                                            v
                                 +------------------------+
                                 |   Rotation Lambda      |
                                 | (rotation_lambda.py)   |
                                 +-----------+------------+
                                             |
                                updates password in database
                                             |
                                             v
                                  +-----------------------+
                                  |     MySQL Database    |
                                  +-----------------------+

🎯 Features

Securely stores DB credentials inside AWS Secrets Manager

Uses a custom Lambda function to rotate secrets

Uses PyMySQL to update DB password

Automatically validates new password before promotion

Supports manual and scheduled rotation

CLI + Python-based secret retrieval

📂 Repository Structure
├── rotation_lambda.py            # Lambda rotation handler (main logic)
├── get_secret.py                 # Client script to fetch AWSCURRENT secret
├── lambda-trust.json             # IAM trust policy for Lambda role
├── role-policy.json              # Inline IAM policy for rotation Lambda
├── secrets-policy.json           # Inline IAM policy for CLI user to manage secrets
├── steps.md                      # (Optional) Deployment/Demo steps
└── README.md                     # Project documentation (this file)


Add other helpful content like:

├── demo/                         # Screenshots of AWS Console (optional)
└── rotation_lambda.zip           # Packaged Lambda (ignored if .gitignore)

🛠️ Prerequisites

Python 3.8+

AWS CLI installed & configured

IAM privileges to create:

Secrets

Lambda functions

IAM roles/policies

🚀 Setup & Deployment
1️⃣ Create the Secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name myproject/db/production \
  --description "DB credentials" \
  --secret-string '{"username":"app_user","password":"InitialP@ssw0rd!","engine":"mysql","host":"mydb.example.com","port":3306,"dbname":"myappdb"}' \
  --region ap-south-1

2️⃣ Create IAM Role for Rotation Lambda
Trust Policy

File: lambda-trust.json

aws iam create-role \
  --role-name secrets-rotation-lambda-role \
  --assume-role-policy-document file://lambda-trust.json

Attach Lambda Logging
aws iam attach-role-policy \
  --role-name secrets-rotation-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

Attach Inline Role Policy

File: role-policy.json

aws iam put-role-policy \
  --role-name secrets-rotation-lambda-role \
  --policy-name SecretsRotationPolicy \
  --policy-document file://role-policy.json

3️⃣ Package the Rotation Lambda
mkdir lambda_pkg
cp rotation_lambda.py lambda_pkg/
pip install pymysql -t lambda_pkg/
cd lambda_pkg && zip -r ../rotation_lambda.zip . && cd ..

4️⃣ Deploy the Lambda
aws lambda create-function \
  --function-name my-rotation-lambda \
  --runtime python3.10 \
  --role <ROLE_ARN> \
  --handler rotation_lambda.lambda_handler \
  --zip-file fileb://rotation_lambda.zip \
  --timeout 300 \
  --region ap-south-1

5️⃣ Enable Secret Rotation
aws secretsmanager rotate-secret \
  --secret-id myproject/db/production \
  --rotation-lambda-arn <LAMBDA_ARN> \
  --rotation-rules AutomaticallyAfterDays=30 \
  --region ap-south-1

🧪 Testing Rotation
Trigger a manual rotation:
aws secretsmanager rotate-secret \
  --secret-id myproject/db/production \
  --region ap-south-1

View rotation logs:
aws logs tail /aws/lambda/my-rotation-lambda --follow

📥 Retrieve the Secret (Python)

Run:

python get_secret.py --secret myproject/db/production --region ap-south-1


Expected output:

{
  "username": "app_user",
  "password": "NEW_ROTATED_PASSWORD",
  "host": "mydb.example.com"
}

🎥 Demo Steps (for your video)

Show the secret stored in Secrets Manager

Show the Lambda rotation code

Show the packaged zip file

Show Lambda function creation

Enable rotation

Trigger rotation

Show CloudWatch logs (create, set, test, finish)

Fetch secret using get_secret.py

Prove the password changed

👨‍💻 Technologies Used

AWS Secrets Manager

AWS Lambda

AWS IAM

AWS CLI

Python (PyMySQL, boto3)

⭐ Contributing

Feel free to open issues and submit PRs.
