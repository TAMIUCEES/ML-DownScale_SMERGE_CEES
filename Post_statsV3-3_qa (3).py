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
d2 = r"/scratch/user/u.as341717/QA/merged_output_6.csv"  # SMERGE merged_output_6.csv
d3 = r"/scratch/user/u.as341717/QA/AHRR_Hist_Mean.csv" #r"/scratch/user/u.as341717/QA/merged_output_5.csv"  # AHRR
warnings.filterwarnings("ignore")
state = sys.argv[2]  # "TXS"
model_name = sys.argv[3]  # "RapRF"
g_name = r"Grid_" + model_name + "_" + state + "_"
s_grids = "0"  # sys.argv[5]
print(d1)
print(g_name)
data = pd.read_csv(d1, engine='pyarrow')#.sample(frac=0.10)
data['Date'] = pd.to_datetime(data['Date'], format="%Y-%m-%d")

hist_data = pd.read_csv(d2, engine='pyarrow')
hist_data2 = pd.read_csv(d3, engine='pyarrow')

qa = pd.read_csv(r"/scratch/user/u.as341717/QA/!?!?!_QA-FLAGSv6.csv".replace("!?!?!", state), engine='pyarrow')
qa['Date'] = pd.to_datetime(qa['Date'], format="%Y-%m-%d")

land = pd.read_csv("//scratch/group/p.ees250195.000/Landcover/Landcover2026.csv",engine='pyarrow')

sub = pd.read_csv(r"/scratch/user/u.as341717/QA/F-AHRR_!?!?!_500_longuF.csv".replace("!?!?!", state), engine='pyarrow')
sub['Date'] = pd.to_datetime(sub['Date'], format="%Y-%m-%d")
try:
    sub.drop(columns=["index"], inplace=True)
    sub.dropna(inplace=True)
except:
    print("1")

# data['Date'] = pd.to_datetime(data['Date'], format="%Y-%m-%d")
#data = data[data['Year'] >= 2009]

data = data.merge(qa, on=['Date', 'PageName'])
data = data.merge(sub, on=['Date', 'PageName'])
hist_data = hist_data[hist_data['State'] == state].reset_index()
hist_data2 = hist_data2[hist_data2['State'] == state].reset_index()
land = land[land['State'] == state].reset_index()

print("Number of Unique PageName Pixels Before Cutting: " + str(data['PageName'].nunique()))
try:
    data.drop(columns=["index"], inplace=True)
    data.dropna(inplace=True)
except:
    print("1")
 
try:
    data.drop(columns=["index_x", "index_y"], inplace=True)
    #data.dropna(inplace=True)
except:
    print("2")
 
try:
    data.drop(columns=["level_0"], inplace=True)
    #data.dropna(inplace=True)
except:
    print("3")
try:
    data.drop(columns=[""], inplace=True)
    #data.dropna(inplace=True)
except:
    print("4")
 
data['Soil'] = data['Sand'] + data['Silt'] + data['Clay']
data = data[(data['Soil'] > 0.9999) & (data['Soil'] < 1.0001)]
print(data.columns)

try:
    data.drop(columns=["index"], inplace=True)
    data.dropna(inplace=True)
except:
    print("")
data.reset_index(inplace=True)
data = core.anomly_cal_mono(data, 'ML_')

n_before = len(data)

data = data.merge(hist_data[['PageName', 'Month', 'SMERGE_MEAN']], on=['PageName', 'Month'])
data.rename(columns={'SMERGE_MEAN': 'SMERGE_M'}, inplace=True)
data['SMERGE_A'] = data['SMERGE'] - data['SMERGE_M']
#data = data[data['SMFLAG'] == 1]
smflag_after = len(data)
print("Total percentage SMERGE low values removed:" + f"({100 * (n_before - smflag_after) / max(n_before, 1):.1f}%)" )

# data_mlm = core.anomly_cal_hist_mean(data, 'ML_')
# data = data.merge(data_mlm[['PageName', 'Month', 'ML__M']], on=['PageName', 'Month'])
# print(data_mlm)
# data['ML__A'] = data['ML_'] - data['ML__M']

# data_mlm = core.anomly_cal_hist_mean(data, 'ML_')
# data = data.merge(data_mlm[['PageName', 'Month', 'ML__M']], on=['PageName', 'Month'])
# print(data_mlm)
# data['ML__A'] = data['ML_'] - data['ML__M']


# data_mlm = core.anomly_cal_hist_mean(data, 'ML_')

# data = data[abs(data['ML__A']) < 0.35]
ml_after = len(data)
print(str(n_before)+"__________________"+str(ml_after))
print("Total percentage ML outlier removed:" + f"({100 * (n_before - ml_after) / max(n_before, 1):.1f}%)" )

