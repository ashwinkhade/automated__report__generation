"""
AWS Lambda handler.

Use with Mangum to expose the FastAPI app as a Lambda function behind API Gateway.
Deploy with `serverless` or `aws sam`:

    pip install mangum
    handler = backend.utils.lambda_handler.handler
"""
try:
    from mangum import Mangum
    from backend.main import app
    handler = Mangum(app)
except ImportError:  # mangum optional
    def handler(event, context):  # type: ignore
        return {
            "statusCode": 500,
            "body": "mangum is not installed. Run `pip install mangum`.",
        }
