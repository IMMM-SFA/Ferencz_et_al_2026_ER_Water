# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os 
import geopandas
import contextily as cx

#%% Import Artes data 

os.chdir("Path to Figure_3 files")

LAC_bounds = geopandas.read_file("LAC_region_boundary.shp") 
Node_df = pd.read_csv("Artes_nodes_GIS.csv")
Artes_df = geopandas.read_file("Artes_Nodes.shp")  
links = pd.read_csv("Links_PyArtes.csv")
link_key = pd.read_csv("Link_Key_PyArtes.csv")

#%% Process data 

# Populate links.type with Link Key information from Artes 
for i in range(len(links.iloc[:,0])):
    for j in range(len(link_key.iloc[:,0])):
        if links.From[i] == link_key.Origin_Node[j] and \
            links.To[i] == link_key.End_Node[j]:
            links.Type[i] = link_key.Type[j]
            continue

# Add coordinates to links using Artes_df node coordinates 
for i in range(len(links.iloc[:,0])): 
    for j in range(len(Node_df.iloc[:,0])):
        if links.From[i] == Node_df.Artes_ID[j]:
            links.From_X[i] = Node_df.X[j]
            links.From_Y[i] = Node_df.Y[j]
        if links.To[i] == Node_df.Artes_ID[j]:
            links.To_X[i] = Node_df.X[j]
            links.To_Y[i] = Node_df.Y[j]

# Drop rows where To or From node coordinates are missing 
for i in range(len(links.iloc[:,0])): 
    for j in range(4):
        if links.iloc[i,3+j] == 0:
            links.iloc[i,3+j] = np.nan

links = links.dropna()

#%% 
Artes_df = Artes_df.to_crs(epsg=3857) # convert CRS to basemap CRS 
LAC_bounds = LAC_bounds.to_crs(epsg=3857)

#%%
fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
# ylim = ([3.98E6 ,4.08E6])
# xlim = ([-1.325E7, -1.309E7])
# ax.set_xlim(xlim)
# ax.set_ylim(ylim)

# Plot "GeoDataFrame"
for i in range(len(links.iloc[:,0])): 
    ax.plot([links.iloc[i,3], links.iloc[i,5]], [links.iloc[i,4], links.iloc[i,6]], color = 'red', alpha = 0.5)
#Artes_df.plot(column = Artes_df.Type , figsize=(10, 10), ax = ax, legend = True)
Artes_df.plot(color = 'black', ax = ax)
LAC_bounds.plot(ax = ax, color = "none", edgecolor = "Black")
#Artes_df.plot(color = 'gray' , figsize=(10, 10), ax = ax)
#x.add_basemap(ax)


#%%  

links_gw = links.copy()
links_gw['filter'] = np.zeros(len(links_gw))

links_gw = links_gw.where(links_gw.Type[:] == 'Groundwater') 
links_gw = links_gw.dropna()

nodes_gw = Artes_df.copy()
nodes_gw['filter'] = np.zeros(len(nodes_gw))
nodes_gw_list = links_gw.From[:].unique()
nodes_gw_list = np.concatenate((nodes_gw_list, links_gw.To[:].unique()), axis = 0)
for i in range(len(nodes_gw.iloc[:,0])):
    for j in range(len(nodes_gw_list)):
        if nodes_gw.Artes_ID[i] == nodes_gw_list[j]:
            nodes_gw.iloc[i,6] = 1

nodes_gw = nodes_gw.where(nodes_gw.iloc[:,6] == 1) 
nodes_gw = nodes_gw.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
# ylim = ([3.99E6 ,4.08E6])
# xlim = ([-1.320E7, -1.307E7])

# ax.set_xlim(xlim)
# ax.set_ylim(ylim)

