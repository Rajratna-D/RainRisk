"""
MahaRainRisk: Bilingual Agrometeorological Farmer Advisory Engine
Maps real-time & predicted drought risk categories into actionable, crop-specific
recommendations in Marathi (मराठी) and English, strictly anchored to Maharashtra's
4 State Agricultural Universities:
1. MPKV Rahuri (Western Maharashtra / Scarcity Zone)
2. VNMKV Parbhani (Marathwada)
3. PDKV Akola (Vidarbha)
4. BSKKV Dapoli (Konkan Coastal)
"""

import os
import sys
import json
from typing import Dict, Any, Optional

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Official University Allocations across all 36 Districts
UNIVERSITY_MAPPING = {
    # VNMKV Parbhani (Marathwada)
    "Chhatrapati Sambhajinagar": "VNMKV Parbhani",
    "Jalna": "VNMKV Parbhani",
    "Beed": "VNMKV Parbhani",
    "Dharashiv": "VNMKV Parbhani",
    "Latur": "VNMKV Parbhani",
    "Nanded": "VNMKV Parbhani",
    "Parbhani": "VNMKV Parbhani",
    "Hingoli": "VNMKV Parbhani",

    # MPKV Rahuri (Western Maharashtra & Scarcity Zone)
    "Ahmednagar": "MPKV Rahuri",
    "Pune": "MPKV Rahuri",
    "Solapur": "MPKV Rahuri",
    "Satara": "MPKV Rahuri",
    "Sangli": "MPKV Rahuri",
    "Kolhapur": "MPKV Rahuri",
    "Nashik": "MPKV Rahuri",
    "Dhule": "MPKV Rahuri",
    "Jalgaon": "MPKV Rahuri",
    "Nandurbar": "MPKV Rahuri",

    # PDKV Akola (Vidarbha)
    "Akola": "PDKV Akola",
    "Amravati": "PDKV Akola",
    "Buldhana": "PDKV Akola",
    "Washim": "PDKV Akola",
    "Yavatmal": "PDKV Akola",
    "Wardha": "PDKV Akola",
    "Nagpur": "PDKV Akola",
    "Bhandara": "PDKV Akola",
    "Gondia": "PDKV Akola",
    "Chandrapur": "PDKV Akola",
    "Gadchiroli": "PDKV Akola",

    # BSKKV Dapoli (Konkan)
    "Thane": "BSKKV Dapoli",
    "Palghar": "BSKKV Dapoli",
    "Raigad": "BSKKV Dapoli",
    "Ratnagiri": "BSKKV Dapoli",
    "Sindhudurg": "BSKKV Dapoli",
    "Mumbai City": "BSKKV Dapoli",
    "Mumbai Suburban": "BSKKV Dapoli"
}

UNIVERSITY_DETAILS = {
    "VNMKV Parbhani": {
        "full_name_en": "Vasantrao Naik Marathwada Krishi Vidyapeeth, Parbhani",
        "full_name_mr": "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ, परभणी",
        "primary_crops": ["Soybean", "Cotton", "Tur (Pigeon Pea)", "Bajra", "Rabi Jowar"],
        "soil_focus": "Deep Black Vertisols (काळी जमीन) & Rain-Shadow Drought Stress"
    },
    "MPKV Rahuri": {
        "full_name_en": "Mahatma Phule Krishi Vidyapeeth, Rahuri",
        "full_name_mr": "महात्मा फुले कृषी विद्यापीठ, राहुरी",
        "primary_crops": ["Sugarcane", "Rabi Jowar", "Bajra", "Pomegranate", "Onion", "Soybean"],
        "soil_focus": "Deccan Scarcity Zone (पर्जन्यछायेचा दुष्काळ प्रवण पट्टा) & Canal/Well Irrigation"
    },
    "PDKV Akola": {
        "full_name_en": "Dr. Panjabrao Deshmukh Krishi Vidyapeeth, Akola",
        "full_name_mr": "डॉ. पंजाबराव देशमुख कृषी विद्यापीठ, अकोला",
        "primary_crops": ["Cotton", "Soybean", "Tur", "Gram (Chana)", "Nagpur Mandarin Orange"],
        "soil_focus": "Central Vidarbha Purna Alluvium & Rainfed Cotton-Soybean Tract"
    },
    "BSKKV Dapoli": {
        "full_name_en": "Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth, Dapoli",
        "full_name_mr": "डॉ. बाळासाहेब सावंत कोकण कृषी विद्यापीठ, दापोली",
        "primary_crops": ["Kharif Rice (Bhat)", "Alphonso Mango", "Cashew (Kaju)", "Finger Millet (Ragi)"],
        "soil_focus": "Lateritic Coastal Soils (जांभा माती) & High Runoff Moisture Scarcity"
    }
}

