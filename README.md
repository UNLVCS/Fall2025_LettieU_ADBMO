# README
<span style="color:#555555;">This repository contains all code, files, and documents used for web scraping metadata from sponsor websites for the ADBMO project.</span>

<h3>The most updated version of the code is located in the <code>webscraper</code> folder.</h4>

<details>
<summary><strong>What is <code>main.py?</code>?</strong></summary>
<br>
<p><code>main.py</code> is the main script that runs the entire workflow. </p>

  <p><strong>Functions in <code>main.py</code> include:</strong></p>
  <ul>
    <li><strong><code>main()</code></strong> – arranges the entire pipeline. It:
      <ul>
        <li>Loads each sites configuration (URL, container, pagination info, and detail getter function).</li>
        <li>Calls <code>setup_driver()</code> from <code>selenium_setup.py</code> to create a headless Chrome driver for Selenium.</li>
        <li>Calls <code>get_all_pages()</code> from <code>link_collectors.py</code> to collect article URLs.</li>
        <li>Loops through links and saves each page as an HTML file using<code>save_html()</code> from <code>utils.py</code></li>
        <li>Calls <code>find_alz_articles()</code> from <code>utils.py</code> to keep only HTMLs that contain Alzheimer's related keywords.</li>
        <li>Calls the correct site specefic details function from <code>detail_getters.py</code> to extract article metadata and create a PDF.</li>
        <li>Appends all extracted article metadata into a CSV file (<code>alz_articles.csv</code>) using pandas.</li>
      </ul>
    </li>
  </ul>
</details>

<hr>

