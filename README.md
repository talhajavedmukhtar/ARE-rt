# ARE-rt

This code takes as input a banners dataset and generates rules for discovering and annotating IoT devices.

---------------
Pre-requisites
---------------

- Python3 version > 3.7

--------------
Setup
--------------
- Install the required dependencies using: pip3 install -r requirements.txt

- Rename "config_sample.py" to "config.py" and configure the following parameters:

        BANNERS_FILE                Path to the input banners file which contains the banners.
        NUM_PROCESS_BANNERS         Limit for number of banners to process (if not all)
        OUT_PATH                    Absolute Path to intermediate log files and final rules file
        API_KEYS                    List of Google Custom Search API Keys which can be obtained from:
                                    https://developers.google.com/custom-search/v1/overview 
        CSE_ID                      Custom Search Engine ID which can be obtained from: 
                                    https://cse.google.com/cse/all

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

## Paper Title
Using Application Layer Banner Data to automatically identify IoT devices

## Authors
Talha Javed Mukhtar, Muhammad Haseeb, Muhammad Abdullah, Mobin Javed


