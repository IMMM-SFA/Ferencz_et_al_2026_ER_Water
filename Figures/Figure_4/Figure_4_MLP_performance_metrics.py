import os 
import pandas as pd
import matplotlib.pyplot as plt 

# Path to Figure 4 data 
os.chdir("path to /Figure_4/Figure_4_files")

# import provider results 
cty_azu = pd.read_csv("CTY_AZU_MLP_Artes_vs_predicted_shortage.csv", index_col = 0)
cty_lax = pd.read_csv("CTY_LAX_MLP_Artes_vs_predicted_shortage.csv", index_col = 0)
cty_lbh = pd.read_csv("CTY_LBH_MLP_Artes_vs_predicted_shortage.csv", index_col = 0)
LAC_region = pd.read_csv("LAC_MLP_Artes_vs_predicted_shortage.csv", index_col = 0)

# import MLP performance metrics 
metrics = pd.read_csv("MLP_performance_metrics.csv", index_col = 0)

# Plots of Artes model vs MLP test set
plt.figure()
plt.title("Total shortage: Artes vs emulator for CTY_AZU")
plt.scatter(cty_azu.test, cty_azu.predict, s = 4, alpha = 0.05)
plt.ylabel('MLP test [acre-feet]')
plt.xlabel('Artes truth [acre-feet]')

plt.figure()
plt.title("Total shortage: Artes vs emulator for CTY_LAX")
plt.scatter(cty_lax.test, cty_lax.predict, s = 4, alpha = 0.05)
plt.ylabel('MLP test [acre-feet]')
plt.xlabel('Artes truth [acre-feet]')

plt.figure()
plt.title("Total shortage: Artes vs emulator for CTY_LBH")
plt.scatter(cty_lbh.test, cty_lbh.predict, s = 4, alpha = 0.05)
plt.ylabel('MLP test [acre-feet]')
plt.xlabel('Artes truth [acre-feet]')

plt.figure()
plt.title("Total shortage: Artes vs emulator for LAC Region")
plt.scatter(LAC_region.test, LAC_region.predict, s = 4, alpha = 0.05)
plt.ylabel('MLP test [acre-feet]')
plt.xlabel('Artes truth [acre-feet]')

# Plot metrics distributions 
drop = ['INF_CSB', 'PRV_WMI', 'IRR_KIN', 'PRV_SGR', 'MWC_VHT']
metrics = metrics.drop(drop, axis = 1)

# Box and whisker plot: BIAS
fig, ax = plt.subplots(figsize=(2, 4), dpi=300)  # increase dpi here
bp = ax.boxplot(
    metrics.iloc[3,:97],
    vert=True,
    patch_artist=True,  # needed to control box facecolor; we'll set it to 'none'
    boxprops=dict(facecolor='none', edgecolor='black', linewidth=1.5),
    whiskerprops=dict(color='black', linewidth=1.5),
    capprops=dict(color='black', linewidth=1.5),
    medianprops=dict(color='crimson', linewidth=2),
    flierprops=dict(
        marker='o', markerfacecolor='black', markeredgecolor='black', markersize=4
    ),
)

ax.set_ylabel('BIAS', fontsize=10)
ax.grid(True, axis='y', linestyle='--', alpha=0.4)
fig.tight_layout()

# Box and whisker plot: R^2
fig, ax = plt.subplots(figsize=(2, 4), dpi=300)  # increase dpi here
bp = ax.boxplot(
    metrics.iloc[0,:97],
    vert=True,
    patch_artist=True,  # needed to control box facecolor; we'll set it to 'none'
    boxprops=dict(facecolor='none', edgecolor='black', linewidth=1.5),
    whiskerprops=dict(color='black', linewidth=1.5),
    capprops=dict(color='black', linewidth=1.5),
    medianprops=dict(color='crimson', linewidth=2),
    flierprops=dict(
        marker='o', markerfacecolor='black', markeredgecolor='black', markersize=4
    ),
)

ax.set_ylabel('R2', fontsize=10)
ax.grid(True, axis='y', linestyle='--', alpha=0.4)
fig.tight_layout()


# Box and whisker plot: MAPE
fig, ax = plt.subplots(figsize=(2, 4), dpi=300)  # increase dpi here
bp = ax.boxplot(
    100*metrics.iloc[2,:97],
    vert=True,
    patch_artist=True,  # needed to control box facecolor; we'll set it to 'none'
    boxprops=dict(facecolor='none', edgecolor='black', linewidth=1.5),
    whiskerprops=dict(color='black', linewidth=1.5),
    capprops=dict(color='black', linewidth=1.5),
    medianprops=dict(color='crimson', linewidth=2),
    flierprops=dict(
        marker='o', markerfacecolor='black', markeredgecolor='black', markersize=4
    ),
)

ax.set_ylabel('MAPE', fontsize=10)
ax.grid(True, axis='y', linestyle='--', alpha=0.4)
fig.tight_layout()
