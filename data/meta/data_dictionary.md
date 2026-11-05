# MahaRainRisk: Data Dictionary & Feature Specification
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning & Farmer Advisory Platform  
**Reference Document:** *Data Sources and Data Plan* (October 2026) & *RainRisk Database Design* (October 2026)  
**Target User:** Maharashtra Smallholder Farmers, Village Krishi Sahayaks, District Agronomy Officers

---

## 1. Administrative & Geographic Entities (`data/geo/`)

### Table: `lgd_maharashtra_master.csv`
Represents the official administrative hierarchy per the Ministry of Panchayati Raj Local Government Directory (LGD).

| Column Name | Type | Unit / Format | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `state_lgd_code` | Integer | Standard LGD | Official LGD State Code for Maharashtra | `27` |
| `division_name` | String | UTF-8 Text | Administrative Revenue Division (6 total) | `Chhatrapati Sambhajinagar` |
| `division_name_mr` | String | Devanagari UTF-8 | Division name in Marathi | `छत्रपती संभाजीनगर` |
| `district_lgd_code` | Integer | Standard LGD | Official LGD District Code | `482` |
| `district_name` | String | Text | District name in English | `Chhatrapati Sambhajinagar` |
| `district_name_mr` | String | Devanagari UTF-8 | District name in Marathi | `छत्रपती संभाजीनगर` |
| `taluka_lgd_code` | Integer | Standard LGD | Official LGD Sub-district / Taluka Code | `4123` |
| `taluka_name` | String | Text | Taluka name in English | `Paithan` |
| `taluka_name_mr` | String | Devanagari UTF-8 | Taluka name in Marathi | `पैठण` |
| `latitude` | Float | Decimal Degrees | Centroid latitude (WGS 84, EPSG:4326) | `19.4795` |
| `longitude` | Float | Decimal Degrees | Centroid longitude (WGS 84, EPSG:4326) | `75.3854` |
| `agro_climatic_zone` | String | Text | Official ICAR/State Agro-Climatic Zone | `Central Maharashtra Plateau Zone` |
| `agro_climatic_zone_mr` | String | Devanagari UTF-8 | Agro-Climatic Zone in Marathi | `मध्य महाराष्ट्र पठारी विभाग` |
| `major_crops` | String | Comma-separated | Primary Kharif & Rabi crops grown | `Cotton, Soybean, Bajra, Tur, Sugarcane` |
| `major_crops_mr` | String | Devanagari UTF-8 | Major crops in Marathi | `कापूस, सोयाबीन, बाजरी, तूर, ऊस` |
| `soil_type` | String | Text | Predominant soil taxonomy & depth | `Medium to Deep Black Cotton Soil (Vertisol)` |
| `normal_annual_rainfall_mm` | Float | Millimeters (mm) | 1991–2020 IMD climatological normal rainfall | `685.4` |

---

## 2. Climatological & Meteorological Features (`data/interim/imd_rainfall.parquet`)

### Daily Taluka Climatological Variables (1990–2026)

| Feature Name | Type | Unit | Range / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `taluka_lgd_code` | Integer | LGD Code | Primary Key | Linked to `lgd_maharashtra_master` |
| `date` | Date | `YYYY-MM-DD` | 1990-01-01 to Present | Daily observation timestamp |
| `rainfall_mm` | Float | mm/day | `>= 0.0` | 24-hr cumulative precipitation (08:30 IST) |
| `temp_max_c` | Float | °C | `15.0 to 49.0` | Maximum surface air temperature (2m) |
| `temp_min_c` | Float | °C | `5.0 to 35.0` | Minimum surface air temperature (2m) |
| `temp_mean_c` | Float | °C | Calculated | `(temp_max_c + temp_min_c) / 2` |
| `is_rainy_day` | Boolean | `0 / 1` | Binary | `1` if `rainfall_mm >= 2.5 mm`, else `0` |
| `dry_spell_duration_days` | Integer | Days | `>= 0` | Consecutive days with rainfall `< 2.5 mm` during Kharif |
| `rainfall_anomaly_pct` | Float | % | `-100.0 to +500.0%` | Percentage departure from 30-year daily normal |

---

## 3. Atmospheric & Oceanic Teleconnection Features (`data/interim/teleconnections.parquet`)

| Feature Name | Source | Temporal Res | Unit | Description & Impact on Maharashtra Monsoon |
| :--- | :--- | :--- | :--- | :--- |
| `nino34_sst` | NOAA CPC | Monthly | °C | Sea surface temperature in Niño 3.4 region (5°N–5°S, 170°W–120°W) |
| `nino34_anomaly` | NOAA CPC | Monthly | °C Anomaly | SST departure from 1991–2020 base period |
| `oni` | NOAA CPC | 3-Month Running Mean | °C | Oceanic Niño Index. `ONI >= +0.5°C` indicates El Niño (triggers monsoon break spells) |
| `dmi` | JAMSTEC / BoM | Monthly | °C Anomaly | Dipole Mode Index (IOD). Positive DMI suppresses El Niño drought effects in Maharashtra |
| `iod_phase` | Categorical | Text | `Positive`, `Neutral`, `Negative` | State of the Indian Ocean Dipole |

