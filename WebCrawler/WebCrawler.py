import scrapy
import os
import sys
import re
import PyPDF2
from utils import cleanTags, isEmptyLine
import config
sys.path.append('../../')


class PageSpider(scrapy.Spider):
    name = "WebCrawler"

    def __init__(self, urlsFileName, outPath):
        self.urls = list()
        self.outPath = outPath
        urlsFile = open(urlsFileName)

        for line in urlsFile:
            self.urls.append(line.rstrip())

    def start_requests(self):
        for index, url in enumerate(self.urls):
            if url.endswith(".pdf"):
                request = scrapy.Request(url=url, callback=self.parsePDF)
            else:
                request = scrapy.Request(url=url, callback=self.parseHTML)
            request.meta["index"] = str(index)
            yield request

    def parsePDF(self, response):
        outFileName = response.meta.get("index")
        # temporarily save to disk for parsing
        with open(os.path.join(self.outPath, outFileName + ".pdf"), "wb") as f:
            f.write(response.body)
        pdfFileObj = open(
            os.path.join(
                self.outPath,
                outFileName +
                ".pdf"),
            'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        allText = ""
        # only process the first k pages
        for pageNum in range(0,
                             min(config.PDF_PAGES_TO_PROCESS,
                                 pdfReader.numPages)):
            pageObj = pdfReader.getPage(pageNum)
            allText += pageObj.extractText()
        with open(os.path.join(self.outPath, outFileName), "w") as f:
            f.write(allText)

    def parseHTML(self, response):
        outFileName = response.meta.get("index")
        scripts = [cleanTags(s.get()) for s in response.css('script')]
        styles = [cleanTags(s.get()) for s in response.css('style')]
        textElements = [i.get() for i in response.css('::text')]
        filteredText = [
            text for text in textElements if not isEmptyLine(text) and (
                text not in scripts) and (
                text not in styles)]

        with open(os.path.join(self.outPath, outFileName), "w", encoding="utf-8") as f:
            f.write("\n".join(filteredText))
