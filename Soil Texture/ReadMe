# Soil Texture Data Process: SSURGO / gNATSGO to Sand, Silt, Clay Rasters

## Overview

The process turns SSURGO or gNATSGO soil tables into one sand, silt and clay percentage per map unit (MUKEY) for the top 40 cm of soil, then joins those values to the MapunitRaster so every grid cell carries a texture value. These become the Sand, Silt and Clay inputs to the downscaling model.

The calculation is three roll-ups: horizon to component, component to map unit, then map unit to raster. At each level the values are weighted and renormalized so they sum to 100%.

gNATSGO is a gap-filled mosaic of SSURGO and STATSGO2 and uses the same table structure, so the steps are identical for either source.

## Inputs

Three sources are needed, all from the state gNATSGO geodatabase (for Oklahoma, `gNATSGO_OK.gdb`). Each table is trimmed to the fields below before any calculation.

| Source | Provides | Fields kept |
| --- | --- | --- |
| MapunitRaster_10m | MUKEY for each 10 m cell | Raster value (MUKEY) |
| Component table | Composition % of each component in a map unit | OBJECTID, comppct_r, comppct_l, mukey, cokey |
| Horizon (chorizon) table | Sand, silt and clay by depth layer | OBJECTID, hzname, hzdepb_r, hzthk_r, sandtotal_r, silttotal_r, claytotal_r, cokey, chkey |

The keys link the tables: a MUKEY holds several components (cokey), and each component holds several horizons (chkey). The `_r` suffix is the representative value; `_l` is the low value.

## Step 1: Weight each horizon to the top 40 cm

Each horizon contributes in proportion to how much of its thickness falls inside 0 to 40 cm. Five helper columns in the Horizon table work out that thickness.

| Column | Logic | Result |
| --- | --- | --- |
| Cal_1 | sandtotal_r is blank | -1 if blank, else 0 |
| Cal_2 | Top of horizon (hzdepb_r - hzthk_r) is deeper than 40 cm | 0 if entirely below 40 cm, else 1 |
| Cal_3 | Horizon straddles 40 cm (hzdepb_r > 40) | hzthk_r - (hzdepb_r - 40), the part above 40 cm; 0 if Cal_2 is 0 |
| Cal_4 | Cal_3 with negatives removed | Thickness above 40 cm for straddling horizons |
| Cal_5 | Horizon ends above 40 cm (hzdepb_r < 40) | hzthk_r, the full thickness |

A horizon is used only when Cal_1 + Cal_2 = 1, meaning it has data and starts above 40 cm. The Excel workflow pastes these columns as values before the next calculation.

The weighted values are then:

```math
\text{SandTotal\_1} = \text{sandtotal\_r} \cdot \frac{\text{Cal\_4} + \text{Cal\_5}}{40}
```

SiltTotal_1 and ClayTotal_1 use the same weight with silttotal_r and claytotal_r. Summed over a full 40 cm profile, the weights add to 1, so a component's weighted values add up to its depth-averaged texture.

## Step 2: Roll horizons up to components

In the Component table, the weighted horizon values are summed for each cokey, then normalized and scaled by the component's share of the map unit.

1. Sum the weighted sand, silt and clay of every horizon with the same cokey (TotalSand_2, TotalSilt_2, TotalClay_2), and add them to get SoilTotal_2.
2. Normalize so the three values total 100 (the `_3` columns). This matters for profiles shallower than 40 cm, whose weights add to less than 1. A component with no sand data stays at 0.
3. Multiply each by comppct_r / 100 (the `_4` columns), so each component counts in proportion to its area share.
4. Set Adjust_Comp to comppct_r when the component has texture data, otherwise 0. This is used in the next step to drop components such as water or rock outcrop.

```math
\text{TotalSand\_3} = \text{TotalSand\_2} \cdot \frac{100}{\text{SoilTotal\_2}} \qquad \text{TotalSand\_4} = \text{TotalSand\_3} \cdot \frac{\text{comppct\_r}}{100}
```

## Step 3: Roll components up to map units

In the unique MUKEY table, the component values are summed per MUKEY and rescaled so the result is a percentage of the components that have data.

