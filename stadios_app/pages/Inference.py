import streamlit as st
import numpy as np
from sparql.SparqlManager import SparqlManager
import pyautogui


def load_manifestation_treatments(manager, disease, development):
    return manager.get_common_treament(disease, development)


def load_manifestation_follow_up(manager, disease, development):
    return manager.get_common_follow_up(disease, development)


def load_european_parameters(manager, study_identifier):
    return manager.get_european_parameters(study_identifier)


def load_coordinates(manager, disease, study_identifier, country, parameter_type):
    return manager.get_parameters_coordinates(disease, study_identifier, country, parameter_type)


def page_initialization(param_list):
    disease_options = param_list[0]
    development_options = param_list[1]
    first_study_identifier_options = param_list[4]
    first_study_identifier_options = np.append(first_study_identifier_options, 'ALL')
    secodn_study_identifier_options = param_list[4]
    countries = param_list[5]

    st.header("Common elements among manifestations")
    disease_selected = st.selectbox('Select disease', disease_options)
    development_selected = st.selectbox('Select development', development_options)
    common_points_options = ['Treatment_Strategy', 'FollowUp_Strategy']
    common_point_selected = st.selectbox('Select intersection element', common_points_options)

    if st.button('Show manifestations intersection'):
        if common_point_selected == 'Treatment_Strategy':
            st.dataframe(load_manifestation_treatments(sparql_manager, disease_selected,
                                                       development_selected))
        if common_point_selected == 'FollowUp_Strategy':
            st.dataframe(load_manifestation_follow_up(sparql_manager, disease_selected,
                                                      development_selected))

    st.header("Parameters whose geographical context is within the European Union")
    study_identifier_selected = st.selectbox('Select study ID', first_study_identifier_options)
    if st.button('Show european parameters'):
        st.dataframe(load_european_parameters(sparql_manager, study_identifier_selected))

    st.header("Geological nearest params")
    parameter_type_options = ['Utility', 'Population', 'Cost']
    disease_selected = st.selectbox('Disease', disease_options)
    study_identifier_selected = st.selectbox('Study ID', secodn_study_identifier_options)
    country_selected = st.selectbox('Select country', countries)
    parameter_type_selected = st.selectbox('Parameter type', parameter_type_options)

    if st.button('Show nearest parameters'):
        st.dataframe(load_coordinates(sparql_manager, disease_selected, study_identifier_selected, country_selected,
                                      parameter_type_selected))


if __name__ == '__main__':
    st.set_page_config(page_title="StaDiOS-App", layout="wide")
    st.title("StaDiOS Inference")

    if st.sidebar.button("Reset"):
        pyautogui.hotkey("ctrl", "F5")

    sparql_manager = SparqlManager()
    parameters_list = sparql_manager.get_selection_parameters()
    page_initialization(parameters_list)






