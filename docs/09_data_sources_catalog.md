# RainRisk Data Sources Catalog

This document lists all data sources for the RainRisk project. The data is divided into two sections: the datasets currently in use, and the new datasets planned for addition.

Every dataset includes its official source link, what the data is, why we use it, how it benefits the project, and key additional information.

---

## Section 1: Existing Data Sources Currently in Use

### 1. IMD 117-Year Historical Subdivisional Rainfall Dataset (1901 to 2017)
* **Source Link:** [https://data.gov.in/resource/sub-divisional-monthly-rainfall-1901-2017](https://data.gov.in/resource/sub-divisional-monthly-rainfall-1901-2017)
* **Official Institution:** India Meteorological Department (IMD), National Data Centre, Pune.

#### What is it?
This is a historical rainfall archive that records monthly, seasonal, and annual rainfall totals across all 36 meteorological subdivisions of India for 117 years (from 1901 to 2017).

#### Why we are using it
It serves as the main historical foundation of our project. It gives us more than a century of recorded rain data so we can study long-term weather trends, drought cycles, and monsoon patterns across India.

#### How will it benefit us?
* It allows us to calculate the official 50-year baseline known as the Long Period Average (LPA) for each region.
* It lets us calculate how much any year was above or below normal rainfall.
* It provides the numbers needed to create prior-year lags and multi-year rolling features for our machine learning models.

#### Additional information
Three remote island and mountain subdivisions (Andaman and Nicobar Islands, Arunachal Pradesh, and Lakshadweep) have genuine missing years in the historical records. Our code uses calendar-grid reindexing so our multi-year rolling calculations never accidentally jump across missing years.

---

### 2. NOAA PSL Nino 3.4 Sea Surface Temperature (SST) Anomalies
* **Source Link:** [https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data](https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data)
* **Official Institution:** National Oceanic and Atmospheric Administration (NOAA) Physical Sciences Laboratory (PSL).

#### What is it?
This dataset tracks monthly temperature changes on the surface of the central-eastern Pacific Ocean (the Nino 3.4 region). It records whether the ocean waters are warmer (El Nino) or cooler (La Nina) than normal from 1870 to the present day.

#### Why we are using it
The Pacific Ocean has a massive influence on the Indian monsoon. When surface waters in the central Pacific become abnormally warm, air patterns shift across the globe. This shift regularly causes descending dry air over India, which often weakens the summer monsoon.

#### How will it benefit us?
* It adds global climate signals to our models instead of relying only on local rainfall numbers.
* It increased our model test accuracy from 52.7% to 56.0% and boosted balanced accuracy from 34.7% to 43.2%.
* It lowered our severe error rate so the model rarely confuses heavy rain with severe drought.

#### Additional information
We only use winter (December to February) and spring (March to May) values before June 1st. Because our prediction is made before the monsoon starts, this ensures our features are completely free of future data leakage.

---

### 3. JAMSTEC / NOAA PSL Indian Ocean Dipole Mode Index (DMI)
* **Source Link:** [https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data](https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data)
* **Official Institution:** Japan Agency for Marine-Earth Science and Technology (JAMSTEC) and NOAA PSL.

#### What is it?
This index measures the difference in sea surface temperature between the western tropical Indian Ocean (near Africa) and the eastern tropical Indian Ocean (near Indonesia). It covers the period from 1870 to the present.

#### Why we are using it
The Indian Ocean Dipole is the local ocean driver right next to India. When the western Indian Ocean is warmer than usual (called a Positive Dipole), extra moisture evaporates and gets pushed into India by the wind. This extra moisture can protect India from drought even when an El Nino is happening in the Pacific.

#### How will it benefit us?
* It acts as a counter-balance to the Pacific El Nino signal.
* It explains why some strong El Nino years did not lead to a drought in India (such as in 1997).
* Multiplying the Nino 3.4 value by the Dipole value gives the model an interaction feature that shows how both oceans behave together.

#### Additional information
Like our Pacific ocean data, we only take the spring values leading up to May. This keeps all inputs strictly prior to the monsoon season.

---

### 4. IMD Hydromet Division Operational Rainfall Legend Document
* **Source Link:** [https://mausam.imd.gov.in/](https://mausam.imd.gov.in/)
* **Official Institution:** India Meteorological Department, Hydromet Division, New Delhi.
* **Archived File:** Saved locally at `docs/sources/IMD_District_Rainfall_Distribution_legend_source.pdf`

#### What is it?
This is an official IMD daily rainfall bulletin that includes the exact operational table used by Indian meteorologists to classify rainfall categories.

#### Why we are using it
Early drafts of our project used estimated boundary numbers for the rarest category ("No Rainfall"). We obtained this official document to confirm the exact numbers directly from the IMD rather than guessing.

#### How will it benefit us?
* It proved that "No Rain" means exactly -100% departure (meaning zero rain recorded against a normal baseline).
* It confirmed that the range from -99% down to -60% belongs to "Large Deficient".
* It gives our project 100% source backing so examiners and domain experts know our labels are authentic.

#### Additional information
Even though our 117-year dataset contains no historical year with a full -100% drop, keeping this official definition ensures our codebase matches live IMD standards.

---

## Section 2: Planned Data Sources to be Added

### 1. EQUINOO (Equatorial Indian Ocean Oscillation) Zonal Wind Index
* **Source Link:** [https://www.iitm.res.in/](https://www.iitm.res.in/)
* **Official Institution:** Indian Institute of Science (IISc), Bangalore, and Indian Institute of Tropical Meteorology (IITM), Pune.

#### What is it?
This is an index that tracks east-west wind anomalies blowing near the ocean surface in the central equatorial Indian Ocean. It covers monthly records from 1901 to the present.

#### Why we are using it
It is the wind and air partner to the Indian Ocean Dipole. Renowned research by Indian scientists (Prof. Sulochana Gadgil and team) showed that El Nino alone only explains about 30% of monsoon variation, but El Nino combined with EQUINOO explains more than 80% of extreme drought and heavy rainfall years in India.

#### How will it benefit us?
* It solves the problem of false drought alarms. Whenever an El Nino occurs, our current model might assume drought is coming, but checking EQUINOO winds tells us if the atmosphere will protect the monsoon.
* It is expected to boost our balanced accuracy by 6% to 8%.
* It gives our project direct backing from top Indian monsoon research papers.

#### Additional information
This dataset comes in clean monthly text files that match our exact 1901 to 2017 timeline. We only take the March to May spring winds before the monsoon begins.

---

### 2. Atlantic Multidecadal Oscillation (AMO) Sea Surface Temperature Index
* **Source Link:** [https://psl.noaa.gov/data/correlation/amon.us.long.data](https://psl.noaa.gov/data/correlation/amon.us.long.data)
* **Official Institution:** NOAA Physical Sciences Laboratory (PSL).

#### What is it?
This index tracks natural cycles of heating and cooling in the surface waters of the North Atlantic Ocean. It spans from 1856 to the present day in monthly values.

#### Why we are using it
The Indian monsoon moves through 30-year wet and dry phases. The Atlantic Ocean heats up and cools down over 60- to 70-year cycles. When the North Atlantic is in a warm phase, it warms the air over Europe and Asia, which strengthens the monsoon pressure system over India for decades.

#### How will it benefit us?
* It gives our decision trees a clear indicator of the background climate epoch.
* It prevents the model from getting confused by multi-decade shifts between dry eras (like the 1970s and 1980s) and wetter eras (like the 1940s and 1950s).
* It improves model generalization on historical test data.

#### Additional information
The data file is a simple, lightweight text table hosted by NOAA. It takes less than one second to download and requires very simple code to join into our training matrix.

---

### 3. Northwest India Heat Low Pressure (Mean Sea Level Pressure)
* **Source Link:** [https://psl.noaa.gov/data/gridded/data.20thC_ReanV3.html](https://psl.noaa.gov/data/gridded/data.20thC_ReanV3.html)
* **Official Institution:** NOAA-CIRES-DOE 20th Century Reanalysis Project (20CRv3).

#### What is it?
This dataset records historical air pressure at sea level across the globe from the 1800s to 2015. We focus on the spring air pressure over the Thar desert and northwest India (latitude 25N to 30N, longitude 68E to 74E).

#### Why we are using it
Rain does not just happen because of past rain; it is pulled into India by an atmospheric heat engine. As northern India gets hot during April and May, a strong low-pressure zone forms. This low pressure acts like a giant vacuum cleaner that pulls moist ocean winds from the southern hemisphere across the equator into India.

#### How will it benefit us?
* It adds a direct physical force into our machine learning model.
* A deeper low-pressure zone in May indicates a vigorous, early monsoon onset.
* It helps the model predict good monsoon years even when ocean temperatures look neutral.

#### Additional information
We only need one monthly number per year (the average May air pressure over northwest India). That means we only download a tiny slice of data (around 120 kilobytes) rather than gigabytes of global weather files.

---

### 4. Multi-Scale Standardized Precipitation Index (SPI-3 and SPI-12)
* **Source Link:** [https://library.wmo.int/records/item/39735-standardized-precipitation-index-user-guide](https://library.wmo.int/records/item/39735-standardized-precipitation-index-user-guide)
* **Official Institution:** World Meteorological Organization (WMO) Standard Drought Guidelines.

#### What is it?
The Standardized Precipitation Index is the global standard used by weather agencies to measure drought. It fits rainfall numbers into a mathematical curve (a Gamma distribution) and converts them into a standard scale where zero is normal, negative numbers mean drought, and positive numbers mean surplus.

#### Why we are using it
Raw percentage departure can be misleading. In dry western Rajasthan, average rainfall is small, so a 30% drop is normal yearly variation. But in wet Kerala, a 30% drop means a huge water shortage. Simple percentage drops treat both situations as identical, which confuses machine learning algorithms.

#### How will it benefit us?
* It normalizes drought severity across all 36 subdivisions so dry and wet states are compared on equal terms.
* It requires zero new downloads because we can compute it using Python directly from the rainfall CSV already inside our project.
* It adds 3-month spring moisture buildup (SPI-3) and 12-month annual water deficit (SPI-12) as clean features.

#### Additional information
We calculate this using the standard SciPy statistics package in Python. Because it runs on existing project data, it can be tested immediately with no risk of network errors.

---

### 5. SPEIbase Global Standardized Precipitation Evapotranspiration Index
* **Source Link:** [https://spei.csic.es/database.html](https://spei.csic.es/database.html)
* **Official Institution:** Spanish National Research Council (CSIC).

#### What is it?
This is a long-term global drought dataset covering 1901 to the present. Unlike simple rain indexes, it measures both rainfall and how much water evaporates into the air due to high temperatures.

#### Why we are using it
Rainfall alone does not tell the full story of dry soil. If pre-monsoon temperatures are very high, moisture quickly evaporates from the ground. This heat creates a "flash drought" where plants dry out even if a small amount of rain fell.

#### How will it benefit us?
* It accounts for rising temperatures and heat waves before the monsoon arrives.
* It serves as a strong proxy for dry soil and reservoir depletion heading into June.
* It helps our model identify droughts driven by severe heat rather than just missing clouds.

#### Additional information
The data is public and free for academic research. We extract the May 6-month index value for each subdivision coordinate to capture conditions right at the start of the summer season.

---

### 6. Kharif Crop Calendars and Vulnerability Tables
* **Source Link:** [https://data.gov.in/](https://data.gov.in/) and [https://agricoop.nic.in/](https://agricoop.nic.in/)
* **Official Institution:** Directorate of Economics and Statistics (DES), Ministry of Agriculture and Farmers Welfare, Government of India.

#### What is it?
This is a collection of official agricultural tables showing the primary crops grown in each region during the monsoon (such as Paddy, Cotton, Soybean, Pulses, and Bajra), along with their sowing dates and water requirements.

#### Why we are using it
A risk model is much more valuable when it explains what the risk means for people on the ground. Just telling a farmer or district official that there is a 60% chance of deficient rain is not enough. They need to know what will happen to their crops.

#### How will it benefit us?
* It powers practical recommendations in our web application.
* When high drought risk is detected, the system can automatically suggest shifting to short-duration pulses, delaying sowing by two weeks, or setting up drip irrigation.
* It upgrades the project from a pure machine learning test into a practical decision support system for agriculture.

#### Additional information
This dataset is stored as a simple, fast lookup table in our backend code. It does not slow down model calculations and runs instantly in the web dashboard.
