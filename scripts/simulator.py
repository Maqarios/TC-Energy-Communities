import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta

# This document was generated by ChatGPT
# ChatGPT parameters
# Parameters:
# Frequency: Daily
# Period: simulate it for 2023
# Output file: json
# Country: Munich, Germany
# roof area: 600 sqm
# Number of stories: 6 (excluding roof)
# Average apartment size: 100 sqm
# roof type: flat with 70% free space
# Building electricity consumption (excluding apartments): 5kWh per sqm per year
# Elderly household consumption: 2.5 to 3.5 kwh per day
# Elderly stay at home period: 95% per day
# Population density: 30% elderly, 30% families, 40% singles
# number of apartments: 20

# Parameters
roof_area = 600
free_roof_area = 0.7 * roof_area
solar_radiation_base = 1.5  # kWh/m²/day (baseline for January)
pv_efficiency = 0.15
daily_pv_generation_base = free_roof_area * solar_radiation_base * pv_efficiency

building_consumption_per_sqm_per_year = 7.3
building_size = 600
total_building_consumption_base = (
    building_consumption_per_sqm_per_year * building_size
) / 365

elderly_daily_consumption_base = np.random.uniform(2.5, 3.5, 6).sum()
families_daily_consumption_base = 6 * 10
singles_daily_consumption_base = 8 * 5
total_household_consumption_base = (
    elderly_daily_consumption_base
    + families_daily_consumption_base
    + singles_daily_consumption_base
)

total_daily_consumption_base = (
    total_building_consumption_base + total_household_consumption_base
)

# Cost parameters
cost_per_sqm = 200  # Cost of PV installation per sqm
maintenance_cost_per_year = 500  # Annual maintenance cost

# Calculate the total cost
initial_installation_cost = free_roof_area * cost_per_sqm
total_years = (
    datetime.strptime("2024-12-31", "%Y-%m-%d")
    - datetime.strptime("2023-01-01", "%Y-%m-%d")
).days / 365
total_maintenance_cost = maintenance_cost_per_year * total_years
total_cost = initial_installation_cost + total_maintenance_cost

# Seasonal factors
pv_generation_factors = {
    1: 0.75,
    2: 0.75,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 1.25,
    7: 1.25,
    8: 1.25,
    9: 1.0,
    10: 1.0,
    11: 1.0,
    12: 0.75,
}

consumption_factors = {
    1: 1.25,
    2: 1.25,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 0.75,
    7: 0.75,
    8: 0.75,
    9: 1.0,
    10: 1.0,
    11: 1.0,
    12: 1.25,
}


# Function to get factors based on month
def get_factors(month):
    pv_factor = pv_generation_factors[month]
    consumption_factor = consumption_factors[month]
    return pv_factor, consumption_factor


# Simulate for a given period (January 2023 in this case)
start_date = "2020-01-01"
end_date = "2024-12-31"
dates = pd.date_range(start=start_date, end=end_date)
data = []

for date in dates:
    month = date.month
    pv_generation_factor, consumption_factor = get_factors(month)

    daily_pv_generation = daily_pv_generation_base * pv_generation_factor
    total_daily_consumption = total_daily_consumption_base * consumption_factor

    daily_generation = np.random.normal(
        daily_pv_generation, daily_pv_generation * 0.1
    )  # 10% variability
    daily_consumption = np.random.normal(
        total_daily_consumption, total_daily_consumption * 0.1
    )  # 10% variability

    data.append(
        {
            "date": date.strftime("%Y-%m-%d"),
            "generation_kWh": daily_generation,
            "consumption_kWh": daily_consumption,
        }
    )

# Calculate statistics
generation_stats = {
    "mean": np.mean([d["generation_kWh"] for d in data]),
    "std": np.std([d["generation_kWh"] for d in data]),
}

consumption_stats = {
    "mean": np.mean([d["consumption_kWh"] for d in data]),
    "std": np.std([d["consumption_kWh"] for d in data]),
}

# Output JSON
output = {
    "Data": data,
    "Generation": f"{generation_stats['mean']} +/- {generation_stats['std']} kWh",
    "Consumption": f"{consumption_stats['mean']} +/- {consumption_stats['std']} kWh",
    "PV System Cost": {
        "Initial Installation Cost": initial_installation_cost,
        "Total Maintenance Cost": total_maintenance_cost,
        "Total Cost": total_cost,
    },
}

# Save to file
output_file_path = "app/data/simulation.json"
with open(output_file_path, "w") as f:
    json.dump(output, f, indent=4)

output_file_path
