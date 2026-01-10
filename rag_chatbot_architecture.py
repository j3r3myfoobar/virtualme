with Diagram("RAG Chatbot Architecture", show=False, direction="LR"):
    user = User("User (Web Browser with Deep Chat UI)")

    with Cluster("AWS Cloud"):
        with Cluster("CDN Layer"):
            cloudfront = CloudFront("Amazon CloudFront")
            s3_frontend = S3("Amazon S3 (Static Frontend)")
            cloudfront >> Edge(label="Serves static content") >> s3_frontend

        with Cluster("DNS & API Layer"):
            route53 = Route53("Amazon Route 53")
            api_gateway = APIGateway("Amazon API Gateway")

        with Cluster("Compute Layer"):
            lambda_function = Lambda("AWS Lambda (Chatbot Handler)")

        with Cluster("AI Layer"):
            bedrock = Bedrock("Amazon Bedrock (Nova 2 Lite, Titan)")

        with Cluster("Storage Layer"):
            dynamodb = Dynamodb("Amazon DynamoDB (Vector Store)")

        with Cluster("Monitoring Layer"):
            cloudwatch = Cloudwatch("Amazon CloudWatch")
            xray = XRay("AWS X-Ray")

    # Connections
    user >> Edge(label="Accesses frontend") >> cloudfront
    user >> Edge(label="Sends /chat POST request") >> route53 >> api_gateway
    api_gateway >> Edge(label="Invokes") >> lambda_function

    lambda_function >> Edge(label="LLM inference & embeddings") >> bedrock
    lambda_function >> Edge(label="Vector similarity search") >> dynamodb

    lambda_function >> Edge(label="Logs") >> cloudwatch
    lambda_function >> Edge(label="Traces") >> xray
