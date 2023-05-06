import streamlit as st
import matplotlib.pyplot as plt
import pyautogui
from pathlib import Path
from analyzer.CostEffectivenessAnalyzer import CostEffectivenessAnalyzer
from sparql.SparqlManager import SparqlManager


@st.cache_data()
def load_ce_dataframe(sparql_query):
    return ontology_analyzer.get_analysis(sparql_query)


def callback():
    st.session_state.load_state = True


def resetcall():
    st.session_state.load_state = False


def download_ce_dataframe_button(dataframe):
    return st.download_button(
        label="Download CE as CSV",
        data=dataframe.to_csv(index=False).encode('utf-8'),
        file_name='ce_analysis.csv',
        mime='text/csv',
    )


def download_ce_results_button(dataframe):
    return st.download_button(
        label="Download CE results as CSV",
        data=dataframe.to_csv(index=False).encode('utf-8'),
        file_name='ce_results_analysis.csv',
        mime='text/csv',
    )


def main_page_initialization(param_list, sparql_query):
    st.title("StaDiOS - Cost-Effectiveness Analyzer")
    st.header("Cost-Effectiveness Dataframe")

    disease_selected = st.selectbox('Select disease', param_list[0], on_change=resetcall)
    development_selected = st.selectbox('Select development', param_list[1], on_change=resetcall)
    study_identifier_selected = st.selectbox('Select study ID', param_list[4], on_change=resetcall)
    follow_up_selected = st.selectbox('Select follow up', param_list[2], on_change=resetcall)
    treatment_selected = st.selectbox('Select treatment', param_list[3], on_change=resetcall)

    if st.button('Generate CE Analysis', on_click=callback) or st.session_state.load_state:

        filter_option = "\n FILTER(?disease = std:" + disease_selected + " && ?development = std:" + \
                        development_selected + " && ?followUpStrategy = std:" + follow_up_selected + \
                        " && ?treatmentStrategy = std:" + treatment_selected + ") . \n"
        filter_study_option = "FILTER(STR(?studyIdentifier) =" + '"' + \
                              study_identifier_selected + '") .' + "\n } "

        try:
            ce_dataframe = load_ce_dataframe(sparql_query + filter_option + filter_study_option)
            st.dataframe(ce_dataframe, width=1500, height=600)

            download_ce_dataframe_button(ce_dataframe)

            st.header("Cost-Effectiveness Results")
            grouped_params = ['interventionKind', 'detectionStrategy',
                              'treatmentStrategy', 'followUpStrategy']
            grouped_df = ce_dataframe.groupby(grouped_params, as_index=False)[['Branch Lifetime Cost',
                                                                               'Branch Annual Cost',
                                                                               'Branch QALY']].sum()
            st.dataframe(grouped_df)

            download_ce_results_button(grouped_df)

            st.header("Graphic analysis")
            # Specific groupings we want from the data
            grouping_options = st.multiselect('Grouping of parameters',
                                              ['interventionKind', 'detectionStrategy',
                                               'treatmentStrategy', 'followUpStrategy'])
            # Column of the cost-effective analysis to be analyzed
            final_parameters_options = ['Branch QALY', 'Branch Lifetime Cost',
                                        'Branch Annual Cost', 'Branch Probability']

            final_selected_parameter = st.selectbox('Select disease', final_parameters_options)
            # Quantitative values to be compared for the different groupings
            params_to_display = ['count', 'sum', 'mean', 'min', 'max']

            if st.button('Generate Graphic Analysis'):

                # Bar chart to compare the desired parameters of the different groupings
                fig, ax = plt.subplots(figsize=(15, 7))
                diagram = ce_dataframe.groupby(grouping_options).agg(
                    {final_selected_parameter: params_to_display})
                diagram.plot.barh(ax=ax)

                for bars in ax.containers:
                    ax.bar_label(bars, fontweight='bold')

                st.pyplot(fig)
        except KeyError:
            st.write('The selected study does not have sufficient information to perform a '
                     'CE analysis. \n\n' +
                     'To verify that the information included in the ontology is correct, '
                     "we invite you to review our bibliography: "
                     "[StaDiOS](https://alu0101028491.github.io/TFG_StaDiOS/)")


if __name__ == '__main__':
    st.set_page_config(page_title="StaDiOS-App", layout="wide")

    if st.sidebar.button("Reset"):
        pyautogui.hotkey("ctrl", "F5")
    if 'load_state' not in st.session_state:
        st.session_state.load_state = False

    sparql_manager = SparqlManager()
    ontology_analyzer = CostEffectivenessAnalyzer()

    query = Path('data/sparql_prefixes').read_text() + '\n' + Path(
        'data/cost_effectiveness_query').read_text()

    parameters_list = sparql_manager.get_selection_parameters()

    main_page_initialization(parameters_list, query)
