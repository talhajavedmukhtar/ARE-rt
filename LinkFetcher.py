import config
from googleapiclient.discovery import build
import logging


class LinkFetcher():

    def getUrlsGoogle(self, query, key, **kwargs):
        '''
        This function obtains Google search result URLs against a query.
        :param query: A string containing query keywords
        :param key: A string containing Google search API key
        :return: A list of strings containing URLs
        '''
        try:
            service = build("customsearch", "v1", developerKey=key)
            results = service.cse().list(q=query, cx=config.CSE_ID).execute()
        except Exception as e:
            logging.exception(
                "Error in fetching links from Google search: " + str(e))
            results = {}
        return results
