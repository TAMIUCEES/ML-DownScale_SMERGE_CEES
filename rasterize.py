import sys
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping
import seaborn as sns

data_path = sys.argv[1]
state = sys.argv[2]
var_c = sys.argv[3]

arg_val = sys.argv[4].lower()
is_corr = arg_val in ("true", "1", "yes")

# Define file paths
shapefile_path = "/scratch/group/p.ees250195.000/grids/Grid_"+state+"_500_State_ExportFeatures.shp"

# Load the shapefile
grid = gpd.read_file(shapefile_path)

# Load the external data (Assuming it's a CSV)
data = pd.read_csv(data_path)

# Ensure the key column exists in both datasets
if "PageName" not in grid.columns or "PageName" not in data.columns:
    raise ValueError("PageName column missing in one or both datasets.")

# Perform the table join
grid = grid.merge(data, on="PageName", how="left")

mod = ''
output_raster = data_path.replace('DataClean/', 'DataClean/Rasters/').replace('.csv', '_' + var_c + '.png')

# Ensure var_c column exists
if var_c not in grid.columns:
    raise ValueError("ML__y column missing after join. Check data consistency.")

# Set raster properties
xmin, ymin, xmax, ymax = grid.total_bounds
resolution = 100
width = int((xmax - xmin) / resolution)
height = int((ymax - ymin) / resolution)

# Define raster transform
transform = rasterio.transform.from_origin(xmin, ymax, resolution, resolution)

# Rasterize using var_c column
shapes = ((mapping(geom), value) for geom, value in zip(grid.geometry, grid[var_c]))

raster = rasterize(
    shapes=shapes,
    out_shape=(height, width),
    transform=transform,
    fill=-9999,  # NoData value
    dtype="float32"
)

# Save the raster as GeoTIFF
with rasterio.open(
    output_raster,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="float32",
    crs=grid.crs,
    transform=transform,
    nodata=-9999
) as dst:
    dst.write(raster, 1)

print(f"Rasterization complete! Saved as {output_raster}")

if is_corr == True:
    import matplotlib.pyplot as plt
    import rasterio.plot
    import numpy as np
    from matplotlib.colors import ListedColormap

    # Define the custom colors
    colors = ["blue", "dodgerblue", "lightskyblue", "lightblue", "pink", "lightcoral", "red", "firebrick"]
    cmap = ListedColormap(colors)

    # Open the raster file
    with rasterio.open(output_raster) as src:
        raster_data = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        nodata_value = src.nodata

    # Mask the nodata values for plotting
    raster_data_masked = np.ma.masked_equal(raster_data, nodata_value)

    # Define the bins for the color scale (0 to 0.8 with 8 bins)
    bins = np.linspace(0, 0.8, len(colors) + 1)

    # Assign each data point to a bin
    binned_data = np.digitize(raster_data_masked, bins) - 1
    binned_data[raster_data_masked.mask] = -1  # Assign a value outside bin range for masked data

    # Create a new colormap with transparency for the nodata value (-1)
    colors_with_nodata = [(0, 0, 0, 0)] + colors
    cmap_with_nodata = ListedColormap(colors_with_nodata)

    # Plot the raster with transparent nodata values and defined color scale
    plt.figure(figsize=(8, 6))
    image = rasterio.plot.show(binned_data, cmap=cmap_with_nodata, extent=extent, ax=plt.gca(), clim=[-1, len(colors)])

    # Create a colorbar with the specified bins and labels
    cbar = plt.colorbar(image.get_images()[0], ticks=np.arange(0.5, len(colors) + 0.5), label=var_c + " Values")
    cbar.ax.set_yticklabels([f'{bins[i]:.2f} - {bins[i+1]:.2f}' for i in range(len(colors))])

    plt.title("Rasterized " + var_c + mod)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

if is_corr == False:
    import matplotlib.pyplot as plt
    import numpy as np

    # Open the raster file
    with rasterio.open(output_raster) as src:
        raster_data = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        nodata_value = src.nodata  # -9999

    # Mask nodata before computing stats or plotting
    raster_data_masked = np.ma.masked_equal(raster_data, nodata_value)

    vmin = data[var_c].min()
    vmax = data[var_c].max()
    print(vmin)
    print(vmax)

    # Plot the raster
    plt.figure(figsize=(8, 6))
    plt.imshow(raster_data_masked, cmap="rainbow", extent=extent, origin="upper", vmin=vmin, vmax=vmax)
    plt.colorbar(label=var_c + " Values")
    plt.title("Rasterized " + var_c + mod)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

plt.savefig(output_raster, dpi=500)