# Pipelines

## Overview

The system is built around four pipelines, each with a clear responsibility.

---

## IngestionPipeline

* Fetches data from APIs and scraping
* Computes weather scores
* Outputs CSV files

---

## StoragePipeline

* Uploads files to AWS S3
* Generates S3 keys

---

## LoadPipeline

* Downloads files from S3
* Stores them locally for processing

---

## DWHPipeline

* Loads files into DataFrames
* Applies transformations
* Inserts data into AWS RDS PostgreSQL database

---

## Key Concepts

### Transformations

* Type casting (numeric, datetime)
* UUID conversion
* JSON parsing

---

### Data Quality

* Handling NaN → None → SQL NULL
* Filtering invalid records

---

### Loading Strategies

* Bulk inserts for performance
* Upserts / conflict handling
* Delete + insert for time-based tables

---

## Execution Order

1. IngestionPipeline
2. StoragePipeline
3. LoadPipeline
4. DWHPipeline

---

## Consistency Rule

All pipelines should run within the same batch to ensure data consistency.
