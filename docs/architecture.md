# Architecture & Design

## Overview

This project implements a modular data architecture to ingest, store, process, and analyze hotel and weather data.

The system follows a layered approach:

* Data Sources
* Data Pipelines
* Storage (Data Lake & Data Warehouse)
* Analytics

---

## Design Principles

The architecture is built around core data engineering principles:

* **Separation of concerns** (ingestion, storage, processing)
* **Idempotent pipelines** (safe re-execution)
* **Reproducible data processing**
* **Clear data flow** from raw data to analytics
* **Batch-oriented processing** for consistency

---

## Data Flow

Sources → Ingestion → Local Files → S3 → Load → Local Staging → DWH → Analytics

---

## Components

### Data Sources

* GPS coordinates API (used for forecast API parameters)
* Weather API (forecast data)
* Web scraping (hotel search results)

---

### IngestionPipeline

* Collects raw data from APIs and scraping
* Computes intermediate metrics (weather score)
* Outputs structured CSV files

---

### StoragePipeline

* Uploads generated files to AWS S3
* Generates S3 object keys

---

### LoadPipeline

* Downloads files from S3 using object keys
* Stores them in a local staging directory

---

### DWHPipeline

* Loads files into pandas DataFrames
* Applies transformations (typing, cleaning, validation)
* Inserts data into PostgreSQL using SQLAlchemy

---

### Data Lake (AWS S3)

* Stores raw and intermediate datasets
* Enables reprocessing without re-ingestion

---

### Data Warehouse (AWS RDS PostgreSQL)

* Managed PostgreSQL database hosted on AWS RDS
* Stores structured and curated datasets
* Optimized for analytical queries and reporting
* Supports SQL-based transformations and ranking logic


---

### Analytics

* SQL queries for ranking destinations and hotels
* Map-based visualizations (e.g., Mapbox)

---

## Pipeline Responsibilities

| Pipeline  | Responsibility                     |
| --------- | ---------------------------------- |
| Ingestion | Collect and structure raw data     |
| Storage   | Persist data in S3 (data lake)     |
| Load      | Retrieve data into local staging   |
| DWH       | Transform and load into PostgreSQL |

---

## Data Consistency Strategy

To ensure consistency across datasets:

* Each pipeline run produces a **coherent data snapshot**
* Weather forecasts, derived scores, and hotel data are **aligned in time**
* No mixing of data from different runs
* Pipelines are executed in a **controlled order within the same batch**

---

## Key Challenges

* Handling **evolving weather forecasts** over time
* Managing **NaN vs NULL** between pandas and PostgreSQL
* Ensuring **consistent ranking logic** across transformations
* Maintaining **temporal consistency** between datasets

---

## Optimization Strategy

* Use of **SQL window functions** (e.g., `DENSE_RANK`) for efficient ranking
* **Indexing** on key columns (`destination_id`, `dt`, `score`)
* **Early filtering** to reduce data volume
* Batch processing to improve performance and consistency

---

## Key Takeaways

* Modular pipeline design improves maintainability
* Clear separation between storage and processing layers
* Analytical queries are optimized using SQL-native features
* Data consistency is enforced through batch execution
