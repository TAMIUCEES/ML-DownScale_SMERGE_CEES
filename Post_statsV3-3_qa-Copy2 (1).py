import sys
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, kendalltau
from Post_Stats import core
import dask.dataframe as dd
import warnings

d1 = sys.argv[1] #r"/scratch/user/u.as341717/Vision2/RapRF_TXS_500v7.csv"
state = sys.argv[2]
d2 = r"/scratch/user/u.as341717/QA/merged_output_6.csv"  # SMERGE merged_output_6.csv
d3 = r"/scratch/user/u.as341717/QA/AHRR_Hist_Mean.csv" #r"/scratch/user/u.as341717/QA/merged_output_5.csv"  # AHRR
warnings.filterwarnings("ignore")
data = pd.read_csv(d1, engine='pyarrow')#.sample(frac=0.10)
data['Date'] = pd.to_datetime(data['Date'], format="%Y-%m-%d")

land = pd.read_csv("//scratch/group/p.ees250195.000/Landcover/Landcover2026.csv",engine='pyarrow')
land = land[land['State'] == state].reset_index()

data = data.merge(land[['PageName', 'Year', 'LandC']], on=['PageName', 'Year'])

#Developed 21, 22, 23, 24
#Category A (Herbaceous, Cropland, Developed)
category_A = [71, 81, 82,21,22,23,24]
#Category B (Scrubland, Barren)
category_B = [52, 31]
#Category C (Forest, Wetlands)
category_C = [41, 42, 43, 90, 95]


data_A = data.loc[data['LandC'].isin(category_A)]
data_B = data.loc[data['LandC'].isin(category_B)]
data_C = data.loc[data['LandC'].isin(category_C)]
data_D = data.loc[~data['LandC'].isin([21,22,23,24])]

print("Cat A:" +str((len(data_A)/len(data))*100)+"%")
print("Cat B:" +str((len(data_B)/len(data))*100)+"%")
print("Cat C:" +str((len(data_C)/len(data))*100)+"%")
print("Cat D:" +str((len(data_D)/len(data))*100)+"%")
