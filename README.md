# Ferencz-et_al_2026_ER_Water

**Stress Testing Urban Water Security: A Sensitivity‑Based Evaluation of Drivers Water Shortage in the Los Angeles Region During Severe Drought**

Stephen B. Ferencz<sup>1\*</sup>, Chris R. Vernon Last<sup>1</sup>,  Erik Porse<sup>2</sup>, Patrick Reed <sup>3</sup>, and Jim Yoon<sup>1, 

<sup>1 </sup>Pacific Northwest National Laboratory, Richland, WA, USA.

<sup>2 </sup> California Institute for Water Resources, University of California Agriculture and Natural Resources, Davis, CA 

<sup>2 </sup> School of Civil and Environmental Engineering, Cornell University, Ithica, NY 

\* corresponding author:  stephen.ferencz@pnnl.gov

## Abstract
Uncertainties in future water supply and demand pose major challenges for urban water systems’ ability to understand and manage risk. In regions with shared supply sources, hierarchical governance, and diverse supply portfolios, these uncertainties compound, making it difficult to characterize vulnerabilities and identify underlying drivers of water shortage risk. With multiple shared supply sources and a highly fragmented physical and institutional supply system, Los Angeles County (LAC) exemplifies these challenges. We adapt the Artes regional water supply optimization model for LAC to perform a variance‑based Sobol global sensitivity analysis to quantify how 11 uncertain supply and demand parameters influence water shortages across more than 90 water providers during severe multi‑year drought. Results show that Metropolitan Water District (MWD) imports are the most dominant single factor, even for many providers without a direct MWD connection. Groundwater yields and antecedent reservoir storage also have broad regional influence, while near-term efforts related to reuse and residential efficiency are less influential. High total‑order Sobol indices reveal that nonlinear parameter interactions, rather than single factors, drive system‑level vulnerability. Scenario analysis shows a sharp increase in shortage frequency when MWD imports fall below ~500,000 acre‑feet annually but also shows that even modest groundwater availability thresholds can substantially reduce risk. This study provides a framework for stress testing complex urban water systems to generate actionable insights into the key parameters that drive risk and inform more targeted and effective drought planning and management efforts.

## Journal reference
_your journal reference_

## Code reference
References for each minted software release for all code involved.  

## Data reference

### Input data
- This work adapts the [Artes](https://github.com/erikporse/artes) optimization model -- a network flow based optimization model designed for Gurobi -- using Pyomo and IPOPT. Our model relies on much of the underlying model structure and water system attribute inputs (topology of water system connections and their link capacities) used by Artes. Detailed description of the model we use for this experiment is provided in the Supplement to the paper. 
- Water service provider monthly [water supply data](https://www.waterboards.ca.gov/water_issues/programs/conservation_portal/conservation_reporting.html). Used to update monthly demands for service regions. Supply data for 2017-2021 is used to derive average monthly demands for water providers. Indoor and outdoor components were informed by the baseline outdoor demand from [Ferencz et al. 2025](https://data.msdlive.org/records/s581n-tye84). 
- Topology for added service providers sourced from [Urban Water Management Plans](https://wuedata.water.ca.gov/uwmp_plans.asp?cmd=2020). 
- Geospatial data for water service boundaries. [California Drinking Water System Area Boundary Layer (SABL)](https://www.arcgis.com/home/item.html?id=b2b64ea93a954b7caab0f0999f47e019). 

### Output data
All simulation outputs are available at:
Ferencz, S., Yoon, J., & Vernon, C. (2026). Sensitivity Analysis of Drivers Water Shortage in the Los Angeles Region During Drought (Version v1) [Data set]. MSD-LIVE Data Repository. https://doi.org/10.57931/3363338

## Contributing modeling software
| Model | Version | Repository Link | Usage |
|-------|---------|-----------------|-------|
| IPOPT   | 3.11.1  | https://github.com/coin-or/Ipopt | optimization solver | 
| Pyomo   | 6.4.4 | https://www.pyomo.org/ | optimization programming |
| SALIb   | 1.4.7 | https://github.com/SALib/SALib | Sobol sensitivity sampling and analysis |
| scikit-learn | 1.0.2 | https://scikit-learn.org | multilayer perceptron shortage emulator |
| GeoPandas | 0.9.0 | https://geopandas.org/ | geospatial visualization |

## Reproduce my experiment

1. Install the software components required to conduct the experiment from [contributing modeling software](#contributing-modeling-software)
2. The entire experiment workflow is documented in the Workflow directory. Each step builds on the outputs from the previous step. ReadMe files in each subdirectory of Workflow describe the inputs and outputs of each step.
3. Code for analysis and visualization is provided the Figures directory. Large file size outputs used for analysis are stored in the associated [MSDLive repository](https://doi.org/10.57931/3363338) and need to be downloaded for analysis. 

| Script Name | Description | How to Run |
| --- | --- | --- |
| `step_one.py` | Script to run the first part of my experiment | `python3 step_one.py -f /path/to/inputdata/file_one.csv` |
| `step_two.py` | Script to run the second part of my experiment | `python3 step_two.py -o /path/to/my/outputdir` |

## Reproduce my figures
Use the scripts found in the `figures` directory to reproduce the figures used in this publication.

| Figure Number(s) | Script Name | Description | How to Run |
| --- | --- | --- | --- |
| 1, 2 | `generate_plot.py` | Description of figure, ie. "Plots the difference between our two scenarios" | `python3 generate_plot.py -input /path/to/inputs -output /path/to/outuptdir` |
| 3 | `generate_figure.py` | Description of figure, ie. "Shows how the mean and peak differences are calculated" | `python3 generate_figure.py -input /path/to/inputs -output /path/to/outuptdir` |

