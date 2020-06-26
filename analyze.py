import json
import sys
import csv
import ast
import json
import config
import os

totalBanners = 0
equivalentDevTypes = {
    "nas": ["nvs"],
    "scada gateway": ["gateway"],
    "DSL modem": ["modem"],
    "cable modem": ["modem"],
    "network": ["router", "gateway", "access point", "switch", "switches"],
    "infrastructure router": ["router"],
    "DVR": ["video recorder", "video encoder"],
    "scada router": ["router"],
    "soho router": ["router"],
    "wireless modem": ["modem"],
    "DSL/cable modem": ["modem"],
    "laser printer": ["printer"],
    "Security Camera": ["camera", "ipcam", "netcam", "cam"],
    "Router/Gateway": ["router", "gateway"]
}


def listToString(s):
    '''
    This function lists to strings
    :param s: A list
    :return: A string
    '''
    str1 = ""
    for ele in s:
        str1 += ele
    return str1


def getRulesStats(rules, ruleNumToBannerMap):
    '''
    This function returns useful statistics for rules
    :param rules: A dictionary of rules - {rule#: rule}
    :return: A dictionary containing useful stats
    '''
    device = 0
    vendor = 0
    product = 0
    device_vendor = 0
    device_product = 0
    vendor_product = 0
    device_vendor_product = 0

    devices = set()
    vendors = set()
    products = set()

    deviceToBannerMap = dict()
    vendorToBannerMap = dict()
    productToBannerMap = dict()

    for ruleNum, rule in rules.items():
        banner = ruleNumToBannerMap[ruleNum]

        if "deviceType" in rule and "vendor" in rule and "product" in rule:
            device_vendor_product += 1
            devices.add(rule['deviceType'])
            vendors.add(rule['vendor'])
            products.add(rule['product'])
            deviceToBannerMap.setdefault(rule['deviceType'], set()).add(banner)
            vendorToBannerMap.setdefault(rule['vendor'], set()).add(banner)
            productToBannerMap.setdefault(rule['product'], set()).add(banner)

        elif "deviceType" in rule and "vendor" in rule:
            device_vendor += 1
            devices.add(rule['deviceType'])
            vendors.add(rule['vendor'])
            deviceToBannerMap.setdefault(rule['deviceType'], set()).add(banner)
            vendorToBannerMap.setdefault(rule['vendor'], set()).add(banner)

        elif "deviceType" in rule and "product" in rule:
            device_product += 1
            devices.add(rule['deviceType'])
            products.add(rule['product'])
            deviceToBannerMap.setdefault(rule['deviceType'], set()).add(banner)
            productToBannerMap.setdefault(rule['product'], set()).add(banner)

        elif "vendor" in rule and "product" in rule:
            vendor_product += 1
            vendors.add(rule['vendor'])
            products.add(rule['product'])
            vendorToBannerMap.setdefault(rule['vendor'], set()).add(banner)
            productToBannerMap.setdefault(rule['product'], set()).add(banner)

        elif "deviceType" in rule:
            device += 1
            devices.add(rule["deviceType"])
            deviceToBannerMap.setdefault(rule['deviceType'], set()).add(banner)

        elif "vendor" in rule:
            vendor += 1
            vendors.add(rule['vendor'])
            vendorToBannerMap.setdefault(rule['vendor'], set()).add(banner)

        elif "product" in rule:
            product += 1
            products.add(rule['product'])
            productToBannerMap.setdefault(rule['product'], set()).add(banner)

    for dev, banners in deviceToBannerMap.items():
        deviceToBannerMap[dev] = len(banners)
    deviceToBannerMap = {
        k: v for k,
        v in sorted(
            deviceToBannerMap.items(),
            key=lambda item: item[1],
            reverse=True)}

    for ven, banners in vendorToBannerMap.items():
        vendorToBannerMap[ven] = len(banners)
    vendorToBannerMap = {
        k: v for k,
        v in sorted(
            vendorToBannerMap.items(),
            key=lambda item: item[1],
            reverse=True)}

    for prod, banners in productToBannerMap.items():
        productToBannerMap[prod] = len(banners)
    productToBannerMap = {
        k: v for k,
        v in sorted(
            productToBannerMap.items(),
            key=lambda item: item[1],
            reverse=True)}

    stats = {
        "<devices>": device,
        "<vendors>": vendor,
        "<products>": product,
        "<devices, vendor>": device_vendor,
        "<devices, product>": device_product,
        "<vendors, products>": vendor_product,
        "<device, vendor, product>": device_vendor_product,
        "<devices list>": deviceToBannerMap,
        "<vendors list>": vendorToBannerMap,
        "<products list>": productToBannerMap}

    return stats


