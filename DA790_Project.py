'''
* Name: Lettie Unkrich
* Description: The program will scrape 100+ websites looking for articles related to alzheimer's, extract relevant data, and store it into
an excel spreadsheet. When gathering the data, it will firstly check if an API is available and convenient to use. If either condition
is false, the program will move on to using the Requests library with BeautifulSoup4, and only turn to Selenium if dynamic elements 
require it. Selenium will use the firfox driver.
* Input: The code requires the website urls to the news/press release home page.
* Output: A excel spreadsheet of the metadata collected from alzheimer related articles.
''' 

# ==========================================================================================
#                             WEEKLY NOTES, QUESTIONS, PROBLEMS AND LINKS
# ==========================================================================================
'''
Notes:

Questions:
- Is it preferred that I output body to excel file or do a pdf?
- For Alzheon Inc there are event, press realses, and news being pulled. Do we want all those?
    - if just want one, can I change the link, or do I need to change code to only pull wanted articles?
- For output like csv and terminal text, would you like me to upload a current version every week or overwrite old one?
    
Problems:
- need to check api code, because every site returned an api is not available
- Code uses BS and if it finds nothing it then attempts Selenium, causes code to take FOREVER to run.
- Alzheon site has multiple space separated classes. Was not one class like ADEL. Need to adjust body code.
- Could delete author and etc code for ADEL since it does not have authors on article pages.

Fixed Problems:
- 

Links:
- 

'''

# ==========================================================================================
#                                IMPORTS AND INSTALL COMMANDS
# ==========================================================================================

# pip3 install selenium
# pip3 install webdriver-manager
# pip3 install beautifulsoup4

