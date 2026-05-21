import os 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas

os.chdir("Path to Figure_2_files")
provider_groups = pd.read_csv("Provider_MWD_groupings.csv")
demand_indoor_artes = pd.read_csv("Artes_V0_indoor_demand_baseline.csv", index_col = 0)
demand_outdoor_artes = pd.read_csv("Artes_V0_outdoor_demand_baseline_adjusted_for_reuse.csv", index_col = 0)
demand_id = pd.read_csv("Demand_node_root_ids.csv") 
demand_id = list(demand_id.ID[:])

demand_baseline = pd.DataFrame(data = np.zeros((101, 3)), columns = ['demand_indoor','demand_outdoor','demand_total'], index = demand_id)

# Aggregate total demands by demand root_id (e.g., CTY_ALH = CTY_ALH_Indoor + CTY_ALH_Outdoor)
for i in range(101):
    for j in range(101):
        if demand_id[i] == demand_indoor_artes.ID[j][:-7]:
            demand_baseline.iloc[i,0] = demand_indoor_artes.iloc[j,2:14].sum()

for i in range(101):
    for j in range(97):
        if demand_id[i] == demand_outdoor_artes.ID[j][:-8]:
            demand_baseline.iloc[i,1] = demand_outdoor_artes.iloc[j,2:14].sum()
            
demand_baseline.demand_total = demand_baseline.demand_indoor + demand_baseline.demand_outdoor

provider_groups = provider_groups.iloc[:, 0:7]
provider_groups = pd.merge(provider_groups, demand_baseline, left_on='Demand_node', 
                            right_index = True, how='inner')  
group_by_region = provider_groups.groupby(['MWD_region']).sum()
group_by_region.loc['Total'] = group_by_region.sum()

# Create features 
provider_groups['total_supply'] = np.sum(provider_groups.iloc[:,3:7], axis = 1)
provider_groups['GW_frac'] = provider_groups.GW/provider_groups.demand_total
provider_groups['Reuse_frac'] = provider_groups.Reuse/provider_groups.demand_total
provider_groups['Import_frac'] = provider_groups.Imports/provider_groups.demand_total
provider_groups['ratio_Supply_Demand'] = provider_groups.total_supply/provider_groups.demand_total
provider_groups['fraction_outdoor_Demand'] = provider_groups.demand_outdoor/provider_groups.demand_total

#%% Mapping 
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
    
provider_supply = pd.merge(service_bnds, provider_groups, left_on='Artes_serv', 
                            right_on = 'Demand_node', how='inner')    

provider_supply.drop(57, inplace = True)

# Map of provider groups 
ax = provider_supply.plot(column = 'MWD_region', edgecolor = None, legend = False)
plt.tight_layout()
ax.set_axis_off()



# Map of individual provider supply sources, ratio of supply source to total demand
ax = provider_supply.plot(column = 'GW_frac', vmin = 0, vmax = 1, cmap = 'Blues', 
                          edgecolor = None, legend = True)
ax.set_axis_off()

ax = provider_supply.plot(column = 'Import_frac', vmin = 0, vmax = 1, cmap = 'Oranges'
                          , edgecolor = None, legend = True)
ax.set_axis_off()

ax = provider_supply.plot(column = 'Reuse_frac', vmin = 0, vmax = 0.5, cmap = 'Purples'
                          , edgecolor = None, legend = True)
ax.set_axis_off()

# ax = provider_supply.plot(column = 'ratio_Supply_Demand', vmin = 1, vmax = 3, cmap = 'seismic', edgecolor = None, legend = True)
# ax.set_axis_off()

ax = provider_supply.plot(column = 'fraction_outdoor_Demand', vmin = 0.1, vmax = 0.6, 
                          cmap = 'BrBG', edgecolor = None, legend = True)
ax.set_axis_off()

#%% Optional Bonus: Demand and Supply pie charts for MWD wholesale regions 
#            MWD = MWD independant retailers 

# Data for the pie chart
labels = ['Imports', 'GW', 'Reuse'] #, 'Surface']
colors = ['lightgray', 'grey', 'black']
for i in range(7):
    # Create the pie chart
    plt.pie(group_by_region.iloc[i,0:3], colors = colors, startangle=90)
    
    # Add a title
    plt.title(group_by_region.index[i])
    
    # Ensure the circle is drawn as a circle and not an ellipse
    plt.axis('equal')
    
    # Display the chart
    plt.show()
    

# Data for the pie chart
labels = ['Indoor', 'Outdoor'] #, 'Surface']

for i in range(7):
    # Create the pie chart
    plt.pie(group_by_region.iloc[i,4:6], colors = ['bisque','palegreen'], startangle=90)
    
    # Add a title
    plt.title(group_by_region.index[i])
    
    # Ensure the circle is drawn as a circle and not an ellipse
    plt.axis('equal')
    
    # Display the chart
    plt.show()
    