# ──────────────────────────────────────────────────────────────────────────────
# QA storm/cloud filtering - year-split because the QA encoding changes:
#   Year <= 2013 ... AVHRR CDR (AVH13C1), C-ATBD CDRP-ATBD-0459 Rev2
#   Year >= 2014 ... VIIRS CDR (NPP13C1), C-ATBD CDRP-ATBD-1267 Rev0
# Both stored in the same 'QA-AHRR' column as 16-bit integers.
# ──────────────────────────────────────────────────────────────────────────────
 
# --- AVHRR bitmasks (Year <= 2013) ---
# Bits listed LSB (0) to MSB (15)
#   Bit  0  - unused
#   Bit  1  - cloudy                       1 = yes
#   Bit  2  - cloud shadow                 1 = yes
#   Bit  3  - over water                   1 = yes
#   Bit  4  - sunglint                     1 = yes
#   Bit  5  - dense dark vegetation        1 = yes
#   Bit  6  - night / high solar zenith    1 = yes
#   Bit  7  - channels 1-5 valid           1 = yes  (0 = all invalid)
#   Bit  8  - channel 1 invalid            1 = yes
#   Bit  9  - channel 2 (NIR) invalid      1 = yes
#   Bit 10  - channel 3 invalid            1 = yes
#   Bit 11  - channel 4 invalid            1 = yes
#   Bit 12  - channel 5 invalid            1 = yes
#   Bit 13  - RHO3 invalid                 1 = yes
#   Bit 14  - BRDF correction issues       1 = yes
#   Bit 15  - polar flag (lat>60 land)     1 = yes
AVHRR_CLOUDY       = (1 << 1)   # 0x0002
AVHRR_CLOUD_SHADOW = (1 << 2)   # 0x0004
# sunglint (bit 4), night/high-zenith (bit 6), invalid channels (bits 8-9)
# excluded - too aggressive; cuts valid winter obs and overlaps legacy filters
 
AVHRR_MASK = (
    AVHRR_CLOUDY       
)

# |
#     AVHRR_CLOUD_SHADOW
# --- VIIRS bitmasks (Year >= 2014) ---
# Bits listed LSB (0) to MSB (15)
#   Bits 0-1  - cloud state: 00=clear 01=prob.clear 10=prob.cloudy 11=cloudy
#   Bit  2    - cloud shadow               1 = yes
#   Bits 3-5  - land/water flag
#   Bit  6    - aerosol quality            1 = OK, 0 = poor  (inverted logic)
#   Bit  7    - unused
#   Bit  8    - thin cirrus reflective     1 = yes
#   Bit  9    - thin cirrus emissive       1 = yes
#   Bit 10    - cloud flag                 1 = cloud
#   Bits 11-14- unused
#   Bit 15    - snow/ice                   1 = yes
VIIRS_CLOUD_STATE_MASK = 0x0003  # bits 0-1 together
VIIRS_CLOUD_SHADOW     = (1 << 2)   # 0x0004
VIIRS_LAND_WATER_SHIFT = 3          # bits 3-5 are the land/water field
VIIRS_LAND_WATER_MASK  = 0x0038     # isolates bits 3-5
# land/water values (after >> 3): 0=land+desert  1=land no desert
#   2=inland water  3=sea water  5=coastal - keep only 0 and 1
VIIRS_LAND_WATER_MIN_NONLAND = (2 << VIIRS_LAND_WATER_SHIFT)  # 0x0010 - inland water threshold
VIIRS_CLOUD_FLAG       = (1 << 10)  # 0x0400
# thin cirrus (bits 8-9) and aerosol quality (bit 6) excluded - too aggressive
# over Great Plains; cirrus has minimal effect on NIR-based NDVI and aerosol
# poor flags capture dust/smoke events that carry real soil moisture signal
 
# Legacy threshold filters (sensor-era anomalies, kept as-is)
# data = data[~((data['Year'] <= 2013) & ((data['QA-AHRR'] >= 16500) & (data['QA-AHRR'] < 16600)))]
# data = data[~((data['Year'] >= 2014) & (data['QA-AHRR'] >= 255))]
 
qa_int = data['QA-AHRR'].astype(int)
is_avhrr = data['Year'] <= 2013
is_viirs = data['Year'] >= 2014
 
