""" Take a webpage text and find <device type, vendor, product> tuples in it """

import re
import string
import config
from bs4 import BeautifulSoup


class NameFinder():
    def __init__(self, pageText):
        dateTime = r'\d+[\/:\-]\d+[\/:\-\s]*[\dAaPpMn]*'
        self.pageText = re.sub(dateTime, '', pageText)
        self.idxtoLineNoMap = {}

    def createIdxtoLineNoMap(self, text):
        ''' 
        This function creates a dictionary that maps webpage text lines to their line number.
        :param text: A string containing webpage text
        :return: A dictionary that maps webage text lines to their line numbers
        '''
        lineStartIdxes = [m.start(0) + len(m.group(0))
                          for m in re.finditer(r"\. ", text)]
        prevIdx = 0
        lineNum = 0
        idxtoLineNoMap = dict()

        for idx in lineStartIdxes:
            for idx in range(prevIdx, idx):
                idxtoLineNoMap[idx] = lineNum
            prevIdx = idx
            lineNum += 1

        # Map entry for the last line
        for idx in range(prevIdx, len(text) + 1):
            idxtoLineNoMap[idx] = lineNum

        self.idxtoLineNoMap = idxtoLineNoMap

    def linefy(self, text):
        ''' 
        This function breaks down webpage text into a list of strings containing individual text lines.
        :param text: A string containing webpage content
        :return: the webpage text with newlines replaced by ". ", a list of strings containing individual webpage text lines
        '''
        text = text.replace(".\n", ". ")
        text = text.replace("\n", ". ")
        text = text.replace("\\n", ". ")
        self.createIdxtoLineNoMap(text)
        return text, text.split(". ")

    def findProducts(self, text):
        ''' 
        This function extracts product names from a line of webpage text.
        :param text: A string containing a line of webpage text.
        :return: A list of strings containing product names
        '''
        p = re.compile(
            r"\b[A-Za-z]+[-]?[A-Za-z]*[0-9]+[-]?[-]?[A-Za-z0-9]*\.?[0-9a-zA-Z]*\b")
        prods = list(set(p.findall(text)))
        foundProds = self.findItemsInText(text, prods)
        return foundProds

    def findItemsInText(self, text, items):
        ''' 
        This function extracts items from a line of webpage text.
        :param text: A string containing a line of webpage text.
        :return: A list of strings containing items
        '''
        found = []
        for item in items:
            if item in text:
                itemRegex = "\\b" + item + "\\b"
                found = found + [(item, m.start(0), self.idxtoLineNoMap[m.start(0)])
                                 for m in re.finditer(itemRegex, text)]
        return found

    def findAnnotations(
            self,
            linefiedData,
            devicesInText,
            vendorsInText,
            productsInText):
        ''' 
        This function extracts annotations from a webpage text.
        :param linefiedData: A list of strings containing individual lines of webpage text
        :param devicesInText: A list of strings containing device types
        :param vendorsInText: A list of strings containing vendor names
        :param productsInText: A list of strings containing product names
        :return: A list of strings containing annotations
        '''
        annotations = []
        lineToItems = {}

        for device in devicesInText:
            lineNo = device[2]

            if lineNo not in lineToItems.keys():
                lineToItems[lineNo] = {
                    "devices": [device], "vendors": [], "products": []}
            else:
                lineToItems[lineNo]["devices"].append(device)

        for vendor in vendorsInText:
            lineNo = vendor[2]

            if lineNo not in lineToItems.keys():
                lineToItems[lineNo] = {
                    "devices": [], "vendors": [vendor], "products": []}
            else:
                lineToItems[lineNo]["vendors"].append(vendor)

        for prod in productsInText:
            lineNo = prod[2]

            if lineNo not in lineToItems.keys():
                lineToItems[lineNo] = {
                    "devices": [], "vendors": [], "products": [prod]}
            else:
                lineToItems[lineNo]["products"].append(prod)

        for line, items in lineToItems.items():
            # filter lines which only have only entity type since they will
            # fail the local dependency check
            if sum([(len(eType) > 0) for eType in lineToItems[line].values()]) == 1:
                continue
            annotationsInLine = set()

            for device in items["devices"]:
                for vendor in items["vendors"]:
                    atLeastOneProd = False

                    for prod in items["products"]:
                        check1 = (vendor[1] < prod[1]) and (vendor[1] < device[1])
                        check2 = device[1] < prod[1]
                        check3 = (prod[1] - vendor[1] - len(vendor[0])) < 3

                        if check1 and (check2 or check3):
                            annotationsInLine.add(
                                (device[0], vendor[0], prod[0]))
                            atLeastOneProd = True

                    if not atLeastOneProd:
                        if vendor[1] < device[1]:
                            annotationsInLine.add(
                                (device[0], vendor[0], None))
        
            if len(annotationsInLine) <= config.MAX_ANNOTATIONS_PER_LINE: 
                annotations.extend(list(annotationsInLine))

        return annotations

    def extractInfo(self, devices, vendors):
        ''' 
        This function extracts annotations (device type, vendor, product) from webpage text by matching them
        with a pre-compiled list of device types and vendor names.
        :param devices: A pre-compiled list of device types
        :param vendors: A pre-compiled list of vendor name
        :return: list of strings containing annotations, and bools specifying if devices, vendors, 
                 products, both device and vendor, or all three are found from webpage text.
        '''
        joinedData, linefiedData = self.linefy(self.pageText.lower())
        devicesInText = self.findItemsInText(joinedData, devices)
        vendorsInText = self.findItemsInText(joinedData, vendors)
        productsInText = self.findProducts(joinedData)

        devicesFound = False
        if len(devicesInText) > 0:
            devicesFound = True

        vendorsFound = False
        if len(vendorsInText) > 0:
            vendorsFound = True

        productsFound = False
        if len(productsInText) > 0:
            productsFound = True

        annotations = self.findAnnotations(
            linefiedData, devicesInText, vendorsInText, productsInText)

        deviceTypeAndVendorFound = False
        if len(annotations) > 0:
            deviceTypeAndVendorFound = True

        deviceTypeVendorAndProductFound = False
        for annotation in annotations:
            if annotation[2] is not None:
                deviceTypeVendorAndProductFound = True
                break

        return annotations, devicesFound, vendorsFound, productsFound, deviceTypeAndVendorFound, deviceTypeVendorAndProductFound
