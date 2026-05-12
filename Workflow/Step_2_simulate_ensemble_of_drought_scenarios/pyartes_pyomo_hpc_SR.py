import os
import argparse
import numpy as np
import pandas as pd
from pyomo.environ import (
    ConcreteModel, 
    SolverFactory, 
    Var, 
    NonNegativeReals, 
    Set, 
    Constraint, 
    Objective, 
    minimize, 
    SolverStatus, 
    TerminationCondition,
    exp
)

def run_scenario(
    scenario: int,
    input_path: str,
    output_path: str,
    scenarios_file: str,
    save: bool = True,
):

    # parameter multiplier scenarios (each row is a scenario)
    scenarios = pd.read_csv(scenarios_file) #, index_col=0)
    sim_name = 'scenario_row_' + str(scenarios.scenario[scenario]) 

    # Define the months and (multiple) years for the simulation
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    # Define years. (here we run 3 years).
    years = [0,1,2]


    # Input files
    links_file = os.path.join(input_path, "Artes_V0_links_baseline_QC.csv")
    reuse_links_file = os.path.join(input_path, "Artes_V0_reuse_links_final.csv")
    managed_aquifer_recharge_links_file = os.path.join(input_path, "Artes_V0_sb_links.csv")
    inflow_timeseries_file = os.path.join(input_path, "Artes_V0_monthly_inflows.csv")
    initial_storage_file = os.path.join(input_path, "Artes_V0_storage_initial.csv")
    storage_properties_file = os.path.join(input_path, "Artes_V0_storage_modified_DVR.csv")
    groundwater_withdrawl_constraints_file = os.path.join(input_path, "Artes_V0_GWBs.csv")
    wastewater_plant_capacity_file = os.path.join(input_path, "Artes_V0_wrp_capacities.csv")
    wastewater_plant_reuse_capacity_file = os.path.join(input_path, "Artes_V0_wrp_reuse_capacity.csv")
    spreading_basin_capacity_file = os.path.join(input_path, "Artes_V0_sb_capacities.csv")
    import_monthly_fractions_file = os.path.join(input_path, "Import_monthly_fractions.csv")
    supply_links_file = os.path.join(input_path, "Artes_V0_supply_links_baseline.csv")

    indoor_demand_file = os.path.join(input_path, "Artes_V0_indoor_demand_baseline.csv")
    outdoor_demand_file = os.path.join(input_path, "Artes_V0_outdoor_demand_baseline_adjusted_for_reuse.csv")
    outdoor_eff_target_file = os.path.join(input_path, "efficiency_target_outdoor.csv") # NEW 
    indoor_eff_target_file = os.path.join(input_path, "efficiency_target_indoor.csv") # NEW
        
    # Read other input files
    import_monthly_fractions = pd.read_csv(import_monthly_fractions_file, index_col=0)

    dry_years = ['1987', '1988','1989','1990','1991','1992','2007','2008','2009','2010']
    indx = [1,2,3,4,5,6,21,22,23,24] # positional indexes for dry year imports 
    mean_monthly_fractions_drought = np.mean(import_monthly_fractions.iloc[indx, :], axis=0)

    demand_indoor_artes = pd.read_csv(indoor_demand_file, index_col=0)
    demand_outdoor_artes = pd.read_csv(outdoor_demand_file, index_col=0)
    
    indoor_demand_ids = list(demand_indoor_artes.iloc[:,0])
    outdoor_demand_ids = list(demand_outdoor_artes.iloc[:,0])

    inflows_hist = pd.read_csv(inflow_timeseries_file, index_col=0)
    inflows_monthly_avg_dry = pd.DataFrame(data=np.zeros((len(inflows_hist.iloc[:,0]),12)))
    inflows_monthly_avg_dry.insert(0, 'ID', inflows_hist.ID)
    inflow_times = list(inflows_hist.columns)
    inflow_times.pop(0)
    for i in range(len(inflow_times)):
        if inflow_times[i][0:4] in dry_years:
            pass
        else:
            column_id = inflow_times[i]
            inflows_hist = inflows_hist.drop([column_id], axis=1)
    for i in range(len(inflows_hist.iloc[:,0])):
        location_inflow_array = np.zeros((len(dry_years),12))
        for j in range(len(dry_years)):
            location_inflow_array[j,:] = inflows_hist.iloc[i, 1+12*j:1+12*(j+1)]
        inflows_monthly_avg_dry.iloc[i,1:13] = np.mean(location_inflow_array, axis=0)
    inflows_modified = inflows_monthly_avg_dry.copy()

    # -------------------- Parameters & Fixed Data --------------------
    reuse_multiplier = scenarios.reuse[scenario] # scenario = row of sensitivity parameter multiplier dataframe
    link_monthly_multiplier = 0.25
    link_annual_multiplier = 1 
    inflow_multiplier = 1
    initial_res_storage_multiplier = scenarios.initial_storage[scenario] 

    # Separate MULTIPLIERS FOR IMPORTS AND GW 
    mean_import_LAA = 1 * 10**5 # ac-ft/yr
    mean_import_MWD = 7 * 10**5 # ac-ft/yr
    
    import_multiplier_LAA = scenarios.imports_laa[scenario]
    import_multiplier_MWD = scenarios.imports_met[scenario]
     
    gw_multiplier = scenarios.gw_yield_other[scenario]
    gw_multiplier_CEN = scenarios.gw_cen[scenario]
    gw_multiplier_MSG = scenarios.gw_sgb[scenario]
    gw_multiplier_SFE = scenarios.gw_sf[scenario]
    gw_multiplier_WCS = scenarios.gw_wcb[scenario]
    
    # Demand MULTIPLIERS # NEW
    indoor_eff = scenarios.indoor_eff[scenario]
    outdoor_eff = scenarios.outdoor_eff[scenario] 

    # Links 
    links_table = pd.read_csv(links_file, index_col=0)
    arcs = [(row.Origin_Node, row.End_Node) for row in links_table.itertuples()] 

    capacity = {(arc[0], arc[1]): row.Capacity for arc, row in zip(arcs, links_table.itertuples())}
    reuse_links = pd.read_csv(reuse_links_file)
    reuse_arcs = [(row.Origin_Node, row.End_Node) for row in reuse_links.itertuples()]
    reuse_capacity = {}
    for idx, row in reuse_links.iterrows():
        if row['Origin_Node'] != '?':
            reuse_capacity[reuse_arcs[idx]] = row['Capacity'] * (1 + reuse_multiplier)
            
    mar_links = pd.read_csv(managed_aquifer_recharge_links_file)
    mar_arcs = [(row.Origin_Node, row.End_Node) for row in mar_links.itertuples()]
    # mar_capacity = {(arc[0], arc[1]): row.Capacity for arc, row in zip(mar_arcs, mar_links.itertuples())}

    # Storage 
    initial_storage_df = pd.read_csv(initial_storage_file, index_col=0)
    storage_properties_df = pd.read_csv(storage_properties_file, index_col=0)
    mask = initial_storage_df['Initial_Volume'] > 0
    initial_storage_df.loc[mask, 'Initial_Volume'] = storage_properties_df.loc[mask, 'Capacity_Max']
    storage_ids = storage_properties_df['ID'].tolist()
    storage_cap = dict(zip(storage_properties_df['ID'], storage_properties_df['Capacity_Max']))
    storage_min = dict(zip(storage_properties_df['ID'], storage_properties_df['Capacity_Min']))


    supply_links = pd.read_csv(supply_links_file, index_col=0)
    n_supply_links = int(len(supply_links) / 2)
    supply_link_arcs = [(supply_links.iloc[x*2, 0], supply_links.iloc[x*2, 2]) for x in range(n_supply_links)]
    supply_link_capacity = {arc: supply_links.iloc[i*2, 5] * link_annual_multiplier 
                            for i, arc in enumerate(supply_link_arcs)}

    gwb_constraints = pd.read_csv(groundwater_withdrawl_constraints_file)
    gw_limit = {}
    for node in range(len(gwb_constraints.iloc[:,0])):
        
        if gwb_constraints.ID[node] == "GWB_CEN":
            gw_limit[gwb_constraints.ID[node]] = gwb_constraints.Capacity[node] * gw_multiplier_CEN
        elif gwb_constraints.ID[node] == "GWB_MSG":
            gw_limit[gwb_constraints.ID[node]] = gwb_constraints.Capacity[node] * gw_multiplier_MSG 
        elif gwb_constraints.ID[node] == "GWB_SFE":
            gw_limit[gwb_constraints.ID[node]] = gwb_constraints.Capacity[node] * gw_multiplier_SFE
        elif gwb_constraints.ID[node] == "GWB_WCS":
            gw_limit[gwb_constraints.ID[node]] = gwb_constraints.Capacity[node] * gw_multiplier_WCS    
        else:
            gw_limit[gwb_constraints.ID[node]] = gwb_constraints.Capacity[node] * gw_multiplier

    wrp_capacity = pd.read_csv(wastewater_plant_capacity_file)
    wrp_limit = {row.ID: 10 * row.Artes_V0_capacities for row in wrp_capacity.itertuples()}
    wrp_reuse = pd.read_csv(wastewater_plant_reuse_capacity_file)
    wrp_reuse = wrp_reuse[wrp_reuse.Consider_deletion != 1].dropna(thresh=3).reset_index(drop=True)
    wrp_reuse_nodes = list(wrp_reuse['ID'])
    reuse_limit = {row.ID: row.Capacity_updated * (1 + reuse_multiplier) for row in wrp_reuse.itertuples()}

    sb_capacity = pd.read_csv(spreading_basin_capacity_file)
    sb_limit = {row.ID: row.Capacity for row in sb_capacity.itertuples()}
    outlet_nodes = {'SUR_PAC': 10**8}
    surface_nodes = storage_ids.copy()
    if 'SUR_PAC' in surface_nodes:
        surface_nodes.remove('SUR_PAC')

    # The node lists for indoor, outdoor, wrp, gw, and spreading basin are updated in each simulation year
    indoor_nodes = []   
    outdoor_nodes = []  
    wrp_nodes = []      
    gw_nodes = []       
    sb_nodes = []       

    # -------------------- Warm Start Placeholder --------------------
    previous_solution = {}

    # -------------------- Helper Functions for Pyomo --------------------
    def flow_bounds_rule(model, i, j, t):
        return (0, link_monthly_multiplier * capacity[(i, j)])

    def storage_bounds_rule(model, node, t):
        return (storage_min[node], storage_cap[node])

    def monthly_cap_rule(model, i, j, t):
        return model.flow[i, j, t] <= link_monthly_multiplier * capacity[(i, j)]

    def annual_cap_rule(model, i, j):
        total_flow = sum(model.flow[i, j, t] for t in model.months)
        if (i, j) in reuse_capacity:
            return total_flow <= reuse_capacity[(i, j)]
        else:
            return total_flow <= link_annual_multiplier * capacity[(i, j)]

    def mass_balance_rule(model, node, t):
        if node == 'SUR_PAC':
            return Constraint.Skip
        inflow_val = inflow[node][months.index(t)]
        if t == 'Jan':
            return (sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node)
                    + inflow_val + storage[node]
                    == sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node)
                    + model.losses_surface[node, t] + model.storage_vol[node, t])
        else:
            previous_t = months[months.index(t) - 1]
            return (sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node)
                    + inflow_val + model.storage_vol[node, previous_t]
                    == sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node)
                    + model.losses_surface[node, t] + model.storage_vol[node, t])

    def indoor_balance_rule(model, node, t):
        return sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node) == \
            sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node)

    def outdoor_balance_rule(model, node, t):
        return sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node) == \
            sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node) + model.losses_outdoor[node, t]

    def wrp_balance_rule(model, node, t):
        return sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node) == \
            sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node)

    def wrp_inflows_rule(model, node, t):
        return model.wrp_inflows[node, t] >= sum(model.flow[i, j, t] for (i, j) in model.arcs if i == node)

    def indoor_shortage_rule(model, node, t):
        return model.indoor_shortage[node, t] == demand_indoor[node][months.index(t)] - \
            sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node)

    def outdoor_shortage_rule(model, node, t):
        return model.outdoor_shortage[node, t] == demand_outdoor[node][months.index(t)] - \
            sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node)

    def outdoor_shortage_ratio_rule(model, node, t):
        return model.outdoor_shortage_ratio[node, t] == 10 * demand_outdoor[node][months.index(t)] * (model.outdoor_shortage[node, t] / demand_outdoor[node][months.index(t)]) * (model.outdoor_shortage[node, t] / demand_outdoor[node][months.index(t)])
    
    def indoor_shortage_ratio_rule(model, node, t):
        return model.indoor_shortage_ratio[node, t] == 10 * demand_indoor[node][months.index(t)] * (model.indoor_shortage[node, t] / demand_indoor[node][months.index(t)]) * (model.indoor_shortage[node, t] / demand_indoor[node][months.index(t)])

    def supply_annual_constraint_rule(model, i, j):
        supply_link_pair = [(i, j + '_INDOOR'), (i, j + '_OUTDOOR')]
        total_flow = sum(model.flow[a, b, t] for (a, b) in supply_link_pair for t in model.months)
        return total_flow <= supply_link_capacity[(i, j)]

    def outlet_inflow_rule(model, node, t):
        return model.outlet_flow[node, t] == sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node)

    def outlet_flow_balance_rule(model, node, t):
        return model.outlet_flow[node, t] == sum(model.flow[i, j, t] for (i, j) in model.arcs if j == node) - model.losses_PAC[node, t]

    def gw_limit_rule(model, node):
        return sum(model.flow[j, k, t] for (j, k) in model.arcs if j == node for t in model.months) <= gw_limit[node]

    def gw_pumped_rule(model, node):
        return model.pumping[node] == sum(model.flow[j, k, t] for (j, k) in model.arcs if j == node for t in model.months)

    def wrp_reuse_rule(model, node, t):
        return model.treatment_reuse[node, t] == sum(model.flow[j, k, t] for (j, k) in model.reuse_arcs if j == node)

    def sb_recharge_rule(model, node, t):
        return model.sb_recharge[node, t] == sum(model.flow[j, k, t] for (j, k) in model.mar_arcs if j == node)


    #%% 
    # -------------------- Loop over Each Year --------------------
    # Initialize multi-year output arrays
    output_flows_array = None
    output_indoor_shortage_array = None
    output_outdoor_shortage_array = None
    output_monthly_indoor_demand_array = None
    output_monthly_outdoor_demand_array = None
    output_storage_array_full = None
    output_gw_array = None
    output_reuse_array = None
    output_sb_recharge_array = None
    output_losses_array = None
    output_PAC_outlet_array = None

    for year in years:
        print(f"\n\n-------->> Processing year {year}...")
        
        # Update inflow timeseries and dictionary for this year
        inflow_timeseries = inflows_modified.copy()
        inflow_timeseries.iloc[2, 1:13] = import_multiplier_MWD  * mean_import_MWD/2 * mean_monthly_fractions_drought # INF_COL
        inflow_timeseries.iloc[17, 1:13] = import_multiplier_MWD  * mean_import_MWD/2 * mean_monthly_fractions_drought # INF_SWP
        inflow_timeseries.iloc[110, 1:13] = import_multiplier_LAA * mean_import_LAA * mean_monthly_fractions_drought # SUR_OWN (LAA)
        
        inflow_ids = list(inflow_timeseries['ID'])
        inflow = {}
        for i, node in enumerate(inflow_ids):
            if node in ['INF_SWP', 'INF_COL', 'SUR_OWN']:
                inflow[node] = list(inflow_timeseries.iloc[i, 1:13])
            else:
                inflow[node] = list(inflow_timeseries.iloc[i, 1:13] * inflow_multiplier)

        # Update demand timeseries for indoor and outdoor nodes # NEW apply efficiency targets here
        indoor_efficiency_reduction = pd.read_csv(indoor_eff_target_file, index_col = 0)
        demand_indoor_modified = demand_indoor_artes.copy().replace(0, 1)
        for i in range(len(demand_indoor_modified.iloc[:,0])):
            demand_indoor_modified.iloc[i,1:14] = demand_indoor_modified.iloc[i,1:14] -\
                indoor_eff * indoor_efficiency_reduction.iloc[i,1:14] 
                
        indoor_demand_ids = list(demand_indoor_modified.iloc[:, 0])
        demand_indoor = {node: list(demand_indoor_modified.loc[demand_indoor_modified.iloc[:, 0] == node].iloc[0, 2:14])
                         for node in indoor_demand_ids}
        
        outdoor_efficiency_reduction = pd.read_csv(outdoor_eff_target_file, index_col = 0)
        demand_outdoor_modified = demand_outdoor_artes.copy().replace(0, 1)
        for i in range(len(demand_outdoor_modified.iloc[:,0])):
            demand_outdoor_modified.iloc[i,1:14] = demand_outdoor_modified.iloc[i,1:14] -\
                outdoor_eff * outdoor_efficiency_reduction.iloc[i,1:14]
                
        outdoor_demand_ids = list(demand_outdoor_modified.iloc[:, 0])
        demand_outdoor = {node: list(demand_outdoor_modified.loc[demand_outdoor_modified.iloc[:, 0] == node].iloc[0, 2:14])
                          for node in outdoor_demand_ids}
            
        # -------------------- Update Storage for Warm Start --------------------
        storage = {}
        if year == 0:
            #initial_storage_df = initial_storage_df.reindex(storage_ids, fill_value=0) # this overwrote initial storage to 0 
            for node in storage_ids:
                storage_value = initial_storage_df.where(initial_storage_df.ID == node).dropna()
                storage[node] = storage_value['Initial_Volume'].values[0] * initial_res_storage_multiplier
        else:
            # For each storage node (excluding 'SUR_PAC'), use last month from previous year's storage output
            for node in storage_ids:
                if node == 'SUR_PAC':
                    storage[node] = 0
                else:
                    storage[node] = 0.95 * output_storage_array_full[surface_nodes.index(node), year * 12 - 1] # SBF modified to get correct previous Dec storage
        
        # Update node lists (these may be determined by the demand files)
        indoor_nodes = list(demand_indoor.keys())
        outdoor_nodes = list(demand_outdoor.keys())
        wrp_nodes = wrp_reuse_nodes.copy()
        gw_nodes = list(gw_limit.keys())
        sb_nodes = list(sb_limit.keys())
        
        # -------------------- Build the Pyomo Model --------------------
        model = ConcreteModel(name='Artes_V0_annual_foresight')
        model.arcs = Set(initialize=arcs, dimen=2)
        model.months = Set(initialize=months)
        model.reuse_arcs = Set(initialize=reuse_arcs, dimen=2)
        model.mar_arcs = Set(initialize=mar_arcs, dimen=2)
        model.supply_link_arcs = Set(initialize=supply_link_arcs, dimen=2)
        
        # Variables
        model.flow = Var(model.arcs, model.months, domain=NonNegativeReals, bounds=flow_bounds_rule)
        model.indoor_shortage = Var(list(demand_indoor.keys()), months, domain=NonNegativeReals)
        model.outdoor_shortage = Var(list(demand_outdoor.keys()), months, domain=NonNegativeReals)
        model.indoor_shortage_ratio = Var(list(demand_indoor.keys()), months, domain=NonNegativeReals)
        model.outdoor_shortage_ratio = Var(list(demand_outdoor.keys()), months, domain=NonNegativeReals)
        model.outlet_flow = Var(list(outlet_nodes.keys()), months, domain=NonNegativeReals, bounds=(0, 10**8))
        
        storage_nodes = [node for node in storage_ids if node != 'SUR_PAC']
        model.storage_vol = Var(storage_nodes, months, domain=NonNegativeReals, bounds=storage_bounds_rule)
        model.losses_outdoor = Var(outdoor_nodes, months, domain=NonNegativeReals)
        model.losses_surface = Var(surface_nodes, months, domain=NonNegativeReals)
        model.losses_PAC = Var(list(outlet_nodes.keys()), months, domain=NonNegativeReals)
        model.pumping = Var(gw_nodes, domain=NonNegativeReals, bounds=lambda m, node: (0, gw_limit[node]))
        model.treatment_reuse = Var(wrp_reuse_nodes, months, domain=NonNegativeReals,
                                    bounds=lambda m, node, t: (0, reuse_limit[node]))
        model.wrp_inflows = Var(wrp_nodes, months, domain=NonNegativeReals,
                                bounds=lambda m, node, t: (0, wrp_limit[node]))
        model.sb_recharge = Var(sb_nodes, months, domain=NonNegativeReals, bounds=(0, None))
        
        # Constraints
        model.monthly_cap_constraint = Constraint(model.arcs, model.months, rule=monthly_cap_rule)
        model.annual_cap_constraint = Constraint(model.arcs, rule=annual_cap_rule)
        model.mass_balance_constraint = Constraint(surface_nodes, months, rule=mass_balance_rule)
        model.indoor_balance_constraint = Constraint(indoor_nodes, model.months, rule=indoor_balance_rule)
        model.outdoor_balance_constraint = Constraint(outdoor_nodes, model.months, rule=outdoor_balance_rule)
        model.wrp_balance_constraint = Constraint(wrp_nodes, model.months, rule=wrp_balance_rule)
        model.wrp_inflows_constraint = Constraint(wrp_nodes, model.months, rule=wrp_inflows_rule)
        model.indoor_shortage_constraint = Constraint(list(demand_indoor.keys()), model.months, rule=indoor_shortage_rule)
        model.outdoor_shortage_constraint = Constraint(list(demand_outdoor.keys()), model.months, rule=outdoor_shortage_rule)
        model.indoor_shortage_ratio_constraint = Constraint(list(demand_indoor.keys()), model.months, rule=indoor_shortage_ratio_rule)
        model.outdoor_shortage_ratio_constraint = Constraint(list(demand_outdoor.keys()), model.months, rule=outdoor_shortage_ratio_rule)
        model.supply_annual_constraint = Constraint(model.supply_link_arcs, rule=supply_annual_constraint_rule)
        model.outlet_inflow_constraint = Constraint(list(outlet_nodes.keys()), model.months, rule=outlet_inflow_rule)
        model.outlet_flow_balance_constraint = Constraint(list(outlet_nodes.keys()), model.months, rule=outlet_flow_balance_rule)
        model.gw_limit_constraint = Constraint(gw_nodes, rule=gw_limit_rule)
        model.gw_pumped_constraint = Constraint(gw_nodes, rule=gw_pumped_rule)
        model.treatment_reuse_constraint = Constraint(wrp_reuse_nodes, model.months, rule=wrp_reuse_rule)
        model.sb_recharge_constraint = Constraint(sb_nodes, model.months, rule=sb_recharge_rule)
        
        #SBF added 
        #model.sur_losses_constraint = Constraint(surface_nodes, model.months, rule = losses_rule)
        
        #success = False 
        #iterations_exceeded = False
        #outdoor_pen_idx = 0
        outdoor_pen = 1
        #outdoor_pen_values = [.8,1.2,.6, 1.4]
	
        model.objective = Objective(
            expr=(
                0 * sum(model.indoor_shortage[j, t] for j in demand_indoor.keys() for t in months) +
                10 * sum(model.indoor_shortage_ratio[j, t] for j in demand_indoor.keys() for t in months) +
                0 * outdoor_pen * sum(model.outdoor_shortage[j, t] for j in demand_outdoor.keys() for t in months) +
                1 * sum(model.outdoor_shortage_ratio[j, t] for j in demand_outdoor.keys() for t in months) -
                0.0 * sum(model.treatment_reuse[j, t] for j in wrp_reuse_nodes for t in months) -
                0 * 0.0001 * sum(model.outlet_flow[j, t] for j in outlet_nodes.keys() for t in months) -
                0.002 * sum(model.storage_vol[j, t] for j in surface_nodes for t in months) +
                1 * 0.001 * sum(model.pumping[j] for j in gw_nodes)
            ),
            sense=minimize
        )
           
        # while success == False and iterations_exceeded == False:
        #     print(f"\n\n-------->> Simulation attempt year {year}...")
        #     model.objective = Objective(
        #         expr=(
        #             5 * sum(model.indoor_shortage[j, t] for j in demand_indoor.keys() for t in months) +
        #             1*50 * sum(model.indoor_shortage_ratio[j, t] for j in demand_indoor.keys() for t in months) +
        #             0 * outdoor_pen * sum(model.outdoor_shortage[j, t] for j in demand_outdoor.keys() for t in months) +
        #             1*1 * sum(model.outdoor_shortage_ratio[j, t] for j in demand_outdoor.keys() for t in months) -
        #             0.0 * sum(model.treatment_reuse[j, t] for j in wrp_reuse_nodes for t in months) -
        #             1 * 0.0001 * sum(model.outlet_flow[j, t] for j in outlet_nodes.keys() for t in months) -
        #             0.002 * sum(model.storage_vol[j, t] for j in surface_nodes for t in months) +
        #             1 * 0.001 * sum(model.pumping[j] for j in gw_nodes)
        #         ),
        #         sense=minimize
        #     )
            
        # model.objective = Objective(
        #     expr=(
        #         100 * sum(model.indoor_shortage[j, t] for j in demand_indoor.keys() for t in months) +
        #         2 * sum(model.indoor_shortage_ratio_penalty[j, t] for j in demand_indoor.keys() for t in months) +
        #         10 * sum(model.outdoor_shortage[j, t] for j in demand_outdoor.keys() for t in months) +
        #         0.05 * sum(model.outdoor_shortage_ratio_penalty[j, t] for j in demand_outdoor.keys() for t in months) -
        #         0.2 * sum(model.treatment_reuse[j, t] for j in wrp_reuse_nodes for t in months) -
        #         0.0001 * sum(model.outlet_flow[j, t] for j in outlet_nodes.keys() for t in months) -
        #         0.005 * sum(model.storage_vol[j, t] for j in surface_nodes for t in months) +
        #         0.002 * sum(model.pumping[j] for j in gw_nodes)
        #     ),
        #     sense=minimize
        # )
        
        # -------------------- Warm Start: Only set persistent state variable(s) --------------------
        # tol = 1e-6
        # if year > 0 and previous_solution:
        #     # Only warm start storage_vol since inflow, demand, etc. have changed
        #     if 'storage_vol' in previous_solution:
        #         for idx, val in previous_solution['storage_vol'].items():
        #             if val < 0 and val > -1e-4:
        #                 val = 0
                        
        #             if model.storage_vol[idx].ub is not None:
        #                 if model.storage_vol[idx].ub > 1 and abs(val - model.storage_vol[idx].ub) < 1e-3:
        #                     val = model.storage_vol[idx].ub - tol
        #             model.storage_vol[idx].value = val

        solver = SolverFactory('ipopt')
        solver.options['tol'] = 1e-3
        solver.options['acceptable_tol'] = 1e-3
        solver.options['acceptable_dual_inf_tol'] = 5 # try this to help convergence
        solver.options['max_iter'] = 7000
        solver.options['nlp_scaling_method'] = 'gradient-based'
        solver.options['linear_solver'] = 'mumps'
        #solver.options['warm_start_init_point'] = 'yes'
        #solver.options['warm_start_bound_push'] = 1e-4
        #solver.options['warm_start_mult_bound_push'] = 1e-4
        solver.options['print_level'] = 5

        model.write(f'{output_path}/{sim_name}_Artes_V0_annual_foresight.nl', io_options={'symbolic_solver_labels': True})
        
        results = solver.solve(model, tee=True)
        
        # Save the solution for warm starting next iteration (all variables are stored but only state variables will be used)
        previous_solution = {}
        for var in model.component_objects(Var, active=True):
            previous_solution[var.name] = {idx: var[idx].value for idx in var}
        
        # -------------------- Extract Outputs --------------------
        output_flows = {(i, j, t): model.flow[i, j, t].value for (i, j) in model.arcs for t in months}
        output_indoor_shortages = {(node, t): model.indoor_shortage[node, t].value for node in demand_indoor.keys() for t in months}
        output_outdoor_shortages = {(node, t): model.outdoor_shortage[node, t].value for node in demand_outdoor.keys() for t in months}
        output_storage = {(node, t): model.storage_vol[node, t].value for node in surface_nodes for t in months}
        output_losses = {(node, t): model.losses_surface[node, t].value for node in surface_nodes for t in months}
        output_pumping = {node: model.pumping[node].value for node in gw_nodes}
        output_reuse = {(node, t): model.treatment_reuse[node, t].value for node in wrp_reuse_nodes for t in months}
        output_sb_recharge = {(node, t): model.sb_recharge[node, t].value for node in sb_nodes for t in months}
        output_outlet = {(node, t): model.outlet_flow[node, t].value for node in outlet_nodes.keys() for t in months}
        # current_storage_array = np.array([[model.storage_vol[node, t].value for t in months] for node in surface_nodes])
        
        # -------------------- Update Multi-Year Output Arrays --------------------
        if year == 0:
            output_flows_array = np.zeros((len(arcs), 12 * len(years)))
            output_indoor_shortage_array = np.zeros((len(indoor_demand_ids), 12 * len(years)))
            output_outdoor_shortage_array = np.zeros((len(outdoor_demand_ids), 12 * len(years)))
            output_monthly_indoor_demand_array = np.zeros((len(indoor_demand_ids), 12 * len(years)))
            output_monthly_outdoor_demand_array = np.zeros((len(outdoor_demand_ids), 12 * len(years)))
            output_storage_array_full = np.zeros((len(surface_nodes), 12 * len(years)))
            output_gw_array = np.zeros((len(gw_nodes), len(years)))
            output_reuse_array = np.zeros((len(reuse_limit), 12 * len(years)))
            output_sb_recharge_array = np.zeros((len(sb_nodes), 12 * len(years)))
            output_losses_array = np.zeros((len(surface_nodes), 12 * len(years)))
            output_PAC_outlet_array = np.zeros((1, 12 * len(years)))
        
        for i, arc in enumerate(arcs):
            for j, month_val in enumerate(months):
                output_flows_array[i, j + 12 * year] = output_flows[(arc[0], arc[1], month_val)]

        output_flows_df = pd.DataFrame(data = output_flows_array, index=list(capacity.keys()))
        
        for i, node in enumerate(indoor_demand_ids):
            for j, month_val in enumerate(months):
                output_indoor_shortage_array[i, j + 12 * year] = output_indoor_shortages[(node, month_val)]

        output_indoor_shortage_df = pd.DataFrame(data = output_indoor_shortage_array, 
                                                index = indoor_demand_ids)
        
        for i, node in enumerate(outdoor_demand_ids):
            for j, month_val in enumerate(months):
                output_outdoor_shortage_array[i, j + 12 * year] = output_outdoor_shortages[(node, month_val)]

        output_outdoor_shortage_df = pd.DataFrame(data = output_outdoor_shortage_array, 
                                                    index = outdoor_demand_ids)

        for row in range(len(indoor_demand_ids)):
            output_monthly_indoor_demand_array[row, 12*year:12*(year+1)] = demand_indoor_modified.iloc[row,2:14]

                    
        output_monthly_indoor_demand_df = pd.DataFrame(data = output_monthly_indoor_demand_array, 
                                                    index = indoor_demand_ids)
        
        for row in range(len(outdoor_demand_ids)):
            output_monthly_outdoor_demand_array[row, 12*year:12*(year+1)] = demand_outdoor_modified.iloc[row,2:14]

                    
        output_monthly_outdoor_demand_df = pd.DataFrame(data = output_monthly_outdoor_demand_array, 
                                                    index = outdoor_demand_ids)
        
        for i, node in enumerate(surface_nodes):
            for j, t in enumerate(months):
                output_storage_array_full[i, j + 12 * year] = output_storage[(node, t)]

        output_storage_df = pd.DataFrame(data = output_storage_array_full, index = surface_nodes)

        
        for i, node in enumerate(gw_nodes):
            output_gw_array[i, year] = output_pumping[node]

        output_gw_df = pd.DataFrame(data = output_gw_array, index = gw_nodes)

        
        for i, node in enumerate(list(reuse_limit.keys())):
            for j, t in enumerate(months):
                output_reuse_array[i, j + 12 * year] = output_reuse[(node, t)]

        output_reuse_df = pd.DataFrame(data = output_reuse_array, index = list(reuse_limit.keys()))
        
        for i, node in enumerate(sb_nodes):
            for j, t in enumerate(months):
                output_sb_recharge_array[i, j + 12 * year] = output_sb_recharge[(node, t)]

        output_sb_recharge_df = pd.DataFrame(data = output_sb_recharge_array, index = sb_nodes)

        
        for i, node in enumerate(surface_nodes):
            for j, t in enumerate(months):
                output_losses_array[i, j + 12 * year] = output_losses[(node, t)]

        output_losses_df = pd.DataFrame(data = output_losses_array, index = surface_nodes)


        for j, t in enumerate(months):
            output_PAC_outlet_array[0, j + 12 * year] = output_outlet[('SUR_PAC', t)]

        output_PAC_outlet_df = pd.DataFrame(data = output_PAC_outlet_array, index = ['SUR_PAC'])

        
        #print(f"Year {year} optimization complete.\n")
        
        
        
    # monthly supply:  indoor and outdoor
    links_output_indoor_supply = [link for link in output_flows_df.index if link[1] in indoor_demand_ids]
    output_indoor_supply_df = output_flows_df.loc[links_output_indoor_supply]

    links_output_outdoor_supply = [link for link in output_flows_df.index if link[1] in outdoor_demand_ids]
    output_outdoor_supply_df = output_flows_df.loc[links_output_outdoor_supply]

    # monthly imports
    import_nodes = ['INF_SWP', 'INF_COL', 'SUR_OWN']
    links_monthly_imports = [link for link in output_flows_df.index if link[0] in import_nodes]
    output_monthly_imports_df = output_flows_df.loc[links_monthly_imports]

    # monthly groundwater pumping
    links_output_monthly_gw = [link for link in output_flows_df.index if str(link)[2:5] == 'GWB']
    output_monthly_gw_df = output_flows_df.loc[links_output_monthly_gw]

    # monthly reuse 
    output_monthly_reuse_df = output_reuse_df.copy()

    # if save:
    #     output_files = {
    #         f"{output_path}/{sim_name}_link_flows.csv": output_flows_df,
    #         f"{output_path}/{sim_name}_indoor_shortage.csv": output_indoor_shortage_df,
    #         f"{output_path}/{sim_name}_outdoor_shortage.csv": output_outdoor_shortage_df,
    #         f"{output_path}/{sim_name}_indoor_demand.csv": output_monthly_indoor_demand_df,
    #         f"{output_path}/{sim_name}_outdoor_demand.csv": output_monthly_outdoor_demand_df,
    #         f"{output_path}/{sim_name}_storage.csv": output_storage_df,
    #         f"{output_path}/{sim_name}_reuse.csv": output_reuse_df,
    #         f"{output_path}/{sim_name}_annual_gw_pumping.csv": output_gw_df,
    #         f"{output_path}/{sim_name}_sb_recharge.csv": output_sb_recharge_df,
    #         f"{output_path}/{sim_name}_losses.csv": output_losses_df,
    #         f"{output_path}/{sim_name}_PAC_outlet_flow.csv": output_PAC_outlet_df,
    #         f"{output_path}/{sim_name}_flows_indoor_supply.csv": output_indoor_supply_df,
    #         f"{output_path}/{sim_name}_flows_outdoor_supply.csv": output_outdoor_supply_df,
    #         f"{output_path}/{sim_name}_monthly_imports.csv": output_monthly_imports_df,
    #         f"{output_path}/{sim_name}_monthly_gw.csv": output_monthly_gw_df,
    #         f"{output_path}/{sim_name}_monthly_reuse.csv": output_monthly_reuse_df,
    #     }
        
    if save:
        output_files = {
            f"{output_path}/{sim_name}_link_flows.csv": output_flows_df,
            f"{output_path}/{sim_name}_indoor_shortage.csv": output_indoor_shortage_df,
            f"{output_path}/{sim_name}_outdoor_shortage.csv": output_outdoor_shortage_df,
        }
        
        for filename, df in output_files.items():
            df.to_csv(filename)
    
    nl_file = f'{output_path}/{sim_name}_Artes_V0_annual_foresight.nl'
    row_file =  f'{output_path}/{sim_name}_Artes_V0_annual_foresight.row'
    col_file = f'{output_path}/{sim_name}_Artes_V0_annual_foresight.col'
    os.remove(nl_file) 
    os.remove(row_file) 
    os.remove(col_file) 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='Artes_V0',
        description='Runs a single scenario of Artes V0',
        epilog='',
    )

    parser.add_argument('-i', '--input', help='path to input directory')
    parser.add_argument('-o', '--output', help='path to output directory')
    parser.add_argument('-s', '--scenario', help='scenario index to run')
    parser.add_argument('-l', '--list', help='path to a csv file containing the scenarios')
    parser.add_argument('-d', '--dry', action='store_true', help='do not save output files') # don't save output

    args = parser.parse_args()

    run_scenario(
        int(args.scenario),
        input_path=args.input,
        output_path=args.output,
        scenarios_file=args.list,
        save=(not args.dry),
    )
