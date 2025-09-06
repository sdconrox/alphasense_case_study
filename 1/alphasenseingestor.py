#!/usr/bin/env python3

import logging
import requests
import json
from typing import Dict, Any
from pathlib import Path

import tomllib
import click

def load_config(config_path: str = "alphasense.toml") -> Dict[str, str]:
    """
    Load configuration from a TOML file.
    
    Args:
        config_path: Path to the TOML configuration file
        
    Returns:
        Dict containing configuration
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        KeyError: If required configuration is missing
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    
    # Extract auth configuration
    if "alphasense" not in config:
        raise KeyError("Missing [alphasense] section in configuration file")
    
    config = config["alphasense"]
    
    # Validate required fields
    required_fields = [
        "username",
        "password",
        "api_key",
        "client_id",
        "client_secret",
        "auth_url",
        "ingestion_base_url"
    ]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise KeyError(f"Missing required auth fields: {missing_fields}")
    
    return config

def load_metadata_from_json(metadata_path: str) -> Dict[str, Any]:
    """
    Load document metadata from a JSON file.
    
    Args:
        metadata_path: Path to the JSON metadata file
        
    Returns:
        Dict containing document metadata
        
    Raises:
        FileNotFoundError: If the metadata file doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    metadata_file = Path(metadata_path)
    
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return metadata

def authenticate_alphasense(
    api_key: str,
    username: str,
    password: str,
    client_id: str,
    client_secret: str,
    url: str = 'https://api.alpha-sense.com/auth'
) -> Dict[str, Any]:
    """
    Authenticate with AlphaSense API using username/password credentials.
    
    Args:
        api_key: Your AlphaSense API key
        username: Your AlphaSense login email
        password: Your AlphaSense login password
        client_id: Your client ID
        client_secret: Your client secret
        url: The authentication endpoint URL
        
    Returns:
        Dict containing the authentication response
        
    Raises:
        requests.RequestException: If the request fails
    """
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises an exception for bad status codes
    
    return response.json()


def refresh_alphasense_token(
    api_key: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    url: str = 'https://api.alpha-sense.com/auth'
) -> Dict[str, Any]:
    """
    Refresh the access token for AlphaSense API.

    Args:
        api_key: Your AlphaSense API key
        client_id: Your client ID
        client_secret: Your client secret
        refresh_token: The refresh token obtained during initial authentication
        url: The authentication endpoint URL
        
    Returns:
        Dict containing the authentication response
        
    Raises:
        requests.RequestException: If the request fails
    """
    url = 'https://api.alpha-sense.com/auth'
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises an exception for bad status codes
    
    return response.json()

def upload_document_to_alphasense(
    access_token: str,
    document_path: str,
    metadata: Dict[str, Any],
    attachments: list = [],
    base_url: str = 'https://research.alpha-sense.com/services/i/ingestion-api/v1',
    client_id: str = "enterprise-sync"
) -> Dict[str, Any]:
    """
    Upload a document to AlphaSense using the ingestion API.
    
    Args:
        access_token: Bearer token from authentication
        document_path: Path to the main document file
        metadata: Dictionary containing document metadata
        attachments: List of attachment file paths (optional)
        base_url: The ingestion API endpoint base URL
        client_id: Client ID for the request
        
    Returns:
        Dict containing the upload response
        
    Raises:
        FileNotFoundError: If document or attachment files don't exist
        requests.RequestException: If the request fails
    """

    upload_path = '/upload-document'
    base_url += upload_path
    
    headers = {
        'Authorization': f'bearer {access_token}',
        'clientId': client_id
    }
    
    # Prepare the main document file
    document_file = Path(document_path)
    if not document_file.exists():
        raise FileNotFoundError(f"Document file not found: {document_path}")
    
    # Prepare files for upload
    files = []
    
    # Add main document
    files.append(('file', (document_file.name, open(document_file, 'rb'))))
    
    # Add attachments if provided
    if attachments:
        for attachment_path in attachments:
            attachment_file = Path(attachment_path)
            if not attachment_file.exists():
                raise FileNotFoundError(f"Attachment file not found: {attachment_path}")
            
            # Determine MIME type based on file extension
            mime_type = 'application/pdf' if attachment_file.suffix.lower() == '.pdf' else 'application/octet-stream'
            files.append(('attachments', (attachment_file.name, open(attachment_file, 'rb'), mime_type)))
    
    # Prepare form data
    data = {
        'metadata': json.dumps(metadata)
    }
    
    try:
        response = requests.post(base_url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()
    finally:
        # Close all opened files
        for file_tuple in files:
            if len(file_tuple) >= 2 and hasattr(file_tuple[1][1], 'close'):
                file_tuple[1][1].close()

@click.command()
@click.argument('document')
@click.option('-a', '--attachments', multiple=True, help='Path(s) to attachment file(s) (e.g., PDF, DOCX)')
@click.option('-c', '--config', default='alphasense.toml', help='Path to the TOML configuration file')
@click.option('-m', '--metadata', help='Path to JSON file with document metadata')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')

def cli(document, attachments, config, metadata, verbose):
    """AlphaSense Document Ingestor CLI"""
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level=logging.DEBUG)

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose mode on')
    
    logger.info('Starting AlphaSense Ingestor...')

    try:
        as_config = load_config(config)
        logger.info('Authenticating...')
        auth_response = authenticate_alphasense(
            api_key=as_config["api_key"],
            username=as_config["username"],
            password=as_config["password"],
            client_id=as_config["client_id"],
            client_secret=as_config["client_secret"],
            url=as_config["auth_url"]
        )
        logger.debug(auth_response)
        access_token = auth_response['access_token']

        logger.info('Loading metadata...')
        # Handle metadata argument
        if metadata:
            if metadata.endswith('.json'):
                # Load from JSON file
                metadata = load_metadata_from_json(metadata)
            else:
                # Parse as JSON string
                metadata = json.loads(metadata)
        else:
            # Use default metadata
            metadata = {
                "title": "Sample Document", 
                "docAuthors": [{"authorName": "Test Author", "operation": "ADD"}]
            }
        
        logger.info('Uploading...')
        upload_document_to_alphasense(
            access_token=access_token,
            document_path=document,
            attachments=attachments,
            metadata=metadata,
            base_url=as_config["ingestion_base_url"]
        )

    except (FileNotFoundError, KeyError) as e:
        logger.error(f"Configuration error: {e}")
    except requests.RequestException as e:
        logger.error(f"Authentication failed: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON metadata: {e}")
