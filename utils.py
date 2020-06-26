from itertools import chain, combinations
import re


def cleanTags(text):
    '''
    This function removes HTML tags from a webpage text
    :param text: A string containing webpage text
    :return: A string containing webpage text with tags removed
    '''
    tags = [
        "^<script[^>]*>",
        "</script>$",
        "^<style[^>]*>",
        "</style>$"
    ]
    for tag in tags:
        text = re.sub(tag, "", text)
    return text


def isEmptyLine(text):
    '''
    This function checks if a webpage text line is blank/empty.
    :param text: A string containing webpage text line
    :return: True if line is empty or else False
    '''
    to_remove = [" ",
                 "\n",
                 "\r",
                 "\t",
                 "\xa0"]
    for char in to_remove:
        text = text.replace(char, "")
    if text == "":
        return True
    return False


def makeTransactions(banner, annotations):
    '''
    This function creates a transaction using banner and its annotations.
    :param banners: A string containing banner text
    :param annotations: A list of strings containing annotations of the banner
    :return: A list of transactions
    '''
    transactions = []

    for annotation in annotations:
        transaction = [banner]

        for item in annotation:
            if item is not None:
                transaction.append(item)

        transactions.append(transaction)

    return transactions


def makeAllTransactions(bannerToAnnotationsMap):
    '''
    This function creates transactions using banners and their annotations.
    :param banners: A string containing banner text
    :param bannerToAnnotationsMap: A dictionary that maps banners to their annotations
    :return: A list of all transactions
    '''
    allTransactions = []
    for banner, annotations in bannerToAnnotationsMap.items():
        allTransactions += makeTransactions(banner, annotations)

    return allTransactions