def createBannerToLabelsMap(inputDataset):
    '''
    This function creates a dictionary that maps banners to their labels for ground truth
    :return: A dictionary that maps banner to their labels.
    '''
    global totalBanners

    # only consider those banners which generated a non-empty query
    queryLog = json.load(open(config.QUERY_LOG_FILE, encoding="utf-8"))
    for bannerID, query in queryLog.items():
        if query:
            totalBanners += 1

    bannerToLabelsMap = dict()
    for bannerID, item in inputDataset.items():
        deviceTypes = []
        vendors = []
        products = []
        banner = item["banner"]

        for _, field in item.items():
            # All labels (vendor, product, deviceTypes) must be list type
            for element in field:

                if "label" in element:
                    label = element["label"]
                else:
                    continue

                if "deviceTypes" in label:
                    if label["deviceTypes"]:
                        deviceTypes.extend(label["deviceTypes"])

                if "vendor" in label:
                    if label["vendor"]:
                        vendors.extend(label["vendor"])

                if "product" in label:
                    if label["product"]:
                        products.extend(label["product"])

        bannerToLabelsMap[banner] = {
            "deviceTypes": deviceTypes,
            "vendors": vendors,
            "products": products,
            "bannerID": bannerID}

    return bannerToLabelsMap


def checkExists(bannerText, deviceType=None, vendor=None, product=None):
    '''
    This function checks if device labels exist in groundtruth
    :param bannerText: A string containing banner text
    :param deviceType: A string containing device type to check
    :param vendor: A string containing vendor name type to check
    :param product: A string containing product name type to check
    :return: Returns True/False if device labels exists in groundtruth
    '''
    global bannerToLabelsMap
    banner = bannerToLabelsMap[bannerText]

    devicesTypesGT = banner["deviceTypes"]
    vendorsGT = banner["vendors"]
    productsGT = banner["products"]

    if deviceType and devicesTypesGT:
        totalDeviceTypesGT = devicesTypesGT
        deviceType = deviceType.lower().strip()

        for dev in devicesTypesGT:
            if dev in equivalentDevTypes:
                totalDeviceTypesGT.extend(equivalentDevTypes[dev])

        for dev in totalDeviceTypesGT:
            dev = dev.lower().strip()
            if dev != "" and (deviceType in dev or dev in deviceType):
                return True

        return False

    if vendor and vendorsGT:
        for v in vendorsGT:
            vendor = vendor.lower().strip()
            v = v.lower().strip()
            if v != "" and vendor in v or v in vendor:
                return True
        return False

    if product and productsGT:
        for p in productsGT:
            product = product.lower().strip()
            p = p.lower().strip()
            if p != "" and (product in p or p in product):
                return True

        return False

    return True


def prettyWrite(rulesStats):
    '''
    This function writes a given dictionary in a pretty format in "analysis.txt" file
    :param ruleStats: A dictionary
    :return: None. Dictionary contents are written in "analysis.txt" file in pretty format.
    '''
    for title, stat in rulesStats.items():
        analysisFile.write(str(title) + ": " + str(stat) + "\n")


def writeToAnalysis(
        totalRules,
        truePositive,
        falsePositive,
        bannersInRules,
        totalBanners,
        allRules,
        correctRules,
        ruleNumToBannerMap,
        filtered):
    '''
    This function writes to "analysis.txt" file
    :param truePositive: A dictionary of rules - {rule#: rule}
    :param truePositive: An int containing # of true positives in rules
    :param falsePositive: An int containing # of false positives in rules
    :param bannersInRules: A set containing all banners in rules
    :param totalBanners: An int containing total number of banners in dataset
    :param allRules: A dictionary containing all rules - {rule#: rule}
    :param correctRuls: A dictionary containing only the correct rules - {rule#: rule}
    :param filtered: A bool indicating if this function is called for rules with per banner filtering
    :return: A dictionary containing useful stats
    '''
    if filtered:
        string = """
=======================================
With highest confidence per banner filtering:
========================================
\n\n"""
    else:
        string = """
=======================================
Without highest confidence per banner filtering:
========================================
\n\n"""
    analysisFile.write(string)

    precision = str(
        round((truePositive / (truePositive + falsePositive)) * 100, 2)) + "%"

    coverage = str(
        round(
            ((len(bannersInRules)) / totalBanners) * 100,
            2)) + "%"

    analysis = {
        "Total Rules": totalRules,
        "True Positive": truePositive,
        "False Positive": falsePositive,
        "Total Banners": totalBanners,
        "Banners with Rules": len(bannersInRules),
        "Precision": precision,
        "Coverage": coverage}
    prettyWrite(analysis)

    analysisFile.write("\n\n\nRules Stats:\n")
    rulesStats = getRulesStats(allRules, ruleNumToBannerMap)
    prettyWrite(rulesStats)

    analysisFile.write("\n\n\nCorrect Rules Stats:\n")
    rulesStats = getRulesStats(correctRules, ruleNumToBannerMap)
    prettyWrite(rulesStats)

    analysisFile.write("\n" * 4)


