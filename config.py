import os

# NOTE: The default values contain the parameter values used in the submission
#
# Path to the input banners file
BANNERS_FILE = "../data/ferret_banners.json"

# Number of banners to process (if not all)
NUM_PROCESS_BANNERS = 129 

# Absolute Path to intermediate log files and final rules file
OUT_PATH = "/Users/testuser/out/"

# Log files
QUERY_LOG_FILE = os.path.join(OUT_PATH, "queryLog.txt")
LINKS_LOG_FILE = os.path.join(OUT_PATH, "linksLog.txt")
DER_LOG_FILE = os.path.join(OUT_PATH, "derLog.txt")
INTERMEDIATE_FILE = os.path.join(OUT_PATH, "intermediate.txt") 
URLS_FILE = os.path.join(OUT_PATH, "urls.txt") 
RULES_LOG_FILE = os.path.join(OUT_PATH, "rulesLog.txt")
RULES_FILE = os.path.join(OUT_PATH, "rules.csv")
STATS_FILE = os.path.join(OUT_PATH, "pipelineStats.txt")
CORRECT_RULES_FILE = os.path.join(OUT_PATH, "correctRules.txt")

# Pages folder; NOTE directory instead of file
PAGES_PATH = os.path.join(OUT_PATH, "pages/")

# ARE DEBUG LOG
ARE_DEBUG_LOG = os.path.join(OUT_PATH, "ARE.log")

# Google Custom Search API Parameters
# The following parameters must be filled by obtaining an API_key from:
# https://developers.google.com/custom-search/v1/overview 
# API_KEYS = [] # List of keys. The list can contain one item if you are using
                # one key
# CSE_ID = "" # string

UNLIMITED_QUOTA = False # If using billed version
QUOTA_PER_KEY = 100     

# Parameters to implement the 100 requests per second rate limit
SEARCH_API_BATCH_SIZE = 100 
SEARCH_API_WAIT_TIME = 100 #seconds

# Search Query Parameters
TOP_K_WORDS = 5

# Web Crawler Parameters
DOWNLOAD_TIMEOUT = 60 # seconds 
DOWNLOAD_MAXSIZE = 1000000 # bytes 
PDF_PAGES_TO_PROCESS = 5

# Annotation Finder Parameters
# Some pages contain content with no natural line breaks (for example, a .css
# file snippet), and the code ends up treating it as one big line with
# thousands of (meaningless) annotations. The following parameter restricts
# this    
MAX_ANNOTATIONS_PER_LINE = 500

# Apriori algorithm parameters
MIN_SUPPORT = 0.001
MIN_CONFIDENCE = 0.5

