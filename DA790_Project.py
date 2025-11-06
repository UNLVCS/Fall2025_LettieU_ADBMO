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


# ==========================================================================================
#                           FUNCTIONS : LINK CONTAINER FUNCTIONS
# ==========================================================================================
'''
* function_identifier: get_bs_container
* summary: Returns the BeautifulSoup element(s) to search in for links. Prevents the whole page from being scraped if a container is found.
* parameters: 
    - soup: BeautifulSoup that has the whole page.
    - container: optional dictionary that has the keys 'tag' and 'class' specifying the container to focus on.
* return: if container is found, return the container. Else, return the whole soup.
'''
def get_bs_container(soup, container=None):
    try:
        # if container is provided, try to find it
        if container:
            try:
                container_tag = container.get("tag")
                container_class = container.get("class")
            except Exception as e:
                print("Unable to pull tag and/or class from container info.")
                return [soup]

            # Try to find the main container in the soup
            try:
                outer = soup.find(container_tag, class_=container_class)
            except Exception as e:
                print("Container not found.")
                return [soup]

            if outer:
                containers = []
                try:
                    # loop through all child elements in the container
                    children = outer.find_all(True)  # True finds all tags
                    for child in children:
                        if child.find("a", href=True): # only include children that contain links
                            containers.append(child)
                except Exception as e:
                    print("Error occured when looking through children nodes for links.")

                # return children with links if found, otherwise return the main container
                if containers:  
                    return containers
                else:  
                    return [outer]
                
            else:
                print("Container not found. Scraping whole page.")
                return [soup]

        # if no container is provided, return the full soup     
        else: 
            return [soup]

    except Exception as e:
        print("Unexpected error occured in get_bs_container")
        return [soup]


'''
* function_identifier: get_sel_container
* summary: Returns the Selenium element(s) to search for links. 
If container is found it returns the container. If not, it returns none and get_links_sel will return all <a> elements that start with http.
* parameters:
    - driver: selenium webdriver being used for the browser session
    - container: optional dictionary that has the keys 'tag' and 'class' specifying the container to focus on.
* return: if container is found, return the container or the child element that contains links. Else, return the driver so that a whole page search is done.
'''
def get_sel_container(driver, container=None):
    # if container is provided, try to find it
    if container:
        try:
            container_tag = container.get("tag")
            container_class = container.get("class")
        except Exception as e:
            print("Unable to pull tag and/or class from container info.")
            return [driver]

        try:
            # attempt to find the main container using a CSS selector
            try:
                outer = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_tag}.{container_class}"))) 
            except Exception as e:
                print("Container not found or timed out.")
                return [driver]
            
            containers = []
            
            try:
                # look through all children to see if they have links
                children = outer.find_elements(By.XPATH, ".//*")
                for child in children:
                    # only include children that contain <a> links
                    links = child.find_elements(By.TAG_NAME, "a")
                    if links:  
                        containers.append(child)
            except Exception as e:
                print("Error occured when looking through children nodes for links.")
            
            # return children with links if found, otherwise return the main container
            if containers:
                return containers
            else:
                return [outer]
        
        except Exception as e:
            print("Container not found. Using whole page.")

    # fallback: use driver itself to scrape whole page
    return [driver]


# ==========================================================================================
#                          FUNCTIONS : BS AND SEL LINK PULLER FUNCTIONS
# ==========================================================================================
'''
* function_identifier: get_links_bs
* summary: Grabbing all links from a single page using requests by beautiful soup.
* parameters:
    - url: web page url to scrape links from
    - container: optional dictionary that has the keys 'tag' and 'class' specifying a container to focus on. If None, whole page is searched.
* return: list of unique links
'''
def get_links_bs(url, container=None):
    links = []
    try:
        r = requests.get(url, timeout=10)
        time.sleep(3)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # get list of containers to search for links
        containers = get_bs_container(soup, container)

        # loop through each container and find all <a> tags with href attributes
        for c in containers:
            for a in c.find_all("a", href=True):
                href = a["href"]  
                # only keep full URLs that start with "http"
                if href.startswith("http"): 
                    # skip pagination links to avoid infinite loops 
                    if "page=" in href or "/page/" in href: 
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
* summary: Grabbing all links from a single page using selenium. Fallback if get_links_bs() fails.
* parameters:
    - url: web page url to scrape links from
    - driver: selenium webdriver being used for the browser session
    - reload: boolean indicating whether to reload the page
    - container: optional dictionary that has the keys 'tag' and 'class' specifying a container to focus on. If None, whole page is searched.
