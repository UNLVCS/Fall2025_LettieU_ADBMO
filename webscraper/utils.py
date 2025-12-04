import os
import csv
import time
import re
from datetime import datetime
from PIL import Image
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================================================================
#            FUNCTIONS : LOGGING CHECKED LINKS AND LOADING THE FILE
# ==========================================================================================
'''
* function_identifier: log_checked_link
* summary: logs each link that's HTML version has been scanned for keyword(s) into checked_links.csv, preventing duplicate links.
* parameters: 
    - link: the URL that was scanned for Alzheimer related keywords.
    - base_folder: folder to store CSV (default: saved_sites)
    - filename: CSV filename that is storing checked links(deffault: checked_links) 
'''
def log_checked_link(link, base_folder="saved_sites", filename="checked_links.csv"):
    # making sure file exists
    filepath = os.path.join(base_folder, filename)
    try: 
        loggedlinks_dir = os.path.dirname(filepath)
        if loggedlinks_dir != "":
            os.makedirs(loggedlinks_dir, exist_ok=True)
    except Exception as e:
        print("Failed to create directory for checked_links.csv")
        return
        
    # load existing links to avoid duplicates
    existing_links = load_checked_links(base_folder, filename)

    # append new link if it is not a duplicate
    if link not in existing_links:
        try:
            with open(filepath, "a", newline="", encoding="utf-8") as f:
               writer = csv.writer(f)
               writer.writerow([link])
        except Exception as e:
            print("Failed to write checked_links.csv")


'''
* function_identifier: load_checked_links
* summary: loads the csv file that has all previously checked links stored. This is in it's own seperate function because 
    it is needed for the log_checked_links function and for link comparison to prevent code from repetively checking the same links on a site.
* parameters: 
    - base_folder: folderr to store CSV (default: saved_sites)
    - filename: CSV filename that is storing checked links(deffault: checked_links)
'''
def load_checked_links(base_folder="saved_sites", filename="checked_links.csv"):
    filepath = os.path.join(base_folder, filename)
    checked_links = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        checked_links.add(row[0])
        except Exception as e:
            print("Failed to read checked_links.csv")
    return checked_links


# ==========================================================================================
#                          HTML RENAME FUNCTION
# ==========================================================================================
'''
* function_identifier: rename_html_to_title
* summary: renames the HTML and HTML path using the ["CLEAN TITLE"] formed in add_pdf_detail, to prevent overwriting HTMLs in the site folder.
* parameters:
    - html_path: location path to the desired HTML
    - clean_title: the clean version of the title that will replace the current html filename (1.html, 2.html, etc.)
* returns: new html filepath
'''
def rename_html_to_title(html_path, clean_title):
    # if no clean title keep html path
    if not clean_title:
        return html_path
    
    folder = os.path.dirname(html_path)
    new_html_path = os.path.join(folder, clean_title +  ".html")

    try:
        os.replace(html_path, new_html_path)
        return new_html_path
    except:
        return html_path


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
    keywords = ["alzheim"] # add keywords to this list if you wanna expand the search
    alz_html_url = {}

    if not os.path.exists(site_folder):
        print("Site folder does not exist:", site_folder)
        return {}
    
    # loop through all HTML files in the folder
    for html_filename in os.listdir(site_folder):
        if not html_filename.endswith(".html"):
            continue

        # skipping non-numeric filenames since ones named after titles have already been scanned for keyword(s) and metadata
        name = html_filename.replace(".html", "")
        if not name.isdigit():
            continue

        file_number = int(html_filename.replace(".html", ""))
        html_path = os.path.join(site_folder, html_filename)
        url = url_map.get(file_number, None)

        try:
            # read HTML file and extract text
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            page_text = soup.get_text().lower()

            # logging link after text freom HTML is successfully extracted.
            if url:
                log_checked_link(url)

            # keep file if keyword(s) found; otherwise delete
            if any(kw in page_text for kw in keywords):
                alz_html_url[file_number] = url_map.get(file_number, "URL not found")
            else:
                os.remove(html_path)
                if file_number in url_map:
                    del url_map[file_number] 

        except Exception as e:
            print("Error occured when searching HTML for keyword:", html_path)
            # try to remove file and url_map entry if an error occured when searching html
            try:
                if url:
                    log_checked_link(url)
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
            details["CLEAN TITLE"] = None
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
            clean_title = re.sub(r'[\\/*?:"<>|]', "", article_title[:60]).strip()
            clean_title = clean_title.replace(" ", "_")
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
        details["CLEAN TITLE"] = clean_title
        #print ("Saved PDF for:" + article_title)

    except Exception as e:
        print("Failed to create PDF for" + details.get("URL"))
        details["PDF PATH"] = "PDF generation failed"
        details["CLEAN TITLE"] = None

    #print("PDF has been created.")
    return details
