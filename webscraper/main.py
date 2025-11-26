import os
import pandas as pd
from selenium_setup import setup_driver
from link_collectors import get_all_pages
from utils import save_html, find_alz_articles
from detail_getters import get_acadia_pharm_inc_details, get_aliada_details, get_adel_details, get_alzheon_details, get_alz_research_uk_details, get_cognit_ther_details
from detail_getters import get_gemvax_kael_details, get_glaxosmithkline_details, get_neurimph_details

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

    ''' 
    Site Details, how to use page navigation:
       For pagination:
       - Want to use home page scraping only: set bs_page_nav to False and put None for nav_button.
       - Want to use BS numerical pagination: set bs_page_nav to True and nav_button to None.
       - Want to use Selenium Numerical pagination: set bs_page_nav to False and put a button XPath in nav_button. 
       For HTML Creation:
       - Set html_sel_save to true if BS HTML creation is producing '403 forbidden' or etc. 
    '''

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
        "alzheon_inc": { # Alzheon Inc
            "url": "https://asceneuron.com/news-events/",
            "article_container": {"tag": "div", "class": "df-cpts-inner-wrap"},
            "nav_button": "//a[contains(@class, 'df-cptfilter-load-more')]",
            "bs_pagenav_flag": False,
            "detail_getter": get_alzheon_details
            }
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
        #"cognition_ther": { # Cognition Therapeutics
            #"url": "https://ir.cogrx.com/press-releases/",
            #"article_container": {"tag": "div", "class": "lsc-sf-container"},
            #"nav_button": "//a[@rel='next']",
            #"cookie_button": None,
            #"bs_pagenav_flag": False,
            #"detail_getter": get_cognit_ther_details
            #},
        # working, links are only on a home page, no pagination needed. That is why nav_button is None and bs_page_nav is false to skip pagination.
        #"gemvax_kael": { # GemVax & Kael
            #"url": "https://gemvax.com/bbs/board.php?bo_table=releases_en",
            #"article_container": {"tag": "div", "class": "bo_list"},
            #"nav_button": None,
            #"cookie_button": None,
            #"bs_pagenav_flag": False,
            #"detail_getter": get_gemvax_kael_details
        #},
        # working when pulling HTMLs, metdata exxtraction never tested because no links had the designated keyword(s)
        #"glaxosmithkline": { # GlaxoSmithKline
            #"url": "https://us.gsk.com/en-us/media/press-releases/",
            #"article_container": {"tag": "ul", "class": "simple-listing"},
            #"nav_button": "//a[text()='next']",
            #"cookie_button": "//button[@id='preferences_prompt_submit']",
            #"bs_pagenav_flag": False,
            #"html_sel_save": True,
            #"detail_getter": get_glaxosmithkline_details
        #},
        # working when pulling HTMLs, metdata exxtraction never tested because no links had the designated keyword(s)
        #"neurim_pharma": { # Neurim Pharmaceuticals
            #"url": "https://neurim.com/news/",
            #"article_container": {"tag": "div", "class": "row"},
            #"nav_button": "//a[@id='more_posts']",
            #"cookie_button": "//a[@class='cc-btn cc-allow button']",
            #"bs_pagenav_flag": False,
            #"html_sel_save": True,
            #"detail_getter" : "get_neurimph_details"
        #}
    }
    
    # looping through each site in site_details
    for site_name, site_info in site_details.items():
        # creating a site folder for html storage.
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
                print("\nTotal number of new, unlogged, links found on", base_url, ":", len(links))
                total_links += len(links)
            except Exception as e:
                continue
            
            # Skipping everything if no new links are found
            if not links:
                print("No new article links found. Skipping HTML saving and metadata extraction.")
                continue

            # Saving HTML files for found links, one at a time
            print("Attempting to save HTMLS for all new links found on", site_name, "...")
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
                    # extracting metadata from the HTML file using the site's detail getter
                    article_data = site_info["detail_getter"](driver, html_path, url, cookie_button=site_info.get("cookie_button"))
                    if article_data and article_data.get("PDF PATH", "").endswith(".pdf"): # saving articles metdata to CSV file if metadata extraction worked.
                        if "CLEAN TITLE" in article_data:
                            del article_data["CLEAN TITLE"]
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

    # pulling total number of alzheimer related articles from all runs, for output.
    if os.path.exists(csv_path):
        try:
            total_scraped_articles = len(pd.read_csv(csv_path))
        except Exception as e:
            total_scraped_articles = 0
    else:
        total_scraped_articles = 0
    

    print("\n-------------------------------------------------------------------------------------------------------------")
    print(total_links, "new, unlogged, article links found across all sponsor sites this run.")
    print(total_alz_links, "alzheimer related links found this run.")
    print(total_scraped_articles, "cumulative total of scraped Alzheimer related pages (for all runs).")
    print("---------------------------------------------------------------------------------------------------------------")

# ==========================================================================================

if __name__ == "__main__":
    main()
