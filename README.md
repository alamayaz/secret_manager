# AWS Secrets Manager – Automatic Secret Rotation (with Lambda)

## 🔐 Overview
This project demonstrates secure storage and automatic rotation of database credentials using **AWS Secrets Manager** with a custom **AWS Lambda rotation function**.

It includes:
- Creating and storing a secret
- Building and deploying a rotation Lambda
- Packaging Python dependencies
- Enabling automatic secret rotation
- Retrieving the rotated secret using Python

---

## 🏗️ Architecture

```
Application (get_secret.py)
            |
            v
AWS Secrets Manager -----> Rotation Lambda -----> Database (MySQL)
            ^                     |
            |                     v
     Retrieve Secret     Update & Validate Password
```

---

## 📂 Repository Structure

```
├── rotation_lambda.py
├── get_secret.py
├── lambda-trust.json
├── role-policy.json
├── secrets-policy.json
├── README.md
```

---

## 🛠️ Setup Steps

### 1️⃣ Create Secret
```bash
aws secretsmanager create-secret   --name myproject/db/production   --description "DB credentials"   --secret-string '{"username":"app_user","password":"InitialP@ssw0rd!","engine":"mysql","host":"mydb.example.com","port":3306,"dbname":"myappdb"}'   --region ap-south-1
```

### 2️⃣ IAM Role for Lambda
```bash
aws iam create-role   --role-name secrets-rotation-lambda-role   --assume-role-policy-document file://lambda-trust.json
```

Attach policies:
```bash
aws iam attach-role-policy   --role-name secrets-rotation-lambda-role   --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Add inline policy:
```bash
aws iam put-role-policy   --role-name secrets-rotation-lambda-role   --policy-name SecretsRotationPolicy   --policy-document file://role-policy.json
```

---

## 3️⃣ Package Rotation Lambda
```bash
mkdir lambda_pkg
cp rotation_lambda.py lambda_pkg/
pip install pymysql -t lambda_pkg/
cd lambda_pkg && zip -r ../rotation_lambda.zip . && cd ..
```

---

## 4️⃣ Deploy Lambda
```bash
aws lambda create-function   --function-name my-rotation-lambda   --runtime python3.10   --role <ROLE_ARN>   --handler rotation_lambda.lambda_handler   --zip-file fileb://rotation_lambda.zip   --timeout 300   --region ap-south-1
```

---

## 5️⃣ Enable Rotation
```bash
aws secretsmanager rotate-secret   --secret-id myproject/db/production   --rotation-lambda-arn <LAMBDA_ARN>   --rotation-rules AutomaticallyAfterDays=30   --region ap-south-1
```

---

## 🧪 Test Rotation

Trigger rotation:
```bash
aws secretsmanager rotate-secret --secret-id myproject/db/production --region ap-south-1
```

Check logs:
```bash
aws logs tail /aws/lambda/my-rotation-lambda --follow
```

---

## 📥 Retrieve Secret

```bash
python get_secret.py --secret myproject/db/production --region ap-south-1
```

Expected output includes new rotated password.

---

## 🎯 Conclusion
This project fully implements secure secret storage and automated rotation with AWS Secrets Manager and AWS Lambda.

