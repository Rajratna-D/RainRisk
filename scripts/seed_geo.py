"""
MahaRainRisk: Administrative Geography Seeding Script
Generates official Maharashtra administrative tables and GeoJSON layers:
- All 36 Districts with LGD codes, Marathi names, and agro-climatic zones
- Key Talukas across Marathwada, Vidarbha, Western Maharashtra, Khandesh, and Konkan
- Output: lgd_maharashtra_master.csv, maharashtra_districts.geojson, maharashtra_talukas.geojson
"""

import json
import os
import pandas as pd
import numpy as np

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_DIR = os.path.join(BASE_DIR, "data", "geo")
os.makedirs(GEO_DIR, exist_ok=True)

# 36 Districts of Maharashtra Master Reference
DISTRICTS_DATA = [
    # --- Marathwada (Chhatrapati Sambhajinagar Division) - High Drought Vulnerability ---
    {
        "district_lgd": 482, "district": "Chhatrapati Sambhajinagar", "district_mr": "छत्रपती संभाजीनगर",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 19.8762, "lon": 75.3433,
        "normal_rain_mm": 725.8, "soil": "Medium Black Vertisol",
        "crops": "Cotton, Soybean, Bajra, Maize, Sugarcane", "crops_mr": "कापूस, सोयाबीन, बाजरी, मका, ऊस",
        "talukas": [
            {"lgd": 4120, "name": "Aurangabad", "name_mr": "औरंगाबाद", "lat": 19.8762, "lon": 75.3433},
            {"lgd": 4121, "name": "Kannad", "name_mr": "कन्नड", "lat": 20.2642, "lon": 75.1328},
            {"lgd": 4122, "name": "Sillod", "name_mr": "सिल्लोड", "lat": 20.3045, "lon": 75.6517},
            {"lgd": 4123, "name": "Paithan", "name_mr": "पैठण", "lat": 19.4795, "lon": 75.3854},
            {"lgd": 4124, "name": "Gangapur", "name_mr": "गंगापूर", "lat": 19.6997, "lon": 75.0118},
            {"lgd": 4125, "name": "Vaijapur", "name_mr": "वैजापूर", "lat": 19.9272, "lon": 74.7289},
            {"lgd": 4126, "name": "Khuldabad", "name_mr": "खुलताबाद", "lat": 20.0076, "lon": 75.1878},
            {"lgd": 4127, "name": "Phulambri", "name_mr": "फुलंब्री", "lat": 20.0881, "lon": 75.4219},
            {"lgd": 4128, "name": "Soegaon", "name_mr": "सोयगाव", "lat": 20.5367, "lon": 75.3986}
        ]
    },
    {
        "district_lgd": 486, "district": "Jalna", "district_mr": "जालना",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 19.8410, "lon": 75.8864,
        "normal_rain_mm": 688.0, "soil": "Medium Deep Black Soil",
        "crops": "Soybean, Cotton, Sweet Orange (Mosambi), Tur", "crops_mr": "सोयाबीन, कापूस, मोसंबी, तूर",
        "talukas": [
            {"lgd": 4130, "name": "Jalna", "name_mr": "जालना", "lat": 19.8410, "lon": 75.8864},
            {"lgd": 4131, "name": "Bhokardan", "name_mr": "भोकरदन", "lat": 20.2583, "lon": 75.7678},
            {"lgd": 4132, "name": "Jafrabad", "name_mr": "जाफ्राबाद", "lat": 20.2189, "lon": 75.9922},
            {"lgd": 4133, "name": "Badnapur", "name_mr": "बदनापूर", "lat": 19.8690, "lon": 75.7258},
            {"lgd": 4134, "name": "Ambad", "name_mr": "अंबड", "lat": 19.6156, "lon": 75.7878},
            {"lgd": 4135, "name": "Ghansawangi", "name_mr": "घनसावंगी", "lat": 19.5256, "lon": 75.9989},
            {"lgd": 4136, "name": "Partur", "name_mr": "परतूर", "lat": 19.5917, "lon": 76.2167},
            {"lgd": 4137, "name": "Mantha", "name_mr": "मंठा", "lat": 19.6917, "lon": 76.3833}
        ]
    },
    {
        "district_lgd": 484, "district": "Beed", "district_mr": "बीड",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Scarcity Zone", "zone_mr": "दुष्काळी अवर्षण प्रवण विभाग",
        "univ": "VNMKV Parbhani", "lat": 18.9891, "lon": 75.7601,
        "normal_rain_mm": 666.2, "soil": "Shallow to Medium Vertisol",
        "crops": "Soybean, Cotton, Bajra, Tur, Sugarcane", "crops_mr": "सोयाबीन, कापूस, बाजरी, तूर, ऊस",
        "talukas": [
            {"lgd": 4140, "name": "Beed", "name_mr": "बीड", "lat": 18.9891, "lon": 75.7601},
            {"lgd": 4141, "name": "Georai", "name_mr": "गेवराई", "lat": 19.2636, "lon": 75.7533},
            {"lgd": 4142, "name": "Majalgaon", "name_mr": "माजलगाव", "lat": 19.1492, "lon": 76.2231},
            {"lgd": 4143, "name": "Ambejogai", "name_mr": "अंबाजोगाई", "lat": 18.7297, "lon": 76.3861},
            {"lgd": 4144, "name": "Kaij", "name_mr": "केज", "lat": 18.7061, "lon": 76.0125},
            {"lgd": 4145, "name": "Parli", "name_mr": "परळी", "lat": 18.8475, "lon": 76.5333},
            {"lgd": 4146, "name": "Patoda", "name_mr": "पाटोदा", "lat": 18.9333, "lon": 75.4667},
            {"lgd": 4147, "name": "Ashti", "name_mr": "आष्टी", "lat": 18.8042, "lon": 75.1764},
            {"lgd": 4148, "name": "Shirur Kasar", "name_mr": "शिरूर कासार", "lat": 19.1167, "lon": 75.4500},
            {"lgd": 4149, "name": "Wadwani", "name_mr": "वडवणी", "lat": 18.9500, "lon": 76.0167},
            {"lgd": 4150, "name": "Dharur", "name_mr": "धारूर", "lat": 18.8167, "lon": 76.1167}
        ]
    },
    {
        "district_lgd": 485, "district": "Dharashiv", "district_mr": "धाराशिव",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Scarcity Zone", "zone_mr": "दुष्काळी अवर्षण प्रवण विभाग",
        "univ": "VNMKV Parbhani", "lat": 18.1856, "lon": 76.0419,
        "normal_rain_mm": 730.0, "soil": "Medium Black Soil",
        "crops": "Soybean, Jowar, Tur, Gram, Sugarcane", "crops_mr": "सोयाबीन, ज्वारी, तूर, हरभरा, ऊस",
        "talukas": [
            {"lgd": 4151, "name": "Osmanabad", "name_mr": "धाराशिव", "lat": 18.1856, "lon": 76.0419},
            {"lgd": 4152, "name": "Tuljapur", "name_mr": "तुळजापूर", "lat": 18.0108, "lon": 76.0772},
            {"lgd": 4153, "name": "Omerga", "name_mr": "उमरगा", "lat": 17.8428, "lon": 76.6186},
            {"lgd": 4154, "name": "Lohara", "name_mr": "लोहारा", "lat": 17.9667, "lon": 76.3833},
            {"lgd": 4155, "name": "Kalamb", "name_mr": "कळंब", "lat": 18.4989, "lon": 76.0453},
            {"lgd": 4156, "name": "Bhum", "name_mr": "भूम", "lat": 18.4725, "lon": 75.6664},
            {"lgd": 4157, "name": "Paranda", "name_mr": "परांडा", "lat": 18.2567, "lon": 75.4497},
            {"lgd": 4158, "name": "Washi", "name_mr": "वाशी", "lat": 18.5833, "lon": 75.8333}
        ]
    },
    {
        "district_lgd": 487, "district": "Latur", "district_mr": "लातूर",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 18.4088, "lon": 76.5604,
        "normal_rain_mm": 790.0, "soil": "Black Heavy to Medium Vertisol",
        "crops": "Soybean, Tur, Urad, Moong, Sugarcane", "crops_mr": "सोयाबीन, तूर, उडीद, मूग, ऊस",
        "talukas": [
            {"lgd": 4160, "name": "Latur", "name_mr": "लातूर", "lat": 18.4088, "lon": 76.5604},
            {"lgd": 4161, "name": "Ausa", "name_mr": "औसा", "lat": 18.2500, "lon": 76.5000},
            {"lgd": 4162, "name": "Renapur", "name_mr": "रेणापूर", "lat": 18.5500, "lon": 76.6000},
            {"lgd": 4163, "name": "Nilanga", "name_mr": "निलंगा", "lat": 18.1333, "lon": 76.7667},
            {"lgd": 4164, "name": "Udgir", "name_mr": "उदगीर", "lat": 18.3942, "lon": 77.1164},
            {"lgd": 4165, "name": "Ahmadpur", "name_mr": "अहमदपूर", "lat": 18.7058, "lon": 76.9325}
        ]
    },
    {
        "district_lgd": 488, "district": "Nanded", "district_mr": "नांदेड",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 19.1383, "lon": 77.3210,
        "normal_rain_mm": 915.0, "soil": "Medium Black and Alluvial Soil",
        "crops": "Cotton, Soybean, Banana, Tur, Sugarcane", "crops_mr": "कापूस, सोयाबीन, केळी, तूर, ऊस",
        "talukas": [
            {"lgd": 4170, "name": "Nanded", "name_mr": "नांदेड", "lat": 19.1383, "lon": 77.3210},
            {"lgd": 4171, "name": "Biloli", "name_mr": "बिलोली", "lat": 18.7667, "lon": 77.7333},
            {"lgd": 4172, "name": "Mukhed", "name_mr": "मुखेड", "lat": 18.7167, "lon": 77.3667},
            {"lgd": 4173, "name": "Kandhar", "name_mr": "कंधार", "lat": 18.9000, "lon": 77.2000},
            {"lgd": 4174, "name": "Hadgaon", "name_mr": "हदगाव", "lat": 19.5000, "lon": 77.6667},
            {"lgd": 4175, "name": "Kinwat", "name_mr": "किनवट", "lat": 19.6333, "lon": 78.2000}
        ]
    },
    {
        "district_lgd": 489, "district": "Parbhani", "district_mr": "परभणी",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 19.2608, "lon": 76.7748,
        "normal_rain_mm": 830.0, "soil": "Deep Black Vertisol",
        "crops": "Cotton, Soybean, Tur, Jowar", "crops_mr": "कापूस, सोयाबीन, तूर, ज्वारी",
        "talukas": [
            {"lgd": 4180, "name": "Parbhani", "name_mr": "परभणी", "lat": 19.2608, "lon": 76.7748},
            {"lgd": 4181, "name": "Gangakhed", "name_mr": "गंगाखेड", "lat": 18.9500, "lon": 76.7500},
            {"lgd": 4182, "name": "Jintur", "name_mr": "जिंतूर", "lat": 19.6167, "lon": 76.6833},
            {"lgd": 4183, "name": "Pathri", "name_mr": "पाथरी", "lat": 19.2500, "lon": 76.4167}
        ]
    },
    {
        "district_lgd": 490, "district": "Hingoli", "district_mr": "हिंगोली",
        "division": "Chhatrapati Sambhajinagar", "division_mr": "छत्रपती संभाजीनगर",
        "zone": "Central Maharashtra Plateau", "zone_mr": "मध्य महाराष्ट्र पठार",
        "univ": "VNMKV Parbhani", "lat": 19.7173, "lon": 77.1478,
        "normal_rain_mm": 890.0, "soil": "Medium Black Soil",
        "crops": "Soybean, Turmeric (हळद), Cotton, Gram", "crops_mr": "सोयाबीन, हळद, कापूस, हरभरा",
        "talukas": [
            {"lgd": 4190, "name": "Hingoli", "name_mr": "हिंगोली", "lat": 19.7173, "lon": 77.1478},
            {"lgd": 4191, "name": "Basmath", "name_mr": "वसमत", "lat": 19.3333, "lon": 77.1667},
            {"lgd": 4192, "name": "Kalamnuri", "name_mr": "कलमनुरी", "lat": 19.6667, "lon": 77.3333}
        ]
    },

    # --- Western Maharashtra & Scarcity Zone (Pune Division) ---
    {
        "district_lgd": 498, "district": "Pune", "district_mr": "पुणे",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Sub-montane & Scarcity Zone", "zone_mr": "उप-पर्वतीय व अवर्षण प्रवण",
        "univ": "MPKV Rahuri", "lat": 18.5204, "lon": 73.8567,
        "normal_rain_mm": 722.0, "soil": "Medium Black to Red Loam",
        "crops": "Sugarcane, Soybean, Bajra, Onion, Grapes", "crops_mr": "ऊस, सोयाबीन, बाजरी, कांदा, द्राक्षे",
        "talukas": [
            {"lgd": 4200, "name": "Haveli", "name_mr": "हवेली", "lat": 18.5204, "lon": 73.8567},
            {"lgd": 4201, "name": "Baramati", "name_mr": "बारामती", "lat": 18.1517, "lon": 74.5772},
            {"lgd": 4202, "name": "Shirur", "name_mr": "शिरूर", "lat": 18.8250, "lon": 74.3789},
            {"lgd": 4203, "name": "Daund", "name_mr": "दौंड", "lat": 18.4636, "lon": 74.5808},
            {"lgd": 4204, "name": "Indapur", "name_mr": "इंदापूर", "lat": 18.1167, "lon": 75.0333},
            {"lgd": 4205, "name": "Junnar", "name_mr": "जुन्नर", "lat": 19.2081, "lon": 73.8756},
            {"lgd": 4206, "name": "Khed", "name_mr": "खेड", "lat": 18.8500, "lon": 73.9167}
        ]
    },
    {
        "district_lgd": 513, "district": "Solapur", "district_mr": "सोलापूर",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Scarcity Zone", "zone_mr": "दुष्काळी अवर्षण प्रवण विभाग",
        "univ": "MPKV Rahuri", "lat": 17.6599, "lon": 75.9064,
        "normal_rain_mm": 561.4, "soil": "Shallow to Medium Vertisol",
        "crops": "Rabi Jowar, Pomegranate (डाळिंब), Sugarcane, Bajra", "crops_mr": "रब्बी ज्वारी, डाळिंब, ऊस, बाजरी",
        "talukas": [
            {"lgd": 4210, "name": "North Solapur", "name_mr": "उत्तर सोलापूर", "lat": 17.6599, "lon": 75.9064},
            {"lgd": 4211, "name": "South Solapur", "name_mr": "दक्षिण सोलापूर", "lat": 17.5500, "lon": 75.9500},
            {"lgd": 4212, "name": "Barshi", "name_mr": "बार्शी", "lat": 18.2333, "lon": 75.6833},
            {"lgd": 4213, "name": "Pandharpur", "name_mr": "पंढरपूर", "lat": 17.6778, "lon": 75.3283},
            {"lgd": 4214, "name": "Malshiras", "name_mr": "माळशिरस", "lat": 17.8500, "lon": 74.9667},
            {"lgd": 4215, "name": "Karmala", "name_mr": "करमाळा", "lat": 18.4167, "lon": 75.2000},
            {"lgd": 4216, "name": "Madha", "name_mr": "माढा", "lat": 18.0333, "lon": 75.5167},
            {"lgd": 4217, "name": "Sangola", "name_mr": "सांगोला", "lat": 17.4333, "lon": 75.2000},
            {"lgd": 4218, "name": "Mangalwedha", "name_mr": "मंगळवेढा", "lat": 17.5167, "lon": 75.4500}
        ]
    },
    {
        "district_lgd": 502, "district": "Ahmednagar", "district_mr": "अहिल्यानगर (अहमदनगर)",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Scarcity Zone & Central Plateau", "zone_mr": "अवर्षण प्रवण व मध्य पठार",
        "univ": "MPKV Rahuri", "lat": 19.0952, "lon": 74.7480,
        "normal_rain_mm": 501.8, "soil": "Medium Black to Calcareous Soil",
        "crops": "Sugarcane, Bajra, Onion, Soybean, Pomegranate", "crops_mr": "ऊस, बाजरी, कांदा, सोयाबीन, डाळिंब",
        "talukas": [
            {"lgd": 4220, "name": "Nagar", "name_mr": "नगर", "lat": 19.0952, "lon": 74.7480},
            {"lgd": 4221, "name": "Rahuri", "name_mr": "राहुरी", "lat": 19.3900, "lon": 74.6500},
            {"lgd": 4222, "name": "Sangamner", "name_mr": "संगमनेर", "lat": 19.5700, "lon": 74.2100},
            {"lgd": 4223, "name": "Kopargaon", "name_mr": "कोपरगाव", "lat": 19.8900, "lon": 74.4800},
            {"lgd": 4224, "name": "Shrirampur", "name_mr": "श्रीरामपूर", "lat": 19.6200, "lon": 74.6600},
            {"lgd": 4225, "name": "Shevgaon", "name_mr": "शेवगाव", "lat": 19.3400, "lon": 75.2200},
            {"lgd": 4226, "name": "Pathardi", "name_mr": "पाथर्डी", "lat": 19.1700, "lon": 75.1800},
            {"lgd": 4227, "name": "Parner", "name_mr": "पारनेर", "lat": 19.0000, "lon": 74.4400},
            {"lgd": 4228, "name": "Shrigonda", "name_mr": "श्रीगोंदा", "lat": 18.6200, "lon": 74.6900},
            {"lgd": 4229, "name": "Karjat", "name_mr": "कर्जत", "lat": 18.9100, "lon": 75.0100},
            {"lgd": 4230, "name": "Jamkhed", "name_mr": "जामखेड", "lat": 18.7300, "lon": 75.3200}
        ]
    },
    {
        "district_lgd": 507, "district": "Satara", "district_mr": "सातारा",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Ghat & Scarcity Transitional", "zone_mr": "घाट व अवर्षण प्रवण संक्रमण",
        "univ": "MPKV Rahuri", "lat": 17.6805, "lon": 73.9933,
        "normal_rain_mm": 918.0, "soil": "Laterite to Medium Black",
        "crops": "Sugarcane, Soybean, Jowar, Turmeric, Ginger", "crops_mr": "ऊस, सोयाबीन, ज्वारी, हळद, आले",
        "talukas": [
            {"lgd": 4240, "name": "Satara", "name_mr": "सातारा", "lat": 17.6805, "lon": 73.9933},
            {"lgd": 4241, "name": "Karad", "name_mr": "कराड", "lat": 17.2858, "lon": 74.1836},
            {"lgd": 4242, "name": "Phaltan", "name_mr": "फलटण", "lat": 17.9833, "lon": 74.4333},
            {"lgd": 4243, "name": "Man", "name_mr": "माण (दहीवडी)", "lat": 17.7000, "lon": 74.7500},
            {"lgd": 4244, "name": "Khatav", "name_mr": "खटाव (वडूज)", "lat": 17.5833, "lon": 74.4500}
        ]
    },
    {
        "district_lgd": 508, "district": "Sangli", "district_mr": "सांगली",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Krishna Basin & Scarcity Zone", "zone_mr": "कृष्णा खोरे व दुष्काळी विभाग",
        "univ": "MPKV Rahuri", "lat": 16.8524, "lon": 74.5815,
        "normal_rain_mm": 612.0, "soil": "Rich Alluvial to Shallow Red",
        "crops": "Sugarcane, Grapes (द्राक्षे), Turmeric, Soybean", "crops_mr": "ऊस, द्राक्षे, हळद, सोयाबीन",
        "talukas": [
            {"lgd": 4250, "name": "Miraj", "name_mr": "मिरज", "lat": 16.8524, "lon": 74.5815},
            {"lgd": 4251, "name": "Jath", "name_mr": "जत", "lat": 17.0500, "lon": 75.2167},
            {"lgd": 4252, "name": "Tasgaon", "name_mr": "तासगाव", "lat": 17.0333, "lon": 74.6000},
            {"lgd": 4253, "name": "Khanapur", "name_mr": "खानापूर (विटा)", "lat": 17.2667, "lon": 74.5333},
            {"lgd": 4254, "name": "Atpadi", "name_mr": "आटपाडी", "lat": 17.4167, "lon": 74.9167}
        ]
    },
    {
        "district_lgd": 509, "district": "Kolhapur", "district_mr": "कोल्हापूर",
        "division": "Pune", "division_mr": "पुणे",
        "zone": "Sub-montane High Rainfall", "zone_mr": "उप-पर्वतीय अधिक पर्जन्य विभाग",
        "univ": "MPKV Rahuri", "lat": 16.7050, "lon": 74.2433,
        "normal_rain_mm": 1750.0, "soil": "Deep Heavy Alluvial & Lateritic",
        "crops": "Sugarcane, Paddy, Soybean, Groundnut", "crops_mr": "ऊस, भात, सोयाबीन, भुईमूग",
        "talukas": [
            {"lgd": 4260, "name": "Karvir", "name_mr": "करवीर", "lat": 16.7050, "lon": 74.2433},
            {"lgd": 4261, "name": "Hatkanangle", "name_mr": "हातकणंगले", "lat": 16.7500, "lon": 74.4500},
            {"lgd": 4262, "name": "Shirol", "name_mr": "शिरोळ", "lat": 16.7833, "lon": 74.6000},
            {"lgd": 4263, "name": "Kagal", "name_mr": "कागल", "lat": 16.5833, "lon": 74.3167}
        ]
    },

    # --- Khandesh & North Maharashtra (Nashik Division) ---
    {
        "district_lgd": 497, "district": "Nashik", "district_mr": "नाशिक",
        "division": "Nashik", "division_mr": "नाशिक",
        "zone": "Sub-montane & Scarcity", "zone_mr": "उप-पर्वतीय व दुष्काळी विभाग",
        "univ": "MPKV Rahuri", "lat": 19.9975, "lon": 73.7898,
        "normal_rain_mm": 880.0, "soil": "Medium Black to Red Loam",
        "crops": "Grapes, Onion (कांदा), Tomato, Bajra, Soybean", "crops_mr": "द्राक्षे, कांदा, टोमॅटो, बाजरी, सोयाबीन",
        "talukas": [
            {"lgd": 4270, "name": "Nashik", "name_mr": "नाशिक", "lat": 19.9975, "lon": 73.7898},
            {"lgd": 4271, "name": "Niphad", "name_mr": "निफाड", "lat": 20.0833, "lon": 74.1167},
            {"lgd": 4272, "name": "Sinnar", "name_mr": "सिन्नर", "lat": 19.8500, "lon": 74.0000},
            {"lgd": 4273, "name": "Yeola", "name_mr": "येवला", "lat": 20.0333, "lon": 74.4833},
            {"lgd": 4274, "name": "Malegaon", "name_mr": "मालेगाव", "lat": 20.5500, "lon": 74.5333},
            {"lgd": 4275, "name": "Chandwad", "name_mr": "चांदवड", "lat": 20.3333, "lon": 74.2500},
            {"lgd": 4276, "name": "Dindori", "name_mr": "दिंडोरी", "lat": 20.2000, "lon": 73.8333}
        ]
    },
    {
        "district_lgd": 499, "district": "Dhule", "district_mr": "धुळे",
        "division": "Nashik", "division_mr": "नाशिक",
        "zone": "Scarcity / Tapi Valley", "zone_mr": "तापी खोरे दुष्काळी विभाग",
        "univ": "MPKV Rahuri", "lat": 20.9042, "lon": 74.7749,
        "normal_rain_mm": 590.0, "soil": "Medium to Deep Tapi Alluvial",
        "crops": "Cotton, Bajra, Maize, Jowar, Groundnut", "crops_mr": "कापूस, बाजरी, मका, ज्वारी, भुईमूग",
        "talukas": [
            {"lgd": 4280, "name": "Dhule", "name_mr": "धुळे", "lat": 20.9042, "lon": 74.7749},
            {"lgd": 4281, "name": "Sakri", "name_mr": "साक्री", "lat": 20.9333, "lon": 74.3167},
            {"lgd": 4282, "name": "Shirpur", "name_mr": "शिरपूर", "lat": 21.3500, "lon": 74.8833},
            {"lgd": 4283, "name": "Sindkheda", "name_mr": "शिंदखेडा", "lat": 21.2667, "lon": 74.7500}
        ]
    },
    {
        "district_lgd": 501, "district": "Jalgaon", "district_mr": "जळगाव",
        "division": "Nashik", "division_mr": "नाशिक",
        "zone": "Central Plateau & Tapi Valley", "zone_mr": "तापी खोरे व मध्य पठार",
        "univ": "MPKV Rahuri", "lat": 21.0077, "lon": 75.5626,
        "normal_rain_mm": 740.0, "soil": "Deep Black Tapi Alluvial",
        "crops": "Banana (केळी), Cotton (कापूस), Maize, Pulses", "crops_mr": "केळी, कापूस, मका, कडधान्ये",
        "talukas": [
            {"lgd": 4290, "name": "Jalgaon", "name_mr": "जळगाव", "lat": 21.0077, "lon": 75.5626},
            {"lgd": 4291, "name": "Bhusawal", "name_mr": "भुसावळ", "lat": 21.0500, "lon": 75.7833},
            {"lgd": 4292, "name": "Raver", "name_mr": "रावेर", "lat": 21.2500, "lon": 75.9667},
            {"lgd": 4293, "name": "Chalisgaon", "name_mr": "चाळीसगाव", "lat": 20.4667, "lon": 75.0167},
            {"lgd": 4294, "name": "Pachora", "name_mr": "पाचोरा", "lat": 20.6667, "lon": 75.3500},
            {"lgd": 4295, "name": "Jamner", "name_mr": "जामनेर", "lat": 20.8167, "lon": 75.7833}
        ]
    },
    {
        "district_lgd": 500, "district": "Nandurbar", "district_mr": "नंदुरबार",
        "division": "Nashik", "division_mr": "नाशिक",
        "zone": "Satpuda Hill Tribal Zone", "zone_mr": "सातपुडा डोंगरी विभाग",
        "univ": "MPKV Rahuri", "lat": 21.3688, "lon": 74.2405,
        "normal_rain_mm": 860.0, "soil": "Shallow Red to Medium Vertisol",
        "crops": "Cotton, Chilli, Maize, Jowar", "crops_mr": "कापूस, मिरची, मका, ज्वारी",
        "talukas": [
            {"lgd": 4300, "name": "Nandurbar", "name_mr": "नंदुरबार", "lat": 21.3688, "lon": 74.2405},
            {"lgd": 4301, "name": "Shahada", "name_mr": "शहादा", "lat": 21.5500, "lon": 74.4667},
            {"lgd": 4302, "name": "Navapur", "name_mr": "नवापूर", "lat": 21.1667, "lon": 73.8000}
        ]
    },

    # --- Vidarbha (Amravati & Nagpur Divisions) - Cotton-Soybean Distress Zone ---
    {
        "district_lgd": 471, "district": "Akola", "district_mr": "अकोला",
        "division": "Amravati", "division_mr": "अमरावती",
        "zone": "Central Vidarbha Zone", "zone_mr": "मध्य विदर्भ विभाग",
        "univ": "PDKV Akola", "lat": 20.7002, "lon": 77.0082,
        "normal_rain_mm": 795.0, "soil": "Deep Black Vertisol (Purna Basin)",
        "crops": "Cotton, Soybean, Tur, Gram", "crops_mr": "कापूस, सोयाबीन, तूर, हरभरा",
        "talukas": [
            {"lgd": 4310, "name": "Akola", "name_mr": "अकोला", "lat": 20.7002, "lon": 77.0082},
            {"lgd": 4311, "name": "Akot", "name_mr": "आकोट", "lat": 21.1000, "lon": 77.0667},
            {"lgd": 4312, "name": "Balapur", "name_mr": "बाळापूर", "lat": 20.6667, "lon": 76.7833},
            {"lgd": 4313, "name": "Murtizapur", "name_mr": "मूर्तिजापूर", "lat": 20.7333, "lon": 77.3667},
            {"lgd": 4314, "name": "Patur", "name_mr": "पातूर", "lat": 20.4500, "lon": 76.9333}
        ]
    },
    {
        "district_lgd": 470, "district": "Amravati", "district_mr": "अमरावती",
        "division": "Amravati", "division_mr": "अमरावती",
        "zone": "Central Vidarbha & Satpuda", "zone_mr": "मध्य विदर्भ व सातपुडा",
        "univ": "PDKV Akola", "lat": 20.9374, "lon": 77.7796,
        "normal_rain_mm": 870.0, "soil": "Deep Vertisol & Loam",
        "crops": "Soybean, Cotton, Orange (संत्रा), Tur", "crops_mr": "सोयाबीन, कापूस, संत्रा, तूर",
        "talukas": [
            {"lgd": 4320, "name": "Amravati", "name_mr": "अमरावती", "lat": 20.9374, "lon": 77.7796},
            {"lgd": 4321, "name": "Achalpur", "name_mr": "अचलपूर", "lat": 21.2667, "lon": 77.5167},
            {"lgd": 4322, "name": "Morshi", "name_mr": "मोर्शी", "lat": 21.3167, "lon": 78.0167},
            {"lgd": 4323, "name": "Warud", "name_mr": "वरुड", "lat": 21.4667, "lon": 78.2667},
            {"lgd": 4324, "name": "Daryapur", "name_mr": "दर्यापूर", "lat": 20.9167, "lon": 77.3167},
            {"lgd": 4325, "name": "Chandur Bazar", "name_mr": "चांदूर बाजार", "lat": 21.2333, "lon": 77.7500}
        ]
    },
    {
        "district_lgd": 473, "district": "Buldhana", "district_mr": "बुलढाणा",
        "division": "Amravati", "division_mr": "अमरावती",
        "zone": "Central Vidarbha & Ghat", "zone_mr": "मध्य विदर्भ व घाट",
        "univ": "PDKV Akola", "lat": 20.5292, "lon": 76.1843,
        "normal_rain_mm": 745.0, "soil": "Medium Black to Calcareous",
        "crops": "Soybean, Cotton, Maize, Jowar", "crops_mr": "सोयाबीन, कापूस, मका, ज्वारी",
        "talukas": [
            {"lgd": 4330, "name": "Buldhana", "name_mr": "बुलढाणा", "lat": 20.5292, "lon": 76.1843},
            {"lgd": 4331, "name": "Khamgaon", "name_mr": "खामगाव", "lat": 20.6833, "lon": 76.5667},
            {"lgd": 4332, "name": "Shegaon", "name_mr": "शेगाव", "lat": 20.7833, "lon": 76.6833},
            {"lgd": 4333, "name": "Chikhli", "name_mr": "चिखली", "lat": 20.3500, "lon": 76.2500},
            {"lgd": 4334, "name": "Mehkar", "name_mr": "मेहकर", "lat": 20.1500, "lon": 76.5667},
            {"lgd": 4335, "name": "Malkapur", "name_mr": "मलकापूर", "lat": 20.8833, "lon": 76.2000}
        ]
    },
    {
        "district_lgd": 476, "district": "Yavatmal", "district_mr": "यवतमाळ",
        "division": "Amravati", "division_mr": "अमरावती",
        "zone": "Eastern Vidarbha Plateau", "zone_mr": "पूर्व विदर्भ पठार",
        "univ": "PDKV Akola", "lat": 20.3888, "lon": 78.1204,
        "normal_rain_mm": 911.0, "soil": "Medium Black & Red Loam",
        "crops": "Cotton (पांढरे सोने), Soybean, Tur, Gram", "crops_mr": "कापूस, सोयाबीन, तूर, हरभरा",
        "talukas": [
            {"lgd": 4340, "name": "Yavatmal", "name_mr": "यवतमाळ", "lat": 20.3888, "lon": 78.1204},
            {"lgd": 4341, "name": "Pusad", "name_mr": "पुसद", "lat": 19.9167, "lon": 77.5833},
            {"lgd": 4342, "name": "Umarkhed", "name_mr": "उमरखेड", "lat": 19.6000, "lon": 77.7000},
            {"lgd": 4343, "name": "Digras", "name_mr": "दिग्रस", "lat": 20.1000, "lon": 77.7167},
            {"lgd": 4344, "name": "Wani", "name_mr": "वणी", "lat": 20.0667, "lon": 78.9500},
            {"lgd": 4345, "name": "Darwha", "name_mr": "दारव्हा", "lat": 20.3167, "lon": 77.7667}
        ]
    },
    {
        "district_lgd": 472, "district": "Washim", "district_mr": "वाशीम",
        "division": "Amravati", "division_mr": "अमरावती",
        "zone": "Central Vidarbha Zone", "zone_mr": "मध्य विदर्भ विभाग",
        "univ": "PDKV Akola", "lat": 20.1118, "lon": 77.1332,
        "normal_rain_mm": 830.0, "soil": "Medium Black Soil",
        "crops": "Soybean, Cotton, Tur, Wheat", "crops_mr": "सोयाबीन, कापूस, तूर, गहू",
        "talukas": [
            {"lgd": 4350, "name": "Washim", "name_mr": "वाशीम", "lat": 20.1118, "lon": 77.1332},
            {"lgd": 4351, "name": "Risod", "name_mr": "रिसोड", "lat": 19.9667, "lon": 76.7833},
            {"lgd": 4352, "name": "Malegaon Jahangir", "name_mr": "मालेगाव जहाँगीर", "lat": 20.3333, "lon": 77.0333},
            {"lgd": 4353, "name": "Mangrulpir", "name_mr": "मंगरुळपीर", "lat": 20.3167, "lon": 77.3500},
            {"lgd": 4354, "name": "Karanja Lad", "name_mr": "कारंजा लाड", "lat": 20.4833, "lon": 77.4833}
        ]
    },
    {
        "district_lgd": 475, "district": "Wardha", "district_mr": "वर्धा",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Central Vidarbha Zone", "zone_mr": "मध्य विदर्भ विभाग",
        "univ": "PDKV Akola", "lat": 20.7453, "lon": 78.6022,
        "normal_rain_mm": 965.0, "soil": "Deep Black Vertisol",
        "crops": "Cotton, Soybean, Tur, Wheat", "crops_mr": "कापूस, सोयाबीन, तूर, गहू",
        "talukas": [
            {"lgd": 4360, "name": "Wardha", "name_mr": "वर्धा", "lat": 20.7453, "lon": 78.6022},
            {"lgd": 4361, "name": "Hinganghat", "name_mr": "हिंगणघाट", "lat": 20.5500, "lon": 78.8333},
            {"lgd": 4362, "name": "Arvi", "name_mr": "आर्वी", "lat": 20.9833, "lon": 78.2333},
            {"lgd": 4363, "name": "Deoli", "name_mr": "देवळी", "lat": 20.6500, "lon": 78.4833}
        ]
    },
    {
        "district_lgd": 474, "district": "Nagpur", "district_mr": "नागपूर",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Eastern Vidarbha High Rainfall", "zone_mr": "पूर्व विदर्भ अधिक पर्जन्य",
        "univ": "PDKV Akola", "lat": 21.1458, "lon": 79.0882,
        "normal_rain_mm": 1050.0, "soil": "Black Heavy to Red Loam",
        "crops": "Nagpur Orange (संत्रा), Soybean, Cotton, Paddy", "crops_mr": "नागपूर संत्रा, सोयाबीन, कापूस, भात",
        "talukas": [
            {"lgd": 4370, "name": "Nagpur Rural", "name_mr": "नागपूर ग्रामीण", "lat": 21.1458, "lon": 79.0882},
            {"lgd": 4371, "name": "Katol", "name_mr": "काटोल", "lat": 21.2833, "lon": 78.5833},
            {"lgd": 4372, "name": "Saoner", "name_mr": "सावनेर", "lat": 21.4667, "lon": 78.9167},
            {"lgd": 4373, "name": "Umred", "name_mr": "उमरेड", "lat": 20.8500, "lon": 79.3333},
            {"lgd": 4374, "name": "Ramtek", "name_mr": "रामटेक", "lat": 21.4000, "lon": 79.3333}
        ]
    },
    {
        "district_lgd": 469, "district": "Bhandara", "district_mr": "भंडारा",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Eastern Vidarbha Paddy & Lake Zone", "zone_mr": "पूर्व विदर्भ भात व तलाव विभाग",
        "univ": "PDKV Akola", "lat": 21.1667, "lon": 79.6500,
        "normal_rain_mm": 1280.0, "soil": "Sandy Loam & Red Alluvial",
        "crops": "Paddy (भात), Tur, Sugarcane", "crops_mr": "भात, तूर, ऊस",
        "talukas": [
            {"lgd": 4380, "name": "Bhandara", "name_mr": "भंडारा", "lat": 21.1667, "lon": 79.6500},
            {"lgd": 4381, "name": "Tumsar", "name_mr": "तुमसर", "lat": 21.3833, "lon": 79.7333},
            {"lgd": 4382, "name": "Sakoli", "name_mr": "साकोली", "lat": 21.0833, "lon": 79.9833}
        ]
    },
    {
        "district_lgd": 468, "district": "Gondia", "district_mr": "गोंदिया",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Eastern Vidarbha High Rainfall Forest", "zone_mr": "पूर्व विदर्भ वन व भात विभाग",
        "univ": "PDKV Akola", "lat": 21.4597, "lon": 80.1961,
        "normal_rain_mm": 1330.0, "soil": "Lateritic & Red Sandy Loam",
        "crops": "Paddy (भात), Lathyrus, Tur", "crops_mr": "भात, लाखाडी, तूर",
        "talukas": [
            {"lgd": 4390, "name": "Gondia", "name_mr": "गोंदिया", "lat": 21.4597, "lon": 80.1961},
            {"lgd": 4391, "name": "Tirora", "name_mr": "तिरोडा", "lat": 21.4167, "lon": 79.9333},
            {"lgd": 4392, "name": "Amgaon", "name_mr": "आमगाव", "lat": 21.3667, "lon": 80.3833}
        ]
    },
    {
        "district_lgd": 477, "district": "Chandrapur", "district_mr": "चंद्रपूर",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Eastern Vidarbha Forest & Mineral Zone", "zone_mr": "पूर्व विदर्भ पठार व भात",
        "univ": "PDKV Akola", "lat": 19.9615, "lon": 79.2961,
        "normal_rain_mm": 1180.0, "soil": "Sandy Loam to Heavy Black",
        "crops": "Soybean, Cotton, Paddy, Tur", "crops_mr": "सोयाबीन, कापूस, भात, तूर",
        "talukas": [
            {"lgd": 4400, "name": "Chandrapur", "name_mr": "चंद्रपूर", "lat": 19.9615, "lon": 79.2961},
            {"lgd": 4401, "name": "Warora", "name_mr": "वरोरा", "lat": 20.2333, "lon": 79.0000},
            {"lgd": 4402, "name": "Bhadravati", "name_mr": "भद्रावती", "lat": 20.1000, "lon": 79.1167},
            {"lgd": 4403, "name": "Rajura", "name_mr": "राजूरा", "lat": 19.7833, "lon": 79.3667}
        ]
    },
    {
        "district_lgd": 478, "district": "Gadchiroli", "district_mr": "गडचिरोली",
        "division": "Nagpur", "division_mr": "नागपूर",
        "zone": "Eastern Heavy Rainfall Forest Zone", "zone_mr": "पूर्व अधिक पर्जन्य वन विभाग",
        "univ": "PDKV Akola", "lat": 20.1809, "lon": 79.9930,
        "normal_rain_mm": 1420.0, "soil": "Red Sandy & Forest Loam",
        "crops": "Paddy, Minor Millets (नाचणी), Tur", "crops_mr": "भात, नाचणी, तूर",
        "talukas": [
            {"lgd": 4410, "name": "Gadchiroli", "name_mr": "गडचिरोली", "lat": 20.1809, "lon": 79.9930},
            {"lgd": 4411, "name": "Armori", "name_mr": "आरमोरी", "lat": 20.4667, "lon": 79.9833},
            {"lgd": 4412, "name": "Chamorshi", "name_mr": "चामोर्शी", "lat": 19.9333, "lon": 79.9000},
            {"lgd": 4413, "name": "Aheri", "name_mr": "अहेरी", "lat": 19.4167, "lon": 80.0000}
        ]
    },

    # --- Konkan Coastal Zone (Konkan Division) ---
    {
        "district_lgd": 491, "district": "Thane", "district_mr": "ठाणे",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "North Konkan Coastal", "zone_mr": "उत्तर कोकण किनारपट्टी",
        "univ": "BSKKV Dapoli", "lat": 19.2183, "lon": 72.9781,
        "normal_rain_mm": 2450.0, "soil": "Coastal Alluvial & Red Loam",
        "crops": "Paddy, Vegetables, Flowers", "crops_mr": "भात, भाजीपाला, फुले",
        "talukas": [
            {"lgd": 4420, "name": "Thane", "name_mr": "ठाणे", "lat": 19.2183, "lon": 72.9781},
            {"lgd": 4421, "name": "Kalyan", "name_mr": "कल्याण", "lat": 19.2437, "lon": 73.1355},
            {"lgd": 4422, "name": "Murbad", "name_mr": "मुरबाड", "lat": 19.2500, "lon": 73.4000},
            {"lgd": 4423, "name": "Shahapur", "name_mr": "शहापूर", "lat": 19.4500, "lon": 73.3333}
        ]
    },
    {
        "district_lgd": 492, "district": "Palghar", "district_mr": "पालघर",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "North Konkan Coastal & Tribal", "zone_mr": "उत्तर कोकण व आदिवासी विभाग",
        "univ": "BSKKV Dapoli", "lat": 19.6967, "lon": 72.7699,
        "normal_rain_mm": 2350.0, "soil": "Coastal Sandy & Laterite",
        "crops": "Paddy, Chikoo (चीकू), Finger Millet (नाचणी)", "crops_mr": "भात, चीकू, नाचणी",
        "talukas": [
            {"lgd": 4430, "name": "Palghar", "name_mr": "पालघर", "lat": 19.6967, "lon": 72.7699},
            {"lgd": 4431, "name": "Dahanu", "name_mr": "डहाणू", "lat": 19.9667, "lon": 72.7333},
            {"lgd": 4432, "name": "Jawhar", "name_mr": "जव्हार", "lat": 19.9167, "lon": 73.2333},
            {"lgd": 4433, "name": "Wada", "name_mr": "वाडा", "lat": 19.6500, "lon": 73.1333}
        ]
    },
    {
        "district_lgd": 493, "district": "Raigad", "district_mr": "रायगड",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "Central Konkan Coastal", "zone_mr": "मध्य कोकण किनारपट्टी",
        "univ": "BSKKV Dapoli", "lat": 18.5158, "lon": 73.1822,
        "normal_rain_mm": 3100.0, "soil": "Lateritic & Alluvial",
        "crops": "Paddy, Betelnut (सुपारी), Coconut, Mango", "crops_mr": "भात, सुपारी, नारळ, आंबा",
        "talukas": [
            {"lgd": 4440, "name": "Alibag", "name_mr": "अलिबाग", "lat": 18.6414, "lon": 72.8722},
            {"lgd": 4441, "name": "Pen", "name_mr": "पेण", "lat": 18.7333, "lon": 73.1000},
            {"lgd": 4442, "name": "Panvel", "name_mr": "पनवेल", "lat": 18.9894, "lon": 73.1175},
            {"lgd": 4443, "name": "Mahad", "name_mr": "महाड", "lat": 18.0833, "lon": 73.4167},
            {"lgd": 4444, "name": "Roha", "name_mr": "रोहा", "lat": 18.4333, "lon": 73.1167}
        ]
    },
    {
        "district_lgd": 494, "district": "Ratnagiri", "district_mr": "रत्नागिरी",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "South Konkan Coastal", "zone_mr": "दक्षिण कोकण किनारपट्टी",
        "univ": "BSKKV Dapoli", "lat": 16.9902, "lon": 73.3120,
        "normal_rain_mm": 3200.0, "soil": "Lateritic Red Soil",
        "crops": "Alphonso Mango (हापूस आंबा), Cashew (काजू), Paddy", "crops_mr": "हापूस आंबा, काजू, भात",
        "talukas": [
            {"lgd": 4450, "name": "Ratnagiri", "name_mr": "रत्नागिरी", "lat": 16.9902, "lon": 73.3120},
            {"lgd": 4451, "name": "Dapoli", "name_mr": "दापोली", "lat": 17.7667, "lon": 73.1833},
            {"lgd": 4452, "name": "Chiplun", "name_mr": "चिपळूण", "lat": 17.5333, "lon": 73.5167},
            {"lgd": 4453, "name": "Sangameshwar", "name_mr": "संगमेश्वर", "lat": 17.1833, "lon": 73.5500},
            {"lgd": 4454, "name": "Rajapur", "name_mr": "राजापूर", "lat": 16.6667, "lon": 73.5167}
        ]
    },
    {
        "district_lgd": 495, "district": "Sindhudurg", "district_mr": "सिंधुदुर्ग",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "South Konkan High Rainfall", "zone_mr": "दक्षिण कोकण अधिक पर्जन्य",
        "univ": "BSKKV Dapoli", "lat": 16.1158, "lon": 73.6938,
        "normal_rain_mm": 3350.0, "soil": "Lateritic Heavy Red Soil",
        "crops": "Cashew, Mango, Coconut, Spices, Paddy", "crops_mr": "काजू, आंबा, नारळ, मसाल्याची पिके, भात",
        "talukas": [
            {"lgd": 4460, "name": "Kudal", "name_mr": "कुडाळ", "lat": 16.0000, "lon": 73.6833},
            {"lgd": 4461, "name": "Kankavli", "name_mr": "कणकवली", "lat": 16.2667, "lon": 73.7167},
            {"lgd": 4462, "name": "Sawantwadi", "name_mr": "सावंतवाडी", "lat": 15.9000, "lon": 73.8167},
            {"lgd": 4463, "name": "Malvan", "name_mr": "मालवण", "lat": 16.0667, "lon": 73.4667},
            {"lgd": 4464, "name": "Devgad", "name_mr": "देवगड", "lat": 16.3833, "lon": 73.3667}
        ]
    },
    {
        "district_lgd": 496, "district": "Mumbai City", "district_mr": "मुंबई शहर",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "Coastal Urban", "zone_mr": "किनारपट्टी नागरी",
        "univ": "BSKKV Dapoli", "lat": 18.9388, "lon": 72.8353,
        "normal_rain_mm": 2100.0, "soil": "Urban Alluvial",
        "crops": "Urban Horticulture", "crops_mr": "शहरी फलोत्पादन",
        "talukas": [
            {"lgd": 4470, "name": "Mumbai City", "name_mr": "मुंबई शहर", "lat": 18.9388, "lon": 72.8353}
        ]
    },
    {
        "district_lgd": 4901, "district": "Mumbai Suburban", "district_mr": "मुंबई उपनगर",
        "division": "Konkan", "division_mr": "कोकण",
        "zone": "Coastal Urban", "zone_mr": "किनारपट्टी नागरी",
        "univ": "BSKKV Dapoli", "lat": 19.0760, "lon": 72.8777,
        "normal_rain_mm": 2200.0, "soil": "Urban Alluvial",
        "crops": "Urban Horticulture", "crops_mr": "शहरी फलोत्पादन",
        "talukas": [
            {"lgd": 4480, "name": "Kurla", "name_mr": "कुर्ला", "lat": 19.0667, "lon": 72.8833},
            {"lgd": 4481, "name": "Andheri", "name_mr": "अंधेरी", "lat": 19.1167, "lon": 72.8500},
            {"lgd": 4482, "name": "Borivali", "name_mr": "बोरिवली", "lat": 19.2333, "lon": 72.8667}
        ]
    }
]

