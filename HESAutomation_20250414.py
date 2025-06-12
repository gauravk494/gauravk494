from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
from selenium.webdriver.common.keys import Keys

class HESAutomation:
    def __init__(self, config=None):
        self.config = config or {
            'HES_URL': "https://eqahes.kimbal.io/Account/Login",
            'EMAIL': "tarun@kimbal.io",
            'PASSWORD': "Tarun@crystal2023",
            'COMMAND_DELAY': 30,
            'WAIT_TIMEOUT': 40,
            'METER_LIST': ['AKL0000016'],
            'COM_TYPE': 'RF'
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
        self.wait = WebDriverWait(self.driver, self.config['WAIT_TIMEOUT'])

        self.current_datetime = datetime.now()
        self.next_date = (self.current_datetime + timedelta(days=1)).date()
        self.tod_activation_time = (self.current_datetime + timedelta(seconds=59)).strftime('%Y-%m-%d %H:%M:%S')

    def delay(self, seconds=None):
        time.sleep(seconds if seconds else self.config['COMMAND_DELAY'])

    def setup(self):
        self.driver.get(self.config['HES_URL'])
        self.delay(3)

    def element_action(self, xpath, action='click', value=None):
        try:
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

            if action == 'click':
                element.click()
            elif action == 'send_keys':
                element.clear()
                element.send_keys(value)
            elif action == 'select':
                Select(element).select_by_index(value)

            self.delay(2)
            return True
        except Exception as e:
            print(f"Error performing {action} on element {xpath}: {str(e)}")
            return False

    def login(self, email, password):
        """Login to HES with improved error handling"""
        try:
            print("Attempting to login...")
            
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
            email_input.send_keys(email)
            self.delay(1)
            
            password_input.clear()
            password_input.send_keys(password)
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
        self.element_action("//span[normalize-space()='Meters']")
        self.element_action("//input[@id='FieldFilter']", 'send_keys', meter_number)
        dropdown_toggle_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='btn btn-primary btn-xs dropdown-toggle']")))
        self.driver.execute_script("arguments[0].click();", dropdown_toggle_element) # JavaScript click
        # Explicitly wait for a generic command link to be clickable within the dropdown, ensuring the menu is open and interactive
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Get RTC']")))
        self.delay(0.5) # Small delay to ensure dropdown menu items are fully interactive

    def execute_command(self, meter_number, command_name, com_type, **params):
        try:
            print(f"\nExecuting {command_name}")
            self.navigate_to_meter(meter_number)
            self.delay(1) # Add a 1-second delay to ensure dropdown contents are interactive

            # Wait for a generic command link within the dropdown to be clickable, ensuring the menu is open
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Get RTC']")))
            self.delay(0.2) # Small delay to ensure menu items are fully interactive after they are clickable

            # Now, wait for and click the specific command link
            command_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[normalize-space()='{command_name}']")))
            self.driver.execute_script("arguments[0].click();", command_link)

            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'modal-content')))

            if 'input_value' in params:
                field_to_target = params.get('field_id', 'Period')  # Default to 'Period' if not specified
                input_field = self.wait.until(EC.visibility_of_element_located((By.ID, field_to_target)))
                input_field.click()
                input_field.clear()
                self.driver.execute_script("arguments[0].value = arguments[1];", input_field, str(params['input_value']))
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", input_field)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", input_field)
                self.delay(2)

            if 'select_value' in params:
                select_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-control")))
                Select(select_elem).select_by_index(params['select_value'])
                self.delay(2)

            com_select = self.wait.until(EC.presence_of_element_located((By.ID, 'MeterTemplateId')))
            Select(com_select).select_by_index(com_type)
            self.delay(2)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]"))).click()
            print(f"Command executed: {command_name}")
            self.delay(self.config['COMMAND_DELAY'])
            return True

        except Exception as e:
            print(f"Failed to execute {command_name}: {str(e)}")
            return False

    def run_test_sequence(self, meter_number, com_type):
        print(f"\nExecuting SET commands using COM {com_type}...")
        set_commands = [
            ('Set Profile capture Period', {'input_value': 900, 'field_id': 'Period'}),      
            ('Set Demand Integration Period', {'input_value': 900, 'field_id': 'Period'}),
            ('Set Instant Capture Period', {'input_value': 900, 'field_id': 'Period'}),
            ('Set Payment Mode', {'select_value': 1}),
            ('Set Netmetering Mode', {'select_value': 1}),
            ('Set Load Limit', {'input_value': 11111, 'field_id': 'LoadLimit'}),
            ('Set Load Curtailment (Lockout Period)', {'input_value': 900, 'field_id': 'Period'}),
            ('Set Load Curtailment (Interval Time)', {'input_value': 300, 'field_id': 'Interval'}),
            ('Set Load Curtailment (Reconnection Attempts)', {'input_value': 3, 'field_id': 'Attempts'}),
            ('Set Tamper Occurrence Interval', {'input_value': 30, 'field_id': 'Interval'}),
            ('Set Tamper Restoration Interval', {'input_value': 30, 'field_id': 'Interval'})
        ]

        for command, params in set_commands:
            self.execute_command(meter_number, command, com_type, **params)
            self.delay(2)

        print(f"\nExecuting GET commands using COM {com_type}...")
        get_commands = [
            'Get RTC', 'Get Load Limit', 'Get Profile Capture Period', 'Get Demand Integration Period',
            'Get Current Limit', 'Get Name Plate', 'Get Netmetering Mode', 'Get Payment Mode',
            'Get Meter Battery Health', 'Get Billing Date', 'Get Relay Status',
            'Get ESW', 'Get Internal FW Version', 'Get Tamper Occurrence Interval',
            'Get Tamper Restoration Interval', 'Get Instant Capture Period',
            'Get Load Curtailment (Lockout Period)', 'Get Load Curtailment (Interval Time)',
            'Get Load Curtailment (Reconnection Attempts)', 'Request Instantaneous Profile', 'MD Reset',
            'Activate Calendar'
        ]

        for command in get_commands:
            self.execute_command(meter_number, command, com_type)
            self.delay(2)

        print(f"\nExecuting Connect/Disconnect tests using COM {com_type}...")
        self.execute_command(meter_number, 'Connect/Disconnect Relay', com_type, select_value=1)
        self.delay()
        self.execute_command(meter_number, 'Connect/Disconnect Relay', com_type, select_value=0)

        print("\nExecuting final ping...")
        self.execute_command(meter_number, 'Ping Meter', com_type)

    def run_tests(self):
        start_time = datetime.now()
        results = {'total_tests': 0, 'successful_tests': 0, 'failed_tests': 0, 'meters_tested': [], 'errors': []}

        try:
            print(f"Starting test execution at {start_time}")
            self.setup()

            if self.login(self.config['EMAIL'], self.config['PASSWORD']):
                com_type = self.config.get('COM_TYPE', 'RF')
                com_indices = self.COM_TYPES.get(com_type, [1])

                for meter in self.config['METER_LIST']:
                    try:
                        print(f"\nTesting meter: {meter}\n{'-'*50}")
                        results['total_tests'] += 1
                        results['meters_tested'].append(meter)

                        for com_index in com_indices:
                            self.run_test_sequence(meter, com_index)

                        results['successful_tests'] += 1
                    except Exception as e:
                        error_msg = f"Error testing meter {meter}: {str(e)}"
                        print(error_msg)
                        results['failed_tests'] += 1
                        results['errors'].append(error_msg)
            else:
                raise Exception("Login failed")

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            print(error_msg)
            results['errors'].append(error_msg)

        finally:
            end_time = datetime.now()
            duration = end_time - start_time

            print("\nTest Execution Summary\n" + "=" * 50)
            print(f"Start Time: {start_time}")
            print(f"End Time: {end_time}")
            print(f"Duration: {duration}")
            print(f"Total Meters Tested: {len(results['meters_tested'])}")
            print(f"Successful Tests: {results['successful_tests']}")
            print(f"Failed Tests: {results['failed_tests']}")

            if results['errors']:
                print("\nErrors encountered:")
                for error in results['errors']:
                    print(f"- {error}")

            print("\nClosing browser...")
            self.driver.quit()
            return results

if __name__ == "__main__":
    try:
        config = {
            'HES_URL': "https://eqahes.kimbal.io/Account/Login",
            'EMAIL': "tarun@kimbal.io",
            'PASSWORD': "Tarun@crystal2023",
            'COMMAND_DELAY': 30,
            'WAIT_TIMEOUT': 40,
            'METER_LIST': ['MH9008700'],
            'COM_TYPE': 'CELLULAR' # Can be 'RF', 'CELLULAR', or 'TCP'
        }

        hes = HESAutomation(config)
        results = hes.run_tests()

        if results['failed_tests'] > 0:
            print("One or more tests failed.")
        else:
            print("All tests passed successfully.")

    except Exception as e:
        print(f"Fatal error: {str(e)}")
