import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas

# Sobol results from the synthetic ensembles are available at the MSDLive repository 
# MLP_generated_shortages. These are outputs from Step 4 of the Workflow 

# Change to folder with Sobol results you want to plot, this uses the MWD higher import 
# range of 500,000 to 700,000 acre-feet/year. 
#os.chdir("../MLP_generated_shortages/mwd_higher/") 

result_S1 = pd.read_csv("param_values_26624_sobol_emulator_mwd_higher.csv_s1.csv", index_col = 0) # S1 results
result_ST = pd.read_csv("param_values_26624_sobol_emulator_mwd_higher.csv_sT.csv", index_col = 0) # ST results

top_3_S1 = pd.DataFrame(columns = ['first', 'second', 'third'], index = result_S1.index)
top_3_ST = pd.DataFrame(columns = ['first', 'second', 'third'], index = result_ST.index)

for i in range(101):
    order = result_S1.iloc[i,:].sort_values(ascending=False).index
    top_3_S1.iloc[i,:] = order[0:3]
    
for i in range(101):
    order = result_ST.iloc[i,:].sort_values(ascending=False).index
    top_3_ST.iloc[i,:] = order[0:3]


#%% Figure 6: Mapping ranked ST (or S1) results. This maps the top 3. 
#             Only the top 2 were used in the paper.
 
# service_bnds = have the service region shapefile in data folder or load from path to where it is stored
# this shapefile available in the Figure 2 and Figure 5 github Figure files 
# and also the Supporting_data folder of the MSDLive repo
service_bnds = geopandas.read_file("Artes_service_regions_updated.shp")
service_bnds = service_bnds.to_crs(epsg=3857) # convert CRS to basemap CRS 

service_bnds = service_bnds.where(service_bnds.Artes_se_3 == 1)
service_bnds = service_bnds.dropna(thresh = 3)
service_bnds = service_bnds.reset_index(drop = True)

for i in range(92):
    if service_bnds.Artes_serv[i][0:7] == 'IOU_PWC':
        service_bnds.Artes_serv[i] = 'IOU_PWC'
    elif service_bnds.Artes_serv[i][0:11] == 'IOU_SWS_WLM':
        service_bnds.Artes_serv[i] = 'IOU_SWS_WLM'
    else:
        continue 
    
provider_S1_rank = pd.merge(service_bnds, top_3_S1, left_on='Artes_serv', 
                            right_index = True, how='inner')

provider_ST_rank = pd.merge(service_bnds, top_3_ST, left_on='Artes_serv', 
                            right_index = True, how='inner')

# Create a dictionary for custom color mapping
SA_colors = {
    'imports_met': 'purple',
    'imports_laa': 'violet',
    'gw_yield_other': 'navy',
    'gw_cen': 'blue',
    'gw_wcb': 'aqua',
    'gw_sgb': 'cyan',
    'gw_sf': 'slategray',
    'reuse': 'tomato',
    'initial_storage': 'gold',
    'dummy': 'white',
    'indoor_eff': 'limegreen',
    'outdoor_eff': 'seagreen'
}

# Replace "provider_ST_rank" with "provider_S1_rank" for S1 results (provided in Supplement of paper)
index_rank = ['first', 'second', 'third']
for i in range(3):
    provider_ST_rank['color'] = provider_ST_rank[index_rank[i]].map(SA_colors)
    
    ax = provider_ST_rank.plot(column = provider_ST_rank[index_rank[i]], legend = True, 
                               categorical=True, color=provider_ST_rank['color'], edgecolor = None)
    ax.set_axis_off()
    ax.set_title(index_rank[i] + ' ST')

#%% Figure 7: Sobol ST (or S1) distributions with region LAC value 

# merge Sobol results with provider groupings 
# import provider groupings - available in Figure_6_and_7 files
provider_groups_labels = pd.read_csv("Provider_MWD_groupings.csv")

result_ST = result_ST.drop("dummy", axis = 1) # drop "dummy" which was a sobol parameter that had no relation to the Artes model 
result_S1 = result_S1.drop("dummy", axis = 1)

S1_grps = pd.merge(result_S1, provider_groups_labels, left_index=True,
                                right_on = 'Demand_node', how = 'inner')
ST_grps = pd.merge(result_ST, provider_groups_labels, left_index=True,
                                right_on = 'Demand_node', how = 'inner')

# aggregate ST (or S1) parameters for efficiency, groundwater, and imports 
result_ST['eff_total'] = result_ST['indoor_eff'] + result_ST['outdoor_eff']
result_ST['gw_total'] = result_ST['gw_yield_other'] + result_ST['gw_cen'] + result_ST['gw_wcb'] + result_ST['gw_sgb'] + result_ST['gw_sf']
result_ST['imports_total'] = result_ST['imports_met'] + result_ST['imports_laa'] 

result_S1['eff_total'] = result_S1['indoor_eff'] + result_S1['outdoor_eff']
result_S1['gw_total'] = result_S1['gw_yield_other'] + result_S1['gw_cen'] + result_S1['gw_wcb'] + result_S1['gw_sgb'] + result_S1['gw_sf']
result_S1['imports_total'] = result_S1['imports_met'] + result_S1['imports_laa'] 

import seaborn as sns
df = ST_grps.copy() # change to S1_grps for S1 results 
drop = ['INF_CSB', 'IRR_KIN', 'CTY_IND', 'IRR_SMT','MWD']
df = df[~df['Demand_node'].isin(drop)]

# optional filter by region
#df = df[df['MWD_region'] == 'West Basin MWD']
df = df.iloc[:, :-2]
df['eff_total'] = df['indoor_eff'] + df['outdoor_eff']
df['gw_total'] = df['gw_yield_other'] + df['gw_cen'] + df['gw_wcb'] + df['gw_sgb'] + df['gw_sf']
df['imports_total'] = df['imports_met'] + df['imports_laa'] 

# Melt to long format
long = df.melt(var_name='Parameter', value_name='Value')

SA_colors = {
    'imports_met': 'purple',
    'imports_laa': 'violet',
    'gw_yield_other': 'navy',
    'gw_cen': 'blue',
    'gw_wcb': 'cornflowerblue',
    'gw_sgb': 'cyan',
    'gw_sf': 'slategray',
    'reuse': 'tomato',
    'initial_storage': 'gold',
    'indoor_eff': 'limegreen',
    'outdoor_eff': 'seagreen',
    'eff_total': 'green',
    'gw_total': 'blue',
    'imports_total': 'magenta'
}

# change result_ST to result_S1 for S1 results for LAC
# Basic violin plot
plt.figure(figsize=(5, 5), dpi = 300)
sns.violinplot(data=long, x='Parameter', y='Value', palette = SA_colors, linewidth=0.0, inner='quartile', cut=0, scale='width')
plt.scatter(np.arange(14), result_ST.loc['LAC'], color = 'white', s = 10)
plt.xticks(rotation=90)
plt.ylim([0,1])
plt.grid(True)
plt.title('ST Distributions: MWD Less Severe (MWD higher)') # change lable to S1 for S1 results
plt.tight_layout()