def createLabeledFilteredRules(bannerToRuleLinesMap, ruleNumToBannerMap):
    # Create "rules.filtered.labeled.csv" file
    rulesLabeledFilteredFile = open(
        os.path.join(
            config.OUT_PATH,
            "rules.filtered.labeled.csv"),
        "w",
        encoding="utf-8")

    totalRules = 0
    truePositive = 0
    falsePositive = 0
    bannersInRules = set()

    correctRules = dict()
    allRules = dict()

    for banner, rulesLines in bannerToRuleLinesMap.items():
        bannersInRules.add(bannerToLabelsMap[banner]["bannerID"])

        for rulesLine in rulesLines:

            for l in csv.reader(
                [rulesLine],
                quotechar='"',
                delimiter=',',
                quoting=csv.QUOTE_ALL,
                    skipinitialspace=True):
                csvLine = l

            ruleNum = rulesLine.split(",")[0]
            rule = ast.literal_eval(csvLine[1])
            allRules[ruleNum] = rule
            totalRules += 1
            rulesLabeledFilteredFile.write(rulesLine)

            if not ruleNumToFlagMap[ruleNum]:
                falsePositive += 1
            else:
                truePositive += 1
                correctRules[ruleNum] = rule

    writeToAnalysis(
        totalRules,
        truePositive,
        falsePositive,
        bannersInRules,
        totalBanners,
        allRules,
        correctRules,
        ruleNumToBannerMap,
        filtered=True)


if __name__ == "__main__":
    inputDataset = json.load(open(config.BANNERS_FILE, encoding="utf8"))
    rulesFile = open(config.RULES_FILE, encoding="utf8")
    rulesLabeledFile = open(
        os.path.join(
            config.OUT_PATH,
            "rules.labeled.csv"),
        "w",
        encoding="utf-8")
    rulesLabeledFile.write(",Items,Support,Confidence\n")
    analysisFile = open(os.path.join(config.OUT_PATH, "analysis.txt"), "w")
    next(rulesFile)
    rulesLines = rulesFile.readlines()

    bannerToLabelsMap = createBannerToLabelsMap(inputDataset)
    ruleNumToBannerMap = dict()
    totalRules = 0
    bannersInRules = set()
    ruleNumToFlagMap = dict()
    correctRules = dict()
    allRules = dict()
    # bannerToRuleLinesMap keeps rules with highest confidence against banner
    bannerToRuleLinesMap = dict()

    for l in csv.reader(
            rulesLines,
            quotechar='"',
            delimiter=',',
            quoting=csv.QUOTE_ALL,
            skipinitialspace=True):

        totalRules += 1
        rule = ast.literal_eval(l[1])
        ruleNum = l[0]
        ruleLine = rulesLines[int(ruleNum)]
        banner = rule["banner"]
        bannersInRules.add(bannerToLabelsMap[banner]["bannerID"])
        confidence = l[3]
        ruleNumToBannerMap[ruleNum] = banner

        if "deviceType" in rule:
            deviceType = rule["deviceType"]
            if not checkExists(banner, deviceType=deviceType):
                ruleNumToFlagMap[ruleNum] = False

        if "vendor" in rule:
            vendor = rule["vendor"]
            if not checkExists(banner, vendor=vendor):
                ruleNumToFlagMap[ruleNum] = False

        if "product" in rule:
            product = rule["product"]
            if not checkExists(banner, product=product):
                ruleNumToFlagMap[ruleNum] = False

        if ruleNum not in ruleNumToFlagMap:
            ruleNumToFlagMap[ruleNum] = True
            correctRules[ruleNum] = rule

        allRules[ruleNum] = rule
        ruleLabel = ruleNumToFlagMap[str(ruleNum)]
        labeledRuleLine = ruleLine.rstrip() + "," + str(ruleLabel) + "\n"

        rulesLabeledFile.write(labeledRuleLine)

        if banner not in bannerToRuleLinesMap:
            bannerToRuleLinesMap.setdefault(banner, []).append(labeledRuleLine)

        for rLine in bannerToRuleLinesMap[banner]:

            if rLine == labeledRuleLine:
                break

            currentConfidence = rLine.split(",")[-2]
            if float(confidence) > float(currentConfidence):
                bannerToRuleLinesMap[banner] = [labeledRuleLine]
                break
            if float(currentConfidence) == float(confidence):
                bannerToRuleLinesMap.setdefault(
                    banner, []).append(labeledRuleLine)
                break

    truePositive = 0
    falsePositive = 0

    for ruleNum, flag in ruleNumToFlagMap.items():
        if flag:
            truePositive += 1
        else:
            falsePositive += 1

    writeToAnalysis(
        totalRules,
        truePositive,
        falsePositive,
        bannersInRules,
        totalBanners,
        allRules,
        correctRules,
        ruleNumToBannerMap,
        filtered=False)

    createLabeledFilteredRules(bannerToRuleLinesMap, ruleNumToBannerMap)
