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
        """
        Initialize the StockChecker with optional URL, check interval, and links directory.

        Args:
            url (str, optional): The URL to check for stock status. Defaults to None.
            check_interval (int, optional): The interval in seconds between stock checks. Defaults to 300.
            links_directory (str, optional): The directory where CSV files are stored. Defaults to "./links".

        Environment Variables:
            CHECK_INTERVAL (int): The default interval in seconds if not provided.
            LOG_LEVEL (str): The logging level for the application.
            USER_AGENT (str): The user agent for HTTP requests.

        The method also sets up logging and loads environment variables.
        """

        # load environment variables from .env file
        load_environment()

        # Set up variables
        self.url = url
        self.check_interval = check_interval or int(os.getenv('CHECK_INTERVAL', 300))
        self.links_directory = Path(links_directory)
        self.headers = get_request_headers()
        
        # Set up logging
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
        """Fetch HTML content from the given URL.

        Args:
            url (str): The URL to fetch

        Returns:
            Optional[str]: The HTML content if successful, None otherwise
        """
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
        """Context manager for a Selenium WebDriver instance.

        Yields a headless Chrome WebDriver instance. The instance is created with a
        user agent matching the value of the 'User-Agent' header set by the
        StockChecker instance. The instance is automatically quit when the context
        manager is exited.

        """
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
        """Fetch HTML content from the given URL using Selenium.

        Args:
            url (str): The URL to fetch

        Returns:
            Optional[str]: The HTML content if successful, None otherwise
        """
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
        Parse HTML content to determine stock status by looking for add to cart buttons.
        
        Args:
            html_content (str): The HTML content to parse
            site_name (str): The name of the site being checked

        Returns:
            tuple[bool, str, str]: (is_in_stock, product_name, site_name)
        """
        if not html_content:
            return None, None, None

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get product name from h1 tag
        product_name = soup.find('h1').text.strip() if soup.find('h1') else 'Product'
        
        # Find all submit buttons
        submit_buttons = soup.find_all('button', attrs={'type': 'submit'})
        
        # Check if any submit button contains "Add to cart" text
        is_in_stock = False
        for button in submit_buttons:
            # Get all text content from the button
            button_text = button.get_text(strip=True, separator=' ').lower()
            
            # Check if button is not disabled and contains "add to cart"
            is_disabled = (
                button.get('aria-disabled') == 'true' or
                'disabled' in button.attrs or
                'sold out' in button_text.lower()
            )
            
            if 'add to cart' in button_text and not is_disabled:
                is_in_stock = True
                break
        
        # Log the findings for debugging
        logging.debug(f"""
            Site: {site_name}
            Product: {product_name}
            Submit buttons found: {len(submit_buttons)}
            In stock: {is_in_stock}
        """)
        
        return is_in_stock, product_name, site_name

    def check_stock(self, url: Optional[str] = None, site_name: Optional[str] = None) -> tuple[bool, str, str]:
        """
        Check stock status of a product at a given URL.

        Args:
            url (Optional[str]): The URL of the product to check. Defaults to None.
            site_name (Optional[str]): The name of the site being checked. Defaults to None.

        Returns:
            tuple[bool, str, str]: (is_in_stock, product_name, site_name)
        """
        check_url = url or self.url
        if not check_url:
            raise ValueError("No URL provided")
        html_content = self.get_html_from_url(check_url)
        return self.parse_stock_status(html_content, site_name)

    def check_stock_with_selenium(self, url: Optional[str] = None, site_name: Optional[str] = None) -> tuple[bool, str, str]:
        """
        Check stock status of a product at a given URL using Selenium.

        Args:
            url (Optional[str]): The URL of the product to check. Defaults to None.
            site_name (Optional[str]): The name of the site being checked. Defaults to None.

        Returns:
            tuple[bool, str, str]: (is_in_stock, product_name, site_name)
        """
        check_url = url or self.url
        if not check_url:
            raise ValueError("No URL provided")
        html_content = self.get_html_with_selenium(check_url)
        return self.parse_stock_status(html_content, site_name)

    def monitor_multiple(self, urls: List[dict], notification_email: Optional[str] = None, use_selenium: bool = False):
        """
        Monitor multiple URLs for stock availability and notify via email if in stock.
        
        Args:
            urls (List[dict]): A list of dictionaries with 'url' and 'site_name' keys to monitor.
            notification_email (Optional[str]): Email address to send notifications if a product is in stock.
            use_selenium (bool): Flag to determine whether to use Selenium for fetching HTML content.
        
        Behavior:
            - Continuously checks stock status for given URLs at the specified interval.
            - Uses 'Requests' or 'Selenium' for HTML fetching based on `use_selenium` flag.
            - Sends an email notification if a product is found in stock.
            - Allows user to quit monitoring by pressing 'q'.
        """
        # Create an event to signal when to stop monitoring
        should_exit = threading.Event()
        
        def on_quit():
            """
            Called when the user presses 'q' to quit monitoring. Sets the 'should_exit'
            event and prints a message to the console.
            """
            should_exit.set()
            print("\nExiting...")
        
        # Set up keyboard listener
        keyboard.on_press_key('q', lambda _: on_quit())
        
        print(f"Starting stock monitor for {len(urls)} products")
        print(f"Using {'Selenium' if use_selenium else 'Requests'}")
        print(f"Checking every {self.check_interval} seconds...")
        print("\nPress 'q' to quit at any time...")

        # Main monitoring loop
        while not should_exit.is_set():
            # Check stock for each URL
            for entry in urls:
                # Check if monitoring should be stopped
                if should_exit.is_set():
                    break
                    
                try:
                    # Check stock
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

                    # Print stock status
                    if is_in_stock:
                        print(f"\n[{datetime.now()}] {site_name} - {product_name} is in stock!")
                        if notification_email:
                            self.send_notification(notification_email, product_name)
                    else:
                        print(f"\n[{datetime.now()}] {site_name} - {product_name} is out of stock")

                # Handle exceptions
                except Exception as e:
                    logging.error(f"Error checking {entry['url']}: {e}")
            
            # Sleep for specified interval
            if not should_exit.is_set():
                time.sleep(self.check_interval)
        
        # Clean up keyboard listener
        keyboard.unhook_all()

    def send_notification(self, to_email: str, product_name: str):
        """
        Send an email notification to the given address when a product is in stock.

        Args:
            to_email (str): The email address to send the notification to.
            product_name (str): The name of the product that is now in stock.

        Behavior:
            - Uses the email configuration from the environment variables.
            - Sends a plaintext email with the subject "Stock Alert: <product_name>" and
              the message "The product '<product_name>' is now in stock!\nURL: <url>".
            - Logs an error if there is an issue sending the notification.
        """
        # Get email configuration from environment
        email_config = get_email_config()
        
        try:
            # Send email
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
            
        # Handle exceptions
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")

if __name__ == "__main__":
    # DEBUG:
    print("--DEBUG--")




    
