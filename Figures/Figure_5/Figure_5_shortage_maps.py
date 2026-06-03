import os 
import numpy as np
import pandas as pd
import geopandas

os.chdir("Path to Figure_5_files") # add simulated outputs shortage data to this folder  

# this File or Files are in the Simulated_outputs folder of the MSDLive repo
total_shortage = pd.read_csv("worst_year_total_shortage_full_ensemblescenario.csv", index_col = 0) # used for paper 
#outdoor_shortage = pd.read_csv("outdoor_shortage_test_ensemble.csv", index_col = 0) # could plot outdoor only 
#indoor_shortage = pd.read_csv("indoor_shortage_test_ensemble.csv", index_col = 0) # or indoor only 

# All other files are located in the Figure_5_files folder 
scenarios = pd.read_csv("param_values_13312_sobol_HPC.csv", index_col = 0) # scenario multipliers, used for the Table in Figure 5 

demand_indoor_artes = pd.read_csv('Artes_V0_indoor_demand_baseline.csv', index_col = 0)
demand_outdoor_artes = pd.read_csv('Artes_V0_outdoor_demand_baseline_adjusted_for_reuse.csv', index_col = 0)
demand_id = total_shortage.columns 

demand_baseline = pd.DataFrame(data = np.zeros((101, 3)), columns = ['indoor','outdoor','total'], index = demand_id)
for i in range(101):
    for j in range(101):
        if demand_id[i] == demand_indoor_artes.ID[j][:-7]:
            demand_baseline.iloc[i,0] = demand_indoor_artes.iloc[j,2:14].sum()

for i in range(101):
    for j in range(97):
        if demand_id[i] == demand_outdoor_artes.ID[j][:-8]:
            demand_baseline.iloc[i,1] = demand_outdoor_artes.iloc[j,2:14].sum()
            
demand_baseline.total = demand_baseline.indoor + demand_baseline.outdoor
demand_baseline.total.sum()
demand_baseline.loc['LAC'] = {'indoor': sum(demand_baseline.indoor), 'outdoor': sum(demand_baseline.outdoor)
                              , 'total': sum(demand_baseline.total)}

total_shortage['LAC'] = total_shortage.sum(axis = 1) # Calculate total regional shortage 

#%% Map outdoor shortage for selected scenario (row of scenarios dataframe)
# For figure 5 
# scenario row: 13, 430, 364, 551

shortage = total_shortage.loc[430]/demand_baseline.total # can select total or outdoor
shortage.name = 'shortage'

service_bnds = geopandas.read_file("Artes_service_regions_updated.shp") # shapefile of provider boundaries  
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

# merge shortage dataframe with service_bnd shapefile for plotting geospatial results 
provider_shortage = pd.merge(service_bnds, shortage, left_on='Artes_serv', 
                            right_index = True, how='inner')    

ax = provider_shortage.plot(column = "shortage", vmin = 0, vmax = 0.5, cmap = 'magma_r', edgecolor = None, legend = True)
ax.set_axis_off()

# ax = provider_shortage.plot(column = '20_perc', vmin = 0, vmax = 1, cmap = 'magma_r', edgecolor = None, legend = True)
# ax.set_axis_off()