# This python file stores all functions that pull links / handle pagination

import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import load_checked_links

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
                # only keep full URLs that start with "http" and do not end in ".pdf"
                if href.startswith("http") and not href.lower().endswith(".pdf"): 
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
            # only keep full URLs that start with "http" and do not end with ".pdf"
            if href and href.startswith("http") and not href.lower().endswith(".pdf"):
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
* function_identifier: get_home_page()
* summary: Grab all article links from the base_url; for when no pagination is required for a site
* parameters:
    - site_name: name of the website
    - site_info: dictionary containing site-specefic information
    - driver: selenium webdriver used for button based page navigation
* return: a set of unique internal article links found across all pages
'''
def get_home_page(site_name, site_info, driver, checked_links):
    all_links = set() # stores unique links
    base_url = site_info["url"]
    container = site_info.get("article_container") # container for articles
    print("Pagination is not needed for this site. Scraping links off", base_url,"home page.")

    try:
        home_links = get_all_links(base_url, driver, container=container) or []
        home_links = filter_internal_links(home_links, base_url)
        new_links = set(home_links) - checked_links
        all_links.update(new_links)
        print("Found", len(home_links), "links on home page,", len(new_links), "are new.")
        return all_links
    except Exception as e:
        print("Failed to get links from home page as fallback:", e)
        return set()


'''
* function_identifier: get_pages_bs()
* summary: Go through all pages of a base_url and grab article links from all page(s) by using bs numerical navigation.
* parameters:
    - site_name: name of the website
    - site_info: dictionary containing site-specefic information
    - driver: selenium webdriver used for button based page navigation
* return: a set of unique internal article links found across all pages
'''
def get_pages_bs(site_name, site_info, driver, checked_links):
    all_links = set() # stores unique links
    base_url = site_info["url"]
    container = site_info.get("article_container") # container for articles
    print("Checking", base_url,"for links using beautiful soup numerical pagination.")

    # try home page
    try:
        print("Searching home page...")
        base_links = get_all_links(base_url, driver, container=container) or []
        base_links = filter_internal_links(base_links, base_url)
        base_links = set(base_links) - checked_links
        all_links.update(base_links)
    except Exception as e:
        print("Failed to get links from base url.")

    # Numeric page navigation (?page=num or &page=num)
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
            page_links = get_all_links(url, driver, container=container) or [] 
            page_links = filter_internal_links(page_links, base_url)
            page_links_set = set(page_links)
            
            new_links = page_links_set - all_links - checked_links 
            
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

    return all_links, numeric_success

'''
* function_identifier: get_pages_sel()
* summary: Go through all pages of a base_url and grab article links from all page(s) by using sel button navigation.
* parameters:
    - site_name: name of the website
    - site_info: dictionary containing site-specefic information
    - driver: selenium webdriver used for button based page navigation
* return: a set of unique internal article links found across all pages
'''
def get_pages_sel(site_name, site_info, driver, checked_links):
    all_links = set() # stores unique links
    base_url = site_info["url"]
    nav_button = site_info.get("nav_button") # for selenium based button navigation
    container = site_info.get("article_container") # container for articles
   
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
                new_links = page_links_set - all_links - checked_links

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
                if button_count > 2:
                    print("Stopping since max amount of button presses has been reached for testing purposes.")
                    break

            except TimeoutException:
                print("No more Next/Load More buttons found. Stopping button navigation.")
                break
            except Exception as e:
                print("Error during button navigation.")
    
    except Exception as e:
        print("Button navigation failed or Site has no buttons to be pressed.")
    
    return all_links

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
    checked_links = load_checked_links() # loading previously logged links
   
    # determines if numeric pagination using bs is applicable.
    try:
        bs_needed = site_info.get("bs_pagenav_flag")
    except Exception as e:
        bs_needed = True

    # Skip numeric page navigation if bs_needed is false
    if bs_needed is False:
        numeric_success = False
    else: 
        bs_links, numeric_success = get_pages_bs(site_name, site_info, driver, checked_links)
        if numeric_success: # only use links if numeric pagination succeeded.
            all_links.update(bs_links)
                
    # If numerical page navigation fails, try doing button navigation with selenium
    if not numeric_success and nav_button:
        sel_links = get_pages_sel(site_name, site_info, driver, checked_links)
        all_links.update(sel_links)

    # for if a site has a home page only and doesn't need pagination
    if not all_links:
        home_links = get_home_page(site_name,site_info, driver, checked_links)
        all_links.update(home_links)

    return list(all_links)