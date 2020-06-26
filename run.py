from QueryGenerator import QueryGenerator
from LinkFetcher import LinkFetcher
from NameFinder import NameFinder
from RuleGenerator import RuleGenerator
from staticLists.devices import devices
from staticLists.vendors import vendors
from utils import *
import json
import logging
import config
import threading
import time
import concurrent.futures
import os
import signal
import sys
from datetime import datetime
import random
numOfBanners = config.NUM_PROCESS_BANNERS
stagesList = [
    "get_queries",
    "get_links",
    "get_pages",
    "get_annotations",
    "get_rules"]


def parseArguments(args):
    '''
    This function parses command-line arguments.
    :param args: A list of command-line arguments
    :return: None. Pipeline stages and number of banners are selected based on command-line arguments (if supplied).
    '''
    if not args:
        return
    global stagesList
    global numOfBanners
    helpMsg = """
    Usage: python run.py [options]
    --run_from_stage <stage> <# banners(optional)>   Provide the stage and # of banners to resume from amongst
                                                    'get_queries', 'get_links','get_pages','get_annotations'.

    --help                  Display this help information

    """

    if args[0] == "--help" and len(args) == 1:
        print(helpMsg)
        stagesList = []
        exit()
    elif args[0] != "--run_from_stage" or len(args) < 2 or len(args) > 3 or args[1] not in stagesList:
        print(helpMsg)
        raise Exception('Unknown command line argument.')

    if len(args) == 3:
        numOfBanners = args[2]

    startStage = args[1]

    if startStage != "get_queries":
        stagesList.remove("get_queries")
    else:
        return
    if startStage != "get_links":
        stagesList.remove("get_links")
    else:
        return
    if startStage != "get_pages":
        stagesList.remove("get_pages")
    else:
        return
    if startStage != "get_annotations":
        stagesList.remove("get_annotations")
    else:
        return


def timeout(signum, frame):
    raise Exception('Timed out.')


def getURLs(query, key, urlToQueryMap):
    '''
    This function returns Google search result URLs against a query.
    :param query: A list containing query keywords
    :param urlToQueryMap: A dictionary that maps URLs to their queries
    :return: A list of URLs
    '''
    links = []
    results = LinkFetcher().getUrlsGoogle(query, key)
    try:
        if "items" in results:
            for item in results["items"]:
                link = item["link"]
                links.append(link)
                if link in urlToQueryMap:
                    urlToQueryMap[link].append(query)
                else:
                    urlToQueryMap[link] = [query]
    except Exception as e:
        logging.exception(
            "Exception occurred while trying to fetch links for query " +
            str(query) +
            ", returned results: " +
            str(results) +
            ", Exception: " +
            str(e))

    return links


def logQueries(queries):
    '''
    This function generates "queryLog" intermediate logs.
    :param allQueries: A list of all queries
    :return: A dictionary of "queryLog"(see README for format). "queryLog.txt" is saved in config.OUT_PATH directory
    '''
    log = {}
    queryGenLog = open(config.QUERY_LOG_FILE, "w")
    for i, query in enumerate(queries):
        log[i + 1] = query
    queryGenLog.write(json.dumps(log, indent=4))
    queryGenLog.close()
    return log


def logLinks(urlToQueryMap, allQueries):
    '''
    This function generates "linksLog" intermediate logs.
    :param urlToQueryMap: A dictionary that maps URLs to their queries
    :param allQueries: A list of all queries
    :return: A dictionary of "linksLog"(see README for format). "linksLog.txt" is saved in config.OUT_PATH directory
    '''
    log = {}
    for i, query in enumerate(allQueries):
        log[i + 1] = {"query": query, "links": []}

    linksLog = open(config.LINKS_LOG_FILE, "w")
    for url, queries in urlToQueryMap.items():
        for query in queries:
            indices = [
                i + 1 for i,
                val in enumerate(allQueries) if val == query]
            for index in indices:
                log[index]["links"].append(url)

    linksLog.write(json.dumps(log, indent=4))
    linksLog.close()
    return log


def logDER(logSoFar, bannerToAnnotationsMap, allBanners):
    '''
    This function generates "derLog" intermediate logs.
    :param logSoFar: A dictionary of "linksLog" intermediate logs from get_links stage
    :param bannerToAnnotationsMap: A dictionary that maps banners to their annotations
    :param allBanners: A list of all banners
    :return: A dictionary of "derLog"(see README for format). "derLog.txt" is saved in config.OUT_PATH directory
    '''
    log = logSoFar
    allBanners = [x["banner"] for x in allBanners]
    for banner, annotations in bannerToAnnotationsMap.items():
        index = allBanners.index(banner)
        log[str(index + 1)]["annotations"] = annotations
    derLog = open(config.DER_LOG_FILE, "w")
    derLog.write(json.dumps(log, indent=4))
    return log


