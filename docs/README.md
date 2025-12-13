# Virtual Me - Documentation

## Current Documentation

### Production Setup & Operations

**Main Documentation**: See [../README.md](../README.md) for complete setup and deployment instructions.

### Key Features

- **Security**: Production-grade IAM policies, CORS restrictions, rate limiting
- **Monitoring**: CloudWatch alarms, X-Ray tracing, comprehensive logging
- **Architecture**: Serverless RAG with DynamoDB vector storage
- **Deployment**: Terraform IaC with optional remote state backend

## Additional Resources

### Architecture Review
See [SENIOR_ENGINEER_REVIEW.md](SENIOR_ENGINEER_REVIEW.md) for detailed architectural analysis and recommendations.

### Historical Documentation
Planning and migration documents are archived in [archive/](archive/) for reference:
- Phase 1 Implementation Plan
- LangChain 0.3 Migration
- Bedrock Integration Proof

## Quick Links

**Setup:**
- [Main README](../README.md) - Complete getting started guide
- [Quickstart Guide](../QUICKSTART.md) - Fastest path to deployment
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines

**Infrastructure:**
- [Terraform Configuration](../terraform/) - IaC setup
- [Deployment Scripts](../scripts/) - Automation scripts

**Monitoring:**
```bash
# View alarms
aws cloudwatch describe-alarms

# View X-Ray traces
aws xray get-service-graph --start-time $(date -u -d '1 hour ago' +%s) --end-time $(date +%s)

# View Lambda logs
aws logs tail /aws/lambda/virtual-me-chatbot-prod --follow
```

## Support

For issues or questions:
- Check the [main README](../README.md) troubleshooting section
- Review [SENIOR_ENGINEER_REVIEW.md](SENIOR_ENGINEER_REVIEW.md) for architectural guidance
- Open a GitHub issue for bugs or feature requests
