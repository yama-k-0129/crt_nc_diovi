import numpy as np
import xarray as xr
from datetime import datetime
import re
import netCDF4 as nc

def parse_date_time(date_time_str):
    match = re.match(r'(\d{4})/\s*(\d{1,2})/\s*(\d{1,2})\s+(\d{2}):(\d{2})', date_time_str)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        return datetime(year, month, day, hour, minute)
    else:
        raise ValueError(f"Unable to parse date-time string: {date_time_str}")

def parse_coordinate(coord_str):
    match = re.match(r'(\d+\.\d+)([EWNS])([+-])(\d+\.\d+)', coord_str)
    if match:
        value, direction, sign, step = match.groups()
        value = float(value)
        step = float(step)
        if direction in ['W', 'S']:
            value = -value
        if sign == '-':
            step = -step
        return value, step
    else:
        raise ValueError(f"Unable to parse coordinate string: {coord_str}")

def parse_text_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = []
    times = []
    lons = None
    lats = None
    nx, ny = None, None

    current_data = []
    for line_number, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        if '/' in line:  # This is a timestamp line
            if current_data:
                if nx is not None and ny is not None:
                    padded_data = np.zeros((ny, nx))
                    for i, row in enumerate(current_data):
                        padded_data[i, :len(row)] = row
                    data.append(padded_data)
                current_data = []
            
            parts = line.split()
            date_time_str = ' '.join(parts[:3])  # Combine date and time
            try:
                times.append(parse_date_time(date_time_str))
            except ValueError as e:
                print(f"Error parsing date-time on line {line_number}: {e}")
                print(f"Problematic line: {line}")
                continue
            
            # Extract grid size and coordinates
            try:
                grid_size = parts[4].strip('()').split('x')
                nx, ny = int(grid_size[0]), int(grid_size[1])
                
                if lons is None:
                    lon_start, lon_step = parse_coordinate(parts[5])
                    lat_start, lat_step = parse_coordinate(parts[6])
                    lons = np.linspace(lon_start, lon_start + lon_step * (nx - 1), nx)
                    lats = np.linspace(lat_start, lat_start - abs(lat_step) * (ny - 1), ny)
            except (ValueError, IndexError) as e:
                print(f"Error parsing grid size or coordinates on line {line_number}: {e}")
                print(f"Problematic line: {line}")
                continue
        elif line.startswith('AMeDAS:') or line.startswith('Radar:'):
            # Skip lines that start with 'AMeDAS:' or 'Radar:'
            continue
        else:
            # This is a data line
            try:
                values = [float(v) for v in line.split()]
                current_data.append(values)
            except ValueError as e:
                print(f"Error parsing data on line {line_number}: {e}")
                print(f"Problematic line: {line}")
                continue

    if current_data:
        if nx is not None and ny is not None:
            padded_data = np.zeros((ny, nx))
            for i, row in enumerate(current_data):
                padded_data[i, :len(row)] = row
            data.append(padded_data)

    return np.array(data), np.array(times), lons, lats

def create_formatted_netcdf(data, times, lons, lats, output_file, lon_range, lat_range):
    # Extract the data within the specified range
    lon_mask = (lons >= lon_range[0]) & (lons <= lon_range[1])
    lat_mask = (lats >= lat_range[0]) & (lats <= lat_range[1])
    
    extracted_data = data[:, lat_mask][:, :, lon_mask]
    extracted_lons = lons[lon_mask]
    extracted_lats = lats[lat_mask]

    # Create a new NetCDF file
    with nc.Dataset(output_file, 'w', format='NETCDF4') as ncfile:
        # Define dimensions
        ncfile.createDimension('lon', len(extracted_lons))
        ncfile.createDimension('lat', len(extracted_lats))
        ncfile.createDimension('time', len(times))

        # Create variables
        lon_var = ncfile.createVariable('lon', 'i2', ('lon',), zlib=True)
        lat_var = ncfile.createVariable('lat', 'i2', ('lat',), zlib=True)
        time_var = ncfile.createVariable('time', 'i4', ('time',), zlib=True)
        precip_var = ncfile.createVariable('precip', 'i2', ('time', 'lat', 'lon'), zlib=True, complevel=9, chunksizes=(1, len(extracted_lats), len(extracted_lons)))

        # Assign values and attributes to variables
        lon_var[:] = np.round((extracted_lons - 137) / 0.0125).astype('i2')
        lon_var.long_name = "longitude"
        lon_var.units = "degrees_east"
        lon_var.scale_factor = 0.0125
        lon_var.add_offset = 137.
        lon_var._Storage = "contiguous"
        lon_var._Endianness = "little"

        lat_var[:] = np.round((extracted_lats - 35) / 0.00833333333333333).astype('i2')
        lat_var.long_name = "latitude"
        lat_var.units = "degrees_north"
        lat_var.scale_factor = 0.00833333333333333
        lat_var.add_offset = 35.
        lat_var._Storage = "contiguous"
        lat_var._Endianness = "little"

        time_var[:] = nc.date2num(times, units="seconds since 1970-01-01 00:00:00 +0:00")
        time_var.long_name = "time"
        time_var.units = "seconds since 1970-01-01 00:00:00 +0:00"
        time_var._Storage = "contiguous"
        time_var._Endianness = "little"

        precip_var[:] = np.round(extracted_data * 10).astype('i2')
        precip_var.long_name = "precipitation"
        precip_var.units = "mm/h"
        precip_var.valid_min = 0
        precip_var.scale_factor = 0.1
        precip_var._Storage = "chunked"
        precip_var._ChunkSizes = [1, len(extracted_lats), len(extracted_lons)]
        precip_var._DeflateLevel = 9
        precip_var._Endianness = "little"

        # Add global attributes
        ncfile.Conventions = "CF-1.6"
        ncfile.title = "Radar AMeDAS Analysis data"
        ncfile.institution = "Tokyo (RSMC), Japan Meterological Agency"
        ncfile.source = "JMA GPV"
        ncfile.history = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Converted"
        ncfile.references = "JMA GPV"
        ncfile.comment = "Converted by Hitachi Power Solutions Co., Ltd."
        
        # Remove the problematic _Format attribute
        # ncfile._Format = "netCDF-4"  # This line is removed

    print(f"Formatted NetCDF file saved as {output_file}")

# メイン実行部分
if __name__ == "__main__":
    input_file = "../CD_data/output.txt"  # 入力ファイルのパスを適切に設定してください
    output_file = "output_formatted.nc"  # 出力ファイルのパスを適切に設定してください

    # 抽出する範囲を指定
    lon_range = (134.5, 136.5)
    lat_range = (34.0, 36.0)

    try:
        data, times, lons, lats = parse_text_file(input_file)
        create_formatted_netcdf(data, times, lons, lats, output_file, lon_range, lat_range)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()