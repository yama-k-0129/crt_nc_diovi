import xarray as xr

# NetCDFファイルを開く
ds = xr.open_dataset('output_formatted.nc')

# データセットの概要を表示
print(ds)

# 特定の変数のデータを表示
print(ds['precip'].values)