# The Prescriptive Action Matrix (0: Safe, 1: Watch, 2: Alert, 3: Severe, 4: Extreme)
ADVISORY_MATRIX = {
    0: {
        "badge_color": "#10B981", # Emerald
        "status_en": "Safe / Normal Condition",
        "status_mr": "सुरक्षित / सामान्य स्थिती",
        "actions": {
            "moisture_conservation": {
                "en": "Soil moisture reserves are adequate. Continue standard intercultural weeding and ridge maintenance.",
                "mr": "जमिनीत पुरेसा ओलावा उपलब्ध आहे. नेहमीप्रमाणे कोळपणी व आंतरमशागत चालू ठेवावी."
            },
            "foliar_and_nutrients": {
                "en": "Apply standard university recommended fertilizer doses (NPK) according to crop growth stage.",
                "mr": "पिकाच्या वाढीच्या अवस्थेनुसार विद्यापीठाने शिफारस केलेले नियमित रासायनिक खतांचे हप्ते द्यावेत."
            },
            "irrigation": {
                "en": "No supplementary irrigation required. Avoid over-watering to prevent fungal root rot.",
                "mr": "सध्या संरक्षित पाण्याची गरज नाही. अतिरिक्त पाण्यामुळे मूळकुजव्या रोग होणार नाही याची दक्षता घ्यावी."
            },
            "contingency": {
                "en": "Routine monitoring. Ensure proper drainage in low-lying field patches to avoid waterlogging.",
                "mr": "शेतात पाणी साचणार नाही यासाठी पाण्याचा निचरा व्यवस्थित ठेवावा."
            }
        }
    },
    1: {
        "badge_color": "#FBBF24", # Amber
        "status_en": "Watch (Mild Moisture Stress)",
        "status_mr": "लक्ष ठेवा (अल्प ओलावा तूट)",
        "actions": {
            "moisture_conservation": {
                "en": "Carry out shallow hoeing (कोळपणी) to create a dust mulch and seal soil cracks, breaking capillary moisture loss.",
                "mr": "जमिनीला पडणाऱ्या भेगा बुजवण्यासाठी आणि बाष्पीभवन रोखण्यासाठी डवरणी/हलकी कोळपणी करून धूळ आच्छादन तयार करावे."
            },
            "foliar_and_nutrients": {
                "en": "Spread organic farm residue, straw, or sugarcane trash (5 t/ha) between rows to retain soil moisture.",
                "mr": "पिकांच्या दोन ओळींत काडीकचरा, पिकांचे अवशेष किंवा पाचटाचे (५ टन/हेक्टर) आच्छादन करावे."
            },
            "irrigation": {
                "en": "Conserve farm pond storage. Postpone non-critical fertilizer applications until soil moisture improves.",
                "mr": "शेततळ्यातील पाणी सुरक्षित ठेवावे. जमिनीतील ओलावा वाढेपर्यंत कोरड्या जमिनीत खतांचा वापर टाळावा."
            },
            "contingency": {
                "en": "Monitor extended weather forecasts for monsoon revival. Check for sucking pests under dry heat.",
                "mr": "हवामान अंदाजावर लक्ष ठेवावे. कोरड्या हवेत रसशोषक किडींचा प्रादुर्भाव तपासण्यासाठी नियमित पाहणी करावी."
            }
        }
    },
    2: {
        "badge_color": "#F97316", # Orange
        "status_en": "Alert (Moderate Drought Stress)",
        "status_mr": "सतर्कता (मध्यम दुष्काळ ताण)",
        "actions": {
            "moisture_conservation": {
                "en": "Soil moisture in root zone is depleting rapidly. Create compartmental bunds across slopes to arrest any rain runoff.",
                "mr": "मुळांच्या भागातील ओलावा वेगाने कमी होत आहे. उताराला आडवे बांध घालून पडणाऱ्या पावसाचे पाणी जागीच जिरवावे."
            },
            "foliar_and_nutrients": {
                "en": "Spray 1% Potassium Nitrate (KNO₃, 100g in 10L water) or 8% Kaolin to induce stomatal closure and arrest leaf wilt.",
                "mr": "पानातील पाण्याचे बाष्पीभवन कमी करण्यासाठी १% पोटॅशियम नायट्रेट (१०० ग्रॅम प्रति १० लिटर पाणी) किंवा ८% केओलिनची पानांवर फवारणी करावी."
            },
            "irrigation": {
                "en": "Provide life-saving protective irrigation via drip or alternate-furrow method during evening or early morning.",
                "mr": "एकाआड एक सरी पद्धतीने किंवा ठिबक सिंचनाने संध्याकाळच्या वेळी पिकास संरक्षित जीवदान पाणी द्यावे."
            },
            "contingency": {
                "en": "Avoid top-dressing with nitrogenous chemical fertilizers (Urea) as it increases drought shock and vegetative wilt.",
                "mr": "जमिनीत ओलावा नसताना युरिया खताचा वापर अजिबात करू नये, यामुळे पिके जळण्याचा धोका वाढतो."
            }
        }
    },
    3: {
        "badge_color": "#EF4444", # Red
        "status_en": "Severe Drought (High Crop Stress)",
        "status_mr": "तीव्र दुष्काळ (गंभीर पीक ताण)",
        "actions": {
            "moisture_conservation": {
                "en": "High risk of permanent wilting. Nip terminal growing buds in Cotton/Tur (शेंडा खुडणे) to shed excess transpiration load.",
                "mr": "कपाशी व तुरीमध्ये झाडावरील पाण्याचा ताण कमी करण्यासाठी तात्काळ शेंडे खुडावेत (Terminal Bud Nipping)."
            },
            "foliar_and_nutrients": {
                "en": "Foliar spray of 2% Urea + 1% Potassium Chloride (MOP) to sustain plant metabolism stalled by dry roots.",
                "mr": "मुळांचे पोषण थांबल्यामुळे २% युरिया (२०० ग्रॅम) अधिक १% पोटॅश (१०० ग्रॅम प्रति १० लिटर पाणी) फवारावे."
            },
            "irrigation": {
                "en": "Ration remaining groundwater strictly. Prioritize micro-drip only for high-value orchards (Pomegranate/Sweet Orange) and seed plots.",
                "mr": "विहीर व कूपनलिकेचे पाणी केवळ फळबागा (डाळिंब/मोसंबी) व बियाणे प्लॉट वाचवण्यासाठी अत्यंत काटेकोरपणे ठिबकद्वारे वापरावे."
            },
            "contingency": {
                "en": "Prepare contingency arrangements for livestock fodder. Prevent complete crop desiccation before green salvage.",
                "mr": "जनावरांच्या चाऱ्याची सोय करावी. पीक पूर्ण सुकण्याआधी गरज पडल्यास चाऱ्यासाठी वापर करण्याबाबत विचार करावा."
            }
        }
    },
    4: {
        "badge_color": "#7F1D1D", # Deep Crimson
        "status_en": "Extreme Drought (Critical Emergency)",
        "status_mr": "अति तीव्र दुष्काळ (आपत्कालीन परिस्थिती)",
        "actions": {
            "moisture_conservation": {
                "en": "Main Kharif crop has exceeded irreversible wilting point. Do NOT invest in expensive chemical fertilizers or pesticides.",
                "mr": "मुख्य पीक वाचण्याची शक्यता कमी झाली आहे. महागड्या खतांवर किंवा कीटकनाशकांवर विनाकारण खर्च करू नये."
            },
            "foliar_and_nutrients": {
                "en": "Spray 2% soluble urea solution solely on surviving green shoots if light shower occurs.",
                "mr": "अल्प पाऊस झाल्यास जिवंत झाडांवर केवळ २% युरियाचे द्रावण फवारावे."
            },
            "irrigation": {
                "en": "Complete irrigation shutdown for seasonal crops. Reserve all remaining well water strictly for drinking and livestock survival.",
                "mr": "हंगामी पिकांचे पाणी पूर्णपणे थांबवावे. उर्वरित पाणी केवळ पिण्यासाठी आणि जनावरांच्या संवर्धनासाठी राखीव ठेवावे."
            },
            "contingency": {
                "en": "Contingency Sowing: If late rains arrive, plant short-duration, drought-hardy contingency crops: Horse Gram (Kulthi), Moth Bean (Matki), or Fodder Pearl Millet (Bajra). Avoid re-sowing expensive soybean/cotton.",
                "mr": "दुबार पेरणीचा इशारा: उशिरा पाऊस झाल्यास सोयाबीन किंवा कपाशीची दुबार पेरणी करू नये. त्याऐवजी कमी पाण्यात येणारे हुलगा (कुळीथ), मटकी किंवा चवळी यासारखी आकस्मिक पिके घ्यावीत."
            }
        }
    }
}

