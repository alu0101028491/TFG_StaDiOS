import pandas as pd
from abc import ABC
from SPARQLWrapper import JSON
from pandas import json_normalize
from analyzer.Analyzer import Analyzer
from itertools import product


class CostEffectivenessAnalyzer(Analyzer, ABC):
    """ Class for the definition and implementation of cost-effectiveness analysis of the StaDiOs ontology.
    """

    def __init__(self):
        Analyzer.__init__(self)
        self.LAST_YEAR = 2023
        self.GENERAL_INDEX = [69.53, 72.111, 73.773, 76.046, 79.234, 81.129, 84.598, 85.281,
                              86.158, 88.975, 90.753, 93.188, 93.373, 92.141, 91.876, 94.609,
                              95.153, 96.085, 97.139, 97.583, 103.567, 109.67]
        self.HEALTHCARE_INDEX = [86.313, 88.385, 90.115, 90.337, 90.946, 92.417, 90.668, 90.732,
                                 89.542, 88.267, 85.699, 96.032, 97.271, 97.175, 96.828, 97.551,
                                 97.848, 98.694, 99.149, 99.62, 100.5]
        self.FIRST_YEAR = self.LAST_YEAR - len(self.GENERAL_INDEX) + 1

    @staticmethod
    def adjust_detection_probability(dataframe):
        dataframe.loc[dataframe['DetectionCase'] == 'True Positive', 'DetectionProbability'] = \
            dataframe['sensitivity'] * dataframe['prevalenceAtBirth']
        dataframe.loc[dataframe['DetectionCase'] == 'False Positive', 'DetectionProbability'] = \
            (1 - dataframe['sensitivity']) * (1 - dataframe['prevalenceAtBirth'])
        dataframe.loc[dataframe['DetectionCase'] == 'True Negative', 'DetectionProbability'] = \
            dataframe['specificity'] * (1 - dataframe['prevalenceAtBirth'])
        dataframe.loc[dataframe['DetectionCase'] == 'False Negative', 'DetectionProbability'] = \
            (1 - dataframe['specificity']) * (dataframe['prevalenceAtBirth'])

        return dataframe

    def screening_simulation(self, dataframe):
        dataframe.insert(6, 'hasDisease', 'Disease')
        dataframe.insert(7, 'DetectionCase', 'False Negative')
        dataframe.insert(12, 'DetectionProbability', 1.0)
        dataframe = dataframe.reset_index(drop=True)

        # True positive configuration - No manifestation, only detection and treatment costs
        dataframe = pd.concat([dataframe, dataframe[-1:]]).reset_index(drop=True)
        dataframe.loc[dataframe.index[-1], ['hasDisease', 'DetectionCase', 'DetectionProbability',
                                            'manifestation', 'manifestationProbability',
                                            'manifestationInitialAmount', 'manifestationAnnualAmount',
                                            'utilityValue']] = \
            ['Disease', 'True Positive', 1.0, 'NONE', 0.0, 0.0, 0.0, 1.0]

        # False positive configuration - No manifestation, only detection costs
        dataframe = pd.concat([dataframe, dataframe[-1:]]).reset_index(drop=True)
        dataframe.loc[dataframe.index[-1], ['hasDisease', 'DetectionCase', 'DetectionProbability',
                                            'manifestation', 'manifestationProbability',
                                            'manifestationInitialAmount', 'manifestationAnnualAmount',
                                            'utilityValue', 'followUpAmount', 'treatmentStrategyAmount']] = \
            ['No Disease', 'False Positive', 1.0, 'NONE', 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]

        # True negative configuration - No manifestation, only detection costs
        dataframe = pd.concat([dataframe, dataframe[-1:]]).reset_index(drop=True)
        dataframe.loc[dataframe.index[-1], ['hasDisease', 'DetectionCase', 'DetectionProbability',
                                            'manifestation', 'manifestationProbability',
                                            'manifestationInitialAmount', 'manifestationAnnualAmount',
                                            'utilityValue', 'followUpAmount', 'treatmentStrategyAmount']] = \
            ['No Disease', 'True Negative', 1.0, 'NONE', 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]

        return self.adjust_detection_probability(dataframe)

    @staticmethod
    def standard_simulation(dataframe):
        dataframe.insert(6, 'hasDisease', 'Disease')
        dataframe.insert(7, 'DetectionCase', 'NONE')
        dataframe.insert(12, 'DetectionProbability', 1.0)
        dataframe = dataframe.reset_index(drop=True)

        dataframe = pd.concat([dataframe, dataframe[-1:]]).reset_index(drop=True)
        dataframe.loc[dataframe.index[-1], ['hasDisease', 'DetectionCase', 'DetectionProbability', 'manifestation',
                                            'manifestationProbability', 'manifestationInitialAmount',
                                            'manifestationAnnualAmount', 'utilityValue', 'followUpAmount',
                                            'treatmentStrategyAmount']] = \
            ['No Disease', 'NONE', 1.0, 'NONE', 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]

        dataframe.loc[dataframe['hasDisease'] == 'Disease', 'DetectionProbability'] = dataframe['prevalenceAtBirth']
        dataframe.loc[dataframe['hasDisease'] == 'No Disease', 'DetectionProbability'] = \
            1 - dataframe['prevalenceAtBirth']

        return dataframe

    def adjust_branch_probability(self, dataframe):
        dataframe['Branch Probability'] = 0.0
        ref_column = 'manifestation'

        # Get the unique values in the reference column
        ref_values = dataframe[ref_column].unique()
        ref_values = [i for i in ref_values if i != 'NONE']

        # Generate all combinations of "Yes" and "No" values
        combos = list(product(['Yes', 'No'], repeat=len(ref_values)))
        new_df = pd.DataFrame(columns=[ref_column] + [f'{ref_values[i]}' for i in range(len(ref_values))])

        # We generate dataframe with the possible combinations of manifestations
        for i, combo in enumerate(combos):
            new_row = {ref_column: dataframe['detectionStrategy'].unique()}
            for j, value in enumerate(combo):
                new_row[f'{ref_values[j]}'] = value
            new_df.loc[i] = new_row
        # We replace the "Yes" and "No" values by the probability of each manifestation
        for column in new_df.columns[1:]:
            row = dataframe.loc[dataframe[ref_column] == column]
            new_df.loc[new_df[column] == 'Yes', column] = row['manifestationProbability'].values[0]
            new_df.loc[new_df[column] == 'No', column] = 1 - row['manifestationProbability'].values[0]

        # We add a column with the real probability of each combination of manifestations
        new_df['Probability'] = new_df.iloc[:, 1:].apply(lambda x: x.prod(), axis=1)
        if new_df['Probability'].sum() != 1.0:
            raise Exception('Incorrect probabilities included - Not within 0-1 range')
        # Sum of the absolute probabilities of manifestations
        proportion_sum = dataframe['manifestationProbability'].sum()

        # For each combination associated with a manifestation we multiply its actual
        # probability by the probability of detection. We add them all together and obtain
        # the absolute probability of each manifestation.
        for column in new_df.iloc[:, 1:-1]:
            row = dataframe.loc[dataframe[ref_column] == column].squeeze()

            manifestation_prob = row['manifestationProbability']

            sum = new_df.loc[new_df[column] == manifestation_prob, 'Probability'].sum()
            dataframe.loc[dataframe['manifestation'] == column, 'Branch Probability'] = \
                (dataframe['DetectionProbability'] * sum) / proportion_sum

        return dataframe

    def get_query(self, sparql_query):
        self.sparql_wrapper.setQuery(sparql_query)
        self.sparql_wrapper.setReturnFormat(JSON)

        # Ask for the result in JSON format
        result = self.sparql_wrapper.query().convert()
        result = json_normalize(result["results"]["bindings"])

        simplified_df = result.filter(regex='value')
        simplified_df = simplified_df.rename(columns=lambda col: col.replace(".value", ""))
        simplified_df = simplified_df.apply(
            lambda row: row.replace(
                {'http://www.semanticweb.org/storh/ontologies/2022/11/StaDiOS#': ''}, regex=True))

        return simplified_df

    def update_cost(self, cost, original_year, new_year, use_general_index):

        # Update costs according to the Spanish Consumer Price Index (CPI)
        ipc = []

        if original_year == new_year:
            return cost
        elif original_year > self.LAST_YEAR | original_year < self.FIRST_YEAR:
            raise Exception('Parameter out of range')
        elif new_year > self.LAST_YEAR | new_year < self.FIRST_YEAR:
            raise Exception('Parameter out of range')

        if use_general_index:
            ipc = self.GENERAL_INDEX
        else:
            ipc = self.HEALTHCARE_INDEX

        original_ipc = ipc[original_year - self.FIRST_YEAR]
        new_ipc = ipc[new_year - self.FIRST_YEAR]
        return cost * round(1000 * new_ipc / original_ipc) / 1000.0

    def update_dataframe_costs(self, dataframe):
        dataframe['detectionStrategyAmount'] = dataframe.apply(
            lambda row: self.update_cost(row['detectionStrategyAmount'],
                                         row['detectionStrategyYear'],
                                         self.LAST_YEAR, True), axis=1)

        dataframe['manifestationInitialAmount'] = dataframe.apply(
            lambda row: self.update_cost(row['manifestationInitialAmount'],
                                         row['manifestationYear'],
                                         self.LAST_YEAR, True), axis=1)

        dataframe['manifestationAnnualAmount'] = dataframe.apply(
            lambda row: self.update_cost(row['manifestationAnnualAmount'],
                                         row['manifestationYear'], self.LAST_YEAR, True), axis=1)

        dataframe['followUpAmount'] = dataframe.apply(
            lambda row: self.update_cost(row['followUpAmount'],
                                         row['followUpYear'], self.LAST_YEAR, True), axis=1)

        dataframe['treatmentStrategyAmount'] = dataframe.apply(
            lambda row: self.update_cost(row['treatmentStrategyAmount'],
                                         row['treatmentYear'], self.LAST_YEAR, True), axis=1)

        diagnosis_cost = max(
            dataframe.loc[dataframe['interventionKind'] == 'DIAGNOSIS', 'detectionStrategyAmount'].unique())
        screening_cost = min(
            dataframe.loc[dataframe['interventionKind'] == 'SCREENING', 'detectionStrategyAmount'].unique())
        # When screening is positive, a diagnostic test is needed to confirm the disease.
        dataframe.loc[dataframe["DetectionCase"] == "True Positive", "detectionStrategyAmount"] += diagnosis_cost
        dataframe.loc[dataframe["DetectionCase"] == "False Positive", "detectionStrategyAmount"] += diagnosis_cost
        # When diagnosis is positive, a screening test is needed too.
        dataframe.loc[(dataframe['interventionKind'] == "DIAGNOSIS")
                      & (dataframe['hasDisease'] == 'Disease'), 'detectionStrategyAmount'] += screening_cost
        # These subjects will not be subjected to a diagnostic test, so they do not have their costs.
        dataframe.loc[(dataframe['interventionKind'] == "DIAGNOSIS")
                      & (dataframe['hasDisease'] == 'No Disease'), 'detectionStrategyAmount'] = 0.0

        return dataframe

    def get_analysis(self, sparql_query):
        simplified_df = self.get_query(sparql_query)

        simplified_df['sensitivity'] = simplified_df['sensitivity'].apply(pd.to_numeric)
        simplified_df['specificity'] = simplified_df['specificity'].apply(pd.to_numeric)
        simplified_df['manifestationProbability'] = simplified_df['manifestationProbability'].apply(pd.to_numeric)
        simplified_df['prevalenceAtBirth'] = simplified_df['prevalenceAtBirth'].apply(pd.to_numeric)

        interventions = simplified_df.intervention.unique()
        grouped_interventions = simplified_df.groupby(simplified_df.intervention)
        interventions_df = list()

        for intervention in interventions:
            interventions_df.append(grouped_interventions.get_group(intervention))

        for i in range(len(interventions_df)):
            if 'SCREENING' in interventions_df[i]['interventionKind'].unique() \
                    and 'NEONATAL' in interventions_df[i]['populationKind'].unique():
                interventions_df[i] = self.screening_simulation(interventions_df[i])
            else:
                interventions_df[i] = self.standard_simulation(interventions_df[i])

            interventions_df[i] = self.adjust_branch_probability(interventions_df[i])

        # It is convenient to say which parameters we want to treat as numerical parameters.
        numeric_params = ['populationAverageAge', 'populationUtilityValue', 'DetectionProbability',
                          'detectionStrategyAmount', 'lifeExpectancy', 'manifestationProbability',
                          'manifestationInitialAmount', 'manifestationAnnualAmount', 'utilityValue', 'followUpAmount',
                          'treatmentStrategyAmount', 'detectionStrategyYear', 'manifestationYear', 'followUpYear',
                          'treatmentYear', 'Branch Probability']

        # Full analysis table - Has some extra but not crucial information
        full_dataframe = pd.DataFrame()

        # We unify the sub-tables
        for i in range(len(interventions_df)):
            full_dataframe = pd.concat([full_dataframe, interventions_df[i]], axis=0).reset_index(drop=True)
        for i in numeric_params:
            full_dataframe[i] = full_dataframe[i].apply(pd.to_numeric)

        # We update the costs to the present time and adjust costs for somewhat specific cases
        full_dataframe = self.update_dataframe_costs(full_dataframe)

        # We create a final dataframe with the most important columns of our analysis
        ce_dataframe = full_dataframe[
            ['disease', 'interventionKind', 'hasDisease', 'DetectionCase', 'detectionStrategy', 'development',
             'manifestation', 'followUpStrategy', 'treatmentStrategy', 'populationAverageAge', 'populationUtilityValue',
             'DetectionProbability', 'detectionStrategyAmount', 'lifeExpectancy', 'manifestationProbability',
             'manifestationInitialAmount', 'manifestationAnnualAmount', 'utilityValue', 'followUpAmount',
             'treatmentStrategyAmount', 'Branch Probability']].copy()

        # Probability of reaching each event not including manifestations
        ce_dataframe.loc[ce_dataframe['manifestationProbability'] == 0.000, 'Branch Probability'] = \
            ce_dataframe['DetectionProbability']

        # Lifetime cost associated with a manifestation
        ce_dataframe['Branch Lifetime Cost'] = \
            ce_dataframe['Branch Probability'] * \
            (ce_dataframe['detectionStrategyAmount'] + ce_dataframe['manifestationInitialAmount'] +
             ((ce_dataframe['followUpAmount'] + ce_dataframe['treatmentStrategyAmount']) *
              ce_dataframe['lifeExpectancy']))

        # Annual cost associated with a manifestation
        ce_dataframe['Branch Annual Cost'] = \
            ce_dataframe['Branch Probability'] * \
            (ce_dataframe['detectionStrategyAmount'] +
             (ce_dataframe['lifeExpectancy'] *
              (ce_dataframe['manifestationAnnualAmount'] + ce_dataframe['followUpAmount'] +
               ce_dataframe['treatmentStrategyAmount'])))

        # QALY associated with a manifestation
        ce_dataframe['Branch QALY'] = ce_dataframe['Branch Probability'] * ce_dataframe['lifeExpectancy'] * \
                                      ce_dataframe['populationUtilityValue'] * ce_dataframe['utilityValue']

        return ce_dataframe
