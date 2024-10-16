import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import os
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap

# NetCDFファイルを読み込む
ds = xr.open_dataset('output_formatted.nc')

# カスタムカラーマップの定義
colors = ['#FFFFFF', '#A6F28F', '#3DBA3D', '#263CD9', '#9C1C8C', '#FFA07A']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=n_bins)

# プロットの設定
fig = plt.figure(figsize=(15, 10))
ax = plt.axes(projection=ccrs.PlateCarree())

# 地図の設定
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS)
ax.set_extent([ds.lon.min(), ds.lon.max(), ds.lat.min(), ds.lat.max()])

# 初期フレームの作成
precip = ds.precip.isel(time=0)
im = ax.pcolormesh(ds.lon, ds.lat, precip, transform=ccrs.PlateCarree(), cmap=cmap, vmin=0, vmax=50)

# カラーバーの追加
cbar = plt.colorbar(im, extend='max')
cbar.set_label('Precipitation (mm/h)')

# タイトルの設定
title = ax.set_title('')

# アニメーション更新関数
def update(frame):
    precip = ds.precip.isel(time=frame)
    im.set_array(precip.values.ravel())
    title.set_text(f'Precipitation at {ds.time[frame].values}')
    return im, title

# アニメーションの作成
anim = FuncAnimation(fig, update, frames=len(ds.time), interval=200, blit=True)

# 動画として保存
anim.save('extract_precipitation_animation.mp4', writer='ffmpeg', fps=5)

plt.close(fig)

print("Animation saved as 'precipitation_animation.mp4'")