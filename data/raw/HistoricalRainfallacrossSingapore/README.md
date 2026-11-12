# Historical Rainfall Data

⚠️ **These CSV files are too large for GitHub (8GB+ total)**

## Download Instructions

To run this project, download the historical rainfall data from:

**Source:** [data.gov.sg - Historical Rainfall across Singapore](https://data.gov.sg/)

**Files needed:**
- Historical Rainfall across Singapore (2016).csv
- Historical Rainfall across Singapore (2017).csv
- Historical Rainfall across Singapore (2018).csv
- Historical Rainfall across Singapore (2019).csv
- Historical Rainfall across Singapore (2020).csv
- Historical Rainfall across Singapore (2021).csv
- Historical Rainfall across Singapore (2022).csv
- Historical Rainfall across Singapore (2023).csv
- Historical Rainfall across Singapore (2024).csv

**Place downloaded files in this directory:**
```
data/raw/HistoricalRainfallacrossSingapore/
```

## Quick Start (Demo Mode)

For hackathon demo purposes, you can run the system with sample data:

```bash
# From project root
python scripts/load_sample_data.py
```

This loads 50,000 sample records which is sufficient for demonstration.

## Data Info

- **Format:** CSV
- **Total Size:** ~8.5 GB
- **Records:** Millions of 5-minute interval measurements
- **Stations:** 63 NEA rainfall monitoring stations
- **Coverage:** 2016-2024
