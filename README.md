## Standard Disease Ontology for Simulation 
In Spain, the law requires an economic evaluation of the pros and cons of financing any healthcare technology, whether it is a new one or an expansion on a pre-existing basis. In order to carry out these evaluations, it is common to propose models that represent how the disease evolves and make it possible to measure both the economic results and the health outcomes of individuals, although their development can be very complex, the use of computer tools that make it possible to automate or semi-automate part of the steps can be a great help to researchers. The use of simulation models is becoming more and more common because, in certain aspects, they are more flexible than their traditional format of being carried out as part of an economic evaluation within a clinical trial.

This project proposes the development of a domain-specific ontology, called StaDiOS, to store the knowledge of different economic-health studies on diseases of any kind. Once we have this information model, we implement an application that allows us to reuse it and generate cost-effectiveness analyses using decision trees for the comparison between different health interventions applied to a population suffering from disease under a specific development, and also allows us to generate additional inferences from various data sources in conjunction with StaDiOS.

## Ontology directory
It contains the definition of the StaDiOS ontology. This is an ontology designed to store information on health economic studies of any disease that allows structuring the information to facilitate the creation of economic analyses using decision trees, specifically cost-effectiveness analyses. 

## Cost-effectiveness directory
It contains and displays the simulations and ontological inferences previously performed and gives us an approximation of what we need in the application we have created. It also contains part of all the CSV files generated.

## Stadios-app directory
It contains the code of the application implemented using the Streamlit framework. 