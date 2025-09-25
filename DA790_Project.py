'''
* Name: Lettie Unkrich
* Description: The program will scrape websites looking for articles related to alzheimer's, extract relevant data, and store it into
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
- Would you like us to store every weeks version of our code file in the github repository, or can we overwrite a previous version?
- Is publisher the sponsor?
- What makes an api convienant? For available I have it checking to see if a status of 200 is returned.

Problems:
- FIXED: alzheon_inc_url just keeps loading main page in get_all_pages. Need something that analyzes if the names of links being recorded are already in all_links. If so, quit.
- adel_inc_url will not load if you do https://www.alzinova.com/investors/press-releases/?page=1 even though it follows the ?page=num standard
    - if you manually search by doing ?page=num it reloads home page, if you select next it goes to ?page=num.
- need to check api code, because every site returned an api is not available
- code takes a long time to run because some functions are only using selenium, and not using it as a last resort. I am in progress on fixing it.

Thoughts:
- When grabbing article links should I continue using generic functions or go straight to writing code for each site?
- Could I use bs_matches = 0 and sel_matches = 0 in find_alz_articles to decide if i need to use bs or sel for web scraping?
    - if bs_matches returns 0 it means only sel was used.
    - if so, remove bs code from get_adel_details
    - could even put bs_matches and sel_matches in an earlier function.

Links:
- Ways to remove duplicates from list: https://www.geeksforgeeks.org/python/python-ways-to-remove-duplicates-from-list/

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
#          FUNCTIONS : DRIVER SETUP AND LINK CHECKERS (API, REQUESTS, SELENIUM)
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
* summary: Check if the base_url has an API that is available (status==200) and conveniant (contentType==application/json). Json is a strcutured easily parasbale format.
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
    print("No usable API found for", base_url)
    return None # to show that no usable API was found

'''
* function_identifier: get_links_bs
* summary: Grabbing all links from a single page using requests by beautiful soup
'''
def get_links_bs(url):
    links = []
    try:
        r = requests.get(url, timeout=10)
        time.sleep(3)
        soup = BeautifulSoup(r.text, "html.parser")
        # Generic setup in case site details have not been coded yet 
        for i in soup.find_all("a", href=True): # looks for href= that start with http
            href = i["href"] #<a href = "http"> -> "http" 
            if href.startswith("http"): # if href starts with http append the http to links list
                links.append(href)
    except Exception as e:
        print("Failed to get links from", url, "when using requests by beautifulsoup.")
    return links

'''
* function_identifier: get_links_selenium
* summary: Grabbing all links from a single page using selenium, for fallback if get_links_bs() fails
'''
def get_links_selenium(url, driver): 
    links = []
    try:
        driver.get(url)
        # waiting for page to load all elements  
        link_elements = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a'))) #link elements is a list of all <a> elements on the page
        
        for element in link_elements: # searching through all elements in link_elements
            href = element.get_attribute('href') # grab any links that are stored behind href (<a href='link'>)
            if href and href.startswith("http"):
                links.append(href)
    except Exception as e:
        print("Failed to get links from", url, "with selenium.")
    return links

# ------------------------------------------------------------------------------------------------
#                   FUNCTIONS: PAGE LOOPING AND GENERIC LINK COLLECTOR
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: get_all_links
* summary: Tries to grab all links from a single page using different methods
'''
def get_all_links(site, url, driver):
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
        bs_links = get_links_bs(url)
        if bs_links:
            for link in bs_links:
                links.append(link)
            return links
    
    # Lastly, Selenium will be attempted
    if len(links) == 0:
        sel_links = get_links_selenium(url, driver)
        if sel_links:
            for link in sel_links:
                links.append(link)

    # removing duplicate links by using set() 
    links = list(set(links))
    return links

