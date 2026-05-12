# -*- coding: utf-8 -*-

import os 
import math
import pandas as pd
import numpy as np 

os.chdir("C:/Users/fere556/OneDrive - PNNL/Documents/Artes/Artes_paper/LA_Sensitivity_Analysis_Repo/GitHub/Step_2_simulate_ensemble")

#os.chdir("C:/Users/fere556/Desktop/HPC_testing/Artes_parser_test/")

ensemble_name = "output_sobol_13312"
scenarios_file = "params_values_13312_sobol.csv"

ensemble_size = 1558 # number of model runs
n_cores = 60 # available cores on 1 node 
time = 10 # desired run time in hours
time_string = "10:00:00" # time requested for sbatch hh:mm:ss
runs_per_core_per_hour = 6 # conservative estimate of Artes runs per hour, per core
runs_per_core = runs_per_core_per_hour * time 

cores = math.ceil(ensemble_size/runs_per_core) # number of cores needed 

if cores > n_cores:
    print("requesting more than 1 node")

# create index intervals for ensemble, these are written into the .sh files
indexes = pd.DataFrame(data = np.zeros((cores,2)), columns = ['start','end'])

for i in range(cores):
    indexes.start[i] = i*runs_per_core
    indexes.end[i] = (i+1)*runs_per_core - 1
    
    if i + 1 == cores:
        indexes.end[i] = ensemble_size - 1

# generate .sl and .sh scripts for HPC
for i in range(cores):
    with open("driver_batch.sh", "r") as f: # open driver template
        lines = f.readlines()
    
    # update lines that specify #of scenarios and start and end indexes 
    lines[8] = "total_scenarios=" + str(runs_per_core) + "\n"
    lines[13] = "start_scenario=" + str(int(indexes.start[i])) + "\n"
    lines[14] = "end_scenario=" + str(int(indexes.end[i])) + "\n"   
    parser_command = '/rcfs/projects/im3/gnuparallel/bin/parallel --jobs 16 "python artes_pyomo_hpc_SR.py -i ./Input_Files -o ./output_name -l ./Input_Files/input_name -s " ::: "${scenarios[@]}"\n' 
    parser_command = parser_command.replace('output_name', ensemble_name)
    parser_command = parser_command.replace('input_name', scenarios_file)
    lines[24] = parser_command

    # save new file
    with open("driver_batch_" + str(i+1) + ".sh", "w") as f: 
        f.writelines(lines)
        
    with open("driver_batch_" + str(i+1) + ".sh", "r", newline="") as f: 
        data = f.read() # Remove carriage returns 

    data = data.replace("\r", "") 

    with open("driver_batch_" + str(i+1) + ".sh", "w", newline="\n") as f: 
        f.write(data)
        
for i in range(cores):
    with open("q.sl", "r") as f: # open driver template
        lines = f.readlines()  
    
    # set runtime for each ensemble job
    lines[6] = "#SBATCH -t " + time_string + "\n"
    
    # set driver script name for each ensemble job
    lines[23] = "srun --wait=0 " + "driver_batch_" + str(i+1) + ".sh\n" 
    
    # save new file
    with open("q_batch_" + str(i+1) + ".sl", "w") as f: 
        f.writelines(lines)
        
    with open("q_batch_" + str(i+1) + ".sl", "r", newline="") as f: 
        data = f.read() # Remove carriage returns 

    data = data.replace("\r", "") 

    with open("q_batch_" + str(i+1) + ".sl", "w", newline="\n") as f: 
        f.write(data)
        
# write ensemble driver script that submits all jobs when called
N = cores # any integer 
jobs = [f"q_batch_{i}.sl" for i in range(1, N + 1)] 
bash_text = "#!/bin/bash\n\n"
bash_text += "jobs=(\n"
for j in jobs: 
    bash_text += f' "{j}"\n' 
bash_text += ")\n\n" 
bash_text += 'for j in "${jobs[@]}"; do\n' 
bash_text += ' echo "Submitting $j"\n' 
bash_text += ' sbatch "$j"\n' 
bash_text += "done\n" 
print(bash_text)

with open("q_batch_" + ensemble_name + ".sh", "w") as f: 
    f.write(bash_text)
    
with open("q_batch_" + ensemble_name + ".sh", "r", newline="") as f: 
    data = f.read() # Remove carriage returns 

data = data.replace("\r", "") 

with open("q_batch_" + ensemble_name + ".sh", "w", newline="\n") as f: 
    f.write(data)
    