def logRules(logSoFar, rules, allBanners):
    '''
    This function generates "rulesLog" intermediate logs.
    :param logSoFar: A dictionary of "derLog" intermediate logs from get_annotations stage
    :param rules: A list of all rules
    :param allBanners: A list of all banners
    :return: None. "rulesLog.txt" is saved in config.OUT_PATH directory
    '''
    log = logSoFar
    seenBanners = []
    allBanners = [x["banner"] for x in allBanners]
    for i, obj in log.items():
        log[i]["rules"] = []

    for rule in rules:
        banner = rule["banner"]
        if banner not in seenBanners:
            seenBanners.append(banner)
        index = allBanners.index(banner)
        log[str(index + 1)]["rules"].append(rule)

    ruleLog = open(config.RULES_LOG_FILE, "w")
    ruleLog.write(json.dumps(log, indent=4))
    statsFile = open(config.STATS_FILE, "a")
    statsFile.write("AT LEAST ONE RULE: " + str(len(seenBanners)) + "\n")


def logStats(bannerToStatsMap, bannerToQueryMap):
    '''
    This function generates "pipelineStats" log file.
    :param bannerToStatsMap: A dictionary that maps banners to their annotation statistics
    :param bannerToQueryMap: A dictionary that maps banners to their queries
    :return: None. "pipelineStats.txt" is saved in config.OUT_PATH directory
    '''
    bannersWithSearchResults = 0
    linksLog = json.load(open(config.LINKS_LOG_FILE))
    for bannerID, linksDict in linksLog.items():
        links = linksDict["links"]
        if len(links) > 0:
            bannersWithSearchResults += 1

    statsFile = open(config.STATS_FILE, "w")
    numD = 0
    numV = 0
    numP = 0
    numDV = 0
    numDVP = 0
    numNonEmpty = 0

    for banner, query in bannerToQueryMap.items():
        query = bannerToQueryMap[banner]
        if query != "":
            numNonEmpty += 1

    for banner, stats in bannerToStatsMap.items():
        if stats[0]:
            numD += 1
        if stats[1]:
            numV += 1
        if stats[2]:
            numP += 1
        if stats[3]:
            numDV += 1
        if stats[4]:
            numDVP += 1

    statsFile.write(
        "BANNERS WITH NON-EMPTY QUERIES: " +
        str(numNonEmpty) +
        "\n")
    statsFile.write(
        "BANNERS WITH AT LEAST ONE SEARCH RESULT: " +
        str(bannersWithSearchResults) +
        "\n")
    statsFile.write("AT LEAST ONE DEVICE: " + str(numD) + "\n")
    statsFile.write("AT LEAST ONE VENDOR: " + str(numV) + "\n")
    statsFile.write("AT LEAST ONE PRODUCT: " + str(numP) + "\n")
    statsFile.write("AT LEAST ONE <DEVICE,VENDOR>: " + str(numDV) + "\n")
    statsFile.write("AT LEAST ONE <DEVICE,VENDOR,PROD>: " + str(numDVP) + "\n")
    statsFile.close()


def getBanners(numBannersArg=None):
    '''
    This function reads banners from the banners file.
    :param numBannersArg: Number of banners to read
    :return: A list of all banners
    '''
    data = json.load(open(config.BANNERS_FILE)) 

    global numOfBanners
    if numBannersArg:
        numOfBanners = numBannersArg

    allBanners = []
    done = 0
    for key, obj in data.items():
        allBanners.append(obj)
        done += 1
        if done == int(numOfBanners):
            break

    return allBanners


def getQueriesFromLogs(allBanners):
    '''
    This function obtains search queries directly from existing "queryLog".
    :param allBanners: A list of all banners
    :return: List of all queries, dictionary that maps banners to thier queries,
             and dictionary of that maps queries to their banners
    '''
    queryLog = json.load(open(config.QUERY_LOG_FILE))
    bannerToQueryMap = dict()
    queryToBannerMap = dict()
    bannerIndex = 1

    for _, query in queryLog.items():
        bannerToQueryMap[allBanners[bannerIndex - 1]["banner"]] = query
        if bannerIndex == int(numOfBanners):
            break
        bannerIndex += 1

    for banner, query in bannerToQueryMap.items():
        if query not in queryToBannerMap.keys():
            queryToBannerMap[query] = [banner]
        else:
            queryToBannerMap[query].append(banner)

    allQueries = [query for banner, query in bannerToQueryMap.items()]
    return allQueries, bannerToQueryMap, queryToBannerMap


