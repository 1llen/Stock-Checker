import os
from dotenv import load_dotenv
from pathlib import Path

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path('.') / '.env'
    load_dotenv(env_path)

def get_email_config():
    """Get email configuration from environment variables"""
    return {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD'),
    }

def get_request_headers():
    """Get request headers from environment variables"""
    return {
        'User-Agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        'Accept': os.getenv('ACCEPT_HEADER', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        'Accept-Language': os.getenv('ACCEPT_LANGUAGE', 'en-US,en;q=0.5'),
    }

def get_receiver_email():
    """Get receiver email from environment variable"""
    return os.getenv('RECEIVER_EMAIL')

def get_app_config():
    """Get application configuration from environment variables"""
    return {
        'check_interval': int(os.getenv('CHECK_INTERVAL', 300)),
        'links_directory': os.getenv('LINKS_DIRECTORY', './links'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'csv_filename': os.getenv('CSV_FILENAME', 'pokemon_products.csv')
    }