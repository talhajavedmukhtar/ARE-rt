""" Takes in transactions and generates rules """

from apyori import apriori
import pandas as pd
import csv
import config
from staticLists.devices import devices
from staticLists.vendors import vendors


class RuleGenerator():
    def __init__(self, transactions):
        self.transactions = transactions
        self.banners = list(set([x[0] for x in transactions]))

    def getLabeledRule(self, relationRecord):
        ''' 
        This function generates a rule against a transaction.
        :return: A dictionary containing rule
        '''
        items = set(relationRecord)
        rule = {}
        for item in items:
            if item in self.banners:
                rule["banner"] = item
            elif item in devices:
                rule["deviceType"] = item
            elif item in vendors:
                rule["vendor"] = item
            else:
                rule["product"] = item

        if "banner" not in rule.keys():
            return None

        return rule

    def generate(self):
        ''' 
        This function generates rules from transactions.
        :return: A list of dictionaries containing rules
        '''
        rules = []
        results = list(apriori(self.transactions,
                               min_support=config.MIN_SUPPORT,
                               min_confidence=config.MIN_CONFIDENCE))
        Support = []
        Confidence = []
        Items = []
        for RelationRecord in results:
            for ordered_stat in RelationRecord.ordered_statistics:
                itemsAsSet = self.getLabeledRule(RelationRecord.items)
                if itemsAsSet is not None and itemsAsSet not in Items:
                    Items.append(itemsAsSet)
                    Support.append(RelationRecord.support)
                    Confidence.append(ordered_stat.confidence)

        # represent Items, Support, and Confidence as dataframes
        df = pd.DataFrame(columns=('Items', 'Support', 'Confidence'))
        df['Items'], df['Support'], df['Confidence'] = Items, Support, Confidence
        
        # generates a rules.csv file containing the inferred rules
        rules = df['Items']
        df.to_csv(config.RULES_FILE)

        return Items