import pandas as pd
from bs4 import BeautifulSoup
import time
import requests
import re
import os
# was picking up external links like https://support.microsoft.com/ added library so can code function that pulls internal links only.
from urllib.parse import urlparse

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
#             FUNCTIONS : DRIVER SETUP AND LINK CHECKERS (API, REQUESTS, SELENIUM)
# ==========================================================================================
'''
* function_identifier: setup_driver
* summary: Sets up and initializes the selenium driver in headless mode, will be used for last resort.
* known problems:
    - will change to firefox driver at a later date. Just trying to get other parts of code to work for now.
'''
def setup_driver():
    # Configuring chrome
    options = Options()
    options.add_argument("--headless=new") # will make it to where things run in the background without opening a browser
    options.add_argument("--window-size=1920,1200") # decides window size
    options.add_argument("--log-level=3")  # prevents logs from spamming the terminal. info=0, warning=1, log_error=2, log_fatal=3
    # Initializing a chrome driver that will automatically use the correct driver
    print("Installing ChromeDriver...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    print("Driver setup complete!")
    return driver 

'''
* function_identifier: api_check
* summary: Check if the base_url has an API that is available (status==200) and conveniant (contentType==application/json)
'''
def api_check(base_url):
    try:
        api_url = base_url.rstrip("/") + "/api" # many sites follow this format
        r = requests.get(api_url, timeout=5) # sending a GET request and waiting 5 seconds for the API to respond
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type","")
            if content_type.startswith("application/json"): # ensures we get json and not html
                print("Found API at", api_url)
                return r.json()
    except Exception as e:
        pass

    # No usable API has been found, return None
    return None 

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
            print("Timeout loading page:", url, "while running get_links_selenium.")

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
    if container:
        container_tag = container.get("tag")
        container_class = container.get("class")

        # find the main container
        outer = soup.find(container_tag, class_=container_class)

        if outer:
            containers = []
            # loop through all children of the container
            children = outer.find_all(True)  # True finds all tags
            for child in children.find_all(True): #True gets all tags
                if child.find("a", href=True): # if child has links
                    containers.append(child)

            if containers: # if any children were found with links
                return containers
            else: # fallback and use the main container
                return [outer]
            
        else:
            print("Container not found. Scraping whole page.")
            
    return [soup]


'''
* function_identifier: get_sel_container
* summary: Returns the Selenium element(s) to search in for links. 
If container is found it returns the container. If not, it returns none and get_links_sel will return all <a> elements that start with http.
'''
def get_sel_container(driver, container=None):
    if container:
        container_tag = container.get("tag")
        container_class = container.get("class")
        try:
            # find the main container
            outer = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_tag}.{container_class}"))) 
            containers = []

            # look through all children to see if they have links
            children = outer.find_elements(By.XPATH, ".//*")  # all descendants
            for child in children:
                links = child.find_elements(By.TAG_NAME, "a")
                if links:  # if child has any <a> links
                    containers.append(child)
            
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
    
    # API will attempted 
    if len(links) == 0:
        api_links = api_check(url)
        if api_links:
            for link in api_links:
                links.append(link)
            return links
    
    # Requests by Beautiful Soup will be attempted second
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
    button_xpath = site_info.get("button_xpath") # if beautifulsoup fails, then selenium will look for a button
    container = site_info.get("article_container") # stores what element on a site I want to go through to find links. Do pull links from outside the element.

    # API Check first
    try:
        api = api_check(base_url)
        if api:
            for j in api:
                try:
                    if "url" in j:
                        all_links.add(j["url"])
                except Exception as e:
                    print("Error adding API link." )
            print("Total links collected via API:", len(all_links))
            return all_links
    except Exception as e:
        print("API check failed.")

    # Checking base_url (home page) for links
    try:
        print("Checking", base_url,"for links.")
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
    if not numeric_success and button_xpath:
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
                        print("Number of new links found:", len(new_links)) 
                    else: 
                        print("No new links found on current page.")

                    print("Checking for a button on:", driver.current_url)
                    # look for the button
                    button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, button_xpath)))
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
                    if button_count > 3:
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
* summary: Search through all links and find all articles relating to alzheimers.
'''
def find_alz_articles(driver, links): #using beautiful soup first, then selenium. Was originally only using selenium. 
    alz_article_links = [] # will store all link that have any desired key words (ex.alzheim)
    bs_matches = 0 # will be used to output how many matches were found using beautiful soup
    sel_matches = 0 # will be used to output how many matches were found using selenium
    print("Checking articles for Alzheimer's related content...")

    for link in links: 
        found = False # for tracking if Alzheimer's keyword is found.

        # First try beautifulsoup
        try:
            r = requests.get(link, timeout=10)
            time.sleep(3)
            soup = BeautifulSoup(r.text, "html.parser")
            page_text = soup.get_text().lower() # grabbing all text in lower case
            if "alzheim" in page_text:
                alz_article_links.append(link)
                bs_matches += 1
                found = True
        except Exception as e:
            pass

        # Last resort : try selenium  
        if not found:
            try:  
                driver.get(link)
                time.sleep(3)
                # Wait until body is present then grab the body and extract the text
                try:
                    body_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    body_text = body_element.text.lower()
                except TimeoutException:
                    body_text = ""

                # getting title text
                title_text = driver.title.lower() # gets text inside <title> to extract title

                #checking to see if alzheim is in the body or title text. If so, append the link.
                if "alzheim" in body_text or "alzheim" in title_text:
                    alz_article_links.append(link)
                    sel_matches += 1

            except Exception as e:
                print("Error checking", link, "with Selenium")
                continue

    print("Links with Alzheimer content found using BeautifulSoup:", bs_matches)
    print("Links with Alzheimer content found using Selenium:", sel_matches)
    return alz_article_links




# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: SITE SPECEFIC DETAIL PULLER
# ------------------------------------------------------------------------------------------------
''' COULD DELETE BEAUTIFUL SOUP PART BECAUSE IT RETURNED NOTHING, OR CREATE A BASIC FUNCTION YOU CAN PASS STORAGE LOCATIONS FOR TITLE AND ETC IN.
* function_identifier: get_adel_details
* parameters: this is designed to scrape the details from articles on https://www.alzinova.com/investors/press-releases/ that were found to have the keyword "alzheim."
* note: ADEL does not have publishers or authors on articles
'''
def get_adel_details(driver, link):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "BODY": ""}
    
    # try using beautifulsoup first
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Alzheimer's Disease Expert Lab (ADEL), Inc."
        
        # grabbing title
        title_element = soup.find("div", class_="mfn-title")
        if title_element: #continues if title_element is not empty
            details["TITLE"] = title_element.text.strip() #strip gives a clean output
        
        # grabbing publish date
        date_element = soup.find("span", class_="mfn-date")
        if date_element: # continues if date_element is not empty
            details["PUBLISH DATE"] = date_element.text.strip()
       
        # grabbing author(s) 
        author_element = soup.find("span", class_="author")
        if author_element: # continues if author_element is not empty
            details["AUTHOR(S)"] = author_element.text.strip()

        # grabbing body
        body_container = soup.find("div", class_="mfn-body")
        if body_container:
            paragraphs = body_container.find_all("p")
            details["BODY"] = "\n".join([p.get_text(strip=True) for p in paragraphs])

    except Exception as e:
        print("Beautifulsoup extraction failed for ADEL:", link)

    #if not details["TITLE"] and not details["PUBLISH DATE"] and not details["AUTHOR(S)"] and not details["BODY"]:
        #print("BeautifulSoup returned no details. Now Trying Selenium.")


    # fallback on selenium if beautifulsoup fails.
    if not details["TITLE"] or not details["PUBLISH DATE"] or not details["AUTHOR(S)"] or not details["BODY"]:
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # waiting for elements to load

            # grabbing title
            if not details["TITLE"]: # continues if title is empty
                try:
                    title_element = driver.find_element(By.CLASS_NAME, "mfn-title")
                    details["TITLE"] = title_element.text.strip()
                except:
                    details["TITLE"] = "N/A"


            # grabbing publish date
            if not details["PUBLISH DATE"]: # continues if publish date is empty
                try:
                    date_element = driver.find_element(By.CLASS_NAME, "mfn-date")
                    details["PUBLISH DATE"] = date_element.text.strip()
                except:
                    details["PUBLISH DATE"] = "N/A"

            # grabbing author(s)
            if not details["AUTHOR(S)"]:
                try:
                    author_element = driver.find_element(By.CLASS_NAME, "author")
                    details["AUTHOR(S)"] = author_element.text.strip()
                except:
                    details["AUTHOR(S)"] = "N/A"
            
            # grabbing body
            if not details["BODY"]:
                try:
                    body_container = driver.find_element(By.CLASS_NAME, "mfn-body")
                    paragraphs = body_container.find_elements(By.TAG_NAME, "p")
                    details["BODY"] = "\n".join([p.text.strip() for p in paragraphs])
                except:
                    details["BODY"] = "N/A"

        except Exception as e:
            print("Selenium extraction failed for ADEL:", link)
    
    return details


'''
* function_identifier: get_alzheon_details
* parameters: this is designed to scrape the details from articles on https://asceneuron.com/news-events/ that were found to have the keyword "alzheim."
* problems: site has multiple space separated classes. Was not one class like ADEL.
'''
def get_alzheon_details(driver, link):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "BODY": ""}
    
    # try using beautifulsoup first
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Alzheon Inc."
        
        # grabbing title
        title_element = soup.find("div", class_="entry-title")
        if title_element: #continues if title_element is not empty
            details["TITLE"] = title_element.text.strip() #strip gives a clean output
        
        # grabbing publish date
        date_element = soup.find("span", class_="published")
        if date_element: # continues if date_element is not empty
            details["PUBLISH DATE"] = date_element.text.strip()
       
        # grabbing author(s) 
        author_element = soup.find("span", class_="author vcard")
        if author_element: # continues if author_element is not empty
            details["AUTHOR(S)"] = author_element.text.strip()

        # grabbing body
        body_container = soup.find("div", class_="et_pb_column et_pb_column_2_3 et_pb_column_2  et_pb_css_mix_blend_mode_passthrough")
        if body_container:
            paragraphs = body_container.find_all("p")
            details["BODY"] = "\n".join([p.get_text(strip=True) for p in paragraphs])

    except Exception as e:
        print("Beautifulsoup extraction failed for Alzheon Inc:", link)

    #if not details["TITLE"] and not details["PUBLISH DATE"] and not details["AUTHOR(S)"] and not details["BODY"]:
        #print("BeautifulSoup returned no details. Now Trying Selenium.")


    # fallback on selenium if beautifulsoup fails.
    if not details["TITLE"] or not details["PUBLISH DATE"] or not details["AUTHOR(S)"] or not details["BODY"]:
        try:
            driver.get(link)
            time.sleep(2)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # waiting for elements to load

            # grabbing title
            if not details["TITLE"]: # continues if title is empty
                try:
                    title_element = driver.find_element(By.CLASS_NAME, "entry-title")
                    details["TITLE"] = title_element.text.strip()
                except:
                    details["TITLE"] = "N/A"


            # grabbing publish date
            if not details["PUBLISH DATE"]: # continues if publish date is empty
                try:
                    date_element = driver.find_element(By.CLASS_NAME, "published")
                    details["PUBLISH DATE"] = date_element.text.strip()
                except:
                    details["PUBLISH DATE"] = "N/A"

            # grabbing author(s)
            if not details["AUTHOR(S)"]:
                try:
                    author_element = driver.find_element(By.CLASS_NAME, "author vcard")
                    details["AUTHOR(S)"] = author_element.text.strip()
                except:
                    details["AUTHOR(S)"] = "N/A"
            
            # grabbing body
            if not details["BODY"]:
                try:
                    body_container = driver.find_element(By.CLASS_NAME, "et_pb_column et_pb_column_2_3 et_pb_column_2  et_pb_css_mix_blend_mode_passthrough")
                    paragraphs = body_container.find_elements(By.CLASS_NAME, "et_pb_module et_pb_text et_pb_text_0  et_pb_text_align_left et_pb_bg_layout_light")
                    details["BODY"] = "\n".join([p.text.strip() for p in paragraphs])
                except:
                    details["BODY"] = "N/A"

        except Exception as e:
            print("Selenium extraction failed for Alzheon Inc:", link)
    
    return details


# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: OTHER
# ------------------------------------------------------------------------------------------------
'''
* function_identifier: file_remover
* parameters: requires a file name to be passed through
* return value: if the file exists, remove it. If not, ignore the OSError code and move on.
'''
def file_remover(file_name): #Avoids continuous appending to documents
    try:
        os.remove(file_name)
    except OSError:
        pass


# ==========================================================================================
#                                 MAIN FUNCTION
# ==========================================================================================
def main():
    print("Setting up driver....")
    driver = setup_driver()

    site_details = {
    "adel_inc_url": { # Alzheimer's Disease Expert Lab (ADEL), Inc.
        "url": "https://www.alzinova.com/investors/press-releases/",
        "article_container": {"tag": "div", "class": "mfn-content"},
        "button_xpath": "//div[contains(@class, 'mfn-pagination-link') and contains(@class, 'mfn-next')]",
        "detail_getter": get_adel_details
        },
    "alzheon_inc_url": { # Alzheon Inc
        "url": "https://asceneuron.com/news-events/",
        "article_container": {"tag": "div", "class": "df-cpts-inner-wrap"},
        "button_xpath": "//a[contains(@class, 'df-cptfilter-load-more')]",
        "detail_getter": get_alzheon_details
        }
}
    
    ''' ADD THIS ONCE I GET ALZINOVA WORKING
    ,
    "alzinova_url": { # Alzinova AB
        "url": "https://www.bnhresearch.net/press",
        "article_container": None,
        "button_xpath": "",
        "detail_getter": ""
    },
    "annovis_bio_url": { # Annovis Bio Inc.
        "url": "https://synapse.patsnap.com/news",
        "article_container": None,
        "button_xpath": "",
        "detail_getter": ""
    },
    "aprinoia_ther_url": { # APRINOIA Therapeutics, LLC
        "url": "https://www.ab-science.com/news-and-media/press-releases/",
        "article_container": None,
        "button_xpath": "",
        "detail_getter": ""
    }
    '''
    all_article_details = []

    for site_name, site_info in site_details.items():
        base_url = site_info["url"]
        print("\n-------------------------------------------------------------------------------------------------------------")
        
        try:
            links = get_all_pages(site_name, site_info, driver)
            print("\nTotal number of links found on", base_url, ":", len(links))
        except Exception as e:
            continue
        
        # Filter for Alzheimers related content
        try:
            alz_links = find_alz_articles(driver, links)
            print("\nTotal number of Alzheimer's related links: ", len(alz_links))
        except Exception as e:
            continue

        # extraacting article details
        for link in alz_links:
            article_data = site_details[site_name]["detail_getter"](driver, link)
            if article_data:
                all_article_details.append(article_data)

    #Save results to Excel
    try: 
        file_remover("alz_articles.xlsx")
        df = pd.DataFrame(all_article_details)
        df.to_excel("alz_articles.xlsx", index=False)
        print("Saved results to alz_articles.xlsx")
    except Exception as e:
        print("Failed to save Excel file.")
    
    driver.quit()

# ==========================================================================================

if __name__ == "__main__":
    main()
