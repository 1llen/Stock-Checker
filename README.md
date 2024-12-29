# Stock Checker

A Python-based CLI tool for monitoring stock availability on multiple websites. This tool can check the stock status of products listed in a CSV file, and send email notifications when items come in stock.

## Features

- Monitor multiple websites simultaneously
- Email notifications when items come in stock
- Support for multiple CSV files containing different product lists
- Configurable check intervals
- Environment-based configuration
- Support for both regular HTTP requests and Selenium for dynamic content

## Installation

1. Clone the repository:

```bash
git clone [TODO]
cd Stock-Checker
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file:

```bash
touch .env
```

5. Configure your `.env` file with your email settings and preferences:

```plaintext
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password

# Application Settings
CHECK_INTERVAL=300
LINKS_DIRECTORY=./links
LOG_LEVEL=INFO
CSV_FILENAME=pokemon_products.csv
```

## Setting up Gmail for Notifications

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to Google Account Settings
   - Navigate to Security
   - Find "App Passwords" under 2-Step Verification
   - Generate a new app password for "Mail"
3. Use this app password in your `.env` file

## CSV File Format

Create CSV files in the `links` directory with the following format:

```csv
key,site_name,url
example_product,example_retailer,https://example.link
```

## Usage

1. Start the program:

```bash
python cli.py
```

2. Follow the prompts to:

   - Select a CSV file to monitor
   - Configure email settings
   - Choose which product type to monitor

3. The program will start monitoring and display status updates
4. Press 'q' at any time to stop monitoring and return to the main menu

## Project Structure

```plaintext
pokemon-stock-checker/
├── config/
│   ├── __init__.py
│   └── environment.py
├── links/
│   └── pokemon_products.csv
├── tests/
│   ├── __init__.py
│   └── [test files]
├── .env
├── .env.example
├── cli.py
├── stock_checker.py
└── requirements.txt
```

## Development

To run tests:

```bash
python -m pytest
```

## Troubleshooting

1. If you get SSL errors with Gmail:

   - Make sure you're using an App Password, not your regular password
   - Check that your email address is correct

2. If web scraping fails:
   - Some websites may block automated requests
   - Try enabling Selenium mode
   - Check if the website's HTML structure has changed