# --- per-filter diagnostics ---
avhrr_cloudy_cut       = is_avhrr & ((qa_int & AVHRR_CLOUDY)       != 0)
avhrr_shadow_cut       = is_avhrr & ((qa_int & AVHRR_CLOUD_SHADOW)  != 0)
viirs_state_cut        = is_viirs & ((qa_int & VIIRS_CLOUD_STATE_MASK) == 3)
viirs_shadow_cut       = is_viirs & ((qa_int & VIIRS_CLOUD_SHADOW)  != 0)
viirs_cloudflag_cut    = is_viirs & ((qa_int & VIIRS_CLOUD_FLAG)    != 0)
viirs_landwater_cut    = is_viirs & ((qa_int & VIIRS_LAND_WATER_MASK) >= VIIRS_LAND_WATER_MIN_NONLAND)
 
n = len(data)
print(f"  AVHRR cloudy        : {avhrr_cloudy_cut.sum():>7}  ({100*avhrr_cloudy_cut.sum()/n:.1f}%)")
print(f"  AVHRR cloud shadow  : {avhrr_shadow_cut.sum():>7}  ({100*avhrr_shadow_cut.sum()/n:.1f}%)")
print(f"  VIIRS confident cld : {viirs_state_cut.sum():>7}  ({100*viirs_state_cut.sum()/n:.1f}%)")
print(f"  VIIRS cloud shadow  : {viirs_shadow_cut.sum():>7}  ({100*viirs_shadow_cut.sum()/n:.1f}%)")
print(f"  VIIRS cloud flag    : {viirs_cloudflag_cut.sum():>7}  ({100*viirs_cloudflag_cut.sum()/n:.1f}%)")
print(f"  VIIRS land/water    : {viirs_landwater_cut.sum():>7}  ({100*viirs_landwater_cut.sum()/n:.1f}%)")
# note: overlap between filters means total cut < sum of individual cuts
 
# AVHRR storm filter - cloudy and cloud shadow only
avhrr_bad = is_avhrr & ((qa_int & AVHRR_MASK) != 0)
 
# VIIRS storm filter - confident cloudy only (state == 3), cloud shadow,
# cloud flag, and non-land pixels... prob.cloudy (state == 2) kept to avoid
# over-cutting; cloud flag (bit 10) acts as the safety catch for those
viirs_cloud_state_bad = is_viirs & ((qa_int & VIIRS_CLOUD_STATE_MASK) == 3)
viirs_bits_bad = is_viirs & (
    ((qa_int & VIIRS_CLOUD_SHADOW) != 0) |
    ((qa_int & VIIRS_LAND_WATER_MASK) >= VIIRS_LAND_WATER_MIN_NONLAND)
    # cloud flag (bit 10) excluded - redundant with cloud state field and cuts
    # ~30% of VIIRS data on its own; cloud state == 3 + shadow are sufficient
)
#############################

data = data[~(avhrr_bad | viirs_cloud_state_bad )] #| viirs_bits_bad | viirs_bits_bad
 
n_after = len(data)
print(f"QA storm filter (AVHRR pre-2014 / VIIRS 2014+): "
      f"removed {n_before - n_after} rows "
      f"({100 * (n_before - n_after) / max(n_before, 1):.1f}%)")
 
data = data.merge(hist_data2[['PageName', 'Month', 'AHRR_MEAN']], on=['PageName', 'Month'])
data.rename(columns={'AHRR_MEAN': 'AHRR_M'}, inplace=True)
#data = data[data['AHRR_M'] > 0.1]
data['AHRR_A'] = data['AHRR'] - data['AHRR_M'] 
# data = data[data['AHRR'] < 0.85]
# data = data[data['AHRR'] > 0.1]
data['A_A'] = abs(data['AHRR'] - data['F-AHRR'])
data = data[data['A_A'] < 0.2]
aout_after = len(data)
print("Total percentage, after AHRR outlier removal:" + f"({100 * (n_before - aout_after) / max(n_before, 1):.1f}%)" )



print("Number of Unique PageName Pixels After Cutting: " + str(data['PageName'].nunique()))


# data = data[abs(data['ML__A']) < 0.25]
#data = data[data['AHRR'] > 0.1]
# data['A_A'] = abs(data['AHRR'] - data['F-AHRR'])
# data = data[data['A_A'] < 0.4]
#data = data[data['LAI'] <= 7]

print(data.columns)
# data['AHRR_A'] = data['AHRR_A'].round(4)
# data['SMERGE_A'] = data['SMERGE_A'].round(4)
# data['ML__A'] = data['ML__A'].round(4)
if s_grids == '0':
    smerge_corr = core.averaged_rank_corr(data, 'AHRR_A', 'SMERGE_A')
    print(g_name + '___Smerge Rank Correlation:', smerge_corr)
try:
    ml_corr = core.averaged_rank_corr(data, 'AHRR_A', 'ML__A')
    print(g_name + '___ML_Smerge Rank Correlation:', ml_corr)
