"""
MahaRainRisk: Master Pipeline Orchestrator
Executes the full end-to-end data pipeline:
1. Seed Maharashtra administrative geography
2. Fetch teleconnections (NOAA CPC / JAMSTEC)
3. Fetch WRD major reservoir storage
4. Ingest daily IMD climatology
5. Compute McKee SPI-1, SPI-3, SPI-6
6. Compile master feature panel
7. Train and evaluate production Random Forest classifier
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ("Seeding Maharashtra Geography & LGD Master", "scripts/seed_geo.py"),
    ("Fetching Oceanic Teleconnections (ENSO/IOD)", "etl/fetch_teleconnections.py"),
    ("Ingesting Maharashtra WRD Reservoir Levels", "etl/fetch_reservoirs.py"),
    ("Ingesting IMD High-Resolution Climatology", "etl/fetch_imd.py"),
    ("Computing McKee SPI-1, SPI-3, SPI-6", "etl/compute_spi.py"),
    ("Building Master Feature Panel", "etl/build_master_panel.py"),
    ("Training Production Drought Classifier", "ml/train.py"),
]

def main():
    print("=" * 70)
    print("   MahaRainRisk: Automated End-to-End Data & ML Pipeline")
    print("=" * 70)

    for i, (desc, script_rel) in enumerate(STEPS, start=1):
        script_path = os.path.join(BASE_DIR, script_rel)
        print(f"\n[{i}/{len(STEPS)}] >>> {desc}...")
        res = subprocess.run([sys.executable, script_path], cwd=BASE_DIR)
        if res.returncode != 0:
            print(f"[ERROR] Step {i} ({script_rel}) failed with exit code {res.returncode}")
            sys.exit(1)
        print(f"[OK] Step {i} completed successfully.")

    print("\n" + "=" * 70)
    print("   [SUCCESS] Full MahaRainRisk Data & Model Pipeline Completed!")
    print("   Data artifacts ready in: data/processed/master_panel.parquet")
    print("   Production model ready in: ml/drought_model.joblib")
    print("=" * 70)

if __name__ == "__main__":
    main()
