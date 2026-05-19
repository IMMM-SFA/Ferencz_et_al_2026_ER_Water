import SALib as SALib
from SALib import ProblemSpec
import os 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error

# Path to Training Data 
training_data_path = "./Outputs/output_sobol_13312/" # add absolute path to Artes model outputs of water shortage, generated in Step 2 and processed in Step 3
shortage_results = pd.read_csv(training_data_path + "worst_year_total_shortage_full_ensemblescenario.csv", index_col = 0) # these outputs are from Step 3
input_features = pd.read_csv(training_data_path + "param_values_13312_sobol_HPC.csv", index_col = 0)  # these are in Step 1

for i in range(len(shortage_results.iloc[:,0])):
    if sum(shortage_results.iloc[i,:].values) == 0:
        shortage_results.iloc[i,:] = np.nan
        input_features.iloc[i,:] = np.nan
        
shortage_results = shortage_results.dropna()
input_features = input_features.dropna()

# Calculate total regional shortage 
shortage_results['LAC'] = shortage_results.sum(axis = 1) # total regional shortage = sum of individual shortage columns

# Aggregate shortage to mwd regions: shortage aggregated to MWD wholesale regions
path = "./Inputs/" # add absolute path to Provider_MWD_groupings.csv
provider_groups_labels = pd.read_csv(path + "Provider_MWD_groupings_only.csv")

shortage_results_T = shortage_results.copy()
shortage_T = shortage_results_T.transpose()
shortage_T =  pd.merge(shortage_T , provider_groups_labels, left_index=True,
                                right_on = 'Demand_node', how = 'inner')

shortage_T_groups = shortage_T.groupby(['MWD_region']).sum()
shortage_mwd_groups = shortage_T_groups.transpose()

# Append mwd wholesale region shortage columns to provider results 
shortage_results = pd.concat([shortage_results, shortage_mwd_groups], axis=1)

#%% Generate ensembles to be evaluated by MLP nueral network. For the paper, 
#   this is where we created the upper and lower MWD import scenarios. This 
#   workflow creates the new Sobol parameter ensembles that are then evaluated 
#   by the MLP neural network trained on the Artes simulated outputs 
#   For a direct comparison of Sobol indicies derived from the simulated 
#   ensemble versus the MLP, do not modify the MWD bounds (comment out these 
#   lines of code below). This will generate Sobol indicies for scenarios 
#   that are equivalent to the simulated ensemble. Use a sample size of 512 
#   to match the same ensemble size of 13,312. For convergence testing, the 
#   user can add a list of sample sizes to evaluate (e.g., [4,16,32]). This will
#   generate Sobol samples (as .csv files) for each sample group that will be evaluated by the 
#   MLP neural network. This code block creates new folders to store the outputs 
#   of the synthetic MLP scenarios and saves Sobol samples for each ("param_values...csv"). 

generate_synthetic = True # True: generate synthetic ensembles of Sobol samples
synthetic_scenario = 'Example_mwd_import_lower_range' # change name to desired prefix name that will be used for outputs from synthetic scenarios 
synthetic_scenario_names = [] # leave empty, this list is populated below
synthetic_path = "./Documents/Synthetic_Shortages/" # absolute path that will be created to store outputs for synthetic ensembles 
os.makedirs(synthetic_path + synthetic_scenario, exist_ok=True) # create folder for synthetic scenario ensemble 

if generate_synthetic:
    path_params = "./Inputs/" #  absolute path to SALib_parameter_ranges.csv
    parameter_df = pd.read_csv(path_params + "SALib_parameter_ranges.csv") # csv with parameters and bounds (Same as Step 1)
    
    # # MWD bounds 
    parameter_df.iloc[0,1] = 0.428 # LOWER multiplier bound for MWD: for upper range ensemble set lower bound to 0.71, for lower range ensemble set to 0.428
    parameter_df.iloc[0,2] = 0.71 # UPPER multipleir bound for MWD: for upper range ensemble MWD set upper bound to 1, for lower range ensemble set to 0.71

    # Define problem in SALib
    problem = {'num_vars': len(parameter_df.Parameter),
               'names': list(parameter_df.Parameter.values),
               'bounds': list(parameter_df.iloc[:,1:3].values)
               }
    
    sp = ProblemSpec({'num_vars': len(parameter_df.Parameter),
               'names': list(parameter_df.Parameter.values),
               'bounds': list(parameter_df.iloc[:,1:3].values)
               })
    
    # Generate ensemble 
    column_names = list(parameter_df.Parameter.values)
    samples = [512] # [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048] # 512 samples corresponds to an ensemble of 13,312
    sample_distributions = pd.DataFrame(data = np.zeros((len(samples), len(column_names))), columns = column_names, index = samples)
    sample_base = 2*12+2 # 2*D+2 for second order inidices. D = # of parameters 
    
    for i in range(len(samples)):
        param_values_saltelli = SALib.sample.sobol.sample(problem, samples[i])
        #param_values_saltelli = SALib.sample.saltelli.sample(problem, samples[i]) # OLD method
        
        # Save to DataFrame with field names 
        param_values_df = pd.DataFrame(data = param_values_saltelli, 
                                       columns = parameter_df.Parameter.values)
        
        for j in range(len(column_names)):
            sample_distributions.iloc[i,j] = len(param_values_df.iloc[:,j].unique())
        
        param_values_df.to_csv(synthetic_path + synthetic_scenario + "/param_values_" + str(samples[i]*(2*12+2)) + "_sobol_emulator_" + synthetic_scenario + ".csv")
        synthetic_scenario_names.append("param_values_" + str(samples[i]*(2*12+2)) + "_sobol_emulator_" + synthetic_scenario + ".csv")
        synthetic_results_filenames = []    