def get_farmer_advisory(
    district_name: str,
    taluka_name: str,
    drought_risk_category: int,
    primary_crop: Optional[str] = None,
    smi: Optional[float] = None,
    dam_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generates official, university-anchored bilingual agrometeorological advisory.
    """
    # 1. Resolve University
    univ_name = UNIVERSITY_MAPPING.get(district_name, "MPKV Rahuri")
    univ_info = UNIVERSITY_DETAILS.get(univ_name, UNIVERSITY_DETAILS["MPKV Rahuri"])

    # 2. Resolve Risk Tier
    risk_cat = int(max(0, min(4, drought_risk_category)))
    risk_info = ADVISORY_MATRIX.get(risk_cat, ADVISORY_MATRIX[0])

    # 3. Resolve Target Crop
    crop = primary_crop if primary_crop else univ_info["primary_crops"][0]

    # 4. Generate Output Object
    advisory = {
        "geography": {
            "taluka_name": taluka_name,
            "district_name": district_name,
            "target_crop": crop
        },
        "university_anchor": {
            "university_key": univ_name,
            "university_name_en": univ_info["full_name_en"],
            "university_name_mr": univ_info["full_name_mr"],
            "regional_focus": univ_info["soil_focus"]
        },
        "risk_level": {
            "category_code": risk_cat,
            "status_en": risk_info["status_en"],
            "status_mr": risk_info["status_mr"],
            "badge_color": risk_info["badge_color"]
        },
        "telemetry_context": {
            "soil_moisture_index_pct": smi if smi is not None else "N/A",
            "dam_storage_pct": dam_pct if dam_pct is not None else "N/A"
        },
        "prescriptive_actions": {
            "moisture_conservation": risk_info["actions"]["moisture_conservation"],
            "foliar_and_nutrients": risk_info["actions"]["foliar_and_nutrients"],
            "irrigation_strategy": risk_info["actions"]["irrigation"],
            "contingency_management": risk_info["actions"]["contingency"]
        },
        "source_citation": f"Official Agro-Advisory aligned with {univ_info['full_name_en']} Package of Practices (कृषी दैनंदिनी मार्गदर्शक तत्त्वे)"
    }

    return advisory

if __name__ == "__main__":
    # Test on Paithan (Aurangabad) and Baramati (Pune)
    print("=" * 70)
    print(" Testing MahaRainRisk Bilingual Advisory Engine")
    print("=" * 70)

    # Example 1: Paithan in Alert Stage
    adv_paithan = get_farmer_advisory(
        district_name="Chhatrapati Sambhajinagar",
        taluka_name="Paithan",
        drought_risk_category=2,
        primary_crop="Cotton",
        smi=28.4,
        dam_pct=94.0
    )
    print("\n--- SAMPLE 1: PAITHAN (MARATHWADA - VNMKV PARBHANI) ---")
    print(f"University: {adv_paithan['university_anchor']['university_name_en']}")
    print(f"Status:     {adv_paithan['risk_level']['status_en']} ({adv_paithan['risk_level']['status_mr']})")
    print(f"Foliar (MR): {adv_paithan['prescriptive_actions']['foliar_and_nutrients']['mr']}")
    print(f"Irrigation (MR): {adv_paithan['prescriptive_actions']['irrigation_strategy']['mr']}")

    # Example 2: Baramati in Safe Stage
    adv_baramati = get_farmer_advisory(
        district_name="Pune",
        taluka_name="Baramati",
        drought_risk_category=0,
        primary_crop="Sugarcane",
        smi=58.2,
        dam_pct=100.0
    )
    print("\n--- SAMPLE 2: BARAMATI (WESTERN MAHARASHTRA - MPKV RAHURI) ---")
    print(f"University: {adv_baramati['university_anchor']['university_name_en']}")
    print(f"Status:     {adv_baramati['risk_level']['status_en']} ({adv_baramati['risk_level']['status_mr']})")
    print(f"Action (MR): {adv_baramati['prescriptive_actions']['moisture_conservation']['mr']}")
