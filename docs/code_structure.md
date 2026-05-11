# Code Structure

## Overview
This document describes the overall structure and organization of the kayak Python project.
The codebase is organized into modular components to ensure maintainability and separation of concerns.

---

📁 Project Layout
project/
├── pyproject.toml        # Project configuration & dependencies
├── src/
│   └── kayak/            # Main Python package
│       ├── __init__.py
│       ├── models/       # SQLAlchemy models (database schema)
│       ├── services/     # Business logic & external integrations
│       ├── pipelines/    # Data pipelines (orchestration)
│       └── utils/        # Shared utilities (logging, helpers, etc.)
├── notebooks/            # Jupyter notebooks (exploration & testing)
├── data/                 # Input, output, temp, backup data
└── README.md

## Core Modules

### Pipelines (kayak.pipelines)

* `IngestionPipeline`
* `StoragePipeline`
* `LoadPipeline`
* `DWHPipeline`

Each pipeline is responsible for a specific stage of the data flow.

---

### Services (kayak.services)

* `s3_service.py`

  * Handles interactions with AWS S3

#### Data Collection services

* `get_gps_coordinates.py`

  * Retrieves GPS coordinates for destinations

* `get_weather_forecast.py`

  * Fetches weather forecast data

* `scraping_booking.py`

  * Scrapes hotel data from Booking

---

### Utilities (kayak.utils)

* `file_naming.py`

  * Detects file types and naming conventions

* `logger.py`

  * Logger set up
---

## 🧠 Design Principles

* Modular design
* Reusable components
* Clear separation between pipelines and services
* Encapsulation of external integrations
* Absolute imports for clarity and robustness (kayak.*)
* Editable install (pip install -e .) for development

---

## Benefits

* Easier maintenance
* Improved readability
* Scalable architecture
* Testable components
