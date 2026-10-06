# Data schema

Input CSVs come from an upstream preprocessing pipeline that is not part of this repository. One
row is one 500 m pixel on one date.

| Column | Type | Role | Notes |
| --- | --- | --- | --- |
| `PageName` | str | grouping key | map tile id, used for the monthly climatology in the sanity metric |
| `Date` | str `YYYY-MM-DD` | none | read for completeness |
| `Clay`, `Sand`, `Silt` | float | feature | fractions; rows where the three do not sum to 1 within `[0.9999, 1.0001)` are dropped |
| `Elevation`, `Slope`, `Aspect` | float | feature | terrain |
| `LAI` | float | feature | MODIS MCD15A3H |
| `MODIS` | float | feature | MODIS NDVI |
| `ALB` | float | feature | MODIS MCD43A3 albedo |
| `Temp` | float | feature | temperature |
| `Month`, `Year` | int | feature | raw integers (no cyclic encoding) |
| `SMERGE` | float | target | |
| `AHRR` | float | carried through | AVHRR NDVI; used by the sanity metric and downstream validation |

Rows with a missing value in any of these columns are dropped.

## Feature groups

The GLU and TFT scripts split the 12 features into three groups by position in `var2`. Reordering
`var2` requires updating `STATIC_IDX`, `DYNAMIC_IDX` and `TEMPORAL_IDX`.

| Group | Indices | Features |
| --- | --- | --- |
| static | 0-5 | Clay, Sand, Silt, Elevation, Aspect, Slope |
| dynamic | 6-9 | LAI, MODIS, ALB, Temp |
| temporal | 10-11 | Month, Year |

TabNet, XGBoost and Random Forest take the flat 12-feature vector.

## Sharding

Rank `r` of `N` keeps rows `r, r+N, r+2N, ...`. The torch and XGBoost scripts apply this to the
cleaned data. The Random Forest script streams the CSV and applies it to the raw row index before
cleaning, so its row-to-rank assignment differs slightly. Shards are even and unbiased but are not
spatially or temporally contiguous.