except:
    print("No ML_")

#########################################################################################################################
# if 'LandC' not in data.columns:
#     data = data.merge(land[['PageName', 'Year', 'LandC']], on=['PageName', 'Year'])

# category_A = [71, 81, 82,21,22,23,24]
# #Category B (Scrubland, Barren)
# category_B = [52, 31]
# #Category C (Forest, Wetlands)
# category_C = [41, 42, 43, 90, 95]


# data_A = data.loc[data['LandC'].isin(category_A)]
# data_B = data.loc[data['LandC'].isin(category_B)]
# data_C = data.loc[data['LandC'].isin(category_C)]
# data_D = data.loc[~data['LandC'].isin([21,22,23,24])]

# print("Cat A:" +str((len(data_A)/len(data))*100)+"%")
# print("Cat B:" +str((len(data_B)/len(data))*100)+"%")
# print("Cat C:" +str((len(data_C)/len(data))*100)+"%")
# print("Cat D:" +str((len(data_D)/len(data))*100)+"%")
# if s_grids == '0':
#     smerge_corr = core.averaged_rank_corr(data_A, 'AHRR_A', 'SMERGE_A')
#     print(g_name + '___ GroupA Smerge Rank Correlation:', smerge_corr)
# try:
#     ml_corr = core.averaged_rank_corr(data_A, 'AHRR_A', 'ML__A')
#     print(g_name + '___ GroupA  ML_Smerge Rank Correlation:', ml_corr)
# except:
#     print("No ML_")

# if s_grids == '0':
#     smerge_corr = core.averaged_rank_corr(data_B, 'AHRR_A', 'SMERGE_A')
#     print(g_name + '___ GroupB Smerge Rank Correlation:', smerge_corr)
# try:
#     ml_corr = core.averaged_rank_corr(data_B, 'AHRR_A', 'ML__A')
#     print(g_name + '___GroupB ML_Smerge Rank Correlation:', ml_corr)
# except:
#     print("No ML_")

# if s_grids == '0':
#     smerge_corr = core.averaged_rank_corr(data_C, 'AHRR_A', 'SMERGE_A')
#     print(g_name + '___GroupC Smerge Rank Correlation:', smerge_corr)
# try:
#     ml_corr = core.averaged_rank_corr(data_C, 'AHRR_A', 'ML__A')
#     print(g_name + '___GroupC ML_Smerge Rank Correlation:', ml_corr)
# except:
#     print("No ML_")

# if s_grids == '0':
#     smerge_corr = core.averaged_rank_corr(data_D, 'AHRR_A', 'SMERGE_A')
#     print(g_name + '___GroupD Smerge Rank Correlation:', smerge_corr)
# try:
#     ml_corr = core.averaged_rank_corr(data_D, 'AHRR_A', 'ML__A')
#     print(g_name + '___GroupD ML_Smerge Rank Correlation:', ml_corr)
# except:
#     print("No ML_")


# years = [2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018]
# print('Cutting Forward====================================================================================================================================================================================')
# for y in years:
#     data_t = data[data['Year'] <= y]
#     if s_grids == '0':
#         smerge_corr = core.averaged_rank_corr(data_t, 'AHRR_A', 'SMERGE_A')
#         print(g_name + '___' + str(y) +' Smerge Rank Correlation:', smerge_corr)
#     try:
#         ml_corr = core.averaged_rank_corr(data_t, 'AHRR_A', 'ML__A')
#         print(g_name + '___' + str(y) +' ML_Smerge Rank Correlation:', ml_corr)
#     except:
#         print("No ML_")
# print('Cutting Backward====================================================================================================================================================================================')
# for y in years:
#     data_t = data[data['Year'] >= y]
#     if s_grids == '0':
#         smerge_corr = core.averaged_rank_corr(data_t, 'AHRR_A', 'SMERGE_A')
#         print(g_name + '___' + str(y) +' Smerge Rank Correlation:', smerge_corr)
#     try:
#         ml_corr = core.averaged_rank_corr(data_t, 'AHRR_A', 'ML__A')
#         print(g_name + '___' + str(y) +' ML_Smerge Rank Correlation:', ml_corr)
#     except:
#         print("No ML_")

# if s_grids == '0':
#     grid_smerge = core.rank_corr_gird(data, 'AHRR_A','SMERGE_A', g_name+'SMERGE_A') ############
#     print(grid_smerge['R'].mean())
# try:
#     grid_ml = core.rank_corr_gird(data, 'AHRR_A', 'ML__A', g_name+'ML__A') ##################
#     print(grid_ml['R'].mean())
# except:
#     print("No ML_")