* return: list of unique links
'''
def get_links_sel(url, driver, reload=True, container=None): 
    if reload:
        try:
            # load page and wait until body is present  
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except TimeoutException:
            print("Timeout loading page:", url, "while running get_links_sel.")

    links = []

    # get the containers to search for links
    containers = get_sel_container(driver, container)
    
    # loop through each container and find all <a> elements
    for c in containers:
        link_elements = c.find_elements(By.TAG_NAME, "a")
        for element in link_elements:
            href = element.get_attribute("href")
            # only keep full URLs that start with "http"
            if href and href.startswith("http"):
                # skip pagination links
                if "page=" in href or "/page/" in href: # do not want to add pagination pages to our list of links
                    continue
                links.append(href)
    
    # remove duplicates before returning
    unique_links = list(set(links))
    print("Found", len(unique_links), "links overall on", url, "when using Selenium.")
    return unique_links


# ==========================================================================================
#                          FUNCTIONS : PAGE LOOPING AND GENERIC LINK COLLECTOR
# ==========================================================================================
'''
* function_identifier: get_all_links
* summary: Tries to grab all links from a single page using different methods
* parameters: 
    - url: web page url to scrape links from
    - driver: selenium webdriver being used if the beautifulsoup method fails.
    - container: optional dictionary that has the keys 'tag' and 'class' specifying a container to focus on. If None, whole page is searched.
* return: list of unique links
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
    
    # Fallback, Selenium will be attempted because BS found nothing
    if len(links) == 0:
        sel_links = get_links_sel(url, driver, container=container) # defaults to reload=True
        if sel_links:
            for link in sel_links:
                links.append(link)

    # removing duplicate links before returning 
    links = list(set(links))
    return links

'''
* function_identifier: filter_internal_links()
* summary: Will filter out external links so that only internal links that belong to the same domain are returned.
* parameters:
    - links: list of URLs to filter
    - base_url: the base_url whose domain is used to identify internal links
* return: a list of URLs that are internal to the base URLs domain.
'''
def filter_internal_links(links, base_url):
    internal_links = [] # list for storing internal links

    # Get the domain of the base URL
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # Loop through each link in the list and check if it belongs to the same domain
    for link in links:
        parsed_link = urlparse(link)
        link_domain = parsed_link.netloc

        # if link domain matches the base domain, append it to internal_links list
        if link_domain == base_domain:
            internal_links.append(link)

    return internal_links

