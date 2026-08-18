import math

def safe_float(value, default=None):
    """
    Safely convert a value to float, handling 'None', 'null', and other invalid strings.
    """
    if value is None or str(value).lower() in ['none', 'null', '']:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using Haversine formula.
    """
    # Use safe_float to ensure we have valid numbers
    f_lat1 = safe_float(lat1)
    f_lon1 = safe_float(lon1)
    f_lat2 = safe_float(lat2)
    f_lon2 = safe_float(lon2)

    if None in [f_lat1, f_lon1, f_lat2, f_lon2]:
        return 999.0  # Fallback for missing coordinates
    
    # Convert decimal degrees to radians 
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [f_lat1, f_lon1, f_lat2, f_lon2])

    # Haversine formula 
    dlon = lon2_rad - lon1_rad 
    dlat = lat2_rad - lat1_rad 
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    
    return round(c * r, 2)