---

## 4. Drought Indices & Engineered Features (`data/processed/master_panel.parquet`)

### Standardized Precipitation Indices (SPI)
Calculated via 2-parameter Gamma distribution fit (McKee et al., 1993) on taluka-aggregated rainfall:

| Feature Name | Timescale | Agronomic Relevance | Severe Drought Threshold |
| :--- | :--- | :--- | :--- |
| `spi_1` | 30 Days (1-Month) | Sowing failure, germination stress, topsoil moisture depletion | `SPI_1 <= -1.50` |
| `spi_3` | 90 Days (3-Month) | Mid-season crop stress, flowering/pod-development dry spells | `SPI_3 <= -1.50` |
| `spi_6` | 180 Days (6-Month) | Seasonal agricultural failure, surface reservoir depletion, well failure | `SPI_6 <= -1.50` |

### SPI Classification Standard (WMO-No. 1090)
- `SPI >= +2.00`: Extremely Wet (अत्यंत ओला)
- `+1.50 to +1.99`: Very Wet (खूप ओला)
- `+1.00 to +1.49`: Moderately Wet (मध्यम ओला)
- `-0.99 to +0.99`: Near Normal (सामान्य)
- `-1.00 to -1.49`: Moderate Drought (मध्यम दुष्काळ / Watch)
- `-1.50 to -1.99`: Severe Drought (तीव्र दुष्काळ / Alert)
- `SPI <= -2.00`: Extreme Drought (अति तीव्र दुष्काळ / Disaster)

### Hydrological & Crop Indicators
| Feature Name | Source | Unit | Description |
| :--- | :--- | :--- | :--- |
| `reservoir_storage_pct` | Maha WRD | % Live Storage | Live storage percentage in linked basin dams (e.g. Jayakwadi for Paithan) |
| `groundwater_depth_mbgl`| CGWB / GSDA | Meters bgl | Depth to water level below ground level. `> 10m` indicates acute distress |
| `smi` | SMAP / ERA5-Land | Percentile (0–100) | Soil Moisture Index: root zone (0–100cm) moisture availability |
| `vci` | MODIS / AVHRR | % (0–100) | Vegetation Condition Index. `VCI < 35%` indicates active agricultural drought |

---

## 5. Model Target & Advisory Output (`MahaRainRisk Database Design`)

### Multi-Horizon Drought Early Warning Target: `drought_risk_category`
| Category Code | Label (English) | Label (Marathi) | Criteria / Trigger | Required Action |
| :---: | :--- | :--- | :--- | :--- |
| **0** | Normal / Safe | सुरक्षित (सामान्य) | SPI-3 > -0.5, Reservoir > 60%, Soil moisture healthy | Standard agronomic practices |
| **1** | Watch (Mild Deficit) | लक्ष ठेवा (अल्प तूट) | SPI-3 between -0.5 and -1.0, dry spell 7–10 days | Soil moisture conservation, mulching |
| **2** | Alert (Moderate Drought) | सतर्कता (मध्यम दुष्काळ) | SPI-3 between -1.0 and -1.49, dry spell 11–17 days | Protective irrigation, foliar KNO3 spray, no urea |
| **3** | Severe Drought | तीव्र दुष्काळ | SPI-3 between -1.50 and -1.99, dry spell 18–25 days | Salvage harvesting, life-saving drip only, fodder prep |
| **4** | Extreme Drought | अति तीव्र दुष्काळ | SPI-3 <= -2.00 or dry spell > 25 days | Resowing alert (दुबार पेरणी टाळा), cattle camp support |

---

## 6. Official Advisory Matrix (Anchor: MPKV, VNMKV, PDKV, BSKKV)
All generated farmer advisories are mapped to official state agricultural universities based on agro-climatic zones:
1. **MPKV Rahuri** (*Mahatma Phule Krishi Vidyapeeth*): Western Maharashtra Plateau & Scarcity Zone (Ahmednagar, Pune, Solapur, Nashik, Dhule, Jalgaon, Nandurbar, Satara, Sangli, Kolhapur).
2. **VNMKV Parbhani** (*Vasantrao Naik Marathwada Krishi Vidyapeeth*): Marathwada (Chhatrapati Sambhajinagar, Jalna, Beed, Dharashiv, Latur, Nanded, Parbhani, Hingoli).
3. **PDKV Akola** (*Dr. Panjabrao Deshmukh Krishi Vidyapeeth*): Vidarbha (Akola, Amravati, Buldhana, Washim, Yavatmal, Wardha, Nagpur, Bhandara, Gondia, Chandrapur, Gadchiroli).
4. **BSKKV Dapoli** (*Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth*): Konkan Coastal Zone (Thane, Palghar, Raigad, Ratnagiri, Sindhudurg).