'''
* function_identifier: get_all_pages
* summary: Go through all pages of a base_url and grab article links from all page(s) by using page or button navigation.
* parameters:
    - site_name: name of the website
    - site_info: dictionary containing site-specefic information
    - driver: selenium webdriver used for button based page navigation
* return: a set of unique internal article links found across all pages
'''
def get_all_pages(site_name, site_info, driver):
    all_links = set() # stores unique links
    base_url = site_info["url"]
    nav_button = site_info.get("nav_button") # for selenium based button navigation
    container = site_info.get("article_container") # container for articles
    
    # determines if numeric pagination using bs is applicable.
    try:
        bs_needed = site_info.get("bs_pagenav_flag")
    except Exception as e:
        bs_needed = True

    print("Checking", base_url,"for links.")

    # Skip numeric page navigation if bs_needed is false
    if bs_needed is False:
        numeric_success = False
        print("Skipping numerical page navigation and going straight to button navigation...")
    else: 
        # Checking base_url (home page) for links
        try:
            print("Searching home page...")
            base_links = get_all_links(base_url, driver, container=container)
            base_links = filter_internal_links(base_links, base_url)
            all_links.update(base_links)
        except Exception as e:
            print("Failed to get links from base url.")

        # Try numeric page navigation (?page=num or &page=num)
        page = 0
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

                # get all links on page
                page_links = get_all_links(url, driver, container=container) or [] # calling get_all_links function for link collection
                page_links = filter_internal_links(page_links, base_url)
                page_links_set = set(page_links)
                
                # comparison to see if new_links have been found
                new_links = page_links_set - all_links 
                
                if not new_links: 
                    print("No new links found on page", page)
                    tried_first_pages += 1

                    # If tried page=1 or 2 and got nothing, stop numeric pagination. Did 1 and 2 because some websites start at page=2 and some start at page =1
                    if tried_first_pages >= 2:
                        print("Numeric pagination produced no new links. Switching to button navigation. \n")
                        all_links.clear() # clear links before attempting selenium button based navigation
                        numeric_success = False
                        break
                else:
                    all_links.update(new_links)
                    numeric_success = True
                    print("Found", len(new_links), " new links on", url)
                
                page += 1
                time.sleep(3) 

            except Exception as e:
                print("Error occured when trying to do numerical page=num page search on:", page)
                break
                
    # If numerical page navigation fails, try doing button navigation with selenium
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
            one_link_count = 0 # counts how many repetitive times only one link has been found.
            button_count = 0 # for testing, when I dont wanna run through a whole website. 
            
            while True: # loop until there are no more new links or buttons
                try: 
                    # reload if url changes (reload was causing some sites to reset to home page)
                    reload_needed = driver.current_url != last_url
                    page_links = get_links_sel(driver.current_url, driver, reload=reload_needed, container=container)  
                    page_links = filter_internal_links(page_links, base_url)
                    # only keep new links
                    page_links_set = set(page_links)
                    new_links = page_links_set - all_links 

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

                    # find and click the pagination button
                    print("Checking for a button on:", driver.current_url)
                    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, nav_button)))
                    print("Button found...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", button)
                    click_count += 1
                    time.sleep(3)

                    last_url = driver.current_url

                    # stop if no new links after 2 clicks
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
                    if button_count > 1:
                        print("Stopping since max amount of button presses has been reached for testing purposes.")
                        break

                except TimeoutException:
                    print("No more Next/Load More buttons found. Stopping button navigation.")
                    break
                except Exception as e:
                    print("Error during button navigation.")
        
        except Exception as e:
            print("Button navigation failed or Site has no buttons to be pressed.")
    
    if not all_links:
        print("Pagination is not needed for this site. Scraping links off home page...")
        try:
            home_links = get_all_links(base_url, driver, container=container)
            home_links = filter_internal_links(home_links, base_url)
            all_links.update(home_links)
            print("Found", len(home_links), "links on home page.")
        except Exception as e:
            print("Failed to get links from home page as fallback:", e)

    return list(all_links)


