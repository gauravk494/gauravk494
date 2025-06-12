from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time

class RelayTestAutomation:
    def __init__(self, config=None):
        self.config = config or {
            'HES_URL': "https://eqahes.kimbal.io/Account/Login",
            'EMAIL': "gaurav@kimbal.io",
            'PASSWORD': "Gaurav@2024",
            'COMMAND_DELAY': 10,
            'WAIT_TIMEOUT': 30,
            'METER_LIST': ['AIK900284'],
            'COM_TYPE': 'CELLULAR',
            'DISCONNECT_DELAY': 120,
            'CONNECT_DELAY': 180,
            'ITERATIONS': 5,
            'MD_RESET_DELAY': 30
        }
        
        self.COM_TYPES = {
            'RF': [1, 2],
            'CELLULAR': [3],
            'TCP': [4]
        }
        
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self.wait = WebDriverWait(self.driver, self.config['WAIT_TIMEOUT'])

    def delay(self, seconds=None):
        time.sleep(seconds if seconds else self.config['MD_RESET_DELAY'])

    def login(self):
        """Login to HES with improved error handling"""
        try:
            print("Attempting to login...")
            
            # Load the login page
            self.driver.get(self.config['HES_URL'])
            self.delay(3)
            
            # Wait for page to load and locate elements using different strategies
            try:
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#Email"))
                )
            except:
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "Email"))
                )
            
            try:
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#Password"))
                )
            except:
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "Password"))
                )
            
            # Clear and fill in credentials with explicit waits
            self.delay(2)
            email_input.clear()
            email_input.send_keys(self.config['EMAIL'])
            self.delay(1)
            
            password_input.clear()
            password_input.send_keys(self.config['PASSWORD'])
            self.delay(1)
            
            # Try different methods to locate and click the login button
            try:
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                )
            except:
                try:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                    )
                except:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
                    )
            
            # Click with JavaScript if regular click fails
            try:
                submit_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for login to complete and verify
            self.delay(5)
            
            # Verify successful login by checking for a post-login element
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Meters']"))
                )
                print("Login successful!")
                return True
            except:
                print("Login verification failed")
                return False
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def navigate_to_meter(self, meter_number):
        try:
            meters_menu = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Meters']"))
            )
            meters_menu.click()
            self.delay(2)
            
            filter_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='FieldFilter']"))
            )
            filter_input.clear()
            filter_input.send_keys(meter_number)
            self.delay(2)
            
            dropdown = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[@class='btn btn-primary btn-xs dropdown-toggle']//span[@class='caret']")
                )
            )
            dropdown.click()
            self.delay(2)
            return True
            
        except Exception as e:
            print(f"Failed to navigate to meter: {str(e)}")
            return False

    def execute_md_reset_command(self, meter_number, com_type):
        try:
            print(f"\nExecuting MD Reset command")
            if not self.navigate_to_meter(meter_number):
                return False
            # Click MD Reset command
            command_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='MD Reset']"))
            )
            command_link.click()
            self.delay(3)
            # Select communication type
            com_select = self.wait.until(
                EC.presence_of_element_located((By.ID, 'MeterTemplateId'))
            )
            Select(com_select).select_by_index(com_type)
            self.delay(2)
            # Click confirm button
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]"))
            )
            confirm_button.click()
            print(f"Successfully executed: MD Reset")
            return True
        except Exception as e:
            print(f"Failed to execute MD Reset: {str(e)}")
            return False

    def countdown(self, seconds, message="Waiting"):
        """Display countdown timer in terminal"""
        for remaining in range(seconds, 0, -1):
            print(f"\r{message}: {remaining:3d} seconds remaining...", end='')
            time.sleep(1)
        print("\rWait completed!            ")

    def run_md_reset_cycle(self):
        start_time = datetime.now()
        results = {
            'successful_operations': 0,
            'failed_operations': 0,
            'errors': []
        }
        try:
            print(f"Starting MD Reset test at {start_time}")
            if self.login():
                com_type = self.config.get('COM_TYPE', 'RF')
                com_indices = self.COM_TYPES.get(com_type, [1])
                for meter in self.config['METER_LIST']:
                    print(f"\nTesting meter: {meter}")
                    for iteration in range(self.config['ITERATIONS']):
                        print(f"\nStarting iteration {iteration + 1} of {self.config['ITERATIONS']}")
                        print("-" * 30)
                        for com_index in com_indices:
                            if self.execute_md_reset_command(meter, com_index):
                                print(f"MD Reset command successful")
                                self.countdown(self.config['MD_RESET_DELAY'], "MD Reset delay")
                                results['successful_operations'] += 1
                            else:
                                results['failed_operations'] += 1
            else:
                raise Exception("Login failed")
        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            print(error_msg)
            results['errors'].append(error_msg)
        finally:
            end_time = datetime.now()
            duration = end_time - start_time
            print("\nMD Reset Test Summary")
            print("=" * 50)
            print(f"Total Iterations Completed: {self.config['ITERATIONS']}")
            print(f"Duration: {duration}")
            print(f"Successful Operations: {results['successful_operations']}")
            print(f"Failed Operations: {results['failed_operations']}")
            if results['errors']:
                print("\nErrors encountered:")
                for error in results['errors']:
                    print(f"- {error}")
            self.driver.quit()
            return results

if __name__ == "__main__":
    try:
        config = {
            'HES_URL': "https://eqahes.kimbal.io/Account/Login",
            'EMAIL': "tarun@kimbal.io",
            'PASSWORD': "Tarun@crystal2023",
            'WAIT_TIMEOUT': 30,  # Wait timeout for page load
            'METER_LIST': ['AKL0000016'],  # Meter List: List of meter numbers to test
            'COM_TYPE': 'RF',  # Communication Type: RF, CELLULAR, TCP
            'MD_RESET_DELAY': 100,  # Delay after MD Reset command
            'ITERATIONS': 5  # Configure number of iterations here
        }
        relay_test = RelayTestAutomation(config)
        results = relay_test.run_md_reset_cycle()
        exit(0 if results['failed_operations'] == 0 else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        exit(1)
