from SPARQLWrapper import SPARQLWrapper
from pathlib import Path
from abc import ABC, abstractmethod


class Analyzer:
    """ Abstract class for the definition and implementation of different parsers of the StaDiOs ontology.
    """

    def __init__(self):
        """ Builder overload -- Initialize SparqlWrapper parameters

        """
        self.endpoint = Path('data/sparql_endpoint').read_text()
        self.sparql_wrapper = SPARQLWrapper(self.endpoint, agent="SparqlWrapper - StaDiOS analysis")
        self.prefixes = Path('data/sparql_prefixes').read_text()

    @abstractmethod
    def adjust_detection_probability(self, dataframe):
        """ Adjusts the probability of detection depending on the type of analysis

        :param dataframe: Dataframe to analyze
        :return: Dataframe with adjusted probabilities
        """
        pass

    @abstractmethod
    def screening_simulation(self, dataframe):
        """ Operations to be performed on a screening dataframe to adjust it to decision tree analysis

        :param dataframe: Dataframe to analyze
        :return: Dataframe with adjusted stucture
        """
        pass

    @abstractmethod
    def standard_simulation(self, dataframe):
        """ Operations to be performed on a non-screening dataframe to adjust it to decision tree analysis

        :param dataframe: Dataframe to analyze
        :return: Dataframe with adjusted stucture
        """
        pass

    @abstractmethod
    def adjust_branch_probability(self, dataframe):
        """ We must calculate the combinations between manifestations to
        obtain the absolute probability of each event.

        :param dataframe: Dataframe to analyze
        :return: Dataframe with adjusted stucture
        """
        pass

    @abstractmethod
    def get_query(self, sparql_query):
        """ Perform a standard query to our StaDiOS to obtain analysis information

        :param sparql_query: StaDiOS sparql query
        :return: Dataframe with the minimum information to set up analysis
        """
        pass

    @abstractmethod
    def update_cost(self, cost, original_year, new_year, use_general_index):
        """ Adjusts the cost of the analysis based on relevant legislation

        :param cost: Parameter cost
        :param original_year: Year in which the cost of the parameter was obtained
        :param new_year: Current year
        :param use_general_index: Use of an alternative index
        :return: Updated cost
        """
        pass

    @abstractmethod
    def update_dataframe_costs(self, dataframe):
        """ Adjusts the cost of the analysis based on relevant legislation

        :return: Dataframe with updated costs based on the relevant legislation
        """
        pass

    @abstractmethod
    def get_analysis(self, sparql_query):
        """ It generates an analysis from information obtained from StaDiOS and is determined
        by the type of analyzer.

        :param sparql_query: StaDiOS sparql query
        :return:
        """
        pass
