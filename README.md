# Hotel Data Engineering Pipeline

## Overview

This project implements an end-to-end data pipeline to collect, enrich, and analyze hotel data using weather-based scoring.

The goal is to identify the best travel destinations and hotels based on weather conditions and search results.

---

## Architecture

The pipeline is composed of four main components:

* **IngestionPipeline**

  * Collects data from APIs (weather) and web scraping (hotels)
  * Generates structured datasets (CSV)

* **StoragePipeline**

  * Uploads data to AWS S3 (Data Lake)

* **LoadPipeline**

  * Downloads data from S3 into a local staging area

* **DWHPipeline**

  * Transforms and loads data into PostgreSQL (AWS RDS)
  * Handles data cleaning, typing, and validation

---

## 🔄 Data Flow

Sources → Ingestion → CSV → S3 → Load → Local → DWH → SQL Analytics

---

## Tech Stack

* Python
* pandas
* SQLAlchemy
* Scrapy
* AWS S3 (Data Lake)
* AWS RDS PostgreSQL (Data Warehouse)

---

## Data Model

Main tables:

* `destination`
* `destination_weather_forecast`
* `destination_weather_score_period`
* `hotel_search_param`
* `hotel_search_result`

---

## Key Features

* Weather-based scoring of destinations
* Ranking of destinations and hotels
* Top-N queries using SQL window functions
* Data consistency across pipelines

---

## Data Processing

* Type casting (numeric, datetime)
* NULL handling (NaN → None → SQL NULL)
* JSON parsing
* Batch processing logic

---

## Run

```bash
    KAYAK.ipynb
```

---

## Future Improvements

* Pipeline orchestration (Airflow / Prefect)
* Data validation tests
* Monitoring & logging
* Historical tracking of weather forecasts

## Documentation

- Architecture → docs/architecture.md
- Data model → docs/data_model.md
- SQL queries → docs/sql_queries.md