'''
* function_identifier: get_all_pages
* summary: Go through all pages of a base_url and grab article links from all pages (if there are multiple pages) by following the typical website design ?page=num or &page=num.
* known problems:
    - need to account for page=1, sometimes once you go past the base_url it does not go straight to 2, will go to 1.
    - what about sites that don't do pages? They do a load more (view more) (next) button, etc. Fix function to deal with this.
'''
def get_all_pages(site, base_url, driver):
    all_links = set() # stores unique links

    # API Check first
    api = api_check(base_url)
    if api:
        for j in api:
            if "url" in j:
                all_links.append(j["url"])
        print("Total links collected via API:", len(all_links))
        return all_links

    # If API fails try going through pages next
    page = 1
    while True: # while page != 1 and there is a page=num found, continue to go through all pages and store all links on each page
        if page == 1:
            url = base_url
            print("Checking", url, "for links.")
        else:
            if '?' in base_url:
                url = f"{base_url}&page={page}"
                print("Grabbing links from:", url)
            else:
                url = f"{base_url}?page={page}" 
                print("Grabbing links from:", url)   

        page_links = get_all_links(site, url, driver) # calling get_articles function for link collection
        page_links_set = set(page_links)

        # Do a comparison between page_links_set and all_links to see if there are any new links
        new_links = page_links_set - all_links
        if not new_links: #if there are no new links, stop.
            print("No new links found. Stopping page search.")
            break
        
        all_links.update(new_links) # adds all new links to the all links list, update will remove suplicates automatically
        print("Found", len(new_links), "links on", url)
        page += 1
        time.sleep(3) # being nice

    # add code that attempts to click a 'view more' or 'load more' button using selenium
        
    return list(all_links)


# ------------------------------------------------------------------------------------------------
#                                  FUNCTIONS: ALZHEIMERS FILTERING
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: find_alz_articles
* summary: Search through all links and find all articles relating to alzheimers.
* known problems: 
    - 
'''
def find_alz_articles(driver, links): #using beautiful soup first, then selenium. Was originally only using selenium. 
    alz_article_links = [] # will store all link that have any desired key words (ex.alzheim)
    bs_matches = 0 # will be used to output how many matches were found using beautiful soup
    sel_matches = 0 # will be used to output how many matches were found using selenium
    print("Checking articles for Alzheimer's related content...")

    for link in links: 
        try:
            # First try beautifulsoup
            try:
                r = requests.get(link, timeout=10)
                time.sleep(3)
                soup = BeautifulSoup(r.text, "html.parser")
                page_text = soup.get_text().lower() # grabbing all text in lower case
                if "alzheim" in page_text:
                    alz_article_links.append(link)
                    bs_matches += 1
                    continue #skips selenium if found
            except Exception as e:
                pass

            # Last resort : try selenium    
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
            print("Error checking", link, ":", e)
            continue
    
    print("Links with Alzheimer content found using BeautifulSoup:", bs_matches)
    print("Links with Alzheimer content found using Selenium:", sel_matches)
    return alz_article_links


# ------------------------------------------------------------------------------------------------
#                                  FUNCTIONS: ARTICLE DETAILS PULLER
# ------------------------------------------------------------------------------------------------

''' SHOULD I DELETE THIS?
* function_identifier: generic_detail_puller
* summary: Will extract article details like title, publish date, author, etc. and store them into a dictionary.
* known problems:
    - this is using selenium, selenium should be a backup.
    - driver.title does not always pull the title. Need a better way to do this.
    - need to write code for other details.
