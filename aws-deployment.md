# AWS Deployment Guide

Three reference architectures, from simplest → most production-ready.

---

## Option A — Single EC2 + Docker Compose

Best for: demos, MVPs.

1. Launch an EC2 (Ubuntu 22.04, `t3.medium`+, 30 GB EBS).
2. Open security group ports `22, 80, 8000`.
3. SSH and install Docker:
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git
   sudo usermod -aG docker $USER && newgrp docker
   ```
4. Clone & launch:
   ```bash
   git clone https://github.com/<your-org>/automated-report-generation.git
   cd automated-report-generation
   cp .env.example .env && nano .env   # set SECRET_KEY, OPENAI_API_KEY, AWS_*
   docker compose up -d --build
   ```
5. Browse to `http://<EC2-public-IP>`.

---

## Option B — ECS Fargate + RDS + S3

Best for: scalable production.

```
                ┌─────────────┐
   Route 53 ──▶ │   ALB (443) │
                └─────┬───────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ Frontend│   │ Backend │   │ Backend │   (Fargate tasks)
   │ (nginx) │   │  API    │   │  API    │
   └─────────┘   └────┬────┘   └────┬────┘
                      │             │
                ┌─────▼─────────────▼─────┐
                │ RDS PostgreSQL (multi-AZ)│
                └──────────────────────────┘
                              │
                       ┌──────▼──────┐
                       │   S3 bucket  │  ← reports/, datasets/
                       └──────────────┘
```

Steps:
1. **RDS PostgreSQL** — create a small instance; whitelist Fargate security group.
2. **S3 bucket** — `reportgen-files-<random>`, block-public-access ON.
3. **ECR repos** — `reportgen-backend`, `reportgen-frontend`. Push images:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <acct>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t reportgen-backend -f docker/Dockerfile.backend .
   docker tag reportgen-backend:latest <acct>.dkr.ecr.us-east-1.amazonaws.com/reportgen-backend:latest
   docker push <acct>.dkr.ecr.us-east-1.amazonaws.com/reportgen-backend:latest
   # same for frontend
   ```
4. **ECS Cluster (Fargate)** — create a service per image, attach to ALB target groups.
5. **Secrets Manager** — store `OPENAI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`; inject as ECS env.
6. **IAM** — give the Fargate task role `s3:GetObject/PutObject` on your bucket.
7. **CI/CD** — already wired in `.github/workflows/ci.yml`; add `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` secrets to GitHub and extend the `deploy-aws` job to `aws ecs update-service --force-new-deployment`.

---

## Option C — AWS Lambda + API Gateway + CloudFront

Best for: low-traffic, cost-optimized.

1. Add `mangum` to `requirements.txt`.
2. Use `backend/utils/lambda_handler.py` as the Lambda entrypoint.
3. Package:
   ```bash
   pip install -r backend/requirements.txt -t package/
   cp -r backend package/
   cd package && zip -r ../lambda.zip . && cd ..
   aws lambda update-function-code --function-name reportgen --zip-file fileb://lambda.zip
   ```
4. Front with **API Gateway** (HTTP API, `ANY /{proxy+}` → Lambda).
5. Build frontend (`npm run build`) and serve `dist/` via **S3 + CloudFront**.
6. Use **RDS Proxy** for PostgreSQL to manage connections.

> ⚠️ Lambda has a 15-min timeout and 250 MB layer limit; large datasets are better suited to Option B.