# Plot "GeoDataFrame"
for i in range(len(links_gw.iloc[:,0])): 
    ax.plot([links_gw.iloc[i,3], links_gw.iloc[i,5]], \
            [links_gw.iloc[i,4], links_gw.iloc[i,6]], 
            color = 'blue', alpha = 0.5) #,
            #linewidth = links_gw.iloc[i,7]/10000)
#nodes_gw.plot(column = nodes_gw.Type, ax = ax, markersize = 25, legend = False)
nodes_gw.plot(color = 'black',ax = ax, markersize = 25, legend = False)
LAC_bounds.plot(ax = ax, color = "none", edgecolor = "Black")

# for x, y, label in zip(nodes_gw.geometry.x, nodes_gw.geometry.y, nodes_gw.Artes_ID):
#     ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
#cx.add_basemap(ax)
#cx.add_basemap(ax, zoom = 9, source=cx.providers.Stamen.TonerLite)

#%% Wastewater flows to plants

links_query = links.copy()
links_query['filter'] = np.zeros(len(links_query))

links_query = links_query.where(links_query.Type[:] == 'Wastewater') 
links_query = links_query.dropna()

for i in range(len(links_query.iloc[:,0])):
    if links_query.iloc[i,0][0:3] != 'WRP':
        links_query.iloc[i,8] = 1

links_query = links_query.where(links_query.iloc[:,8] == 1) 
links_query = links_query.dropna(thresh = 4)   

nodes_query = Artes_df.copy()
nodes_query['filter'] = np.zeros(len(nodes_query))
nodes_query_list = links_query.From[:].unique()
nodes_query_list = np.concatenate((nodes_query_list, links_query.To[:].unique()), axis = 0)
for i in range(len(nodes_query.iloc[:,0])):
    for j in range(len(nodes_query_list)):
        if nodes_query.Artes_ID[i] == nodes_query_list[j]:
            nodes_query.iloc[i,6] = 1

nodes_query = nodes_query.where(nodes_query.iloc[:,6] == 1) 
nodes_query = nodes_query.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
# ylim = ([3.99E6 ,4.08E6])
# xlim = ([-1.323E7, -1.307E7])

# ax.set_xlim(xlim)
# ax.set_ylim(ylim)

# Plot "GeoDataFrame"

for i in range(len(links_query.iloc[:,0])): 
    ax.plot([links_query.iloc[i,3], links_query.iloc[i,5]], \
            [links_query.iloc[i,4], links_query.iloc[i,6]], 
            color = 'Grey', alpha = 0.5, linewidth = 2) #,
            #linewidth = links_query.iloc[i,7])
#nodes_query.plot(column = nodes_query.Type, ax = ax, markersize = 25, legend = True)
nodes_query.plot(color = "Black", ax = ax, markersize = 25, legend = True)
LAC_bounds.plot(ax = ax, color = "none", edgecolor = "Black")
# for x, y, label in zip(nodes_gw.geometry.x, nodes_gw.geometry.y, nodes_gw.Artes_ID):
#     ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
cx.add_basemap(ax)

#%% Wastewater flows from plants 

links_query = links.copy()
links_query['filter'] = np.zeros(len(links_query))

for i in range(len(links_query.iloc[:,0])):
    if links_query.iloc[i,0][0:3] == 'WRP':
        links_query.iloc[i,8] = 1

links_query = links_query.where(links_query.iloc[:,8] == 1) 
links_query = links_query.dropna(thresh = 4)   

nodes_query = Artes_df.copy()
nodes_query['filter'] = np.zeros(len(nodes_query))
nodes_query_list = links_query.From[:].unique()
nodes_query_list = np.concatenate((nodes_query_list, links_query.To[:].unique()), axis = 0)
for i in range(len(nodes_query.iloc[:,0])):
    for j in range(len(nodes_query_list)):
        if nodes_query.Artes_ID[i] == nodes_query_list[j]:
            nodes_query.iloc[i,6] = 1

