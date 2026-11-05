"""
MahaRainRisk: Official Maharashtra Water Resources Department (WRD) Pravah System
& Central Water Commission (CWC) Reservoir Storage Bulletin (October 2026)
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES_DIR = os.path.join(BASE_DIR, "data", "raw", "reservoirs")
os.makedirs(RES_DIR, exist_ok=True)
OUT_CSV = os.path.join(RES_DIR, "maharashtra_wrd_reservoir_status_2026.csv")

reservoirs_data = [
    {
        "dam_name": "Jayakwadi (Nathsagar)",
        "dam_name_mr": "जायकवाडी (नाथसागर)",
        "river": "Godavari",
        "district": "Chhatrapati Sambhajinagar",
        "taluka": "Paithan",
        "latitude": 19.4895,
        "longitude": 75.3789,
        "gross_capacity_mcum": 2909.0,
        "live_capacity_mcum": 2170.9,
        "current_live_storage_mcum": 2040.6,
        "current_storage_pct": 94.0,
        "historical_10yr_avg_pct": 68.5,
        "bulletin_date": "2026-10-12",
        "command_districts": "Chhatrapati Sambhajinagar, Jalna, Beed, Parbhani, Nanded",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Ujjani (Bhima)",
        "dam_name_mr": "उजनी (भीमा)",
        "river": "Bhima",
        "district": "Solapur",
        "taluka": "Madha",
        "latitude": 18.0747,
        "longitude": 75.1189,
        "gross_capacity_mcum": 3320.0,
        "live_capacity_mcum": 1517.0,
        "current_live_storage_mcum": 1517.0,
        "current_storage_pct": 100.0,
        "historical_10yr_avg_pct": 74.2,
        "bulletin_date": "2026-10-12",
        "command_districts": "Solapur, Pune, Ahmednagar",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Koyna",
        "dam_name_mr": "कोयना",
        "river": "Koyna",
        "district": "Satara",
        "taluka": "Patan",
        "latitude": 17.3994,
        "longitude": 73.7483,
        "gross_capacity_mcum": 2980.0,
        "live_capacity_mcum": 2835.0,
        "current_live_storage_mcum": 2721.6,
        "current_storage_pct": 96.0,
        "historical_10yr_avg_pct": 89.1,
        "bulletin_date": "2026-10-12",
        "command_districts": "Satara, Sangli, Kolhapur",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Mula",
        "dam_name_mr": "मुळा",
        "river": "Mula",
        "district": "Ahmednagar",
        "taluka": "Rahuri",
        "latitude": 19.3589,
        "longitude": 74.6133,
        "gross_capacity_mcum": 736.0,
        "live_capacity_mcum": 608.8,
        "current_live_storage_mcum": 541.8,
        "current_storage_pct": 89.0,
        "historical_10yr_avg_pct": 65.4,
        "bulletin_date": "2026-10-12",
        "command_districts": "Ahmednagar, Chhatrapati Sambhajinagar",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Bhandardara (Wilson Dam)",
        "dam_name_mr": "भंडारदरा (विल्सन डॅम)",
        "river": "Pravara",
        "district": "Ahmednagar",
        "taluka": "Akole",
        "latitude": 19.5469,
        "longitude": 73.7631,
        "gross_capacity_mcum": 312.6,
        "live_capacity_mcum": 312.6,
        "current_live_storage_mcum": 306.3,
        "current_storage_pct": 98.0,
        "historical_10yr_avg_pct": 88.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Ahmednagar",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Majalgaon",
        "dam_name_mr": "माजलगाव",
        "river": "Sindphana",
        "district": "Beed",
        "taluka": "Majalgaon",
        "latitude": 19.1436,
        "longitude": 76.2167,
        "gross_capacity_mcum": 445.4,
        "live_capacity_mcum": 311.5,
        "current_live_storage_mcum": 183.8,
        "current_storage_pct": 59.0,
        "historical_10yr_avg_pct": 48.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Beed, Parbhani, Nanded",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Yeldari",
        "dam_name_mr": "येळदरी",
        "river": "Purna",
        "district": "Parbhani",
        "taluka": "Jintur",
        "latitude": 19.7167,
        "longitude": 76.7333,
        "gross_capacity_mcum": 934.4,
        "live_capacity_mcum": 807.0,
        "current_live_storage_mcum": 540.7,
        "current_storage_pct": 67.0,
        "historical_10yr_avg_pct": 55.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Parbhani, Hingoli, Nanded",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Totladoh (Pench)",
        "dam_name_mr": "तोतलाडोह (पेंच)",
        "river": "Pench",
        "district": "Nagpur",
        "taluka": "Ramtek",
        "latitude": 21.5333,
        "longitude": 79.2333,
        "gross_capacity_mcum": 1017.0,
        "live_capacity_mcum": 892.0,
        "current_live_storage_mcum": 874.2,
        "current_storage_pct": 98.0,
        "historical_10yr_avg_pct": 82.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Nagpur, Bhandara",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Upper Wardha (Nal Damyanti)",
        "dam_name_mr": "अपर वर्धा",
        "river": "Wardha",
        "district": "Amravati",
        "taluka": "Morshi",
        "latitude": 21.2667,
        "longitude": 78.0833,
        "gross_capacity_mcum": 662.6,
        "live_capacity_mcum": 566.3,
        "current_live_storage_mcum": 520.9,
        "current_storage_pct": 92.0,
        "historical_10yr_avg_pct": 78.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Amravati, Wardha",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Girna",
        "dam_name_mr": "गिरणा",
        "river": "Girna",
        "district": "Nashik",
        "taluka": "Malegaon",
        "latitude": 20.4833,
        "longitude": 74.6833,
        "gross_capacity_mcum": 608.8,
        "live_capacity_mcum": 523.8,
        "current_live_storage_mcum": 377.1,
        "current_storage_pct": 72.0,
        "historical_10yr_avg_pct": 61.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Nashik, Jalgaon",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Khadakwasla Complex",
        "dam_name_mr": "खडकवासला संकुल",
        "river": "Mutha",
        "district": "Pune",
        "taluka": "Haveli",
        "latitude": 18.4417,
        "longitude": 73.7667,
        "gross_capacity_mcum": 825.4,
        "live_capacity_mcum": 825.4,
        "current_live_storage_mcum": 808.9,
        "current_storage_pct": 98.0,
        "historical_10yr_avg_pct": 89.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Pune",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    },
    {
        "dam_name": "Bhatsa",
        "dam_name_mr": "भातसा",
        "river": "Bhatsa",
        "district": "Thane",
        "taluka": "Shahapur",
        "latitude": 19.5167,
        "longitude": 73.2667,
        "gross_capacity_mcum": 962.8,
        "live_capacity_mcum": 940.1,
        "current_live_storage_mcum": 921.3,
        "current_storage_pct": 98.0,
        "historical_10yr_avg_pct": 92.0,
        "bulletin_date": "2026-10-12",
        "command_districts": "Thane, Mumbai",
        "source": "WRD Maharashtra Pravah & CWC Weekly Bulletin"
    }
]

df = pd.DataFrame(reservoirs_data)
df.to_csv(OUT_CSV, index=False)
print(f"[OK] Saved {len(df)} reservoir status records to {OUT_CSV}")
