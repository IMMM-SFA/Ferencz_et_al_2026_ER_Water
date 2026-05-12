# -*- coding: utf-8 -*-
import seaborn as sns
import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

output_path = "C:/Users/fere556/OneDrive - PNNL/Documents/Artes/Artes_paper/LA_Sensitivity_Analysis_Repo/MSDLive/Ensemble_13312/output_sobol_13312/"

#%% Aggregate outputs 

num_scenarios = 13312 # enter # of rows (scenarios) in the paramater multiplier array

sim_name = 'scenario' # name of ensemble, used as prefix for output file names

# Structure of DataFrame for aggregated ouputs is rows are ids and columns
# are the cumulative shortage for each ensemble 
indoor_shortage = pd.read_csv(output_path + sim_name + "_row_0_indoor_shortage.csv")
outdoor_shortage = pd.read_csv(output_path + sim_name + "_row_0_outdoor_shortage.csv")

indoor_shortage_ids = indoor_shortage.iloc[:,0]
outdoor_shortage_ids = outdoor_shortage.iloc[:,0]

indoor_shortage_ids_root = []
outdoor_shortage_ids_root = []

for i in range(len(indoor_shortage_ids)):
    if indoor_shortage_ids[i] == 'INF_CSB':
        indoor_shortage_ids_root.append(indoor_shortage_ids[i])
    else:
        indoor_shortage_ids_root.append(indoor_shortage_ids[i][:-7])

for i in range(len(outdoor_shortage_ids)):
    outdoor_shortage_ids_root.append(outdoor_shortage_ids[i][:-8])
    

demand_root_ids = indoor_shortage_ids_root + outdoor_shortage_ids_root
demand_root_ids = list(set(demand_root_ids))
demand_root_ids.sort()

shortage_sensitivity_total = pd.DataFrame(data = np.zeros((num_scenarios,len(demand_root_ids))), columns = demand_root_ids) 
shortage_sensitivity_indoor = pd.DataFrame(data = np.zeros((num_scenarios,len(demand_root_ids))), columns = demand_root_ids) 
shortage_sensitivity_outdoor = pd.DataFrame(data = np.zeros((num_scenarios,len(demand_root_ids))), columns = demand_root_ids) 
LAC_shortage_sensitivity = pd.DataFrame(data = np.zeros((num_scenarios,1)), columns = ['total_shortage']) 


for i in range(num_scenarios):

    file_name_indoor = sim_name + "_row_" + str(i) + "_indoor_shortage.csv"
    file_name_outdoor = sim_name + "_row_" + str(i) + "_outdoor_shortage.csv"
    
    # Import output files 
    try:
        indoor_shortage = pd.read_csv(output_path + file_name_indoor, index_col = 0)
        outdoor_shortage = pd.read_csv(output_path + file_name_outdoor, index_col = 0)

    except FileNotFoundError:
        
        print("no ipopt output for scenario #" + str(i))
        continue
    
    # Add scenario shortage results to output arrays 
    LAC_shortage_sensitivity.iloc[i, 0] = sum(sum(indoor_shortage.values)) + sum(sum(outdoor_shortage.values))
    
    for n in range(len(demand_root_ids)):
        indoor_shortage_total = 0
        outdoor_shortage_total = 0 
        
        for m in range(len(indoor_shortage_ids_root)):
            
            if demand_root_ids[n] == 'INF_CSB':
                indoor_shortage_total = sum(indoor_shortage.loc['INF_CSB'][-12:])
                break
            
            elif demand_root_ids[n] == indoor_shortage_ids[m][:-7]:
                indoor_shortage_total = sum(indoor_shortage.loc[indoor_shortage_ids[m]][-12:])
                break 
        
            else:
                pass
            
        for m in range(len(outdoor_shortage_ids_root)):
            if demand_root_ids[n] == outdoor_shortage_ids[m][:-8]:
                outdoor_shortage_total = sum(outdoor_shortage.loc[outdoor_shortage_ids[m]][-12:])
                break 
            else: 
                pass
            
        total_shortage = indoor_shortage_total + outdoor_shortage_total
        shortage_sensitivity_total.iloc[i,n] = total_shortage 
        shortage_sensitivity_indoor.iloc[i,n] = indoor_shortage_total
        shortage_sensitivity_outdoor.iloc[i,n] = outdoor_shortage_total

# Save ensemble shortage results 
os.chdir(output_path)
LAC_shortage_sensitivity.to_csv("LAC_shortage_" + sim_name + ".csv")
shortage_sensitivity_total.to_csv("total_shortage_" + sim_name + ".csv")
shortage_sensitivity_indoor.to_csv("indoor_shortage_" + sim_name + ".csv") 
shortage_sensitivity_outdoor.to_csv("outdoor_shortage_" + sim_name + ".csv")
