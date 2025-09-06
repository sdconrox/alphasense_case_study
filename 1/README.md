# AlphaSense Document Ingestion Tool

A Python script for uploading documents to the AlphaSense Enterprise Intelligence Platform via their Ingestion API.

## 📋 What's Implemented

The `alphasenseingestor.py` script provides a complete document upload solution with the following features:

### Core Functionality

- Authentication: OAuth2 password grant flow with AlphaSense API
- Document Upload: Single document upload with optional attachments
- Metadata Management: Support for JSON metadata files or inline JSON
- Configuration Management: TOML-based configuration for credentials
- Error Handling: Comprehensive error handling with detailed logging

### Key Functions

- authenticate_alphasense() - OAuth2 authentication with AlphaSense
- refresh_alphasense_token() - Token refresh for long-running processes
- upload_document_to_alphasense() - Main document upload function
- load_config() - Load authentication credentials from TOML file
- load_metadata_from_json() - Load document metadata from JSON files

## 🚀 How to Run

1. Download and open a terminal to the base folder containing `alphasenseingestor.py`.

        git clone https://github.com/sdconrox/alphasense_case_study.git
        cd alphasense_case_study/1

2. Install

        pip install .

3. Create Configuration File
Create a `alphasense.toml` file with your AlphaSense credentials and URLs:

        [alphasense]
        username = "your_email@company.com"
        password = "your_password"
        api_key = "your_api_key"
        client_id = "your_client_id"
        client_secret = "your_client_secret"
        auth_url = "https://api.alpha-sense.com/auth"
        ingestion_base_url = "https://research.alpha-sense.com/services/i/ingestion-api/v1"

4. Basic Usage Examples

        # Print help text
        alphasenseingestor --help

        # Upload a single document with default metadata
        alphasenseingestor 'document.pdf'
        
        # Upload with custom metadata from JSON file
        alphasenseingestor -m 'metadata.json' 'document.pdf'
        
        # Upload with attachment
        alphasenseingestor -a 'attachment.pdf' 'document.pdf'
        
        # Upload with inline JSON metadata
        alphasenseingestor -m '{"title": "My Report", "sourceType": "Research"}' 'document.pdf'
        
        # Use custom config file with verbose logging
        alphasenseingestor -c 'custom_config.toml' -v 'document.pdf'

5. Metadata Format

Create a `metadata.json` file for document metadata:

        {
            "title": "Quarterly Financial Report",
            "companies": [
                {
                    "value": "US5949181045",
                    "operation": "ADD",
                    "identifier": "ISIN",
                    "salience": "PRIMARY"
                }
            ],
            "docAuthors": [
                {
                    "authorName": "John Doe",
                    "operation": "ADD"
                }
            ],
            "sourceType": "Internal Research",
            "customTags": [
                {
                    "name": "quarterly_report",
                    "visibility": "PUBLIC",
                    "operation": "ADD"
                }
            ]
        }

## 🔧 Required Configuration

### Environment Setup

1. API Credentials: Obtain from AlphaSense admin portal
    - API Key
    - Client ID & Secret
    - Username & Password
2. Configuration File: Store credentials in alphasense.toml
    - Default location: ./alphasense.toml
    - Custom location: Use -c flag
3. Network Access: Ensure access to AlphaSense APIs
    - `https://api.alpha-sense.com` (authentication)
    - `https://research.alpha-sense.com` (document upload)
    - If deployed on-prem, ensure access to domain and subnet of deployment.

### File Requirements

- Documents: PDF, HTML, HTM, TXT, DOC, DOCX, XLS, XLSX, PPT, PPTX, MSG, EML, CSV, XLSB, XLSM, ONE, TSV, ODS
- Attachments: Optional, same format support
- Metadata: Valid JSON format (file or inline)

## 🚀 Production Readiness Roadmap

When scaling from a sample script to a full production pipeline, consider these enhancements:

### 🔥 High Priority

#### Refresh Expired Tokens

- There is currently a function written that will refresh the auth token, but it is not used.

#### Split CLI from Client

- Command Line Interface logic should be separated from client logic.
- This will allow both to be improved upon independently and allow the client to be interface agnostic.

#### Parallel Processing

- Current: Sequential uploads only
- Improvement: Implement async/await with aiohttp for concurrent uploads
- Benefit: 5-10x throughput improvement with proper rate limiting

#### Robust Error Handling

- Retry Logic: Exponential backoff for transient failures
- Circuit Breakers: Prevent cascade failures during outages
- Dead Letter Queue: Store failed uploads for manual review
- Partial Failure Recovery: Resume from last successful upload

#### Monitoring & Observability

- Structured Logging: JSON logs with correlation IDs
- Metrics: Upload success rates, latency, throughput
- Health Checks: API connectivity and authentication status
- Alerting: Failed upload notifications

#### Security Enhancements

- Credential Management: Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
- Token Caching: Secure storage and automatic refresh
- Audit Logging: Track all upload activities

### 🔶 Medium Priority

#### Scalability & Performance

- Batch Processing: Process multiple documents in batches
- Queue System: Use Redis/RabbitMQ for upload job management
- Connection Pooling: Reuse HTTP connections efficiently
- Content Validation: Pre-validate documents before upload

#### Data Management

- Metadata Validation: Schema validation for metadata consistency
- Document Deduplication: Prevent duplicate uploads
- Version Control: Track document versions and updates
- Cleanup Jobs: Remove failed/orphaned uploads

#### DevOps & Deployment

- Containerization: Docker images for consistent deployment
- Configuration Management: Environment-specific configs
- CI/CD Pipeline: Automated testing and deployment
- Infrastructure as Code: Terraform/CloudFormation templates

### 🟡 Low Priority

#### User Experience

- Progress Tracking: Real-time upload progress for large files

### Example Production Architecture

        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
        │   File Watcher  │───▶│   Upload Queue  │───▶│  Worker Nodes   │
        └─────────────────┘    └─────────────────┘    └─────────────────┘
                                        │                        │
                                        ▼                        ▼
                                ┌─────────────────┐    ┌─────────────────┐
                                │ Failed Jobs DLQ │    │ AlphaSense API  │
                                └─────────────────┘    └─────────────────┘
                                        │                        │
                                        ▼                        ▼
                                ┌─────────────────┐    ┌─────────────────┐
                                │   Monitoring    │    │ Success Logging │
                                └─────────────────┘    └─────────────────┘

## 📝 Next Steps

- Immediate: Add refresh logic, separate client from CLI.
- Short-term: Add parallel upload capability with rate limiting, implement retry logic and structured logging
- Medium-term: Add monitoring, security improvements, and batch processing
- Long-term: Build full production pipeline with web interface

For production use, start with parallel processing and error handling improvements, as these provide the highest impact for operational reliability and performance.