'''
def generic_detail_getter(driver, link):
    details = {"PUBLISHER": "", "TITLE": "", "URL": link, "PUBLISH DATE": "", "AUTHOR(S)": "", "BODY": ""}
    
    try: # attempt to get the desired details from the link and store them in the dictionary named 'details' 
        driver.get(link)
        body_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        title_element = driver.find_element(By.TAG_NAME, "h1")
        details["TITLE"] = title_element.text.strip() #strip() removes any extra whitespace before or after title
        details["PUBLISH DATE"] = 0 #look for different formats yyyy-mm-dd, mm-dd-yyyy, jan-dd-yyyy, january-dd-yyyy, etc.

    except Exception as e:
        print("Failed to extract the alzheimer article details from:", link)

    return details

# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: SITE SPECEFIC DETAIL PULLER
# ------------------------------------------------------------------------------------------------

'''
* function_identifier: get_adel_details
* parameters: this is designed to scrape the details from articles on https://www.alzinova.com/investors/press-releases/ that were found to have the keyword "alzheim."
* known problems: 
    - figure out how to pull author(s), publisher, and body
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
        title_element = soup.find("h1", class_= "entry-title")
        if title_element: #continues if title_element is not empty
            details["TITLE"] = title_element.text.strip() #strip gives a clean output
        else:
            #print("No <h1 class='entry-title'> found when using Beautifulsoup, will try Selenium.")
            pass
        # grabbing publish date
        date_element = soup.find("span", class_="published")
        if date_element: #continues if date_element is not empty
            details["PUBLISH DATE"] = date_element.text.strip()
        else:
            #print("No <span class='published'> found when using Beautifulsoup, will try Selenium.")
            pass
        
        # grabbing author(s)
        # grabbing body
    
    except Exception as e:
        print("Beautifulsoup extraction failed for ADEL:", link)

    # fallback on seleniium if beautifulsoup fails.
    try:
        driver.get(link)
        time.sleep(10) # waiting for elements to load

        # selenium fallback for title
        if not details["TITLE"]: # continues if title is empty
            try:
                title_element = driver.find_element(By.TAG_NAME, "h1")
                if title_element.text.strip():
                    details["TITLE"] = title_element.text.strip()
                else:
                    print("Unable to collect title using Selenium.")
            except Exception as e:
                pass
        # selenium fall back for publish date
        if not details["PUBLISH DATE"]: # continues if publish date is empty
            try:
                date_element = driver.find_element(By.CSS_SELECTOR, "span.published") # looking for the first span element that has a class called published.
                if date_element.text.strip():
                    details["PUBLISH DATE"] = date_element.text.strip()
                else:
                    print("Unable to collect publish date using Selenium.")
                    details["PUBLISH DATE"] = "N/A" # no date found
            except Exception as e:
                pass

        # selenium fallback for author(s)
        details["AUTHOR(S)"] = "N/A"
        # selenium fallback for body
               
    except Exception as e:
        print("Selenium extraction failed for ADEL:", link)
    
    return details


'''
* function_identifier: get_alzheon_details
* parameters: this is designed to scrape the details from articles on https://asceneuron.com/news-events/ that were found to have the keyword "alzheim."
'''
def get_alzheon_details(driver, link):
    pass


'''
* function_identifier: pull_article_details
* parameters: Will use a certain sites detail getter function. If a function has not been made for the site
it will use the generic_detail_puller()
'''
def get_article_details(driver, link, site_name):
    # associating site names with their detail locater functions
    site_detail_getters = {
        "adel_inc_url": get_adel_details,
        "alzheon_inc_url": get_alzheon_details
    }

    if site_name in site_detail_getters:
        puller = site_detail_getters[site_name]
    else:
        puller = generic_detail_getter

    return puller(driver, link)


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

    sites = { # changed to dictionary in expectation that all sites might need code tailored to them
        "adel_inc_url": "https://www.alzinova.com/investors/press-releases/", # Alzheimer's Disease Expert Lab (ADEL), Inc.
        "alzheon_inc_url": "https://asceneuron.com/news-events/",  # Alzheon Inc
        "alzinova_url": "https://www.bnhresearch.net/press", # Alzinova AB
        "annovis_bio_url": "https://synapse.patsnap.com/news" # Annovis Bio Inc.
        #"aprinoia_ther_url": "https://www.ab-science.com/news-and-media/press-releases/", # APRINOIA Therapeutics, LLC
    }

    all_article_details = []

    for site_name, site_url in sites.items():
        print("\n-------------------------------------------------------------------------------------------------------------")
        print("Searching ", site_url, "for article links.")
        links = get_all_pages(site_name, site_url, driver)
        print("\nTotal number of links found on", site_url, ":", len(links))
        alz_links = find_alz_articles(driver, links)
        print("\nTotal number of Alzheimer's related links: ", len(alz_links))
        for link in alz_links:
            article_data = get_article_details(driver, link, site_name)
            if article_data:
                all_article_details.append(article_data)


    file_remover("alz_articles.xlsx")
    df = pd.DataFrame(all_article_details)
    df.to_excel("alz_articles.xlsx", index=False)
    print("Saved results to alz_articles.xlsx")
    driver.quit()
# ==========================================================================================

if __name__ == "__main__":

    main()
