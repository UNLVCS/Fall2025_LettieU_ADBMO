# This python file stores every get_<site name>_details function that are used for metadata extraction

from bs4 import BeautifulSoup
from utils import add_pdf_detail, rename_html_to_title

# ------------------------------------------------------------------------------------------------
#                                 FUNCTIONS: SITE DETAIL PULLING FUNCTIONS
# ------------------------------------------------------------------------------------------------
# * parameters for all: 
#   - driver: selenium webdriver
#   - html_path: communicates where html is stored, each html w/ keyword is searched through for metadata.
#   - url: the link associated with the html_path. 
#   - cookie_xpath: optional xpath for a cookie consent button
# * return: a dictionary of cleaned metadata fields

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

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

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

    return details

'''
* function_identifier: get_glaxosmithkline_details
* parameters: this is designed to scrape the details from articles on https://us.gsk.com/en-us/media/press-releases/ that were found to have the keyword "alzheim."
* notes: this site has no authors
'''
def get_glaxosmithkline_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the saved HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "GlaxoSmithKline"

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
                details["PUBLISH DATE"] = date_element.get_text(strip=True)
            else:
                details["PUBLISH DATE"] = "N/A"
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # grabbing author(s) 
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try:
            body_container = soup.find("div", class_="main-container rte child-component")

            if not body_container or not body_container.find("p"):
                body_container = soup.find("div", class_="content-wrapper")

            if body_container:
                paragraphs = body_container.find_all("p")
                all_text = []
                for p in paragraphs:
                    txt = p.get_text(strip=True)
                    if txt:
                        all_text.append(txt)
                details["BODY"] = "\n".join(all_text) if all_text else "N/A"
            else:
                details["BODY"] = "N/A"
        except Exception as e:
            details["BODY"] = "N/A"

    except Exception as e:
        print("Unable to grab metadata from", details["PUBLISHER"], "html file:", url)
    
    # storing pdf version of site
    details = add_pdf_detail(driver, details, site_name = "glaxosmithkline", cookie_xpath=cookie_button)

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))

    return details


'''
* function_identifier: get_neurimph_details
* parameters: this is designed to scrape the details from articles on https://neurim.com/news/ that were found to have the keyword "alzheim."
* notes: this site has no authors
'''
def get_neurimph_details(driver, html_path, url, cookie_button=None):
    details = {"PUBLISHER": "", "TITLE": "", "URL": url, "PUBLISH DATE": "", "AUTHOR(S)": "", "HTML PATH": html_path, "PDF PATH": "", "BODY": ""}

    try:
        # Open the saved HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # grabbing publisher
        details["PUBLISHER"] = "Neurim Pharmaceutical"

        # grabbing title
        try:
            title_element = soup.find("h2")
            if title_element:
                details["TITLE"] = title_element.get_text(strip=True)
            else:
                details["TITLE"] = "N/A"
        except Exception as e:
            details["TITLE"] = "N/A"

        # grabbing publish date
        try:
            date_element = soup.find("div", class_="card-date date")
            if date_element: 
                details["PUBLISH DATE"] = date_element.get_text(strip=True)    
        except Exception as e:
            details["PUBLISH DATE"] = "N/A"

        # grabbing author(s)
        details["AUTHOR(S)"] = "N/A"

        # grabbing body
        try: 
            body_container = soup.select("div.blog-detail-post")
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
    details = add_pdf_detail(driver, details, site_name = "neurim_pharma", cookie_xpath=cookie_button)

    # rename HTML file and HTML file path to prevent overwriting
    details["HTML PATH"] = rename_html_to_title(html_path, details.get("CLEAN TITLE"))
    
    return details