def getQueries(allBanners):
    '''
    This function extracts search queries from the banners.
    :param allBanners: a list of all banners
    :return: List of all queries, dictionary that maps banners to their queries,
             and dictionary that maps queries to their to banners
    '''
    if os.path.exists(config.QUERY_LOG_FILE):
        print("queryLog already exists.")
        getQueriesFromLogs(allBanners)
        allQueries, bannerToQueryMap, queryToBannerMap = getQueriesFromLogs(
            allBanners)
        t1 = datetime.now()
        print("Got queries!", len(allQueries), t1)
        return allQueries, bannerToQueryMap, queryToBannerMap

    QGen = QueryGenerator()
    allQueries = []
    bannerToQueryMap = QGen.generateForAll(allBanners)
    queryToBannerMap = {}

    for banner, query in bannerToQueryMap.items():
        if query not in queryToBannerMap.keys():
            queryToBannerMap[query] = [banner]
        else:
            queryToBannerMap[query].append(banner)

    allQueries = [query for banner, query in bannerToQueryMap.items()]
    t1 = datetime.now()
    print("Got queries!", len(allQueries), t1)
    logQueries(allQueries)
    return allQueries, bannerToQueryMap, queryToBannerMap


def getLinks(allQueries):
    '''
    This function obtains URLs for the search queries.
    :param allQueries: A list of all querries
    :return: None. A list of all URLs is saved in "urls.txt" file in config.OUT_PATH folder
    '''
    urlToQueryMap = {}
    allUrls = []
    uniqueQueries = list(set(allQueries))
    print("Total unique queries", len(uniqueQueries))

    if config.UNLIMITED_QUOTA:
        queryTasks = [uniqueQueries]
    else:
        if (len(config.API_KEYS) * config.QUOTA_PER_KEY) < len(uniqueQueries):
            raise Exception("Not enough key quota to get links for queries")
        queryTasks = [uniqueQueries[x:x + config.QUOTA_PER_KEY]
                      for x in range(0, len(uniqueQueries), config.QUOTA_PER_KEY)]

    for taskNum, task in enumerate(queryTasks):
        print("Getting links for task number", taskNum, "with", len(task),
              "queries")
        added = 0
        for query in task:
            if added == config.SEARCH_API_BATCH_SIZE:
                added = 0
                time.sleep(config.SEARCH_API_WAIT_TIME)
            urls = getURLs(query, config.API_KEYS[taskNum], urlToQueryMap)
            added += 1
            allUrls += urls

    allUrls = list(set(allUrls))

    with open(config.URLS_FILE, "w") as urlsFile:
        for url in allUrls:
            urlsFile.write(url + "\n")

    t2 = datetime.now()
    print("Got links!", len(allUrls), t2)
    log = logLinks(urlToQueryMap, allQueries)


def getPages():
    '''
    This function reads URLs and crawls webpages.
    :return: None. Crawled pages are saved in config.OUT_PATH folder
    '''
    if not os.path.exists(config.PAGES_PATH):
        os.makedirs(config.PAGES_PATH)
    cmd = "scrapy crawl WebCrawler -s LOG_ENABLED=False --logfile " + config.ARE_DEBUG_LOG + " -a urlsFileName=" + \
        config.URLS_FILE + " -a outPath=" + config.PAGES_PATH
    logging.info(cmd)
    os.system(cmd)
    t3 = datetime.now()
    print("Got pages!", t3)


