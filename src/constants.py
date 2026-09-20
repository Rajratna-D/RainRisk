"""
RainRisk: Shared geographic coordinates, regional groupings, color maps, and naming aliases.
"""

# High-contrast color mapping corresponding to IMD meteorological severity levels
CATEGORY_COLORS = {
    "No Rainfall":     "#64748b",
    "Large Deficient": "#f43f5e",
    "Deficient":       "#f59e0b",
    "Normal":          "#10b981",
    "Excess":          "#06b6d4",
    "Large Excess":    "#3b82f6",
}

# Representative subdivision centroid coordinates (lat, lon) for map rendering
COORDS = {
    "Andaman & Nicobar Islands": (11.7, 92.7),
    "Arunachal Pradesh": (28.2, 94.7),
    "Assam & Meghalaya": (26.2, 92.5),
    "Bihar": (25.1, 85.3),
    "Chhattisgarh": (21.3, 81.9),
    "Coastal Andhra Pradesh": (16.5, 80.6),
    "Coastal Karnataka": (14.5, 74.4),
    "East Madhya Pradesh": (23.2, 80.9),
    "East Rajasthan": (26.9, 75.8),
    "East Uttar Pradesh": (26.8, 82.2),
    "Gangetic West Bengal": (22.6, 87.9),
    "Gujarat Region": (22.3, 72.6),
    "Haryana Delhi & Chandigarh": (29.1, 76.8),
    "Himachal Pradesh": (31.1, 77.2),
    "Jammu & Kashmir": (34.1, 74.8),
    "Jharkhand": (23.6, 85.3),
    "Kerala": (10.9, 76.3),
    "Konkan & Goa": (15.5, 73.8),
    "Lakshadweep": (10.6, 72.6),
    "Madhya Maharashtra": (18.5, 74.8),
    "Marathwada": (19.9, 75.3),
    "Matathwada": (19.9, 75.3),
    "Naga Mani Mizo Tripura": (24.7, 93.9),
    "North Interior Karnataka": (15.3, 75.7),
    "Odisha": (20.9, 85.1),
    "Orissa": (20.9, 85.1),
    "Punjab": (31.1, 75.3),
    "Rayalaseema": (14.7, 78.6),
    "Rayalseema": (14.7, 78.6),
    "Saurashtra & Kutch": (22.3, 70.8),
    "South Interior Karnataka": (12.9, 76.5),
    "Sub Himalayan West Bengal": (26.7, 88.4),
    "Sub Himalayan West Bengal & Sikkim": (26.7, 88.4),
    "Tamil Nadu": (11.1, 78.7),
    "Telangana": (17.4, 78.5),
    "Uttarakhand": (30.1, 79.0),
    "Vidarbha": (21.1, 79.1),
    "West Madhya Pradesh": (22.7, 75.9),
    "West Rajasthan": (26.3, 73.0),
    "West Uttar Pradesh": (28.5, 78.5),
}

# IMD regional meteorological classifications
MACRO_REGIONS = {
    "Northwest India": [
        "West Uttar Pradesh", "East Uttar Pradesh", "Uttarakhand", "Haryana Delhi & Chandigarh",
        "Punjab", "Himachal Pradesh", "Jammu & Kashmir", "West Rajasthan", "East Rajasthan",
    ],
    "Central India": [
        "Odisha", "Orissa", "West Madhya Pradesh", "East Madhya Pradesh", "Gujarat Region",
        "Saurashtra & Kutch", "Konkan & Goa", "Madhya Maharashtra", "Marathwada", "Matathwada",
        "Vidarbha", "Chhattisgarh",
    ],
    "South Peninsula": [
        "Andaman & Nicobar Islands", "Coastal Andhra Pradesh", "Telangana", "Rayalaseema", "Rayalseema",
        "Tamil Nadu", "Coastal Karnataka", "North Interior Karnataka", "South Interior Karnataka",
        "Kerala", "Lakshadweep",
    ],
    "East & Northeast India": [
        "Arunachal Pradesh", "Assam & Meghalaya", "Naga Mani Mizo Tripura",
        "Sub Himalayan West Bengal", "Sub Himalayan West Bengal & Sikkim",
        "Gangetic West Bengal", "Jharkhand", "Bihar",
    ],
}

# Historical IMD dataset artifacts retain legacy spelling variants (e.g. 'Matathwada', 'Orissa')
# required by the pre-trained OneHotEncoder pipeline; DISPLAY_NAME_MAP translates them to modern standardized names.
DISPLAY_NAME_MAP = {
    "Matathwada": "Marathwada",
    "Orissa": "Odisha",
    "Rayalseema": "Rayalaseema",
}

CANONICAL_DATASET_NAMES = {
    "Marathwada": "Matathwada",
    "Matathwada": "Matathwada",
    "Odisha": "Orissa",
    "Orissa": "Orissa",
    "Rayalaseema": "Rayalseema",
    "Rayalseema": "Rayalseema",
    "Sub Himalayan West Bengal": "Sub Himalayan West Bengal & Sikkim",
    "Sub Himalayan West Bengal & Sikkim": "Sub Himalayan West Bengal & Sikkim",
}
