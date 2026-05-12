import SALib as SALib
from SALib import ProblemSpec
import numpy as np
import pandas as pd 
import os 

# path to parameters file 
os.chdir("C:/Users/fere556/OneDrive - PNNL/Documents/Artes/Artes_paper/LA_Sensitivity_Analysis_Repo/GitHub/Step_1_generate_sensitivity_ensemble")

# Artes experiment parameters defined csv with parameters and multiplier bounds 
parameter_df = pd.read_csv("SALib_parameter_ranges.csv")

# define problem
problem = {'num_vars': len(parameter_df.Parameter),
           'names': list(parameter_df.Parameter.values),
           'bounds': list(parameter_df.iloc[:,1:3].values)
           }

sp = ProblemSpec({'num_vars': len(parameter_df.Parameter),
           'names': list(parameter_df.Parameter.values),
           'bounds': list(parameter_df.iloc[:,1:3].values)
           })

# sample parameter ranges to generate sensitivity analysis scenario ensembles 

column_names = list(parameter_df.Parameter.values)
sample_base = 2*12+2 # 2*D+2 for second order Sobol inidices, D = # of parameters
samples = [4, 8, 16, 32, 64, 128, 256, 512] # sample size of 512 used for 13,312 scenario ensemble, ensemble size = n samples * sample_base
sample_distributions = pd.DataFrame(data = np.zeros((len(samples), len(column_names))),
                                    columns = column_names, index = samples) # records number unique parameter samples for each ensemble

for i in range(len(samples)):
    param_values_saltelli = SALib.sample.sobol.sample(problem, samples[i])
    
    # Save param array to DataFrame with field names 
    param_values_df = pd.DataFrame(data = param_values_saltelli, 
                                   columns = parameter_df.Parameter.values)
    
    for j in range(len(column_names)):
        sample_distributions.iloc[i,j] = len(param_values_df.iloc[:,j].unique())
    
    # Save 
    param_values_df.to_csv("param_values_" + str(samples[i]*(2*12+2)) + "_sobol.csv")


