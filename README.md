## About

This repo contains supplementary material (code and datasets) for the following paper:

        "Using Application Layer Banner Data to automatically identify IoT devices"
        Talha Javed, Muhammad Haseeb, Muhammad Abdullah, and Mobin Javed
        ACM SIGCOMM Computer and Communication Review (CCR) Issue 50, Volume 3, July 2020 

The CCR paper is a reproducibility study of the following Usenix Security 2018 paper:

        "Acquistional Rule Based Engine for Discovering Internet-of-Things Devices"
        Xuang Feng, Qiang Li, Haining Wang, and Limin Sun
        Usenix Security 2018

The code in this repo implements the ARE engine proposed in the Usenix Security 2018 paper. The engine takes a banners dataset as input and generates rules for discovering and annotating IoT devices. Potentially differing design choices by the authors of this code (compared to the original ARE paper) are documented in Section 3 of the CCR paper.  

---------------
Pre-requisites
---------------

- Python3 version > 3.7

--------------
Setup
--------------
- Install the required dependencies using: pip3 install -r requirements.txt

- Configure the following parameters in “config.py”:

        BANNERS_FILE                Path to the input banners file which contains the banners.
        NUM_PROCESS_BANNERS         Limit for number of banners to process (if not all)
        OUT_PATH                    Absolute Path to intermediate log files and final rules file
        API_KEYS                    List of Google Custom Search API Keys which can be obtained from:
                                    https://developers.google.com/custom-search/v1/overview 
        CSE_ID                      Custom Search Engine ID which can be obtained from: 
                                    https://cse.google.com/cse/all

- **Important Note**: You must configure the CSE to search the entire web. Please use the following steps to configure the CSE correctly:

        1) Go to https://cse.google.com/cse/all.
        2) Click on the "Add" button. Provide any name of your liking for the search engine and enter any URL in the "Sites to search" box for now. Now, click on "CREATE" button at the bottom. You'll see a page containing the text "Congratulations! You've successfully created your search engine".
        3) On this page, right next to "Modify your search engine", click on the "Control Panel" button. This will take you to the CSE settings/setup page. Your Search engine ID is also displayed in this page.
        4) Scroll down and turn on the button right next to "Search the entire web" and wait for a second until the changes are saved.
        5) Finally, on the same page under "Sites to search", delete the URL you provided in the first step. Your CSE is now configured to search the entire web.

--------------
Banner Files
--------------

The banner files contains banners uniquely identified by their banner-IDs. The files are in json formatted in the following way:

    "<banner-ID>": {
                "type"      : Banner type (e.g, HTTP, FTP, etc.)
                "banner"    : Banner text
                "ips"       : List of IP addresses of the devices
                "<Labels>"  : List of labels (e.g, Censys labels, Ferret Labels) corresponding to each device
                    {
                        "ip"    : IP address of the device,
                        "label" : {
                            "deviceTypes"   : List of device types associated with the device
                            "vendor"        : Vendor information of the device
                            "product"       : Product/model name of the device
                        }
                    }

----------------
Running the code
----------------

Run the code as:
    $ python run.py 

        - run.py runs the code pipeline on the banners file and produces two outputs: "rules.csv" containing the list of rules, and a set of intermediate log files.
          The outputs are saved in the OUT_PATH directory.

        - The code pipeline consists of the following stages: get_banners, get_queries, get_links, get_pages, get_annotations, and get_rules.
          
        - get_banners reads banner texts from the banners files, get_queries obtains search queries for Google search from the banner texts,
          get_links grabs URLS from Google search results, get_pages grabs webpages, get_annotations extracts annotations from the webpages,
          and get_rules produces the rules files.

        - To resume the code pipeline from an intermediate stage of the code pipeline:
            $ python run.py --run_from_stage <stage> <# banners>   
          
          The resume stage can be 'get_queries', 'get_links','get_pages', and 'get_annotations'.
          <# banners> are the numbers of banners for which to resume the code. This is an optional parameter. 
          
          For example,
            $ python run.py --run_from_stage get_pages 500

        - To display help information:
            $ python run.py --help


-----------------------
Analyzing the Log Files
-----------------------

The intermediate log files are stored in the OUT_PATH directory and pertain to each stage of the code pipeline.
The code generates following log files:

        - "queryLog.txt" which contains banner to search query mappings. Format: 
            <banner-ID> : <query keywords> 

        - "urls.txt" which contains the list of all URLs obtained from the Google search against the queries.

        - "linksLog.txt" which contains URLs for the pages obtained from Google search against the queries. Format:
                "<banner-ID>": {
                        "query" : Query keywords for the banner
                        "links" : List of URLs obtained from the Google search against the query
                }

        - "derLog.txt" which contains the annotations extracted from the webpages. Format:
                "<banner-ID>": {
                        "query"         : Query keywords for the banner
                        "links"         : List of URLs/links obtained from the Google search
                        "annotations"   : List of the extracted annotations corresponding to each URL/link
                }

        - "intermediate.txt" which contains the annotation findings for URLs. Format:
                <URL> <Annotations>, <Vendor found? (True/False)>, <Product found? (True/False)>, <Both device type and vendor found? (True/False)>, <Device type, vendor, and product found? (True/False)>

        - "rulesLog.txt" which contains the list of generated rules. Format:
                "<banner-ID>": {
                        "query"         : Query keywords for the banner
                        "links"         : List of URLs/links obtained from the Google search against the query
                        "annotations"   : List of the extracted annotations corresponding to each URL/link
                        "rules"         : List of the generated rules corresponding to the banner
                }

        - "pipelineStats.txt" which contains the overall statistics of the code pipeline. Format:
                "BANNERS WITH NON-EMPTY QUERIES": Number of banners for which the code was able to obtain a non-empty query
                "AT LEAST ONE DEVICE": Number of banners for which the code was able to obtain only the device type information.
                "AT LEAST ONE VENDOR": Number of banners for which the code was able to obtain only the vendor information.
                "AT LEAST ONE PRODUCT": Number of banners for which the code was able to obtain only the product/model information.
                "AT LEAST ONE <DEVICE,VENDOR>": Number of banners for which the code was able to obtain both device type and vendor information.
                "AT LEAST ONE <DEVICE,VENDOR,PROD>": Number of banners for which the code was able to obtain device, vebdor, and product information.


--------------------
Analyzing the Rules
--------------------

The final rules are stored in the "rules.csv" file in the OUT_PATH directory. Format:
    <rule #>, <rule items>, <support level>, <confidence level>

To find precision and recall numbers for the rules, simply run the code as:
    $ python analyze.py

It will read the input banners file (located in config.BANNERS_FILE) and rules.csv file to perform analysis. The analysis results are saved in "analysis.txt" file in the config.OUT_PATH directory.