# ==========================================================================================
#                          FUNCTIONS : HTML SAVING AND ALZHEIMERS FILTERING
# ==========================================================================================
'''
* function_identifier: save_html
* summary: saves an HTML for a single URL (site_folder/<file_number>.html)
* parameters:
    - driver: selenium webdriver (used if BS fails)
    - url: the web page URL to save
    - site_folder: folder where HTML files will be saved
    - file_number: number used to create the HTML file name (ex. '1.html')
    - cookie_button: optional path to cookies accept button
    - url_map: optional dictionary to map file_number to URL for reference
    - html_sel_save: boolean that is True if BS needs to be skipped.
* returns: file path of saved html, or None if failed.
'''
def save_html(driver, url, site_folder, file_number, cookie_button=None, url_map=None, html_sel_save=None):
    # creating folder if it does not already exist
    if not os.path.exists(site_folder):
        os.makedirs(site_folder)

    # defining the HTML file path
    html_filename = str(file_number) + ".html"
    html_path = os.path.join(site_folder, html_filename)

    # tells code whether to use BS or Sel
    use_requests = not bool(html_sel_save)

    if use_requests:    
        # try using BeautifulSoup to create HTML
        try: 
            r = requests.get(url, timeout=10)
            time.sleep(2)
            soup = BeautifulSoup(r.text, "html.parser")
            html_content = soup.prettify()

            # save HTML
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # updating url_map so that url can stay associated with .html
            if url_map is not None:
                url_map[file_number] = url

            return html_path
        except Exception as e:
            pass

    # fallback on selenium if bs fails
    try:
        driver.get(url)
        time.sleep(2)

        if cookie_button:
            try:
                cookies_handler(driver, cookie_button)
            except:
                pass
        
        # waiting for body element to load
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
        except Exception as e:
            return None
            print("Body element not detected for", url)
        
        # scrolling page because some JS heavy sites require scrolling to load all elements
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_height = 0
        while current_height < scroll_height:
            driver.execute_script("window.scrollTo(0, " + str(current_height) + ");")
            time.sleep(1)
            current_height += 600
            scroll_height = driver.execute_script("return document.body.scrollHeight")
        time.sleep(1)

        # Get fully rendered DOM
        html_content = driver.execute_script("return document.documentElement.outerHTML;")

        # save HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # updating url_map so that url can stay associated with .html
        if url_map is not None:
            url_map[file_number] = url
        
        return html_path

    except Exception as e:
        print("Beautiful Soup and Selenium failed when trying to make a .html for:", url)
        return None      

    
'''
* function_identifier: find_alz_articles
* summary: Check all saved HTML files in a site folder for keyword(s). Delete file and remove from dictionary if keyword not found.
* parameters: 
    - site_folder: folder containing saved HTML files.
    - url_map: dictionary mapping file_number to URL for all saved HTML files.
* returns: dictionary of filtered articles {file_number:url} containing the keyword(s)
* note: starting html saves here because this is the first time article links are opened and read. 
'''
def find_alz_articles(site_folder, url_map): 
    alz_html_url = {}
    
    if not os.path.exists(site_folder):
        print("Site folder does not exist:", site_folder)
        return {}
    
    # loop through all HTML files in the folder
    for html_filename in os.listdir(site_folder):
        if not html_filename.endswith(".html"):
            continue

        file_number = int(html_filename.replace(".html", ""))
        html_path = os.path.join(site_folder, html_filename)

        try:
            # read HTML file and extract text
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            page_text = soup.get_text().lower()

            # keep file if keyword(s) found; otherwise delete
            if "alzheim" in page_text:
                alz_html_url[file_number] = url_map.get(file_number, "URL not found")
            else:
                os.remove(html_path)
                if file_number in url_map:
                    del url_map[file_number] 

        except Exception as e:
            print("Error occured when searching HTML for keyword:", html_path)
            # try to remove file and url_map entry if an error occured when searching html
            try:
                if os.path.exists(html_path):
                    os.remove(html_path)
                if file_number in url_map:
                    del url_map[file_number]
            except Exception as e:
                pass
            continue

    return alz_html_url
                                       

# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: PDF CREATION FUNCTIONS
# ------------------------------------------------------------------------------------------------
''' 
* function_identifier: cookies_handler
* summary: Uses selenium driver to look for common cookie consent popups and clicks the accept button.
* parameters: 
    - driver: selenium webdriver
    - cookie_xpath: XPath for the cookie accept button
* return: true if cookie button was found and clicked. Otherwise, false.
'''
def cookies_handler(driver, cookie_xpath):
    # if no xpath, do nothing
    if not cookie_xpath:
        return False
    
    try:
        # wait for cookies button to be clickable
        cookie_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, cookie_xpath)))
        # scroll button into view and click
        driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
        time.sleep(1)
        cookie_button.click()
        print("Accepted cookies.") 
        time.sleep(1) # giving page time to load without cookie consent popup
        return True
    except Exception as e:
        #print("No cookie popup found")
        return False

    