nodes_query = nodes_query.where(nodes_query.iloc[:,6] == 1) 
nodes_query = nodes_query.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
# ylim = ([3.99E6 ,4.08E6])
# xlim = ([-1.323E7, -1.307E7])

# ax.set_xlim(xlim)
# ax.set_ylim(ylim)

key = {'Recycling' : 'purple',
       'String' : 'purple',
       'Surface': 'blue',
       'Wastewater': 'black'}

# Plot "GeoDataFrame"

for i in range(len(links_query.iloc[:,0])): 
    ax.plot([links_query.iloc[i,3], links_query.iloc[i,5]], \
            [links_query.iloc[i,4], links_query.iloc[i,6]], 
            color = 'purple', alpha = 0.5) #,
            #linewidth = links_query.iloc[i,7])
#nodes_query.plot(column = nodes_query.Type, ax = ax, markersize = 25, legend = True)
nodes_query.plot(color = 'black', ax = ax, markersize = 25, legend = True)
LAC_bounds.plot(ax = ax, color = "none", edgecolor = "Black")
# for x, y, label in zip(nodes_gw.geometry.x, nodes_gw.geometry.y, nodes_gw.Artes_ID):
#     ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
#cx.add_basemap(ax)

#%% Imported flows from import recieving nodes to other model nodes 

links_query = links.copy()
links_query['filter'] = np.zeros(len(links_query))

links_query = links_query.where(links_query.Type[:] == 'Imported') 
links_query = links_query.dropna()

# for i in range(len(links_query.iloc[:,0])):
#     if links_query.iloc[i,0][0:3] != 'WRP':
# #         links_query.iloc[i,8] = 1

# links_query = links_query.where(links_query.iloc[:,8] == 1) 
# links_query = links_query.dropna(thresh = 4)   

nodes_query = Artes_df.copy()
nodes_query['filter'] = np.zeros(len(nodes_query))
nodes_query_list = links_query.From[:].unique()
nodes_query_list = np.concatenate((nodes_query_list, links_query.To[:].unique()), axis = 0)
for i in range(len(nodes_query.iloc[:,0])):
    for j in range(len(nodes_query_list)):
        if nodes_query.Artes_ID[i] == nodes_query_list[j]:
            nodes_query.iloc[i,6] = 1

nodes_query = nodes_query.where(nodes_query.iloc[:,6] == 1) 
nodes_query = nodes_query.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
ylim = ([3.98E6 ,4.08E6])
xlim = ([-1.325E7, -1.309E7])

ax.set_xlim(xlim)
ax.set_ylim(ylim)

# Plot "GeoDataFrame"

for i in range(len(links_query.iloc[:,0])): 
    ax.plot([links_query.iloc[i,3], links_query.iloc[i,5]], \
            [links_query.iloc[i,4], links_query.iloc[i,6]], 
            color = 'Orange', alpha = 0.5) #,
            #linewidth = links_query.iloc[i,7])
#nodes_query.plot(column = nodes_query.Type, ax = ax, markersize = 25, legend = True)
nodes_query.plot(color = 'black', ax = ax, markersize = 25, legend = False)
LAC_bounds.plot(ax = ax, color = "none", edgecolor = "Black")
# for x, y, label in zip(nodes_gw.geometry.x, nodes_gw.geometry.y, nodes_gw.Artes_ID):
#     ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
#cx.add_basemap(ax)

#%% Surface water nodes 

links_query = links.copy()
links_query['filter'] = np.zeros(len(links_query))

links_query = links_query.where(links_query.Type[:] == 'Surface') 
links_query = links_query.dropna()

# for i in range(len(links_query.iloc[:,0])):
#     if links_query.iloc[i,0][0:3] != 'WRP':
# #         links_query.iloc[i,8] = 1

# links_query = links_query.where(links_query.iloc[:,8] == 1) 
# links_query = links_query.dropna(thresh = 4)   

