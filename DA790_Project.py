'''
* Name: Lettie Unkrich
* Description: The program will scrape 100+ websites looking for articles related to alzheimer's, extract relevant data, and store it into
an excel spreadsheet. When gathering the data, it will firstly check if an API is available and convenient to use. If either condition
is false, the program will move on to using the Requests library with BeautifulSoup4, and only turn to Selenium if dynamic elements 
require it. 
* Input: The code requires the website urls to the news/press release home page.
* Output: A csv file of the metadata collected from alzheimer related articles.
''' 


# ==========================================================================================
#                                IMPORTS AND INSTALL COMMANDS
# ==========================================================================================

# pip3 install selenium
# pip3 install webdriver-manager
# pip3 install beautifulsoup4
# pip3 install Pillow

import pandas as pd
from bs4 import BeautifulSoup
import time
import requests
import re
import os
# was picking up external links like https://support.microsoft.com/ added library so can code function that pulls internal links only.
from urllib.parse import urlparse
# helps to create unique values for file names or etc.
from datetime import datetime
# Using pillow library to open and convert images
from PIL import Image

# selenium stuff
# let's user launch a browser
from selenium import webdriver
# let's user customize how chrome runs
from selenium.webdriver.chrome.options import Options
# will auto-download and manage the correct chrome driver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
# let's user tell Selenium how to find things
from selenium.webdriver.common.by import By
# prevents web scraping from occuring too early by waiting for elements to appear
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# ==========================================================================================


# ==========================================================================================
#             FUNCTIONS : DRIVER SETUP AND LINK CHECKERS (REQUESTS, SELENIUM)
# ==========================================================================================
'''
* function_identifier: setup_driver
* summary: Sets up and initializes the selenium driver in headless mode, will be used for last resort.
'''
def setup_driver():
    # Configuring chrome
    try:
        options = Options()
        options.add_argument("--headless=new") # will make it to where things run in the background without opening a browser
        options.add_argument("--window-size=1920,1200") # decides window size
        options.add_argument("--log-level=3")  # prevents logs from spamming the terminal. info=0, warning=1, log_error=2, log_fatal=3
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)" #Trying to avoid sites from seeing me as a bnot since I am using headless mode.
                    "AppleWebKit/537.36 (KHTML, like Gecko)"
                    "Chrome/118.0.5993.117 Safari/537.36")

        # Initializing a chrome driver that will automatically use the correct driver
        print("Installing ChromeDriver...")
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as e:
            print("Failed to initialize Chrome driver...")
        print("Driver setup complete!\n")
        return driver 
    except Exception as e:
        print("An unexpected error occured during driver setup.")

'''
* function_identifier: get_links_bs
* summary: Grabbing all links from a single page using requests by beautiful soup
'''
def get_links_bs(url, container=None):
    links = []
    try:
        r = requests.get(url, timeout=10)
        time.sleep(3)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # get list of containers to search for links
        containers = get_bs_container(soup, container)

        # loop through each container
        for c in containers:
            # find all <a> tags with href
            for a in c.find_all("a", href=True):
                href = a["href"]  # get the URL from href
                if href.startswith("http"):  # only keep full URLs
                    if "page=" in href or "/page/" in href: # do not want to add pagination pages to our list of links
                        continue
                    links.append(href)
    
    except Exception as e:
        print("Failed to get links from", url, "when using requests by BeautifulSoup.")
    
    # remove duplicates before returning
    unique_links = list(set(links))
    print("Found", len(unique_links), "links overall on", url, "when using Beautiful Soup.")
    return unique_links

'''
* function_identifier: get_links_sel
* summary: Grabbing all links from a single page using selenium, for fallback if get_links_bs() fails
'''
def get_links_sel(url, driver, reload=True, container=None): 
    if reload:
        try:  
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except TimeoutException:
            print("Timeout loading page:", url, "while running get_links_sel.")

    links = []

    # get the containers to search for links
    containers = get_sel_container(driver, container)
    
    # loop through each container
    for c in containers:
        # find all <a> tags inside the container
        link_elements = c.find_elements(By.TAG_NAME, "a")
        for element in link_elements:
            href = element.get_attribute("href")
            if href and href.startswith("http"):
                if "page=" in href or "/page/" in href: # do not want to add pagination pages to our list of links
                    continue
                links.append(href)
    
    # remove duplicates before returning
    unique_links = list(set(links))
    print("Found", len(unique_links), "links overall on", url, "when using Selenium.")
    return unique_links