#%% Create dataframe to store metrics on emulator performance 
indexes = ['r2', 'rmse', 'mape', 'bias']
metrics = pd.DataFrame(data = np.zeros((len(indexes), len(shortage_results.columns))), 
                       columns = shortage_results.columns, index = indexes)

#%% Train MLP neural network and evaluate performance 

# Data for MLP model 
np.random.seed(10)
X = input_features.iloc[:,:].values # X: shape (n_samples, n_features)
column_labels = shortage_results.columns # these are water provider, retail regions, and the entire study area (LAC)

for i in range(len(column_labels)): # Iterate over columns. New MLP trained for each column.  
    # if i == 1: # for testing, this limits how many columns (providers or regions) are evaluated
    #     break
    
    print(i)
    y = np.ravel(shortage_results[column_labels[i]].values) # y: shape (n_samples,)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=10)
    
    # Scale features 
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    
    # FFNN model
    mlp = MLPRegressor(
        hidden_layer_sizes=(512, 256, 128, 64, 32, 16, 8),
        activation="relu",
        solver="adam",
        alpha=1e-4,             # L2 regularization
        batch_size=512,
        learning_rate="adaptive",
        max_iter=1000,          
        early_stopping=True,    # stops when validation score plateaus
        random_state=10
    )
    
    mlp.fit(X_train_sc, y_train)
    
    # Evaluate trained model 
    y_pred = mlp.predict(X_test_sc)
    
    # Metrics 
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2   = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)
    bias = np.mean(y_pred - y_test)
    
    y_train_test_df = pd.DataFrame(data = {'test': y_test, 'predict': y_pred})
    y_train_test_df  =  y_train_test_df.sort_values(by='test')
    y_train_test_df.reset_index(inplace = True, drop = True)
    
    # Comment out this line to not save outputs of model vs emulator values 
    y_train_test_df.to_csv(synthetic_path + column_labels[i] + "_MLP_Artes_vs_predicted_shortage.csv")
    
    # Find index where total shortage is < 5% of max shortage 
    max_short = 0.05 * max(y_train_test_df.test) 
    threshold_index = (y_train_test_df['test'] > max_short).idxmax()
    
    # mape only for shortages > 5% of max shortage
    mape = mean_absolute_percentage_error(y_train_test_df.iloc[threshold_index:,0]
                                          , y_train_test_df.iloc[threshold_index:,1])
    
    metrics.loc['rmse'][i] = rmse
    metrics.loc['r2'][i] = r2
    metrics.loc['mape'][i] = mape
    metrics.loc['bias'][i] = bias
    
    if generate_synthetic:
        
        for j in range(len(synthetic_scenario_names)): # iterate over each predictor ensemble
            
            synthetic_ensemble_params = pd.read_csv(synthetic_path + synthetic_scenario + '/' + synthetic_scenario_names[j], index_col = 0) # use same file as train/test if want to reproduc synthetic values for same ensemble
            
            if i == 0: # create dataframe to store emulator shortages 
                num_scenarios = len(synthetic_ensemble_params.iloc[:,0])
                shortage_synthetic = pd.DataFrame(data = np.zeros((num_scenarios,len(column_labels))),
                                                  columns = column_labels)  
                filename = 'synthetic_shortage_' + synthetic_scenario_names[j][13:]
                synthetic_results_filenames.append(filename)
                
            else: # load saved dataframe with results from previous i iterations 
                
                shortage_synthetic = pd.read_csv(synthetic_path + synthetic_scenario + '/' + synthetic_results_filenames[j], index_col = 0)
            
            # Inference on new data            
            x_new = synthetic_ensemble_params.iloc[:,:].values 
            x_new_sc = scaler.transform(x_new)
            y_new_pred = mlp.predict(x_new_sc)
            
            # Synthetic shortages 
            shortage_synthetic.iloc[:,i] = y_new_pred # save shortages for column i 
            shortage_synthetic.to_csv(synthetic_path + synthetic_scenario + '/' + synthetic_results_filenames[j]) # save DataFrame 