''' 
* function_identifier: add_pdf_detail
* summary: Uses selenium driver to open the article and saves the full webpage as a pdf. Then adds the PDF path to the article details dictionary.
* parameters: 
    - driver: selenium webdriver
    - details: dictionary containing article details
    - folder: folder to save PDF files to
    - cookie_xpath: optional xpath for a cookie consent button
* return: the site specific details dictionary with a new 'PDF LINK' column.
'''
def add_pdf_detail(driver, details, site_name=None, base_folder="saved_sites", cookie_xpath=None):
    try:
        url = details.get("URL", "")
        if not url:
            print("No URL found for this article")
            details["PDF PATH"] = "No URL found"
            return details
        
        # navigating to the articale page using Selenium
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
        except Exception as e:
            details["PDF PATH"] = "Failed to Load Page"
            return details
        
        # checking to see if a folder exists. If not create one.
        try:
            if site_name:
                pdf_folder = os.path.join(base_folder, site_name + "_pdfs")
            else:
                pdf_folder = os.path.join(base_folder, "pdfs")
            os.makedirs(pdf_folder, exist_ok=True)
        except Exception as e:
            details["PDF PATH"] = "Folder Creation Failed"
            return details
        
        # accept cookie popup if XPath is provided
        try:
            if cookie_xpath:
                cookies_handler(driver, cookie_xpath)
        except Exception as e:
            print("No cookie popup found. Continuing...")

        # resizing the browser window so that it fits the entire page
        try:
            total_width = driver.execute_script("return document.documentElement.scrollWidth")
            total_height = driver.execute_script("return document.documentElement.scrollHeight")
            driver.set_window_size(total_width, total_height)
        except Exception as e:
            print("Could not resize window for", url)

        # taking a screenshot of webpage
        try:
            screenshot_path = os.path.join(pdf_folder, "temp_screenshot.png")
            driver.save_screenshot(screenshot_path) # saves screenshot as PNG
        except Exception as e:
            details["PDF PATH"] = "Screenshot failed"
            return details
        
        # convert screenshot to RGB if needed
        try: 
            image = Image.open(screenshot_path)
            if image.mode != "RGB": # Converting to RGB because PDFs require this format
                image = image.convert("RGB")
        except Exception as e:
            details["PDF PATH"] = "Image conversion failed."
            return details
        
        # creating a unique file name whether it be based of article title or timestamp
        try:
            article_title = details.get("TITLE")
            # fallback in case title was unable to be pulled from a get_details function
            if article_title == "N/A":
                now = datetime.now()
                time_marker = now.strftime("%m%d_%H%M%S") #MMDD_HHMMSS 
                article_title = "webpage_"+time_marker

            # removing characters that are not allowed in filenames
            clean_title = re.sub(r'[\\/*?:"<>|]', "", article_title[:60])
            pdf_path = os.path.join(pdf_folder, clean_title + ".pdf")
        except Exception as e:
            print("Problem creating filename for", url)

        # saving image as PDF
        try:
            image.save(pdf_path, "PDF", resolution = 100.0)
        except Exception as e:
            details["PDF PATH"] = "PDF save failed"
            return details
        
        # remove temporary screenshot, since image has been saved as a PDF
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print("Unable to delete temporary screenshot.")

        details["PDF PATH"] = pdf_path
        #print ("Saved PDF for:" + article_title)

    except Exception as e:
        print("Failed to create PDF for" + details.get("URL"))
        details["PDF PATH"] = "PDF generation failed"

    #print("PDF has been created.")
    return details


# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: SITE DETAIL PULLING FUNCTIONS
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: get_acadia_pharm_inc_details
* parameters: this is designed to scrape the details from articles on https://acadia.com/en-us/media/news-releases that were found to have the keyword "alzheim."
* note: no authors listed on site. 
'''
def get_acadia_pharm_inc_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    # try using BS
    try:
        # Open the save HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

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
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url) 

    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "acadia_pharm_inc", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_aliada_details
* parameters: this is designed to scrape the details from articles on https://investors.alnylam.com/press-releases that were found to have the keyword "alzheim."
* note: No authors. BS Found title, publish date, and body.
'''
def get_aliada_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the save HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Aliada Therapuetics"
        
        # grabbing title
        try:
            title_element = soup.find("h2", class_=["press-d-title", "mt-0"])
            if title_element: # continues if title_element is not empty
                details["TITLE"] = title_element.text.strip() # strip gives a clean output
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
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url) 

    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "aliada_ther", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_adel_details
