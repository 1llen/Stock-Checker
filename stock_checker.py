import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from contextlib import contextmanager
import csv
import os
from pathlib import Path
from typing import List, Optional, Dict
from config.environment import load_environment, get_email_config, get_request_headers, get_receiver_email

class StockChecker:
    def __init__(self, url=None, check_interval=300, links_directory="./links"):
        # load environment variables from .env file
        load_environment()

        self.url = url
        self.check_interval = check_interval or int(os.getenv('CHECK_INTERVAL', 300))
        self.links_directory = Path(links_directory)
        self.headers = get_request_headers()
        
        logging.basicConfig(
            filename='stock_checker.log',
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format='%(asctime)s - %(message)s'
        )

    def get_url_list(self, filename: str, key: str) -> List[dict]:
        """
        Retrieves all URLs corresponding to the given key from the CSV file.

        Args:
            filename (str): The name of the CSV file
            key (str): The key to search for in the CSV file

        Returns:
            List[dict]: A list of dictionaries containing url and site_name for the given key
        """
        file_path = self.links_directory / filename
        entries = []

        try:
            with file_path.open(mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                entries = [
                    {
                        'url': row['url'].strip('" \'\t'),
                        'site_name': row['site_name'].strip('" \'\t')
                    }
                    for row in reader
                    if row.get('key').strip('" \'\t') == key
                ]

                if not entries:
                    logging.info(f"No URLs found for key '{key}' in {filename}")
                else:
                    logging.info(f"Found {len(entries)} URLs for key '{key}' in {filename}")

                return entries

        except FileNotFoundError:
            logging.error(f"CSV file not found: {file_path}")
            raise
        except csv.Error as e:
            logging.error(f"Error reading CSV file {filename}: {e}")
            raise
        
    def update_url(self, filename: str, key: str, new_url: str) -> bool:
        """
        Updates the URL for a given key in the CSV file.

        Args:
            filename (str): The name of the CSV file
            key (str): The key to update
            new_url (str): The new URL to associate with the key

        Returns:
            bool: True if update was successful, False otherwise
        """
        file_path = self.links_directory / filename
        temp_file = file_path.with_suffix('.tmp')
        updated = False

        try:
            with file_path.open(mode='r', encoding='utf-8') as csvfile, \
                 temp_file.open(mode='w', encoding='utf-8', newline='') as tempfile:
                reader = csv.reader(csvfile)
                writer = csv.writer(tempfile)

                # Write header
                header = next(reader)
                writer.writerow(header)

                # Update matching row
                for row in reader:
                    if row and row[0] == key:
                        writer.writerow([key, new_url])
                        updated = True
                    else:
                        writer.writerow(row)

            if updated:
                temp_file.replace(file_path)
                logging.info(f"Updated URL for key '{key}' in {filename}")
            else:
                temp_file.unlink()
                logging.info(f"Key '{key}' not found in {filename}")

            return updated

        except Exception as e:
            logging.error(f"Error updating URL in {filename}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    def get_html_from_url(self, url: str) -> Optional[str]:
        """Get HTML content from a URL using requests."""
        try:
            response = requests.get(url, headers=self.headers)
            print(f"\nResponse status code: {response.status_code}")
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching HTML: {str(e)}")
            return None

    @contextmanager
    def get_selenium_driver(self):
        """Context manager for creating and cleaning up Selenium WebDriver."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            yield driver
        finally:
            if driver:
                driver.quit()

    def get_html_with_selenium(self, url: str) -> Optional[str]:
        """Get HTML content from a URL using Selenium."""
        try:
            with self.get_selenium_driver() as driver:
                driver.get(url)
                time.sleep(2)  # Wait for dynamic content
                return driver.page_source
        except WebDriverException as e:
            logging.error(f"Selenium error: {str(e)}")
            return None

    def parse_stock_status(self, html_content: str, site_name: str) -> tuple[bool, str, str]:
        """
        Parse HTML content to determine stock status.
        
        Args:
            html_content (str): The HTML content to parse
            site_name (str): The name of the site being checked

        Returns:
            tuple[bool, str, str]: (is_in_stock, product_name, site_name)
        """
        if not html_content:
            return None, None, None

        soup = BeautifulSoup(html_content, 'html.parser')
        
        out_of_stock_indicators = [
            'out of stock',
            'sold out',
            'currently unavailable',
            'notify me when available'
        ]
        
        product_name = soup.find('h1').text.strip() if soup.find('h1') else 'Product'
        page_text = soup.get_text().lower()
        is_in_stock = not any(indicator in page_text for indicator in out_of_stock_indicators)
        
        return is_in_stock, product_name, site_name

    def check_stock(self, url: Optional[str] = None, site_name: Optional[str] = None) -> tuple[bool, str, str]:
        """Check stock status using requests."""
        check_url = url or self.url
        if not check_url:
            raise ValueError("No URL provided")
        html_content = self.get_html_from_url(check_url)
        return self.parse_stock_status(html_content, site_name)

    def check_stock_with_selenium(self, url: Optional[str] = None, site_name: Optional[str] = None) -> tuple[bool, str, str]:
        """Check stock status using Selenium."""
        check_url = url or self.url
        if not check_url:
            raise ValueError("No URL provided")
        html_content = self.get_html_with_selenium(check_url)
        return self.parse_stock_status(html_content, site_name)

    def monitor_multiple(self, urls: List[dict], notification_email: Optional[str] = None, use_selenium: bool = False):
        """
        Monitor multiple URLs for stock status.
        
        Args:
            urls (List[dict]): List of dictionaries containing 'url' and 'site_name'
            notification_email (Optional[str]): Email address for notifications
            use_selenium (bool): Whether to use Selenium for checking
        """
        print(f"Starting stock monitor for {len(urls)} products")
        print(f"Using {'Selenium' if use_selenium else 'Requests'}")
        print(f"Checking every {self.check_interval} seconds...")

        while True:
            for entry in urls:
                try:
                    if use_selenium:
                        is_in_stock, product_name, site_name = self.check_stock_with_selenium(
                            entry['url'], 
                            entry['site_name']
                        )
                    else:
                        is_in_stock, product_name, site_name = self.check_stock(
                            entry['url'], 
                            entry['site_name']
                        )

                    if is_in_stock:
                        print(f"[{datetime.now()}] {site_name} - {product_name} is in stock!")
                        if notification_email:
                            self.send_notification(notification_email, product_name)
                    else:
                        print(f"[{datetime.now()}] {site_name} - {product_name} is out of stock")

                except Exception as e:
                    logging.error(f"Error checking {entry['url']}: {e}")
            
            print("Press 'q' to quit...")

            if keyboard.is_pressed('q'):
                print("Exiting...")
                break

            time.sleep(self.check_interval)

    def send_notification(self, to_email: str, product_name: str):
        """Send email notification about stock status."""
        email_config = get_email_config()
        
        try:
            msg = MIMEText(f"The product '{product_name}' is now in stock!\nURL: {self.url}")
            msg['Subject'] = f"Stock Alert: {product_name}"
            msg['From'] = email_config['sender_email']
            msg['To'] = to_email
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(
                    email_config['sender_email'],
                    email_config['sender_password']
                )
                server.send_message(msg)
                
            logging.info(f"Notification sent to {to_email}")
            
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")

if __name__ == "__main__":
    # DEBUG:
    print("TODO...")
    