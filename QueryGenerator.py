""" Take a banner and generate all possible queries from it """

from staticLists.devices import devices
from staticLists.vendors import vendors
import re
import enchant
import random
import json
import functools
import config
from bs4 import BeautifulSoup
from sklearn.feature_extraction import stop_words
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import logging


class QueryGenerator():
    def __init__(self):
        self.wordsToNotDiscard = []

        for device in devices:
            words = device.split(" ")
            for word in words:
                if word not in self.wordsToNotDiscard:
                    self.wordsToNotDiscard.append(word)

        for vendor in vendors:
            words = vendor.split(" ")
            for word in words:
                if word not in self.wordsToNotDiscard:
                    self.wordsToNotDiscard.append(word)

    def refineFTP(self, text):
        '''
        This function refines FTP banner text.
        :param text: A string of banner text
        :return: A string of refined banner text
        '''
        # keywords for common computer ftp softwares as per the original paper
        keywords = [
            "filezilla",
            "serv-u"
        ]
        """
        Do not process the banner if the FTP banner contains these keywords
        """
        if any([keyword in text for keyword in keywords]):
            return ""

        return text

    def refineHTTP(self, text):
        '''
        This function refines HTTP banner text.
        :param text: A string of banner text
        :return: A string of refined banner text
        '''
        HTTPNonErrorCodes = [
            "http/",
            "100 Continue",
            "101 Switching Protocols",
            "200 OK",
            "201 Created",
            "202 Accepted",
            "203 Non-authoritative information",
            "204 no content",
            "205 reset content",
            "206 partial content",
            "300 multiple choices",
            "301 moved permanently",
            "302 found",
            "303 see other",
            "304 not modified",
            "305 use proxy",
            "306 (unused)",
            "307 temporary redirect"]

        HTTPErrorCodes = [
            "400 bad request",
            "401 unauthorized",
            "402 payment required",
            "403 forbidden",
            "404 not found",
            "405 method not allowed",
            "406 not acceptable",
            "407 proxy authentication required",
            "408 request timeout",
            "409 conflict",
            "410 gone",
            "411 length required",
            "412 precondition failed",
            "413 request entity too large",
            "414 request-uri too long",
            "415 unsupported media type",
            "416 request range not satisfiable",
            "417 expectation failed",
            "500 internet server error",
            "501 not implemented",
            "502 bad gateway",
            "503 service unavailable",
            "504 gateway timeout",
            "505 http version not supported"]
        # keywords for common heavyweight webservers
        heavyWebservers = [
            "apache",
            "iis",
            "nginx"]

        """
        Do not process the banner if the HTTP response is an error
        """
        if any([errorCode in text for errorCode in HTTPErrorCodes]):
            return ""

        """
        Do not process the banner if it contains heavyweight webservers
        """
        if any([webserver in text for webserver in heavyWebservers]):
            return ""

        for code in HTTPNonErrorCodes:
            text.replace(code.lower(), "")

        patScript = r"(?is)<script[^>]*>(.*?)</script>"
        text = re.sub(patScript, "", text)

        patStyle = r"(?is)<style[^>]*>(.*?)</style>"
        text = re.sub(patStyle, "", text)

        patLinks = r'^https?:\/\/.*[\r\n]*'
        text = re.sub(patLinks, "", text)

        patLinks = r'^http?:\/\/.*[\r\n]*'
        text = re.sub(patLinks, "", text)

        reg = re.compile('<[^<]+?>')
        text = re.sub(reg, '', text)

        dateTime = r'\d+[\/:\-]\d+[\/:\-\s]*[\dAaPpMn]*'
        text = re.sub(dateTime, '', text)

        soup = BeautifulSoup(text, 'html.parser')
        text = soup.text

        return text

    def refineUPNP(self, text):
        '''
        This function refines UPNP banner text.
        :param text: A string of banner text
        :return: a string of refined banner text
        '''
        # remove uuid
        UUIDRemovedBanner = re.sub(
            r'\b[0-9a-z]{8}\b-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-\b[0-9a-z]{12}\b',
            "",
            text)

        # remove date
        splitted = UUIDRemovedBanner.split("\r")
        dateRemovedBanner = []
        for word in splitted:
            loweredWord = word.lower()
            if "date:" not in loweredWord and "location:" not in loweredWord:
                dateRemovedBanner.append(word)

        # convert to string
        refinedText = ""
        for ele in dateRemovedBanner:
            refinedText = refinedText + "\r\n" + ele

        return refinedText

    def refineTELNET(self, text):
        '''
        This function refines Telnet banner text.
        :param text: A string of banner text
        :return: a string of refined banner text
        '''
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        text = text.rstrip('\0')
        return text

    def trim(self, word):
        '''
        This function removes special characters from a string.
        :param word: A string
        :return: A string with special characters removed
        '''
        if word == "":
            return word

        removeFirst = False
        removeLast = False

        extra = ["(", ")", "{", "}", "[", "]", "!", "\"", "'", ",",
                 ":", "\\n", "\n", "\\r", "\r", "\\t", "\t", ".", " "]

        for ele in extra:
            if word[0] is ele:
                removeFirst = True
            if word[len(word) - 1] is ele:
                removeLast = True

        if removeFirst:
            word = word[1:]
        if removeLast:
            word = word[:-1]

        return word

    def removeEscapeChars(self, text):
        '''
        This function removes escape characters from a string.
        :param word: A string
        :return: A string with escape characters removed
        '''
        text = text.replace("\n", " ")
        text = text.replace("\t", " ")
        return text

    def removeStopWords(self, text):
        '''
        This function removes stop words from a string.
        :param word: A string
        :return: A string with stop words removed
        '''
        words = text.split(" ")
        filteredWords = [
            word for word in words if word not in stop_words.ENGLISH_STOP_WORDS]
        return " ".join(filteredWords)

    def removeDictionaryWords(self, text):
        '''
        This function removes dictionary words from a string.
        :param word: A string
        :return: A string with dictionary words removed
        '''
        dictionary = enchant.Dict('en_US')
        words = [word for word in text.split(" ") if word]
        relevantWords = []
        for word in words:
            cleanWord = self.trim(word)
            if cleanWord in self.wordsToNotDiscard:
                relevantWords.append(cleanWord)
                continue
            try:
                if not dictionary.check(cleanWord.lower()):
                    relevantWords.append(cleanWord)
                    continue
            except Exception as e:
                logging.exception(
                    "Exception occurred while removing dictionary words: " + str(e))

        return " ".join(relevantWords)

    def cleanBanner(self, bannerText, bannerType):
        '''
        This function refines banner text according to their types.
        :param bannerText: A string containing banner's text
        :param bannerType: A string containing banner's type
        :return: A string with stop words removed
        '''
        text = bannerText.lower()
        text = self.removeEscapeChars(text)

        if bannerType == "UPNP":
            text = self.refineUPNP(text)
        elif bannerType == "HTTP":
            text = self.refineHTTP(text)
        elif bannerType == "TELNET":
            text = self.refineTELNET(text)
        elif bannerType == "FTP":
            text = self.refineFTP(text)

        text = self.removeDictionaryWords(text)
        text = self.removeStopWords(text)
        return text

    def splitOnSpace(self, sentence):
        return sentence.split()

    def sortCoo(self, cooMatrix):
        tuples = zip(cooMatrix.col, cooMatrix.data)
        return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

    def extractTopnFromVector(self, featureNames, sortedItems, topn=10):
        '''
        This function obtains the feature names and tf-idf score of top n items.
        :param featureNames: A list of feature names
        :param sortedItems: A list of sorted items
        :param topn: An int specifying number of top words to select
        :return: A dictionary mapping top 10 items to their tf-idf scores.
        '''
        # use only topn items from vector
        sortedItems = sortedItems[:topn]
        scoreVals = []
        featureVals = []
        # word index and corresponding tf-idf score
        for idx, score in sortedItems:
            scoreVals.append(round(score, 3))
            featureVals.append(featureNames[idx])

        results = dict()
        for idx in range(len(featureVals)):
            results[featureVals[idx]] = scoreVals[idx]

        return results

    def generateForAll(self, banners):
        '''
        This function extracts queries from all banners.
        :param banners: A list of all banners
        :return: A dictionary mapping banners to their query keywords.
        '''
        cleanedBanners = []
        for banner in banners:
            bannerType = banner["type"]
            bannerText = banner["banner"]
            cleanedBanner = self.cleanBanner(bannerText, bannerType)
            cleanedBanners.append(cleanedBanner)

        cv = CountVectorizer(
            max_df=0.85,
            analyzer=self.splitOnSpace,
            stop_words='english')
        wordCountVector = cv.fit_transform(cleanedBanners)
        tfidfTransformer = TfidfTransformer(smooth_idf=True, use_idf=True)
        tfidfTransformer.fit(wordCountVector)
        featureNames = cv.get_feature_names()

        bannersToKeywords = dict()
        for i, banner in enumerate(cleanedBanners):
            tfidfVector = tfidfTransformer.transform(cv.transform([banner]))
            sortedItems = self.sortCoo(tfidfVector.tocoo())
            keywords = self.extractTopnFromVector(
                featureNames, sortedItems, config.TOP_K_WORDS)
            bannersToKeywords[banners[i]["banner"]] = " ".join(keywords.keys())

        return bannersToKeywords
