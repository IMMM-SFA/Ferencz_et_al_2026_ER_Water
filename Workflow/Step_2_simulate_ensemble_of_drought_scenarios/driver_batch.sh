#!/usr/bin/env /bin/bash

module purge
module load python/miniconda25.5.1
source /share/apps/python/miniconda25.5.1/etc/profile.d/conda.sh
conda activate /rcfs/projects/im3/models/artes/artes_venv

# total number of scenarios
total_scenarios=104

# total number of nodes used to run this job, defined in q.sl
total_nodes=$SLURM_JOB_NUM_NODES

start_scenario=0
end_scenario=16

scenarios=( $(seq $start_scenario $end_scenario) )
echo "${scenarios[@]}"

echo "NODE $SLURM_NODEID: scenarios $start_scenario - $end_scenario"

export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4

/rcfs/projects/im3/gnuparallel/bin/parallel --jobs 16 "python artes_pyomo_hpc_SR.py -i ./Input_Files -o ./output_1 -l ./Input_Files/param_values_104_sobol_v5.csv -s " ::: "${scenarios[@]}"
#/rcfs/projects/im3/gnuparallel/bin/parallel --jobs 16 "python artes_pyomo_hpc_indx_fix.py -i ./Input_Files -o ./output -l ./Input_Files/param_values_48_convergence_testing.csv -s " ::: "${scenarios[@]}"

conda deactivate