nodes_query = Artes_df.copy()
nodes_query['filter'] = np.zeros(len(nodes_query))
nodes_query_list = links_query.From[:].unique()
nodes_query_list = np.concatenate((nodes_query_list, links_query.To[:].unique()), axis = 0)
for i in range(len(nodes_query.iloc[:,0])):
    for j in range(len(nodes_query_list)):
        if nodes_query.Artes_ID[i] == nodes_query_list[j]:
            nodes_query.iloc[i,6] = 1

nodes_query = nodes_query.where(nodes_query.iloc[:,6] == 1) 
nodes_query = nodes_query.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
ylim = ([3.99E6 ,4.08E6])
xlim = ([-1.323E7, -1.307E7])

ax.set_xlim(xlim)
ax.set_ylim(ylim)

# Plot "GeoDataFrame"

for i in range(len(links_query.iloc[:,0])): 
    ax.plot([links_query.iloc[i,3], links_query.iloc[i,5]], \
            [links_query.iloc[i,4], links_query.iloc[i,6]], 
            color = 'blue', alpha = 0.5) #,
            #linewidth = links_query.iloc[i,7])
nodes_query.plot(column = nodes_query.Type, ax = ax, markersize = 25, legend = True)
# for x, y, label in zip(nodes_gw.geometry.x, nodes_gw.geometry.y, nodes_gw.Artes_ID):
#     ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
cx.add_basemap(ax)


#%% Flows from reservoirs

# Reservoirs 
sources = ['INF_SWP','INF_COL','SUR_OWN']
links_imports = links.copy()
links_imports['filter'] = np.zeros(len(links_imports))

for i in range(len(links_imports)):
    for j in range(len(sources)):
        if links_imports.iloc[i,0] == sources[j]:
            links_imports.iloc[i,8] = 1

links_imports = links_imports.where(links_imports.iloc[:,8] == 1) 
links_imports = links_imports.dropna()

nodes_imports = Artes_df.copy()
nodes_imports['filter'] = np.zeros(len(nodes_imports))
nodes_imports_list = links_imports.From[:].unique()
nodes_imports_list = np.concatenate((nodes_imports_list, links_imports.To[:].unique()), axis = 0)
for i in range(len(nodes_imports.iloc[:,0])):
    for j in range(len(nodes_imports_list)):
        if nodes_imports.Artes_ID[i] == nodes_imports_list[j]:
            nodes_imports.iloc[i,6] = 1

nodes_imports = nodes_imports.where(nodes_imports.iloc[:,6] == 1) 
nodes_imports = nodes_imports.dropna(thresh = 4)     

fig, ax = plt.subplots(figsize = (10,10))

# ylim = ([3.95E6 ,4.40E6])
# xlim = ([-1.33E7, -1.300E7])
ylim = ([3.95E6 ,4.125E6])
xlim = ([-1.325E7, -1.300E7])

ax.set_xlim(xlim)
ax.set_ylim(ylim)

# Plot "GeoDataFrame"
key = {'INF_SWP' : 'blue',
       'INF_COL' : 'black',
       'SUR_OWN': 'red'}

for i in range(len(links_imports.iloc[:,0])): 
    ax.plot([links_imports.iloc[i,3], links_imports.iloc[i,5]], \
            [links_imports.iloc[i,4], links_imports.iloc[i,6]], 
            color = key[links_imports.iloc[i,0]], 
            linewidth = links_imports.iloc[i,7]/300000, alpha = 0.5)
nodes_imports.plot(column = nodes_imports.Type, ax = ax, markersize = 50, legend = True)
for x, y, label in zip(nodes_imports.geometry.x, nodes_imports.geometry.y, nodes_imports.Artes_ID):
    ax.annotate(label, xy=(x, y), xytext=(3, -3), textcoords="offset points")
cx.add_basemap(ax)
#cx.add_basemap(ax, zoom = 9, source=cx.providers.Stamen.TonerLite)
