import os
import sys
import keyboard
import threading
from typing import List, Dict, Optional
import csv
from pathlib import Path
from datetime import datetime
import time
from config.environment import load_environment, get_email_config, get_app_config  # Added get_app_config
from stock_checker import StockChecker

class StockCheckerCLI:
    def __init__(self):
        try:
            self.checker = None
            self.monitoring_thread = None
            self.stop_monitoring = False
            load_environment()
            self.email_config = get_email_config()
            self.app_config = get_app_config()
            self.selected_csv = None
            print("Initialization complete.")
        except Exception as e:
            print(f"Error during initialization: {e}")
            raise

    def get_csv_files(self) -> List[Path]:
        """Get all CSV files from the links directory."""
        links_dir = Path(self.app_config['links_directory'])
        if not links_dir.exists():
            print(f"Creating links directory at {links_dir}")
            links_dir.mkdir(parents=True, exist_ok=True)
        
        return sorted(links_dir.glob('*.csv'))

    def select_csv_file(self) -> Optional[str]:
        """Display menu of available CSV files and get user selection."""
        self.clear_screen()
        print("Select CSV File")
        print("--------------")
        
        csv_files = self.get_csv_files()
        if not csv_files:
            print(f"\nNo CSV files found in {self.app_config['links_directory']}")
            print("Please add CSV files to continue.")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        for i, file_path in enumerate(csv_files, 1):
            print(f"{i}. {file_path.name}")
        
        print("\n0. Exit")
        
        try:
            choice = int(input(f"\nEnter your choice (0-{len(csv_files)}): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(csv_files):
                selected_file = csv_files[choice - 1]
                # Verify the file is a valid CSV with required columns
                try:
                    with open(selected_file, 'r') as f:
                        reader = csv.DictReader(f)
                        # Check for required columns
                        required_columns = {'key', 'url', 'site_name'}
                        if not required_columns.issubset(reader.fieldnames):
                            print(f"\nError: {selected_file.name} is missing required columns.")
                            print(f"Required columns: {', '.join(required_columns)}")
                            input("\nPress Enter to try again...")
                            return self.select_csv_file()
                except Exception as e:
                    print(f"\nError reading {selected_file.name}: {e}")
                    input("\nPress Enter to try again...")
                    return self.select_csv_file()
                
                return selected_file.name
            
            raise ValueError()
        except ValueError:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")
            return self.select_csv_file()

    def clear_screen(self):
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_available_keys(self) -> List[str]:
        """Get all unique keys from the selected CSV file."""
        if not self.selected_csv:
            raise ValueError("No CSV file selected")
            
        csv_path = Path(self.app_config['links_directory']) / self.selected_csv
        try:
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                return sorted(list(set(row['key'] for row in reader)))
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []

    def get_email_settings(self) -> Dict[str, str]:
        """Get email settings from user or environment."""
        self.clear_screen()
        print("Email Configuration")
        print("------------------")
        print("1. Use default settings from environment")
        print("2. Enter custom settings")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == "1":
            if not all([self.email_config['sender_email'], self.email_config['sender_password']]):
                print("\nError: Environment variables not properly configured.")
                return self.get_email_settings()
            
            receiver_email = input("\nEnter receiver email address: ").strip()
            return {
                'sender_email': self.email_config['sender_email'],
                'sender_password': self.email_config['sender_password'],
                'receiver_email': receiver_email
            }
        elif choice == "2":
            return {
                'sender_email': input("\nEnter sender email address: ").strip(),
                'sender_password': input("Enter sender email password: ").strip(),
                'receiver_email': input("Enter receiver email address: ").strip()
            }
        else:
            print("\nInvalid choice. Please try again.")
            return self.get_email_settings()

    def display_key_menu(self, keys: List[str]) -> Optional[str]:
        """Display menu of available keys and get user selection."""
        self.clear_screen()
        print("Available Products")
        print("-----------------")
        
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key}")
        
        print("\n0. Exit")
        
        try:
            choice = int(input("\nEnter your choice (0-{}): ".format(len(keys))))
            if choice == 0:
                return None
            if 1 <= choice <= len(keys):
                return keys[choice - 1]
            raise ValueError()
        except ValueError:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")
            return self.display_key_menu(keys)

    def monitor_wrapper(self, urls: List[dict], notification_email: str):
        """Wrapper function for monitoring that can be stopped."""
        self.checker = StockChecker()
        print("\nMonitoring started. Press 'q' to stop and return to menu.")
        print("--------------------------------------------------")
        
        while not self.stop_monitoring:
            try:
                for entry in urls:
                    if self.stop_monitoring:
                        break
                    
                    is_in_stock, product_name, site_name = self.checker.check_stock(
                        entry['url'],
                        entry['site_name']
                    )

                    if is_in_stock:
                        print(f"\n[{datetime.now()}] {site_name} - {product_name} is in stock!")
                        if notification_email:
                            self.checker.send_notification(notification_email, product_name)
                    else:
                        print(f"\n[{datetime.now()}] {site_name} - {product_name} is out of stock")

                if not self.stop_monitoring:
                    time.sleep(self.checker.check_interval)
                    
            except Exception as e:
                print(f"Error during monitoring: {e}")
                if not self.stop_monitoring:
                    time.sleep(self.checker.check_interval)

    def start_monitoring(self, selected_key: str, email_settings: Dict[str, str]):
        """Start the monitoring process in a separate thread."""
        self.clear_screen()
        try:
            urls = self.checker.get_url_list(self.selected_csv, selected_key)
            if not urls:
                print(f"No URLs found for key: {selected_key}")
                input("\nPress Enter to continue...")
                return

            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(
                target=self.monitor_wrapper,
                args=(urls, email_settings['receiver_email'])
            )
            self.monitoring_thread.start()

            # Wait for 'q' press
            keyboard.wait('q')
            self.stop_monitoring = True
            self.monitoring_thread.join()
            
        except Exception as e:
            print(f"Error starting monitoring: {e}")
            input("\nPress Enter to continue...")

    def run(self):
        """Main CLI loop."""
        while True:
            self.clear_screen()
            print("Pokemon Stock Checker")
            print("-------------------")
            
            # Select CSV file
            self.selected_csv = self.select_csv_file()
            if not self.selected_csv:
                break
                
            # Get email settings
            email_settings = self.get_email_settings()
            
            # Initialize checker with email settings
            self.checker = StockChecker()
            
            # Get available keys from selected CSV file
            keys = self.get_available_keys()
            if not keys:
                print(f"No products found in {self.selected_csv}")
                input("\nPress Enter to continue...")
                continue
            
            # Display key menu and get selection
            selected_key = self.display_key_menu(keys)
            if selected_key is None:
                continue  # Go back to CSV selection instead of exiting
            
            # Start monitoring
            self.start_monitoring(selected_key, email_settings)

def main():
    try:
        print("Starting Stock Checker...")
        try:
            cli = StockCheckerCLI()
            print("CLI object created successfully.")
            cli.run()
        except Exception as e:
            print(f"Error creating CLI object: {e}")
            raise
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()