def make_box_polygon(lat, lon, delta=0.14):
    """Generates a small regular polygon bbox centered at lat/lon."""
    coords = [
        [round(lon - delta, 5), round(lat - delta, 5)],
        [round(lon + delta, 5), round(lat - delta, 5)],
        [round(lon + delta, 5), round(lat + delta, 5)],
        [round(lon - delta, 5), round(lat + delta, 5)],
        [round(lon - delta, 5), round(lat - delta, 5)]
    ]
    return coords

def seed_geography():
    print(f"[*] Seeding Maharashtra Administrative Geography into {GEO_DIR}...")
    
    rows = []
    district_features = []
    taluka_features = []
    
    total_talukas = 0

    for d in DISTRICTS_DATA:
        # District level feature
        d_poly = make_box_polygon(d["lat"], d["lon"], delta=0.35)
        district_features.append({
            "type": "Feature",
            "properties": {
                "district_lgd_code": d["district_lgd"],
                "district_name": d["district"],
                "district_name_mr": d["district_mr"],
                "division_name": d["division"],
                "division_name_mr": d["division_mr"],
                "agro_climatic_zone": d["zone"],
                "agro_climatic_zone_mr": d["zone_mr"],
                "university_affiliation": d["univ"],
                "normal_annual_rainfall_mm": d["normal_rain_mm"],
                "soil_type": d["soil"],
                "major_crops": d["crops"],
                "major_crops_mr": d["crops_mr"],
                "latitude": d["lat"],
                "longitude": d["lon"]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [d_poly]
            }
        })

        for t in d["talukas"]:
            total_talukas += 1
            row = {
                "state_lgd_code": 27,
                "state_name": "Maharashtra",
                "state_name_mr": "महाराष्ट्र",
                "division_name": d["division"],
                "division_name_mr": d["division_mr"],
                "district_lgd_code": d["district_lgd"],
                "district_name": d["district"],
                "district_name_mr": d["district_mr"],
                "taluka_lgd_code": t["lgd"],
                "taluka_name": t["name"],
                "taluka_name_mr": t["name_mr"],
                "latitude": t["lat"],
                "longitude": t["lon"],
                "agro_climatic_zone": d["zone"],
                "agro_climatic_zone_mr": d["zone_mr"],
                "university_affiliation": d["univ"],
                "soil_type": d["soil"],
                "normal_annual_rainfall_mm": d["normal_rain_mm"],
                "major_crops": d["crops"],
                "major_crops_mr": d["crops_mr"]
            }
            rows.append(row)

            # Taluka GeoJSON polygon
            t_poly = make_box_polygon(t["lat"], t["lon"], delta=0.12)
            taluka_features.append({
                "type": "Feature",
                "properties": {
                    "taluka_lgd_code": t["lgd"],
                    "taluka_name": t["name"],
                    "taluka_name_mr": t["name_mr"],
                    "district_lgd_code": d["district_lgd"],
                    "district_name": d["district"],
                    "district_name_mr": d["district_mr"],
                    "division_name": d["division"],
                    "division_name_mr": d["division_mr"],
                    "agro_climatic_zone": d["zone"],
                    "agro_climatic_zone_mr": d["zone_mr"],
                    "university_affiliation": d["univ"],
                    "normal_annual_rainfall_mm": d["normal_rain_mm"],
                    "soil_type": d["soil"],
                    "major_crops": d["crops"],
                    "major_crops_mr": d["crops_mr"],
                    "latitude": t["lat"],
                    "longitude": t["lon"]
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [t_poly]
                }
            })

    # Save CSV
    df = pd.DataFrame(rows)
    csv_path = os.path.join(GEO_DIR, "lgd_maharashtra_master.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Saved {len(df)} talukas across {len(DISTRICTS_DATA)} districts to: {csv_path}")

    # Save District GeoJSON
    districts_geojson = {
        "type": "FeatureCollection",
        "features": district_features
    }
    dist_geojson_path = os.path.join(GEO_DIR, "maharashtra_districts.geojson")
    with open(dist_geojson_path, "w", encoding="utf-8") as f:
        json.dump(districts_geojson, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved District GeoJSON ({len(district_features)} features) to: {dist_geojson_path}")

    # Save Taluka GeoJSON
    talukas_geojson = {
        "type": "FeatureCollection",
        "features": taluka_features
    }
    taluka_geojson_path = os.path.join(GEO_DIR, "maharashtra_talukas.geojson")
    with open(taluka_geojson_path, "w", encoding="utf-8") as f:
        json.dump(talukas_geojson, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved Taluka GeoJSON ({len(taluka_features)} features) to: {taluka_geojson_path}")

if __name__ == "__main__":
    seed_geography()