metrics.to_csv(synthetic_path + "MLP_performance_metrics.csv")


#%% Sobol analysis of synthetic shortage scenario ensembles 

data_path = (synthetic_path + synthetic_scenario + "/")
os.chdir(data_path)

parameter_df = pd.read_csv("/SALib_parameter_ranges.csv")  # csv with parameters and bounds (Same as Step 1), edit absolute path so file can be loaded
problem = {'num_vars': len(parameter_df.Parameter),
           'names': list(parameter_df.Parameter.values),
           'bounds': list(parameter_df.iloc[:,1:3].values)
           }
sp = ProblemSpec({'num_vars': len(parameter_df.Parameter),
           'names': list(parameter_df.Parameter.values),
           'bounds': list(parameter_df.iloc[:,1:3].values)
           })

for j in range(len(synthetic_scenario_names)):
    # Import Sobol sequence parameter 
    samples = pd.read_csv(data_path + synthetic_scenario_names[j], index_col = 0) 
    
    samples = samples.to_numpy('float')
    sp.set_samples(samples)
    
    # Analyze sensitivity indicies for each provider 
    # Create DataFrame to store results 
    shortage_sensitivity = pd.read_csv(data_path + synthetic_results_filenames[j], index_col = 0) 
    providers = shortage_sensitivity.columns.values
    sp.set_results(shortage_sensitivity['MWD'].values) # use to initialize 
    Si = sp.analyze_sobol()
    sT, s1, s2 = Si.to_df()
    
    column_names = list(parameter_df.Parameter.values)
    data_arr = np.zeros((len(providers) ,len(column_names)))
    
    shortage_sensitivity_s1 = pd.DataFrame(data = data_arr.copy(), columns = column_names, index = providers)
    shortage_sensitivity_s1_conf = pd.DataFrame(data = data_arr.copy(), columns = column_names, index = providers)
    
    shortage_sensitivity_sT = pd.DataFrame(data = data_arr.copy(), columns = column_names, index = providers)
    shortage_sensitivity_sT_conf = pd.DataFrame(data = data_arr.copy(), columns = column_names, index = providers)
    
    data_arr = np.zeros((len(providers) ,len(s2.iloc[:,0])))
    shortage_sensitivity_s2 = pd.DataFrame(data = data_arr.copy(), columns = s2.index, index = providers)
    shortage_sensitivity_s2_conf = pd.DataFrame(data = data_arr.copy(), columns = s2.index, index = providers)
    
    for i in range(len(providers)):  
        sp.set_results(shortage_sensitivity[providers[i]].values)
        Si = sp.analyze_sobol()
        sT, s1, s2 = Si.to_df()
        
        shortage_sensitivity_s1.loc[providers[i]] = s1.S1.values
        shortage_sensitivity_s1_conf.loc[providers[i]] = s1.S1_conf.values
        
        shortage_sensitivity_sT.loc[providers[i]] = sT.ST.values
        shortage_sensitivity_sT_conf.loc[providers[i]] = sT.ST_conf.values
        
        shortage_sensitivity_s2.loc[providers[i]] = s2.S2.values
        shortage_sensitivity_s2_conf.loc[providers[i]] = s2.S2_conf.values
    
    # Save Sobol results 
    shortage_sensitivity_s1.to_csv(synthetic_scenario_names[j][13:-4] + "_s1.csv")
    shortage_sensitivity_s1_conf.to_csv(synthetic_scenario_names[j][13:-4] + "_s1_conf.csv")
    shortage_sensitivity_s2.to_csv(synthetic_scenario_names[j][13:-4] + "_s2.csv")
    shortage_sensitivity_s2_conf.to_csv(synthetic_scenario_names[j][13:-4] + "_s2_conf.csv")
    shortage_sensitivity_sT.to_csv(synthetic_scenario_names[j][13:-4] + "_sT.csv")
    shortage_sensitivity_sT_conf.to_csv(synthetic_scenario_names[j][13:-4] + "_sT_conf.csv")