* parameters: this is designed to scrape the details from articles on https://www.alzinova.com/investors/press-releases/ that were found to have the keyword "alzheim."
* note: ADEL does not have publishers or authors on articles.
'''
def get_adel_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the save HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # Site has no publishers
        details["PUBLISHER"] = "Alzheimer's Disease Expert Lab (ADEL), Inc."

        # grabbing title
        try:
            title_element = soup.find(class_="mfn-title")
            if title_element: 
                details["TITLE"] = title_element.get_text(strip=True) # strip gives a clean output
            else:
                details["TITLE"] = "N/A"
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find(class_="mfn-date")
            if date_element: 
                details["PUBLISH DATE"] = date_element.get_text(strip=True)
            else:
                details["PUBLISH DATE"] = "N/A"
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # Site has no authors
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.find(class_="mfn-body")
            if body_container:
                paragraphs = body_container.find_all("p")
                all_text = []
                for p in paragraphs:
                    txt = p.get_text(strip=True)
                    if txt:
                        all_text.append(txt)
                details["BODY"] = "\n".join(all_text)
            else:
                details["BODY"] = "N/A"
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "adel_inc", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_alzheon_details
* parameters: this is designed to scrape the details from articles on https://asceneuron.com/news-events/ that were found to have the keyword "alzheim."
* note: BS always finds title, publish date, and author(s) if they existed. No publishers listed.
'''
def get_alzheon_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the save HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

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
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)

    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "alzheon_inc", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_alz_research_uk_details
* parameters: this is designed to scrape the details from articles on https://www.alzheimersresearchuk.org/about-us/latest/news/ that were found to have the keyword "alzheim."
'''
def get_alz_research_uk_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the saved HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Alzheimer's Research UK"
        
        # grabbing title
        try:
            title_element = soup.select_one("h1.fl-heading")
            if title_element:
                details["TITLE"] = title_element.text.strip() # strip gives a clean output
            else:
                details["TITLE"] = "N/A"
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing author and publish date
        try:
            date_elements = soup.select("div.fl-rich-text")
            author = "N/A"
            publish_date = "N/A"

            for date_element in date_elements:
                try:
                    p_tag = date_element.find("p")
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
            print("Unable to extract author or publish date using Selenium on", url)
            details["AUTHOR(S)"] = "N/A"
            details["PUBLISH DATE"] = "N/A"

        # grabbing body
        try: 
            body_container = soup.select("div.fl-module-content.fl-node-content")
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
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "alz_reasearch_uk", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_cognit_ther_details
* parameters: this is designed to scrape the details from articles on https://ir.cogrx.com/press-releases/ that were found to have the keyword "alzheim."
* notes: this site has no authors.
'''
def get_cognit_ther_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the saved HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Cognition Therapeutics"
        
        # grabbing title
        try:
            title_element = soup.find("h1", class_="elementor-heading-title elementor-size-default")
            if title_element:
                details["TITLE"] = title_element.get_text(strip=True)
            else:
                details["TITLE"] = "N/A"
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find("div", class_="pr-date-globe")
            if date_element: # continues if date_element is not empty
                details["PUBLISH DATE"] = date_element.get_text(strip=True)
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # grabbing author(s) 
        details["AUTHOR(S)"] = "N/A"

        # grabbing body (there are multiple instances of elementor-widget-container, need to find the one storing body content.)
        try:
            containers = soup.find_all("div", class_="elementor-widget-container")
            for container in containers:
                if container.find("div", class_="pr-date-globe"):
                    body_container = container
                    break

            if body_container:
                paragraphs = body_container.find_all("p")  # grab all <p> tags in the container
                all_text = []
                for p in paragraphs:
                    txt = p.get_text(strip=True)
                    if txt:  # skip empty paragraphs
                        all_text.append(txt)
                details["BODY"] = "\n".join(all_text) if all_text else "N/A"
            else:
                details["BODY"] = "N/A"
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "congition_ther", cookie_xpath=cookie_button)

    return details