1. SoilTotal_5 = sum of Adjust_Comp for all components in the MUKEY.
2. TotalSand_5, TotalSilt_5 and TotalClay_5 = sum of the `_4` values for those components, multiplied by 100 / SoilTotal_5.
3. SoilTotal_6 = TotalSand_5 + TotalSilt_5 + TotalClay_5. This must equal 100 for every MUKEY.

```math
\text{TotalSand\_5} = \left(\sum_{c \in \text{MUKEY}} \text{TotalSand\_4}_c\right) \cdot \frac{100}{\sum_{c \in \text{MUKEY}} \text{Adjust\_Comp}_c}
```

The SoilTotal_6 check is the main quality control. Any MUKEY that does not total 100 points to a join error or a missing component, and should be fixed before the table is joined to the raster.

## Step 4: Join to the raster

Export the final MUKEY, TotalSand_5, TotalSilt_5 and TotalClay_5 columns as a table and join it to the MapunitRaster_10m on the MUKEY value in ArcGIS Pro. Then export one raster per texture class (sand, silt, clay). Check that the three rasters sum to about 100 in a sample of cells.

The soil rasters are then resampled or clipped to the model grid alongside the other predictors (elevation, slope, aspect, NDVI, albedo and LAI).

## Known issues

- **Horizons ending at exactly 40 cm get zero weight.** Cal_3 requires `hzdepb_r > 40` and Cal_5 requires `hzdepb_r < 40`, so a horizon with `hzdepb_r = 40` is counted by neither. Changing Cal_5 to `hzdepb_r <= 40` fixes it. In the CONUS Horizon table, 7,480 of 3,537,186 rows (0.21%) have `hzdepb_r = 40`, and all of them are affected. The share is small nationally, but its effect on a given map unit depends on whether the dropped horizon was the only one in the top 40 cm.
- **Shallow profiles are rescaled, not extended.** A component with only 25 cm of data is normalized to 100 using those 25 cm, so its texture represents the shallow layers only.
- **Components without data are dropped.** Water, rock outcrop and similar components have no sand value, so they are excluded and the remaining components are rescaled. Map units made up entirely of such components have no texture value.
- **Representative values only.** The process uses the `_r` values and ignores the low and high ranges, so it carries no uncertainty estimate.

## Appendix: formula reference

Column names follow `Soil_Cal_DataModel_Formulas.txt` (DAX measures in the Excel data model).

| Table | Column | Formula |
| --- | --- | --- |
| Horizon | Cal_1 | `IF(sandtotal_r = BLANK(), -1, 0)` |
| Horizon | Cal_2 | `IF((hzdepb_r - hzthk_r) > 40, 0, 1)` |
| Horizon | Cal_3 | `IF(Cal_2 < 1, 0, IF(hzdepb_r > 40, hzthk_r - (hzdepb_r - 40), 0))` |
| Horizon | Cal_4 | `IF(Cal_3 < 0, 0, Cal_3)` |
| Horizon | Cal_5 | `IF(hzdepb_r < 40, hzthk_r, 0)` |
| Horizon | SandTotal_1 (same for Silt, Clay) | `IF((Cal_1 + Cal_2) = 1, sandtotal_r * ((Cal_4 + Cal_5) / 40), BLANK())` |
| Component | TotalSand_2 (same for Silt, Clay) | `SUMX(FILTER(Horizon, Horizon[cokey] = Component[cokey]), Horizon[SandTotal_1])` |
| Component | SoilTotal_2 | `TotalSand_2 + TotalSilt_2 + TotalClay_2` |
| Component | TotalSand_3 | `IF(TotalSand_2 = 0, 0, IF(SoilTotal_2 = 100, TotalSand_2, TotalSand_2 * (100 / SoilTotal_2)))` |
| Component | TotalSand_4 | `TotalSand_3 * (comppct_r / 100)` |
| Component | Adjust_Comp | `IF(TotalSand_2 = 0, 0, comppct_r)` |
| MUKEY | SoilTotal_5 | `SUMX(FILTER(Component, Component[mukey] = mukey), Component[Adjust_Comp])` |
| MUKEY | TotalSand_5 | `SUMX(FILTER(Component, Component[mukey] = mukey), Component[TotalSand_4]) * (100 / SoilTotal_5)` |
| MUKEY | SoilTotal_6 | `TotalSand_5 + TotalSilt_5 + TotalClay_5` |
