# This python file contains the code for setting up the selenium driver. 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ==========================================================================================
#                          FUNCTIONS : SELENIUM DRIVER SETUP 
# ==========================================================================================
'''
* function_identifier: setup_driver
* summary: Sets up and initializes the selenium driver in headless mode, will be used for last resort.
* return: when successful returns an initialized chrome driver, otherwise returns None.
'''
def setup_driver():
    # configuring chrome
    try:
        options = Options()
        options.add_argument("--headless=new") 
        options.add_argument("--window-size=1920,1200") # set window size so that site pages open in desktop mode
        options.add_argument("--log-level=3")  # hiding logs that are not level 3. info=0, warning=1, log_error=2, log_fatal=3
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)" # setting a user agent so that sites won't flag me as a bot
                    "AppleWebKit/537.36 (KHTML, like Gecko)"
                    "Chrome/118.0.5993.117 Safari/537.36")

        # Trying to initialize a chrome driver that will automatically use the correct driver version
        print("Installing ChromeDriver...")
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as e:
            print("Failed to initialize Chrome driver...")
            return None
        
        print("Driver setup complete!\n")
        return driver 
    
    except Exception as e:
        print("An unexpected error occured during driver setup.")
        return None