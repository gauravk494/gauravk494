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

    def execute_request_instantaneous_profile_command(self, meter_number, com_type):
        try:
            print(f"\nExecuting Request Instantaneous Profile command")
            if not self.navigate_to_meter(meter_number):
                return False
            # Click Request Instantaneous Profile command
            command_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Request Instantaneous Profile']"))
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
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]") )
            )
            confirm_button.click()
            print(f"Successfully executed: Request Instantaneous Profile")
            return True
        except Exception as e:
            print(f"Failed to execute Request Instantaneous Profile: {str(e)}")
            return False

    def execute_set_clock_command(self, meter_number, com_type, rtc_datetime):
        try:
            print(f"\nExecuting Set Clock command to set RTC: {rtc_datetime}")
            if not self.navigate_to_meter(meter_number):
                return False
            # Click Set Clock command
            command_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Set Clock']"))
            )
            command_link.click()
            self.delay(3)
            # Set RTC value in the required format
            rtc_input = self.wait.until(
                EC.presence_of_element_located((By.ID, 'RTC'))
            )
            rtc_str = rtc_datetime.strftime('%Y-%m-%d %H:%M:%S')
            self.driver.execute_script("""
                let input = arguments[0];
                input.value = arguments[1];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, rtc_input, rtc_str)
            self.delay(1)
            # Select communication type
            com_select = self.wait.until(
                EC.presence_of_element_located((By.ID, 'MeterTemplateId'))
            )
            Select(com_select).select_by_index(com_type)
            self.delay(2)
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]"))
            )
            confirm_button.click()
            print(f"Successfully executed: Set Clock")
            return True
        except Exception as e:
            print(f"Failed to execute Set Clock: {str(e)}")
            return False

    def countdown(self, seconds, message="Waiting"):
        """Display countdown timer in terminal"""
        for remaining in range(seconds, 0, -1):
            print(f"\r{message}: {remaining:3d} seconds remaining...", end='')
            time.sleep(1)
        print("\rWait completed!            ")

    def run_rollover_through_hes_cycle(self):
        start_time = datetime.now()
        results = {
            'successful_operations': 0,
            'failed_operations': 0,
            'errors': []
        }
        try:
            print(f"Starting Set Clock + Request Instantaneous Profile test at {start_time}")
            if self.login():
                com_type = self.config.get('COM_TYPE', 'RF')
                # For RF, only use RF 1 (index 1), not RF 2
                if com_type == 'RF':
                    com_indices = [1]
                else:
                    com_indices = self.COM_TYPES.get(com_type, [1])
                rtc_increment_min = self.config.get('RTC_INCREMENT_MINUTES', 1)
                for meter in self.config['METER_LIST']:
                    print(f"\nTesting meter: {meter}")
                    last_rtc = None
                    for iteration in range(self.config['ITERATIONS']):
                        print(f"\nStarting iteration {iteration + 1} of {self.config['ITERATIONS']}")
                        print("-" * 30)
                        for com_index in com_indices:
                            # Set RTC: first iteration uses system RTC, subsequent use incremented RTC
                            if iteration == 0 or last_rtc is None:
                                rtc_to_set = datetime.now()
                                last_rtc = rtc_to_set  # Store the first RTC set
                            else:
                                rtc_to_set = last_rtc + timedelta(minutes=rtc_increment_min)
                                last_rtc = rtc_to_set  # Update last_rtc to the value just set
                            print(f"Setting RTC to: {rtc_to_set.strftime('%Y-%m-%d %H:%M:%S')}")
                            if self.execute_set_clock_command(meter, com_index, rtc_to_set):
                                print(f"Set Clock command successful")
                                results['successful_operations'] += 1
                            else:
                                print(f"Set Clock command failed")
                                results['failed_operations'] += 1
                            # Request Instantaneous Profile
                            if self.execute_request_instantaneous_profile_command(meter, com_index):
                                print(f"Request Instantaneous Profile command successful")
                                self.countdown(self.config['MD_RESET_DELAY'], "Request Instantaneous Profile delay")
                                results['successful_operations'] += 1
                            else:
                                print(f"Request Instantaneous Profile command failed")
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
            print("\nSet Clock + Request Instantaneous Profile Test Summary")
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
            'HES_URL': "https://kimbal-demohes.kimbal.io/Account/Login",
            'EMAIL': "preeti.kumari@kimbal.io",
            'PASSWORD': "Preeti@123",
            'WAIT_TIMEOUT': 30,  # Wait timeout for page load
            'METER_LIST': ['AP9001236'],  # Meter List: List of meter numbers to test
            'COM_TYPE': 'RF',  # Communication Type: RF, CELLULAR, TCP
            'MD_RESET_DELAY': 60,  # Delay after Request Instantaneous Profile command
            'ITERATIONS': 1000,  # Configure number of iterations here
            'RTC_INCREMENT_MINUTES': 300  # Configurable RTC increment in minutes (min 1, max 1000)
        }
        relay_test = RelayTestAutomation(config)
        results = relay_test.run_rollover_through_hes_cycle()
        exit(0 if results['failed_operations'] == 0 else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        exit(1)