def getAnnotations(
        allBanners,
        allQueries,
        bannerToQueryMap,
        queryToBannerMap):
    '''
    This function generates annotations.
    :param allBanners: a list of all banners
    :param allQueries: a list of all queries
    :param bannerToQueryMap: a dictionary that maps banners to their queries
    :param queryToBannerMap: a dictionary that maps queries to their banners
    :return: Dictionary that maps banners to their annotations, and dictionary of "DERlogs" intermediate logs
    '''
    urls = []
    urlsFile = open(config.URLS_FILE)
    for line in urlsFile:
        urls.append(line.strip("\n").strip(" "))

    urlToQueryMap = {}
    linksLog = json.load(open(config.LINKS_LOG_FILE))

    done = 0
    for i, obj in linksLog.items():
        query = obj["query"]
        links = obj["links"]

        for link in links:
            if link not in urlToQueryMap.keys():
                urlToQueryMap[link] = [query]
            else:
                urlToQueryMap[link].append(query)

        done += 1
        if done == int(numOfBanners):
            break

    urlToAnnotationsFile = open(config.INTERMEDIATE_FILE, "w")
    urlToAnnotationsFile.write("")
    urlToAnnotationsFile.close()
    urlToAnnotationsFile = open(config.INTERMEDIATE_FILE, "a")

    for i, url in enumerate(urls):
        if url not in urlToQueryMap.keys():
            continue
        try:
            page = open(config.PAGES_PATH + str(i), "rb").read()
            page = page.decode('utf-8')
            url = urls[i]
            annotations, dF, vF, pF, dVF, dVPF = NameFinder(
                page).extractInfo(devices, vendors)
            annotations = sorted(annotations, key=lambda x: (x[2] is None, x))
            urlToAnnotationsFile.write(
                url.strip("\n").strip(" ") +
                " ::: " +
                str(annotations) +
                " ::: " +
                str(dF) +
                " ::: " +
                str(vF) +
                " ::: " +
                str(pF) +
                " ::: " +
                str(dVF) +
                " ::: " +
                str(dVPF) +
                "\n")

        except Exception as e:
            logging.exception(
                "Exception occured during getAnnotations stage while processing page" +
                str(i) +
                ": " +
                str(e))

    urlToAnnotationsFile.close()
    urlToAnnotationsFile = open(config.INTERMEDIATE_FILE)
    bannerToAnnotationsMap = {}
    bannerToStatsMap = {}

    for line in urlToAnnotationsFile:
        url = line.split(" ::: ")[0]
        annotations = eval(line.split(" ::: ")[1])
        anyDeviceType = eval(line.split(" ::: ")[2])
        anyVendor = eval(line.split(" ::: ")[3])
        anyProduct = eval(line.split(" ::: ")[4])
        anyDeviceTypeAndVendor = eval(line.split(" ::: ")[5])
        anyDeviceTypeProdAndVendor = eval(line.split(" ::: ")[6])
        queries = urlToQueryMap[url]

        for query in queries:
            banners = queryToBannerMap[query]
            for banner in banners:
                if banner not in bannerToAnnotationsMap.keys():
                    bannerToAnnotationsMap[banner] = annotations
                else:
                    annotationsToAdd = list(
                        set(bannerToAnnotationsMap[banner] + annotations))
                    annotationsToAdd = sorted(
                        annotationsToAdd, key=lambda x: (
                            x[2] is None, x))
                    bannerToAnnotationsMap[banner] = list(
                        set(bannerToAnnotationsMap[banner] + annotations))

                if banner not in bannerToStatsMap.keys():
                    bannerToStatsMap[banner] = [
                        anyDeviceType,
                        anyVendor,
                        anyProduct,
                        anyDeviceTypeAndVendor,
                        anyDeviceTypeProdAndVendor]
                else:
                    oldStats = bannerToStatsMap[banner]
                    bannerToStatsMap[banner] = [
                        oldStats[0] or anyDeviceType,
                        oldStats[1] or anyVendor,
                        oldStats[2] or anyProduct,
                        oldStats[3] or anyDeviceTypeAndVendor,
                        oldStats[4] or anyDeviceTypeProdAndVendor]

    t4 = datetime.now()
    print("Got annotations!", t4)
    linksLog = json.load(open(config.LINKS_LOG_FILE))
    log = logDER(linksLog, bannerToAnnotationsMap, allBanners)
    logStats(bannerToStatsMap, bannerToQueryMap)
    return bannerToAnnotationsMap, log


def getRules(allBanners, bannerToAnnotationsMap, log):
    '''
    This function generates rules from transactions.
    :param allBanners: A list of all banners
    :param bannerToAnnotationsMap: A dictionary that maps banners to their annotations
    :param log: A dictionary of "derLog" intermediate logs generated by get_annotations stage
    :return: None. "rules.csv" file is saved in config.OUT_PATH folder
    '''
    transactions = makeAllTransactions(bannerToAnnotationsMap)
    rules = RuleGenerator(transactions).generate()
    t5 = datetime.now()
    print("Got rules!", t5)
    logRules(log, rules, allBanners)


if __name__ == "__main__":
    if not os.path.exists(config.OUT_PATH):
        os.makedirs(config.OUT_PATH)
    logging.basicConfig(
        filename=config.ARE_DEBUG_LOG,
        filemode='w',
        format='%(asctime)s %(levelname)s:%(message)s',
        level=logging.DEBUG)
    logging.info('Started')
    parseArguments(sys.argv[1:])
    print("Num of Banners=", numOfBanners)
    allBanners = getBanners()
    allQueries, bannerToQueryMap, queryToBannerMap = getQueries(allBanners)

    if "get_links" in stagesList:
        getLinks(allQueries)
    if "get_pages" in stagesList:
        getPages()
    if "get_annotations" in stagesList:
        bannerToAnnotationsMap, log = getAnnotations(
            allBanners, allQueries, bannerToQueryMap, queryToBannerMap)

    getRules(allBanners, bannerToAnnotationsMap, log)