<details>
  <summary><strong>What is <code>detail_getters.py</code>?</strong></summary>
  <br>

  <p><code>detail_getters.py</code> stores all site-specific functions used to extract metadata (title, author(s), publish date, body text, etc.) from the saved HTML files. Each function opens saved HTMLs using BeautifulSoup, pulls metadata, cleans text, and creates PDFs for each article.</p>

  <p><strong>Functions defined in <code>detail_getters.py</code>:</strong></p>
  <ul>
    <li><code>get_acadia_pharm_inc_details()</code></li> extracts ACADIA pharmaceuticals metadata from saved HTMLs and generates a PDF of each site.
    <li><code>get_aliada_details()</code></li> extracts Aliada Therapuetics metadata from saved HTMLs and generates a PDF.
    <li><code>get_adel_details()</code></li> extracts ADEL (Alzheimer's Disease Expert Lab) metadata from saved HTMLs and generates a PDF.
    <li><code>get_alzheon_details()</code></li> extracts Alzheon Inc. metadata from saved HTMLs and generates a PDF.
    <li><code>get_alz_research_uk_details()</code></li> extracts Alzheimer's Research UK metadata from saved HTMLs and generates a PDF.
    <li><code>get_cognit_ther_details()</code></li> extracts Cognition Therapeutics metadata from saved HTMLs and generates a PDF.
    <li><code>get_gemvax_kael_details()</code></li> extracts Gemvax & Kael metadata from saved HTMLs and generates a PDF.
    <li><code>get_glaxosmithkline_details()</code></li> extracts GlaxoSmithKline metadata from saved HTMLs and generates a PDF.
    <li><code>get_neurimph_details()</code></li> extracts Nerim Pharmaceuticals metadata from saved HTMLs and generates a PDF.
  </ul>
</details>

<hr>

<details>
  <summary><strong>What is <code>link_collectors.py</code>?</strong></summary>
  <br>

  <p><code>link_collectors.py</code> contains all functions related to collecting URLs and handling pagination.

  <p><strong>Container helpers:</strong></p>
  <ul>
    <li><code>get_bs_container()</code></li> attempts to pull articles from a designated container using BeautifulSoup, if container is not found all links from the page will be pulled.
    <li><code>get_sel_container()</code></li> attempts to pull articles from a designated container using Selenium, if container is not found all links from the page will be pulled.
  </ul>

  <p><strong>Link extraction:</strong></p>
  <ul>
    <li><code>get_links_bs()</code> uses BeautifulSoup + Requests to extract links from a page.</li>
    <li><code>get_links_sel()</code> uses Selenium to extract links from a page.</li>
    <li><code>get_all_links()</code> tries to <code>get_links_bs()</code> first. If that finds nothing, it then falls back to <code>get_links_sel()</code>.</li>
  </ul>

  <p><strong>Pagination:</strong></p>
  <ul>
    <li><code>get_home_page()</code> scrapes links from a single home page when no pagination is needed. Filters out previously logged links using <code>checked_links.csv</code>.</li>
    <li><code>get_pages_bs()</code> attempts numeric pagination using query parameters like <code>?page=</code> or <code>&page=</code>. Scrapes each page for internal links, tracks new links, and stops when no new links are found.</li>
    <li><code>get_pages_sel()</code> uses selenium for button based navigation, collecting new links until no more articles are loaded.
    <li><code>get_all_pages()</code> loads <code>checked_links.csv</code> using <code>load_checked_links()</code> from <code>utils.py</code>. 
      <ul>
        <li>Decides whether to use numeric pagination (<code>get_pages_bs()</code>), button navigation (<code>get_pages_sel()</code>), or a single home page scrape (<code>get_home_page()</code>).</li>
        <li>Returns a list of all unique article links for that site.</li>
      </ul>
  </ul>

  <p><strong>Filtering:</strong></p>
  <ul>
    <li><code>filter_internal_links()</code> filters out links with a different domain, so that only links from the same domain are kept. Links with a different domain are stored in the external_links.csv file.</li>
  </ul>
</details>

<hr>

<details>
  <summary><strong>What is <code>selenium_setup.py</code>?</strong></summary>
  <br>

  <p>This file initializes and configures the Selenium browser used to scrape websites.</p>

  <p><strong>Function defined:</strong></p>
  <ul>
    <li><code>setup_driver()</code> creates a headless Chrome driver with:</li>
      <ul>
        <li>Auto-installing ChromeDriver</li>
        <li>A user-agent</li>
        <li>Desktop window size</li>
        <li>Suppressed logging</li>
      </ul>
    <li> The user-agent and desktop window size helped to avoid being flagged as a bot. </li>
  </ul>
</details>

<hr>

<details>
  <summary><strong>What is <code>utils.py</code>?</strong></summary>
  <br>

  <p><code>utils.py</code> contains helper functions for HTML saving, keyword detection, generating PDFs, logging links, and handling cookie popups.</p>

  <p><strong>Logging utilities:</strong></p>
  <ul>
    <li><code>log_checked_link()</code> ensures the <code>checked_links.csv</code> file exists, loads already logged links, and appends a new link row if the link hasn't been logged yet.</li> 
    <li><code>load_checked_links()</code> reads <code>checked_links.csv</code> and returns a set of all previously checked URLs. Used to avoid rechecking the same article links over and over.</li>
  </ul>

  <p><strong>HTML renaming:</strong></p>
  <ul>
    <li><code>rename_html_to_title()</code> renames the HTML and HTML path using the ["CLEAN TITLE"] formed in add_pdf_detail, to prevent overwriting HTMLs in the site folder.</li>

  <p><strong>HTML saving & keyword detection:</strong></p>
  <ul>
    <li><code>save_html()</code> saves HTML of link via BS or Selenium into the sites folder, scrolls page, clicks cookies.</li>
    <li><code>find_alz_articles()</code> searches HTMLs for Alzheimer-related keywords using BeautifulSoup, logs each checked link using <code>log_checked_link()</code>, and keeps only files containing Alzheimer's related keywords.</li>
  </ul>

  <p><strong>Cookie handling:</strong></p>
  <ul>
    <li><code>cookies_handler()</code> waits for a cookie button if an XPath is provided. Scrolls to the button and clicks it. Returns True if button was clicked. False if not.</li>
  </ul>

  <p><strong>PDF creation:</strong></p>
  <ul>
    <li><code>add_pdf_detail()</code> opens URL page with Seleneium, and saves a PNG screenshot of the page. Converts the PNG to RBG and then saves it as a PDF. Stores PDF in a site specefic PDF folder and adds PDF location to PDF PATH in <code>alz_articles.csv</code>.
  </ul>
</details>

<hr>

<details>
  <summary><strong>What is <code>requirements.txt</code>?</strong></summary>
  <br>

  <p>This file lists all required Python packages:</p>
  <ul>
    <li>selenium</li>
    <li>webdriver-manager</li>
    <li>beautifulsoup4</li>
    <li>Pillow</li>
    <li>pandas</li>
    <li>requests</li>
  </ul>
</details>