'''
* function_identifier: get_gemvax_kael_details
* parameters: this is designed to scrape the details from articles on https://gemvax.com/bbs/board.php?bo_table=releases_en that were found to have the keyword "alzheim."
* notes: this site does not require any pagination and has no authors
'''
def get_gemvax_kael_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the saved HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "GemVax & Kael"

        # grabbing title
        try:
            title_element = soup.find("span", class_="bo_v_tit")
            if title_element:
                details["TITLE"] = title_element.get_text(strip=True)
            else:
                details["TITLE"] = "N/A"
        except Exception as e:
            details["TITLE"] = "N/A"
        
        # grabbing publish date
        try:
            date_element = soup.find("strong", class_="if_date")
            if date_element: # continues if date_element is not empty
                full_text = date_element.get_text(strip=True)
                details["PUBLISH DATE"] = full_text.replace("작성일", "").strip()
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # grabbing author(s) 
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.find("div", class_="r-sub-con")
            all_text = []

            if body_container:
                for p in body_container.find_all("p"):  # find all <p> recursively
                    span = p.find("span", lang="EN-US")
                    if span and span.get_text(strip=True):
                        all_text.append(span.get_text(strip=True))
                    elif p.get_text(strip=True):  # fallback to any <p> text if span not found
                        all_text.append(p.get_text(strip=True))

            details["BODY"] = "\n".join(all_text) if all_text else "N/A"
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "gemvax_kael", cookie_xpath=cookie_button)

    return details


