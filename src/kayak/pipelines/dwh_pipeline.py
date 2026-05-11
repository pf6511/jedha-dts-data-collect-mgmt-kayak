from pathlib import Path
import pandas as pd
from sqlalchemy import Engine
from sqlalchemy.orm import Session
import ast
import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete

from kayak.utils import FileNaming
from kayak.models import (Destination, DestinationWeatherForecast, DestinationWeatherScorePeriod, HotelSearchParam, HotelSearchResult)
import json

class DWHPipeline:

    def __init__(self, engine:Engine, logger):
        self.engine = engine
        self.logger = logger

        self.transformers = {
            FileNaming.DESTINATION_GPS: self._transform_destination,
            FileNaming.DESTINATION_WEATHER_FORECAST: self._transform_weather_forecast,
            FileNaming.DESTINATION_WEATHER_SCORE: self._transform_weather_score,
            FileNaming.HOTEL_SEARCH_PARAM: self._transform_hotel_search_param,
            FileNaming.HOTEL_SEARCH_RESULT:self._transform_hotel_search_result
        }

        self.model_loaders = {
            FileNaming.DESTINATION_GPS: self._load_destinations,
            FileNaming.DESTINATION_WEATHER_FORECAST: self._load_weather_forecast,
            FileNaming.DESTINATION_WEATHER_SCORE: self._load_destination_weather_score,
            FileNaming.HOTEL_SEARCH_PARAM: self._load_hotel_search_param,
            FileNaming.HOTEL_SEARCH_RESULT: self._load_hotel_search_result
        }

        self.processing_order = [
                FileNaming.DESTINATION_GPS,
                FileNaming.DESTINATION_WEATHER_FORECAST,
                FileNaming.DESTINATION_WEATHER_SCORE,
                FileNaming.HOTEL_SEARCH_PARAM,
                FileNaming.HOTEL_SEARCH_RESULT,
        ]


    def _to_int(self, series):
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    
    def _to_numeric(self, series: pd.Series) -> pd.Series:
        return pd.to_numeric(series, errors="coerce")
    
    def _to_numeric_with_scale(self, series, scale: int):
        return pd.to_numeric(series, errors="coerce").round(scale)

    def _parse_and_normalize_json(self,x):
        if pd.isna(x):
            return None
        try:
            return ast.literal_eval(x)
        except Exception:
            return None
    
    def _load_dataframe(self, file: Path) -> pd.DataFrame:
        if file.suffix == ".csv":
            return pd.read_csv(file, encoding="utf-8", sep=",")
        elif file.suffix == ".parquet":
            return pd.read_parquet(file)
        else:
            raise ValueError(f"Unsupported file type: {file}")

    def _transform_destination(self, dtf: pd.DataFrame) -> pd.DataFrame:
        dtf["destination_id"] = self._to_int(dtf["destination_id"])
        dtf['gps_lat'] = self._to_numeric(dtf['gps_lat'])
        dtf['gps_long'] = self._to_numeric(dtf['gps_long'])
        return dtf
    
    def _transform_weather_forecast(self, dtf: pd.DataFrame) -> pd.DataFrame:
        dtf["destination_id"] = self._to_int(dtf["destination_id"])
        dtf['dt'] = pd.to_datetime(dtf['dt'], utc=True)
        dtf['temp'] = self._to_numeric_with_scale(dtf['temp'],2)
        dtf['temp_min'] = self._to_numeric_with_scale(dtf['temp_min'],2)
        dtf['temp_max'] = self._to_numeric_with_scale(dtf['temp_max'],2)
        dtf["pressure"] = self._to_int(dtf["pressure"])
        dtf["humidity"] = self._to_int(dtf["humidity"])
        dtf['pop'] = self._to_numeric_with_scale(dtf['pop'],3)
        dtf['clouds_info_dict'] = dtf['clouds_info_dict'].apply(self._parse_and_normalize_json)
        return dtf
    
    def _transform_weather_score(self, dtf: pd.DataFrame) -> pd.DataFrame:
        dtf["destination_id"] = self._to_int(dtf["destination_id"])
        dtf['weather_median_score'] = self._to_numeric_with_scale(dtf['weather_median_score'],3)
        dtf['avg_temp'] = self._to_numeric_with_scale(dtf['avg_temp'],2)
        dtf["weather_rank"] = self._to_int(dtf["weather_rank"])
        dtf['start_date'] = pd.to_datetime(dtf['start_date'], utc=True)
        dtf['end_date'] = pd.to_datetime(dtf['end_date'], utc=True)
        return dtf
    
    def _transform_hotel_search_param(self, dtf:pd.DataFrame) -> pd.DataFrame:
        dtf["checkin_date"] = pd.to_datetime(dtf["checkin_date"]).dt.date
        dtf["checkout_date"] = pd.to_datetime(dtf["checkout_date"]).dt.date
        dtf["search_id"] = dtf["search_id"].apply(uuid.UUID)
        dtf["group_adults"] = self._to_int(dtf["group_adults"])
        dtf["group_children"] = self._to_int(dtf["group_children"])
        return dtf

    def _transform_hotel_search_result(self, dtf:pd.DataFrame) -> pd.DataFrame:
        dtf["destination_id"] = self._to_int(dtf["destination_id"])
        dtf["search_id"] = dtf["search_id"].apply(uuid.UUID) 
        dtf['gps_lat'] = self._to_numeric(dtf['gps_lat'])
        dtf['gps_long'] = self._to_numeric(dtf['gps_long'])
        dtf["score"] = self._to_numeric(dtf['score'])
        dtf["score"] = dtf["score"].astype(object)
        dtf["score"] = dtf["score"].where(pd.notna(dtf["score"]), None)
        return dtf

    def _transform_dataframe(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        transform_fn = self.transformers.get(file_type)

        if transform_fn:
            return transform_fn(df)

        return df
    
    def _load_destinations(self,dtf:pd.DataFrame,session: Session):
        if dtf.empty:
            return
        self.logger.info("Loading %s rows into %s", len(dtf), "destination")
        stmt = insert(Destination).values(dtf.to_dict("records"))

        stmt = stmt.on_conflict_do_nothing(
            index_elements=['destination_id']
        )
        session.execute(stmt)

    def _load_weather_forecast(self,dtf:pd.DataFrame, session: Session):
        if dtf.empty:
            return
        self.logger.info("Loading %s rows into %s", len(dtf), "destination_weather_forecast")
        weather_forecast_start_date = dtf['dt'].min()
        weather_forecast_end_date = dtf['dt'].max()

        session.execute(
            delete(DestinationWeatherForecast).where(
                DestinationWeatherForecast.dt >= weather_forecast_start_date,
                DestinationWeatherForecast.dt <= weather_forecast_end_date
            )
        )

        session.bulk_insert_mappings(
            DestinationWeatherForecast,
            dtf.to_dict("records")
        )

    def _load_destination_weather_score(self,dtf:pd.DataFrame, session:Session):
        if dtf.empty:
            return
        self.logger.info("Loading %s rows into %s", len(dtf), "destination_weather_score_period")
        start = dtf['start_date'].min()
        end = dtf['end_date'].max()
        session.execute(
            delete(DestinationWeatherScorePeriod).where(
                DestinationWeatherScorePeriod.start_date >= start,
                DestinationWeatherScorePeriod.end_date <= end
            )
        )
        session.bulk_insert_mappings(
            DestinationWeatherScorePeriod,
            dtf.to_dict("records")
        )

    def _load_hotel_search_param(self, dtf:pd.DataFrame, session:Session):
        if dtf.empty:
            return
        assert len(dtf) == 1
        self.logger.info("Loading %s rows into %s", len(dtf), "hotel_search_param")
        ## Cascade delete on hotel_search_result
        search_id = dtf.iloc[0]["search_id"]
        session.execute(
            delete(HotelSearchParam).where(
                HotelSearchParam.search_id == search_id
            )
        )

        session.bulk_insert_mappings(
            HotelSearchParam,
            dtf.to_dict("records")
        )

    def _load_hotel_search_result(self, dtf:pd.DataFrame, session:Session):
        if dtf.empty:
            return
        self.logger.info("Loading %s rows into %s", len(dtf), "hotel_search_result")
        valid_columns = set(HotelSearchResult.__table__.columns.keys()) - {"id"}
        dtf = dtf[[col for col in dtf.columns if col in valid_columns]]
        session.bulk_insert_mappings(HotelSearchResult,dtf.to_dict('records'))


    def _load_model(self, dtf:pd.DataFrame, file_type:str, session:Session):
        model_loader_fn = self.model_loaders.get(file_type)

        if model_loader_fn:
            model_loader_fn(dtf, session)

    def _process_file(self, file: Path, session: Session):
        file_type = FileNaming.detect_type(file.name)

        self.logger.info("Processing file: %s (type=%s)", file, file_type)
        dtf = self._load_dataframe(file)
        dtf = self._transform_dataframe(dtf, file_type)
        self._load_model(dtf,file_type,session)

    def _order_file_processing(self, files:list[Path]) -> list[Path]:
        from collections import defaultdict

        files_by_type = defaultdict(list)
        ordered_files = []
        for file in files:
            file_type = FileNaming.detect_type(file.name)
            files_by_type[file_type].append(file)

        for file_type in self.processing_order:
                for file in files_by_type.get(file_type, []):
                    ordered_files.append(file)

        known_types = set(self.processing_order)
        for file_type, files_list in files_by_type.items():
            if file_type not in known_types:
                self.logger.warning("Unknown file type: %s", file_type)
                ordered_files.extend(files_list)

        return ordered_files

    def run(self, files: list[Path]):
        self.logger.info("Starting DWHPipeline...")
        ordered_files = self._order_file_processing(files)
        with Session(self.engine) as session:
            try:
                for file in ordered_files:
                    self._process_file(file, session)

                session.commit()

            except Exception as e:
                self.logger.error("Error in DWHPipeline: %s", e)
                session.rollback()
                raise

        self.logger.info("DWHPipeline completed")