# ==========================================================================================
#                           FUNCTIONS : LINK CONTAINER FUNCTIONS
# ==========================================================================================
'''
* function_identifier: get_bs_container
* summary: Returns the BeautifulSoup element(s) to search in for links. Prevents the whole page from being scraped if a container is found.
If container is found it returns the container. If not, it returns the whole soup.
'''
def get_bs_container(soup, container=None):
    try:
        if container:
            try:
                container_tag = container.get("tag")
                container_class = container.get("class")
            except Exception as e:
                print("Unable to pull tag and/or class from container info.")
                return [soup]

            # Try to find the main container
            try:
                outer = soup.find(container_tag, class_=container_class)
            except Exception as e:
                print("Container not found.")
                return [soup]

            if outer:
                containers = []
                try:
                    # loop through all children of the container
                    children = outer.find_all(True)  # True finds all tags
                    for child in children:
                        if child.find("a", href=True): # if child has links
                            containers.append(child)
                except Exception as e:
                    print("Error occured when looking through children nodes for links.")

                if containers:  # if any children were found with links
                    return containers
                else:  # fallback and use the main container
                    return [outer]
            else:
                print("Container not found. Scraping whole page.")
                return [soup]
        else:
            return [soup]

    except Exception as e:
        print("Unexpected error occured in get_bs_container")
        return [soup]


'''
* function_identifier: get_sel_container
* summary: Returns the Selenium element(s) to search in for links. 
If container is found it returns the container. If not, it returns none and get_links_sel will return all <a> elements that start with http.
'''
def get_sel_container(driver, container=None):
    if container:
        try:
            container_tag = container.get("tag")
            container_class = container.get("class")
        except Exception as e:
            print("Unable to pull tag and/or class from container info.")
            return [driver]

        try:
            # find the main container
            try:
                outer = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_tag}.{container_class}"))) 
            except Exception as e:
                print("Container not found or timed out.")
                return [driver]
            
            containers = []
            # look through all children to see if they have links
            try:
                children = outer.find_elements(By.XPATH, ".//*")  # all descendants
                for child in children:
                    links = child.find_elements(By.TAG_NAME, "a")
                    if links:  # if child has any <a> links
                        containers.append(child)
            except Exception as e:
                print("Error occured when looking through children nodes for links.")
            
            if containers:
                return containers
            else:
                return [outer]
        
        except Exception as e:
            print("Container not found. Using whole page.")

    # fallback: use driver itself to scrape whole page
    return [driver]


# ------------------------------------------------------------------------------------------------
#                       FUNCTIONS: PAGE LOOPING AND GENERIC LINK COLLECTOR
# ------------------------------------------------------------------------------------------------
'''
* function_identifier: get_all_links
* summary: Tries to grab all links from a single page using different methods
'''
def get_all_links(url, driver, container=None):
    links = []
    
    # Requests by Beautiful Soup will be attempted 
    if len(links) == 0:
        bs_links = get_links_bs(url, container=container)
        if bs_links:
            for link in bs_links:
                links.append(link)
            return links
    
    # Lastly, Selenium will be attempted
    if len(links) == 0:
        sel_links = get_links_sel(url, driver, container=container) # defaults to reload = True
        if sel_links:
            for link in sel_links:
                links.append(link)

    # removing duplicate links by using set() 
    links = list(set(links))
    return links

'''
* function_identifier: filter_internal_links()
* summary: Will filter out external links so that only internal links are returned
'''
def filter_internal_links(links, base_url):
    internal_links = [] # list for storing internal links

    # Get the domain of the base URL
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # Loop through each link in the list
    for link in links:
        # Parse the domain of the current link
        parsed_link = urlparse(link)
        link_domain = parsed_link.netloc

        # See if link domain matches the base domain, if it does append it to internal_links list
        if link_domain == base_domain:
            internal_links.append(link)

    return internal_links

