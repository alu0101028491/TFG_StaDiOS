import pandas as pd
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from pathlib import Path
from pandas import json_normalize
from geopy.distance import geodesic as gd


class SparqlManager:
    """ Class for obtaining diverse inference from the StaDiOS ontology
    """

    def __init__(self):
        """ Builder overload -- Initialize SparqlManager parameters
        """
        self.endpoint = Path('data/sparql_endpoint').read_text()
        self.sparql_wrapper = SPARQLWrapper(self.endpoint, agent="SparqlWrapper - StaDiOS analysis")
        self.prefixes = Path('data/sparql_prefixes').read_text()

    def get_query(self, sparql_query):
        """ Method to perform any standard query to the StaDiOS ontology and save
        the resulting information in a dataframe

        :param sparql_query: Custom Sparql query
        :return: Dataframe with query results
        """
        self.sparql_wrapper.setQuery(sparql_query)
        self.sparql_wrapper.setReturnFormat(JSON)

        # Ask for the result in JSON format
        result = self.sparql_wrapper.query().convert()
        result = json_normalize(result["results"]["bindings"])

        simplified_table = result.filter(regex='value')
        simplified_table = simplified_table.rename(columns=lambda col: col.replace(".value", ""))
        simplified_table = simplified_table.apply(
            lambda row: row.replace({'http://www.semanticweb.org/storh/ontologies/2022/11/StaDiOS#': ''}, regex=True))

        return simplified_table

    def get_selection_parameters(self):
        """
        :return: Parameters loaded in StaDiOS that we need to select to generate our analysis
        """
        selection_parameters = self.get_query(self.prefixes + '\n' +
                                              Path('data/get_selection_parameters').read_text())
        study_identifier_parameter = self.get_query(self.prefixes + '\n' +
                                                    Path('data/get_study_identifiers').read_text())
        countries_parameter = self.get_query(self.prefixes + '\n' +
                                             Path('data/get_parameters_countries').read_text())

        diseases_list = selection_parameters.disease.unique()
        developments_list = selection_parameters.development.unique()
        follow_up_list = selection_parameters.followUpStrategy.unique()
        treatmets_list = selection_parameters.treatmentStrategy.unique()
        study_identifiers_list = study_identifier_parameter.studyIdentifier.unique()
        study_identifiers_list = study_identifiers_list[study_identifiers_list != 'Default_study']
        countries_list = countries_parameter.country.unique()
        countries_list = countries_list[countries_list != 'Default']

        return [diseases_list, developments_list, follow_up_list, treatmets_list,
                study_identifiers_list, countries_list]

    def get_common_treament(self, disease, development):
        """ We obtain treatments that have in common the manifestations of a disease under a
        specific development.

        :param disease: Disease
        :param development: Disease-specific development
        :return: Intersection dataframe
        """
        filter_option = "\n FILTER(?disease = std:" + disease + " && ?development = std:" + \
                        development + ") . } \n"

        query = self.prefixes + '\n' + \
                Path('data/get_manifestations_treatments').read_text() + filter_option
        dataframe = self.get_query(query)
        dataframe = dataframe.drop(dataframe[dataframe.treatment == "DefaultTreatmentStrategy"].index)

        return dataframe

    def get_common_follow_up(self, disease, development):
        """ We obtain follow-ups that have in common the manifestations of a disease under a
        specific development.

        :param disease: Disease
        :param development: Disease-specific development
        :return: Intersection dataframe
        """
        filter_option = "\n FILTER(?disease = std:" + disease + " && ?development = std:" + \
                        development + ") . } \n"

        query = self.prefixes + '\n' + Path('data/get_manifestations_follow_up').read_text() + filter_option
        dataframe = self.get_query(query)
        dataframe = dataframe.drop(dataframe[dataframe.followUp == "DefaultFollowUpStrategy"].index)

        return dataframe

    def get_european_parameters(self, study_identifier):
        """ We obtain all the parameters of a study that are within the European Union.

        :param study_identifier: Study unique identifier
        :return: Intersection dataframe
        """
        query = self.prefixes + '\n' + Path('data/get_european_parameters').read_text()
        dataframe = self.get_query(query)

        if study_identifier != 'ALL':
            dataframe = dataframe.loc[(dataframe['studyIdentifier'] == study_identifier)]

        return dataframe

    def get_parameters_coordinates(self, disease, study_identifier, country, parameter_type):
        """ We obtain the parameters loaded in StaDiOS associated with a type of disease and parameter.
        These parameters will be sorted by geographical distance.

        :param disease: Disease
        :param study_identifier: Study unique identifier
        :param country: Country serving as point of origin
        :param parameter_type: Type of parameter to be analyzed
        :return: Intersection dataframe
        """
        query = self.prefixes + '\n' + Path('data/get_parameters_coordinates').read_text()
        aux_dataframe = self.get_nearest_param(self.get_query(query), disease, study_identifier,
                                               country, parameter_type)

        return aux_dataframe

    @staticmethod
    def get_nearest_param(dataframe, disease, study_identifier, country_label, parameter_type):
        """ We obtain the parameters loaded in StaDiOS associated with a type of disease and parameter.
        These parameters will be sorted by geographical distance.

        :param dataframe: All StaDiOS parameters with their associated geographic coordinates
        :param disease: Disease
        :param study_identifier: Study unique identifier
        :param country_label: Country serving as point of origin
        :param parameter_type: Type of parameter to be analyzed
        :return: Intersection dataframe
        """

        # We are left with the available countries and parameters
        distance_list = list()
        aux_table = dataframe[dataframe['disease'] == disease]
        aux_table = aux_table.reset_index()

        # From a country and study of origin we obtain its coordinates
        origin_coordinates = aux_table[(aux_table['countryLabel'] == country_label) & \
                                       (aux_table['studyIdentifier'] == study_identifier)]
        origin_coordinates = re.findall(r'([^( )]+)(?!.*\()', origin_coordinates.iloc[0]['coordinates'])
        origin = (origin_coordinates[0], origin_coordinates[1])

        # We calculate the distances of the rest of the parameters with respect to the point of origin
        for index, row in aux_table.iterrows():
            if row['studyIdentifier'] != study_identifier and row['parameterType'] == parameter_type:
                coordinates = re.findall(r'([^( )]+)(?!.*\()', row['coordinates'])
                destination = (coordinates[0], coordinates[1])
                distance = gd(destination, origin).km
                distance_list.append(
                    {'countryLabel': row['countryLabel'], 'distance': distance, 'distanceUnit': 'km',
                     'studyIdentifier': row['studyIdentifier'], 'parameterType': row['parameterType'],
                     'parameterName': row['parameter'],
                     })

        sorted_distances = sorted(distance_list, key=lambda p: p['distance'])
        return pd.DataFrame(sorted_distances)