# ==========================================================================================
#                                 MAIN FUNCTION
# ==========================================================================================
def main():
    total_alz_links = 0
    total_links = 0
    base_folder = "saved_sites" # folder that will store all htmls
    os.makedirs(base_folder, exist_ok=True) # create folder if it does not exist
    csv_file = "alz_articles.csv"
    csv_path = os.path.join(base_folder, csv_file)
    first_site = not os.path.exists(csv_path) # checking if CSV already exists. If no, add headers. If yes, just add site metadata.

    site_details = {
        #working, has 641 first page links
        #"acadia_pharm_inc": { # ACADIA Pharmaceutical Inc.
            #"url": "https://acadia.com/en-us/media/news-releases",
            #"article_container": {"tag": "div", "class": "results"},
            #"nav_button": "//label[contains(@class, 'show-all') and text()='Show All']",
            #"cookie_button": "//button[contains(@id, 'onetrust-accept-btn-handler')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_acadia_pharm_inc_details
            #}, 
        # working
        #"aliada_th": { # Aliada Therapuetics
            #"url": "https://investors.alnylam.com/press-releases",
            #"article_container": {"tag": "div", "class": "financial-info-table"},
            #"nav_button": "//a[contains(@rel, 'next')]",
            #"cookie_button": "//button[contains(@id, 'onetrust-accept-btn-handler')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_aliada_details
            #},
        # working
        #"adel_inc": { # Alzheimer's Disease Expert Lab (ADEL), Inc.
            #"url": "https://www.alzinova.com/investors/press-releases/",
            #"article_container": {"tag": "div", "class": "mfn-content"},
            #"nav_button": "//div[contains(@class, 'mfn-pagination-link') and contains(@class, 'mfn-next')]",
            #"cookie_button": "//button[contains(@class, 'coi-banner__accept')]",
            #"bs_pagenav_flag": False,
            #"html_sel_save": True,
            #"detail_getter": get_adel_details
            #},
        # working
        #"alzheon_inc": { # Alzheon Inc
            #"url": "https://asceneuron.com/news-events/",
            #"article_container": {"tag": "div", "class": "df-cpts-inner-wrap"},
            #"nav_button": "//a[contains(@class, 'df-cptfilter-load-more')]",
            #"bs_pagenav_flag": False,
            #"detail_getter": get_alzheon_details
            #},
        # working
        #"alz_research_uk": { # Alzheimer's Research UK 
            #"url": "https://www.alzheimersresearchuk.org/about-us/latest/news/",
            #"article_container": {"tag": "div", "class": "pp-content-posts"},
            #"nav_button": "//span[contains(@class, 'pp-grid-loader-text') and text()='Load More']",
            #"cookie_button": "//button[contains(@id, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')]",
            #"bs_pagenav_flag": False,
            #"html_sel_save": True,
            #"detail_getter": get_alz_research_uk_details
            #},
        # working 
        # could possibly use numeric page navigation. Just need to click next once, then flip thorugh pages numerically
        "cognition_ther": { # Cognition Therapeutics
            "url": "https://ir.cogrx.com/press-releases/",
            "article_container": {"tag": "div", "class": "lsc-sf-container"},
            "nav_button": "//a[@rel='next']",
            "cookie_button": None,
            "bs_pagenav_flag": False,
            "detail_getter": get_cognit_ther_details
            },
        # not working yet, links are only on a home page, no pagination needed.
        "gemvax_kael": { # GemVax & Kael
            "url": "https://gemvax.com/bbs/board.php?bo_table=releases_en",
            "article_container": {"tag": "div", "class": "bo_list"},
            "nav_button": None,
            "cookie_button": None,
            "bs_pagenav_flag": False,
            "detail_getter": get_gemvax_kael_details
        }
    }
    
    # looping through each site in site_details
    for site_name, site_info in site_details.items():
        # creting a site folder for html storage.
        try:
            site_folder = os.path.join(base_folder, site_name + "_htmls")
            os.makedirs(site_folder, exist_ok=True)
        except Exception as e:
            print("Unable to find/create site folder for", site_name)

        base_url = site_info["url"]
        print("\n-------------------------------------------------------------------------------------------------------------")
        print("Setting up Selenium driver for", base_url, ".... ")
        driver = setup_driver()

        try:
            # Get all links from site
            try:
                links = get_all_pages(site_name, site_info, driver)
                print("\nTotal number of links found on", base_url, ":", len(links))
                total_links += len(links)
            except Exception as e:
                continue
            
            # Saving HTML files for found links, one at a time
            print("Attempting to save HTMLS for all links found on", site_name, "...")
            url_map = {} # {file_number:url}
            for idx, link in enumerate(links, start=1):
                save_html(driver, link, site_folder, idx, cookie_button=site_info.get("cookie_button"), url_map=url_map, html_sel_save=site_info.get("html_sel_save"))
            # Filter for Alzheimers related content
            print("Searching site HTMLs for keyword(s)...")
            try:
                alz_html_url = find_alz_articles(site_folder, url_map)
                total_alz_links += len(alz_html_url)
                print("Total number of Alzheimer's related links on this site:", len(alz_html_url))
            except Exception as e:
                continue

            # extracting article details
            print("Extracting metadata from HTMLs that had the desired keyword(s)...")
            site_article_details = []
            for file_number, url in alz_html_url.items():
                html_path = os.path.join(site_folder, str(file_number) + ".html")
                try:
                    article_data = site_info["detail_getter"](driver, html_path, url, cookie_button=site_info.get("cookie_button"))
                    if article_data:
                        site_article_details.append(article_data)
                except Exception as e:
                    print("Failed to extract metadata from", html_path)
                    continue

            # saving site metadata to csv
            print("Saving sites metadata to a .csv file...")
            if site_article_details:
                try: 
                    df = pd.DataFrame(site_article_details)
                    df.to_csv(csv_path, mode='a', header=first_site, index=False)
                    print("Saved results to", csv_file, ".")
                    first_site = False
                except Exception as e:
                    print("Failed to save CSV file.")

        finally:
            driver.quit()

    print("\n-------------------------------------------------------------------------------------------------------------")
    print(total_links, "new article links found across all sponsor sites.")
    print(total_alz_links, "new alzheimer links found across all sponsor sites.\n")
    print("---------------------------------------------------------------------------------------------------------------")

# ==========================================================================================

if __name__ == "__main__":
    main()