'''
* function_identifier: get_all_pages
* summary: Go through all pages of a base_url and grab article links from all pages (if there are multiple pages) by following the typical website design ?page=num or &page=num.
'''
def get_all_pages(site_name, site_info, driver):
    all_links = set() # stores unique links
    base_url = site_info["url"]
    nav_button = site_info.get("nav_button") # if beautifulsoup fails, then selenium will look for a button
    container = site_info.get("article_container") # stores what element on a site I want to go through to find links. Do pull links from outside the element.
    try:
        bs_needed = site_info.get("bs_pagenav_flag") # bs_pagenav_flag will = False if BS page navigation is not applicable to a site and only button navigation is.
    except Exception as e:
        bs_needed = True

    print("Checking", base_url,"for links.")

    # Trying pagination with beautiful soup by searching page=num
    if bs_needed is False:
        numeric_success = False
        print("Skipping page navigation and going straight to button navigation...")
    else: 
        # Checking base_url (home page) for links
        try:
            print("Searching home page...")
            base_links = get_all_links(base_url, driver, container=container)
            base_links = filter_internal_links(base_links, base_url)
            all_links.update(base_links)
        except Exception as e:
            print("Failed to get links from base url.")

        # Try going through pages on website using ?page=num or &page=num
        page = 1
        tried_first_pages = 0
        numeric_success = False

        while True: # loop and go through all numbered pages until there are no more new links
            try:
                if '?' in base_url:
                    url = f"{base_url}&page={page}"
                    print("Grabbing links from:", url)
                else:
                    url = f"{base_url}?page={page}" 
                    print("Grabbing links from:", url)   

                page_links = get_all_links(url, driver, container=container) or [] # calling get_all_links function for link collection
                page_links = filter_internal_links(page_links, base_url)
                page_links_set = set(page_links)
                new_links = page_links_set - all_links # Comparison between page_links_set and all_links to see if there are any new links
                
                # Stop pagination if no new links are found.
                if not new_links: 
                    print("No new links found on page", page)
                    tried_first_pages += 1

                    # If tried page=1 or 2 and got nothing, stop numeric pagination. Did 1 and 2 beacusse some websites start at page=2 and some start at page =1
                    if tried_first_pages >= 2:
                        print("Numeric pagination produced no new links. Switching to button navigation. \n")
                        all_links.clear() # wipe previously collected links, because we will need selenium to load the article_container in button navigation
                        numeric_success = False
                        break
                else: # Add all new_links to the all_links list, update will remove duplicates automatically
                    all_links.update(new_links)
                    numeric_success = True
                    print("Found", len(new_links), " new links on", url)
                
                page += 1
                time.sleep(3) 

            except Exception as e:
                print("Error occured when trying to do numerical page=num page search on:", page)
                break
                

    # If going through pages fails, try finding a button and using it (Next, View More, Load More).
    if not numeric_success and nav_button:
        try:
            print("Trying button navigation for", base_url, "...")
            driver.get(base_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            print("Searching home page...")

            prev_count = 0
            click_count = 0 # track how many button clicks have been done
            last_url = driver.current_url
            no_new_count = 0 # counts how many times no new articles were returned after a button click.
            
            button_count = 0 # for testing, when I dont wanna run through a whole website. 
            one_link_count = 0 # used to count how many times only one link has been found repetively

            while True: # loop until there are no more new links or buttons
                try: 
                    
                    # reload if url changes
                    reload_needed = driver.current_url != last_url
                    page_links = get_links_sel(driver.current_url, driver, reload=reload_needed, container=container)  # reload was causing some sites to reset to home page
                    page_links = filter_internal_links(page_links, base_url)

                    # only keep new links
                    page_links_set = set(page_links)
                    new_links = page_links_set - all_links # Comparison between page_links_set and all_links to see if there are any new links

                    if new_links: 
                        all_links.update(new_links) # add the new links to all_links 
                        print("Number of new links found:", len(new_links), "\n") 
                        if len(new_links) == 1: # stop if only 1 new link appears twice in a row.
                            one_link_count +=1
                            if one_link_count >= 2:
                                print("Only one link found twice in a row. Stopping button navigation.")
                                break
                        else:
                            one_link_count = 0
                    else: 
                        print("No new links found on current page.")

                    print("Checking for a button on:", driver.current_url)
                    # look for the button
                    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, nav_button)))
                    print("Button found...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    click_count += 1
                    time.sleep(3)

                    last_url = driver.current_url

                    # if no new links after at least 2 clicks, stop
                    if len(all_links) == prev_count:
                        no_new_count += 1
                        print("No new links found.")
                    else:
                        no_new_count = 0

                    if no_new_count >= 2: 
                        print("No new links loaded after", no_new_count, "clicks. Stopping button navigation.\n")
                        break
                    
                    prev_count = len(all_links)

                    '''
                    -------------------------------------------------------------------------------------
                    # FOR TESTING PURPOSES ONLY, DONT WANNA GO THROUGH WHOLE SITE FOR ANALYSIS
                    # REMOVE WHEN ACTUALLY EVALUATING.
                    -------------------------------------------------------------------------------------
                    '''
                    button_count += 1
                    if button_count > 2:
                        print("Stopping since max amount of button presses has been reached for testing purposes.")
                        break

                except TimeoutException:
                    print("No more Next/Load More buttons found. Stopping button navigation.")
                    break
                except Exception as e:
                    print("Error during button navigation.")
        
        except Exception as e:
            print("Button navigation failed.")
    
    return list(all_links)


# ------------------------------------------------------------------------------------------------
#                                  FUNCTIONS: ALZHEIMERS FILTERING
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: find_alz_articles
* summary: Search through all collected links and find all articles relating to alzheimers.
'''
def find_alz_articles(driver, links, cookie_button=None): #using beautiful soup first, then selenium. Was originally only using selenium. 
    alz_article_links = [] # will store all link that have any desired key words (ex.alzheim)
    bs_matches = 0 # will be used to output how many matches were found using beautiful soup
    sel_matches = 0 # will be used to output how many matches were found using selenium
    print("Checking articles for Alzheimer's related content...")

    '''
    ------------------------------------------------------------------------------
    FOR TESTING PURPOSES ONLY REMOVE THIS FOR FINAL PRODUCT
    ------------------------------------------------------------------------------
    '''
    links_attempted_counter = 0
    '''
    -------------------------------------------------------------------------------
    '''

    for link in links: 
        links_attempted_counter += 1
        found = False # for tracking if Alzheimer's keyword is found.

        # First try beautifulsoup
        try:
            r = requests.get(link, timeout=10)
            time.sleep(3)
            soup = BeautifulSoup(r.text, "html.parser")
            page_text = soup.get_text().lower() # grabbing all text in lower case
            try:
                if "alzheim" in page_text:
                    alz_article_links.append(link)
                    bs_matches += 1
                    found = True
            except Exception as e:
                print("Error checking BS text for keyword(s) in link:", link)
        except Exception as e:
            print("Failed to get page with BS for:",link)

        # Last resort : try selenium  
        if not found:
            try:
                try:  
                    driver.get(link)
                    time.sleep(1)

                    #handle cookies popup if present
                    if cookie_button:
                        cookies_handler(driver, cookie_button, timeout=5)
                
                except Exception as e:
                    print("Unable to open", link, "with driver for keyword(s) analysis...")
                    print("Exception:", e)

                # Wait until body is present then grab the body and extract the text
                try:
                    body_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    body_text = body_element.text.lower()
                except TimeoutException:
                    body_text = ""
                    print("Error retrieving body for keyword(s) analysis using Selenium...")

                # getting title text
                try:
                    title_text = driver.title.lower() # gets text inside <title> to extract title
                except Exception as e:
                    print("Error retrieving title for keyword(s) analysis using Selenium...")

                #checking to see if alzheim is in the body or title text. If so, append the link.
                try:
                    if "alzheim" in body_text or "alzheim" in title_text:
                        alz_article_links.append(link)
                        sel_matches += 1
                except Exception as e:
                    print("Unable to add keyword(s) link to alz_article_links.")

            except Exception as e:
                print("Failed to get page with Selenium for:", link)
                continue

        '''
        ------------------------------------------------------------------------------
        FOR TESTING PURPOSES ONLY REMOVE THIS FOR FINAL PRODUCT
        ------------------------------------------------------------------------------
        '''
        if links_attempted_counter > 9:
            print("Stopping because max number of links for testing (", links_attempted_counter,") have been searched for keyword 'alzheim'.")
            break
        '''
        -------------------------------------------------------------------------------
        '''

    print("Links with Alzheimer content found using BeautifulSoup:", bs_matches)
    print("Links with Alzheimer content found using Selenium:", sel_matches)
    return alz_article_links




# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: PDF CREATION FUNCTIONS
# ------------------------------------------------------------------------------------------------
''' 
* function_identifier: cookies_handler
* parameters: Uses selenium driver to look for common cookie consent popups and clicks the accept button.
'''
def cookies_handler(driver, cookie_xpath, timeout=5):
    if not cookie_xpath:
        return False
    
    try:
        cookie_button = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, cookie_xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
        time.sleep(1)
        cookie_button.click()
        print("Accepted cookies.") 
        time.sleep(1) # giving page time to load without cooke consent popup
        return True
    except Exception as e:
        #print("No cookie popup found")
        return False

    
''' 
* function_identifier: add_pdf_detail
* parameters: Uses selenium driver to open the article and saves the full webpage as a pdf. Then adds the PDF path to the article details dictionary.
* returns the site specific details dictionary with a new 'PDF LINK'column.
'''
def add_pdf_detail(driver, details, folder="alz_article_pdfs", cookie_xpath=None):
    try:
        url = details.get("URL", "")

        if not url:
            print("No URL found for this article")
            details["PDF LINK"] = "No URL found"
            return details
        
        # Checking to see if a folder exists. If not create one.
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception as e:
            details["PDF LINK"] = "Folder Creation Failed"
            return details
        
        # if cookies is there accept pop up
        try:
            if cookie_xpath:
                cookies_handler(driver, cookie_xpath)
        except Exception as e:
            print("No cookie popup found. Continuing...")

        # Resizing the browser window so that it fits the entire page
        try:
            total_width = driver.execute_script("return document.documentElement.scrollWidth")
            total_height = driver.execute_script("return document.documentElement.scrollHeight")
            driver.set_window_size(total_width, total_height)
        except Exception as e:
            print("Could not resize window for", url)

        # Taking a screenshot of webpage
        try:
            screenshot_path = os.path.join(folder, "temp_screenshot.png")
            driver.save_screenshot(screenshot_path) # saves screenshot as PNG
        except Exception as e:
            details["PDF LINK"] = "Screenshot failed"
            return details
        
        # Convert screenshot to a pdf
        try: 
            image = Image.open(screenshot_path)
            if image.mode != "RGB": # Converting to RGB because PDFs require thius format
                image = image.convert("RGB")
        except Exception as e:
            details["PDF LINK"] = "Image conversion failed."
            return details
        
        # Naming file based off of the page title
        try:
            article_title = details.get("TITLE")
            # Fallback in case title was unable to be pulled from a get_details function
            if article_title == "N/A":
                # output webpage + currentmonth, day, and time as HHMMSS
                now = datetime.now()
                time_marker = now.strftime("%m%d_%H%M%S") #MMDD_HHMMSS 
                article_title = f"webpage_{time_marker}"

            # Removing characters that are not allowed in filenames
            clean_title = re.sub(r'[\\/*?:"<>|]', "", article_title[:60])
            file_path = os.path.join(folder, clean_title + ".pdf")
        except Exception as e:
            print("Problem creating filename for", url)

        # Save the image as a PDF
        try:
            image.save(file_path, "PDF", resolution = 100.0)
        except Exception as e:
            details["PDF LINK"] = "PDF save failed"
            return details
        
        # Remove temporary screenshot, since image has been saved as a PDF
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print("Unable to delete temporary screenshot.")

        try:
            # Getting the full path to where the pdf is stored
            absolute_path = os.path.abspath(file_path)
        except Exception as e:
            print("Unable to get absolute path.")
            details["PDF_LINK"] = "Path Error" 
            return details

        details["PDF LINK"] = absolute_path
        #print ("Saved PDF for:" + article_title)

    except Exception as e:
        print("Failed to create PDF for" + details.get("URL"))
        details["PDF LINK"] = "PDF generation failed"

    #print("PDF has been created.")
    return details


# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: SITE DETAIL PULLING FUNCTIONS
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: get_acadia_pharm_inc_details
* parameters: this is designed to scrape the details from articles on https://acadia.com/en-us/media/news-releases that were found to have the keyword "alzheim."
* note: no authors listed on site. Details were successfully pulled using BS. No sel needed.
'''
def get_acadia_pharm_inc_details(driver, link, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "PDF LINK": "", "BODY": ""}   
    
    # try using BS
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "ACADIA Pharmaceuticals Inc."
        
        # grabbing title
        try:
            title_element = soup.find("h1", attrs={"data-astro-cid-u4qoyrkz": True})
            if title_element: #continues if title_element is not empty
                details["TITLE"] = title_element.text.strip() #strip gives a clean output
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find("span", class_="text", attrs={"data-astro-cid-ijeeojtv": True})
            if date_element: # continues if date_element is not empty
                details["PUBLISH DATE"] = date_element.text.strip()
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"


        # grabbing author(s), there are no authors on this site.
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.select("article", class_="gutter-narrow", attrs={"data-astro-cid-zofqh5c7": True})
            if body_container:
                all_text = []
                for block in body_container: # keeping body paragraph text
                    paragraphs = block.find_all("p")
                    for p in paragraphs:
                        txt = p.get_text(strip=True)
                        if txt:
                            all_text.append(txt)
                details["BODY"] = "\n".join(all_text)
        except Exception as e:
            details["BODY"] = "N/A"
        
    except Exception as e:
        print("Beautifulsoup extraction not fully successful.") 

    # storing pdf version of site
    details = add_pdf_detail(driver, details, cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_aliada_details
* parameters: this is designed to scrape the details from articles on https://investors.alnylam.com/press-releases that were found to have the keyword "alzheim."
* note: No authors. BS Found title, publish date, and body.
'''
def get_aliada_details(driver, link, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "PDF LINK": "", "BODY": ""}

    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Aliada Therapuetics"
        
        # grabbing title
        try:
            title_element = soup.find("h2", class_=["press-d-title", "mt-0"])
            if title_element: #continues if title_element is not empty
                details["TITLE"] = title_element.text.strip() #strip gives a clean output
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find("p", class_="event-date")
            if date_element: # continues if date_element is not empty
                details["PUBLISH DATE"] = date_element.text.strip()
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"


        # grabbing author(s), there are no authors on this site.
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.select("div.col-sm-9")
            if body_container:
                all_text = []
                for block in body_container: # keeping body paragraph text
                    paragraphs = block.find_all("p")
                    for p in paragraphs:
                        txt = p.get_text(strip=True)
                        if txt:
                            all_text.append(txt)
                details["BODY"] = "\n".join(all_text)
        except Exception as e:
            details["BODY"] = "N/A"
        
    except Exception as e:
        print("Beautifulsoup extraction not fully successful.") 

    # storing pdf version of site
    details = add_pdf_detail(driver, details, cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_adel_details
* parameters: this is designed to scrape the details from articles on https://www.alzinova.com/investors/press-releases/ that were found to have the keyword "alzheim."
* note: No details were found using BS, removed that section. ADEL does not have publishers or authors on articles.
'''
def get_adel_details(driver, link, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "PDF LINK": "", "BODY": ""}

    # Using selenium only because beautifulsoup returned no details.
    try:
        driver.get(link)
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # waiting for elements to load

        # Site has no publishers
        details["PUBLISHER"] = "Alzheimer's Disease Expert Lab (ADEL), Inc."
        # Site has no authors
        details["AUTHOR(S)"] = "N/A"

        # grabbing title
        try:
            title_element = driver.find_element(By.CLASS_NAME, "mfn-title")
            details["TITLE"] = title_element.text.strip()
        except:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = driver.find_element(By.CLASS_NAME, "mfn-date")
            details["PUBLISH DATE"] = date_element.text.strip()
        except:
            details["PUBLISH DATE"] = "N/A"
            
        # grabbing body
        try:
            body_container = driver.find_element(By.CLASS_NAME, "mfn-body")
            paragraphs = body_container.find_elements(By.TAG_NAME, "p")
            details["BODY"] = "\n".join([p.text.strip() for p in paragraphs])
        except:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Selenium extraction failed for ADEL:", link)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_alzheon_details
* parameters: this is designed to scrape the details from articles on https://asceneuron.com/news-events/ that were found to have the keyword "alzheim."
* note: BS always found title, publish date, and author(s) if they existed. Body was found using Selenium and BS. No publishers listed.
'''
def get_alzheon_details(driver, link, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "PDF LINK": "", "BODY": ""}

    # try using beautifulsoup first
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Alzheon Inc."
        
        # grabbing title
        try:
            title_element = soup.find("h1", class_="entry-title")
            if title_element: #continues if title_element is not empty
                details["TITLE"] = title_element.text.strip() #strip gives a clean output
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find("span", class_="published")
            if date_element: # continues if date_element is not empty
                details["PUBLISH DATE"] = date_element.text.strip()
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # grabbing author(s) 
        try:
            author_element = soup.find("span", class_="author vcard")
            if author_element: # continues if author_element is not empty
                details["AUTHOR(S)"] = author_element.text.strip()
            else:
                details["AUTHOR(S)"] = "N/A"
        except Exception as e:
            details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.select("div.et_pb_text_inner")
            if body_container:
                all_text = []
                for block in body_container: # keeping body paragraph text
                    paragraphs = block.find_all("p")
                    for p in paragraphs:
                        txt = p.get_text(strip=True)
                        if txt:
                            all_text.append(txt)
                details["BODY"] = "\n".join(all_text)
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Beautifulsoup extraction not fully successful. Switching to Selenium for further analysis.")

    # using selenium for body if beautifulsoup fails on body extraction.
    if not details["BODY"]:
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # waiting for elements to load

            # grabbing body
            if not details["BODY"]:
                try:
                    body_blocks = driver.find_elements(By.CSS_SELECTOR, "div.et_pb_text_inner")
                    all_text = []
                    for block in body_blocks:
                        paragraphs = block.find_elements(By.TAG_NAME, "p")
                        for p in paragraphs:
                            txt = p.text.strip()
                            if txt:
                                all_text.append(txt)
                    details["BODY"] = "\n".join(all_text)
                except:
                    details["BODY"] = "N/A"

        except Exception as e:
            print("Unable to locate all metadata for Alzheon Inc:", link)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_alz_research_uk_details
* parameters: this is designed to scrape the details from articles on https://www.alzheimersresearchuk.org/about-us/latest/news/ that were found to have the keyword "alzheim."
* note: Nothing was successfully pulled using BS. Used Selenium only.
'''
def get_alz_research_uk_details(driver, link, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "PDF LINK": "", "BODY": ""}

    # using selenium since BeautifulSoup returned nothing
    try:
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # waiting for elements to load
        except Exception as e:
            print("Selenium driver failed to get Alzheimer's Research UK link:", link)

        # grabbing publisher
        details["PUBLISHER"] = "Alzheimer's Research UK"
        
        # grabbing title
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, "h1.fl-heading")
            details["TITLE"] = title_element.text.strip() # strip gives a clean output
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing author and publish date
        try:
            date_elements = driver.find_elements(By.CSS_SELECTOR, "div.fl-rich-text")
            author = "N/A"
            publish_date = "N/A"

            for date_element in date_elements:
                try:
                    p_tag = date_element.find_element(By.TAG_NAME, "p")
                    if p_tag: # getting text inside <p> tag, ex. "By Alzheimer's Research UK | Friday 25 July 2025"
                        text = p_tag.text.strip()
                        if "|" in text or "by " in text.lower(): # splitting text into two parts. Before and after "\"
                            if "|" in text:
                                parts = text.split("|", 1) # making usre it only splits once
                                author_part = parts[0].strip()
                                date_part = parts[1].strip()

                                if author_part.lower().startswith("by "): # removing 'by' from before author name
                                    author = author_part[3:].strip()
                                else:
                                    author = author_part

                                publish_date = date_part
                            else:
                                author = "N/A"
                                publish_date = text.strip()
                            break
                except Exception as e:
                    continue

            details["AUTHOR(S)"] = author
            details["PUBLISH DATE"] = publish_date

        except Exception as e:
            print("Unable to extract author or publish date using Selenium on", link)
            details["AUTHOR(S)"] = "N/A"
            details["PUBLISH DATE"] = "N/A"

        # grabbing body
        try: 
            body_container = driver.find_elements(By.CSS_SELECTOR, "div.fl-module-content.fl-node-content")
            if body_container:
                all_text = []
                for block in body_container: # keeping body paragraph text
                    paragraphs = block.find_elements(By.TAG_NAME, "p")
                    for p in paragraphs:
                        txt = p.text.strip()
                        if txt:
                            all_text.append(txt)
                details["BODY"] = "\n".join(all_text)
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Unable to locate all metadata for Alzheimer's Research UK:", link)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, cookie_xpath=cookie_button)

    return details


# ==========================================================================================
#                                 MAIN FUNCTION
# ==========================================================================================
def main():
    total_alz_links = 0
    total_links = 0

    site_details = {
        # working
        #"acadia_pharm_inc_url": { # ACADIA Pharmaceutical Inc.
            #"url": "https://acadia.com/en-us/media/news-releases",
            #"article_container": {"tag": "div", "class": "results"},
            #"nav_button": "//label[contains(@class, 'show-all') and text()='Show All']",
            #"cookie_button": "//button[contains(@id, 'onetrust-accept-btn-handler')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_acadia_pharm_inc_details
            #}, 
        # working
        #"aliada_th_url": { # Aliada Therapuetics
            #"url": "https://investors.alnylam.com/press-releases",
            #"article_container": {"tag": "div", "class": "financial-info-table"},
            #"nav_button": "//a[contains(@rel, 'next')]",
            #"cookie_button": "//button[contains(@id, 'onetrust-accept-btn-handler')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_aliada_details
            #},
        # working
        #"adel_inc_url": { # Alzheimer's Disease Expert Lab (ADEL), Inc.
            #"url": "https://www.alzinova.com/investors/press-releases/",
            #"article_container": {"tag": "div", "class": "mfn-content"},
            #"nav_button": "//div[contains(@class, 'mfn-pagination-link') and contains(@class, 'mfn-next')]",
            #"cookie_button": "//button[contains(@class, 'coi-banner__accept')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_adel_details
            #},
        # working
        "alzheon_inc_url": { # Alzheon Inc
            "url": "https://asceneuron.com/news-events/",
            "article_container": {"tag": "div", "class": "df-cpts-inner-wrap"},
            "nav_button": "//a[contains(@class, 'df-cptfilter-load-more')]",
            "bs_pagenav_flag": False,
            "detail_getter": get_alzheon_details
            }
        # working
        # found no alz_articles with BS, only sel.
        #"alz_research_uk_url": { # Alzheimer's Research UK 
            #"url": "https://www.alzheimersresearchuk.org/about-us/latest/news/",
            #"article_container": {"tag": "div", "class": "pp-content-posts"},
            #"nav_button": "//span[contains(@class, 'pp-grid-loader-text') and text()='Load More']",
            #"cookie_button": "//button[contains(@id, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_alz_research_uk_details
            #},
    }
    
    
    all_article_details = []

    for site_name, site_info in site_details.items():
        base_url = site_info["url"]
        print("\n-------------------------------------------------------------------------------------------------------------")
        
        print("Setting up driver....")
        driver = setup_driver()

        try:
            # Get all Pages
            try:
                links = get_all_pages(site_name, site_info, driver)
                print("\nTotal number of links found on", base_url, ":", len(links))
                total_links += len(links)
            except Exception as e:
                continue
            
            # Filter for Alzheimers related content
            try:
                alz_links = find_alz_articles(driver, links, cookie_button=site_info.get("cookie_button"))
                total_alz_links += len(alz_links)
                print("\nTotal number of Alzheimer's related links on this site: ", len(alz_links))
            except Exception as e:
                continue

            # extracting article details
            for link in alz_links:
                article_data = site_details[site_name]["detail_getter"](driver, link, cookie_button=site_info.get("cookie_button"))
                if article_data:
                    all_article_details.append(article_data)
        finally:
            driver.quit()

    print("\n-------------------------------------------------------------------------------------------------------------")
    print(total_links, "new article links found across all sponsor sites.")
    print(total_alz_links, "new alzheimer links found across all sponsor sites.\n")
    
    # Save results to CSV
    try: 
        df = pd.DataFrame(all_article_details)
        df.to_csv("alz_articles.csv", index=False)
        print("Saved results to alz_articles.csv")
    except Exception as e:
        print("Failed to save CSV file.")
    print("---------------------------------------------------------------------------------------------------------------")

# ==========================================================================================

if __name__ == "__main__":
    main()
