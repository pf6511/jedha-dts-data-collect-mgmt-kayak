# Data Model

## Overview

The data model is designed to support the analysis of travel destinations and hotels enriched with weather-based scoring.

It combines:

* Time-series weather data
* Aggregated weather scores
* Hotel search parameters and results

---

## Core Tables

---

### destination

Stores metadata about destinations.

| Column         | Type         | Description       |
| -------------- | ------------ | ----------------- |
| destination_id | Integer (PK) | Unique identifier |
| destination    | String       | Destination name  |
| gps_lat        | Float        | Latitude          |
| gps_long       | Float        | Longitude         |

---

### destination_weather_forecast

Stores weather forecast data for each destination and timestamp.

| Column           | Type             | Description                  |
| ---------------- | ---------------- | ---------------------------- |
| destination_id   | Integer (PK, FK) | Destination reference        |
| dt               | Timestamp (PK)   | Forecast datetime            |
| temp             | Numeric(5,2)     | Temperature                  |
| temp_min         | Numeric(5,2)     | Min temperature              |
| temp_max         | Numeric(5,2)     | Max temperature              |
| pressure         | Integer          | Atmospheric pressure         |
| humidity         | Integer          | Humidity                     |
| weather_main     | String           | Weather category             |
| weather_descr    | String           | Detailed description         |
| clouds_info_dict | JSONB            | Cloud data                   |
| pop              | Numeric(5,3)     | Probability of precipitation |

**Primary Key:** (destination_id, dt)
Ensures uniqueness per forecast timestamp

---

### destination_weather_score_period

Stores aggregated weather metrics over a given time period.

| Column               | Type             | Description           |
| -------------------- | ---------------- | --------------------- |
| destination_id       | Integer (PK, FK) | Destination reference |
| start_date           | Timestamp (PK)   | Period start          |
| end_date             | Timestamp (PK)   | Period end            |
| weather_median_score | Numeric(5,3)     | Median weather score  |
| avg_temp             | Numeric(5,2)     | Average temperature   |
| weather_rank         | Integer          | Ranking (1 = best)    |

**Primary Key:** (destination_id, start_date, end_date)

---

### hotel_search_param

Stores search parameters used for scraping hotel data.

| Column              | Type         | Description              |
| ------------------- | ------------ | ------------------------ |
| search_id           | UUID (PK)    | Unique search identifier |
| checkin_date        | Date         | Check-in date            |
| checkout_date       | Date         | Check-out date           |
| destination_country | String       | Country                  |
| destination_type    | String       | Type (city, region…)     |
| group_adults        | SmallInteger | Number of adults         |
| group_children      | SmallInteger | Number of children       |

---

### hotel_search_result

Stores hotel search results.

| Column         | Type         | Description         |
| -------------- | ------------ | ------------------- |
| id             | Integer (PK) | Unique identifier   |
| search_id      | UUID (FK)    | Reference to search |
| destination_id | Integer (FK) | Destination         |
| hotel_name     | String       | Hotel name          |
| address        | String       | Hotel address       |
| score          | Float        | Hotel rating score  |

---

## Relationships

* **destination → destination_weather_forecast** (1:N)
* **destination → destination_weather_score_period** (1:N)
* **hotel_search_param → hotel_search_result** (1:N)
* **destination → hotel_search_result** (1:N)

---

## Design Choices

### Composite Keys

Used for time-series tables to enforce uniqueness:

* `(destination_id, dt)`
* `(destination_id, start_date, end_date)`

---

### Separation of Raw vs Aggregated Data

* `destination_weather_forecast` → raw data
* `destination_weather_score_period` → derived metrics

---

### JSONB Usage

* `clouds_info_dict` stored as JSONB for flexibility
* Avoids rigid schema for nested weather data

---

### UUID for Search Tracking

* Ensures uniqueness across scraping runs
* Links parameters to results reliably

---

## Data Consistency Considerations

* Weather data is time-dependent and evolving
* Each pipeline run should produce a consistent snapshot
* Hotel results must be associated with a specific search (search_id)

---

## Possible Improvements

* Add `run_id` for full batch traceability
* Introduce historical tracking for weather forecasts
* Normalize hotel data (separate hotel entity)
* Add indexes for performance optimization
