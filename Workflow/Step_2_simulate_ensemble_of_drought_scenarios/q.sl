#!/bin/bash

#SBATCH -A im3
#SBATCH -N 1
#SBATCH --ntasks-per-node 1
#SBATCH -p shared
#SBATCH -t 02:00:00
#SBATCH --job-name artesTest

# This directive tells SLURM where to write the standard output (stdout)
# of your job.
# %x will be replaced by the job name (set via --job-name or the script name).
# %j will be replaced by the job ID.
# The resulting file will look something like: "my_job_name-12345.out"
#SBATCH --output=/rcfs/projects/im3/models/artes/%x-%j.out

# This directive tells SLURM where to write the standard error (stderr)
# of your job.
# Using the same %x-%j pattern ensures the error file matches the
# output file name.
# The resulting file will look something like: "my_job_name-12345.err"
#SBATCH --error=/rcfs/projects/im3/models/artes/%x-%j.err

srun --wait=0 driver.sh

