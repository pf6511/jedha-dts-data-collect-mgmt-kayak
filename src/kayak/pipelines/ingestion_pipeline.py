import pandas as pd
import requests
from typing import TypedDict, Dict, List, Tuple
from pathlib import Path
import os
from datetime import date, datetime, timedelta

from kayak.utils import (
    FileNaming,
    setup_logger)

from kayak.services import (
    GetGPSCoordinates,
    GetWeatherForecast,
    DestinationWeatherForecastInput,
    BookingSpider as hotelsearch,
    DestinationBookingQueryParameters
)

from dataclasses import dataclass

@dataclass
class IngestionPipelineOutputs:
    destination_coordinates_output_filepath: Path = None
    weather_forecast_output_filepath : Path = None
    destination_weather_score_period_file_path:Path = None
    hotel_search_param_file_name: Path = None
    hotel_search_result_file_path:Path = None

    def to_file_list(self) -> list[Path]:
        return [
            self.destination_coordinates_output_filepath,
            self.weather_forecast_output_filepath,
            self.destination_weather_score_period_file_path,
            self.hotel_search_param_file_name,
            self.hotel_search_result_file_path,
        ]

class IngestionPipeline:

    def __init__(self,destinations_input_info_list:List[Dict], output_dir:Path, logger=None):
        self.destinations_input_info_list = destinations_input_info_list
        self.output_dir = output_dir
        import logging
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def remove_file_if_exists(path:Path):
        if os.path.exists(path):
            os.remove(path)
    
    @staticmethod
    def isNoneOrEmpty(ch:str) -> bool:
     return (ch is None or len(ch)==0)

    @staticmethod
    def emptyIfNone(ch:str=None) -> str:
        ("" if ch is None else ch)
    
    
    def load_destination_coordinates(self) -> pd.DataFrame:
        user_agent = 'Edg/129.0.2792.79'
        coordinates_logger = self.logger.getChild("coordinates")
        getcoordinates = GetGPSCoordinates(user_agent,coordinates_logger)
        dest_coordinates_dtf =  getcoordinates.get_destination_gpscoordinates_dataframe(self.destinations_input_info_list)
        #dest_coordinates_dtf.head(1)
        return dest_coordinates_dtf
    
    def load_destination_coordinates_backup(self) -> pd.DataFrame:
        output_file_path = self.output_dir.parent
        backup_file_path = output_file_path/"backup"/f'{FileNaming.get_destination_gps_coordinates_filename()}'
        dest_coordinates_dtf = pd.read_csv(backup_file_path, encoding='utf-8',sep=',')
        return dest_coordinates_dtf
    
    def build_output_file_path(self, file_name) -> Path:
        return self.output_dir/f'{file_name}'

    
    def save_as_csv(self, dtf:pd.DataFrame, file_name:str, replace:bool=True) -> Path:
        file_path = self.build_output_file_path(file_name)
        if replace:
            self.remove_file_if_exists(file_path)
        dtf.to_csv(file_path, encoding='utf-8',sep=',',index = False)
        return file_path

    
    def load_weather_forecasts(self, dest_coordinates_dtf:pd.DataFrame) -> pd.DataFrame:
        # First create list of dict with keys matching get_weather_forecasts dict keys
        user_agent = 'Edg/129.0.2792.79'
        destinations_coordinates_input_dict = (
        dest_coordinates_dtf
            .rename(columns={'gps_long': 'lon', 'gps_lat': 'lat'})
            [['destination_id', 'destination', 'lon', 'lat']]
            .to_dict('records')
        )
        weather_forecast_logger = self.logger.getChild("weather-forecast")
        getweatherforecast = GetWeatherForecast(user_agent,weather_forecast_logger)
        weather_forecasts_dtf = getweatherforecast.get_weather_forecasts(destinations_coordinates_input_dict)
        return weather_forecasts_dtf
    
    def post_process_weather_forecast_dtf(self, weather_forecasts_dtf:pd.DataFrame,dest_coordinates_dtf:pd.DataFrame) -> pd.DataFrame:
        """
        When we pass gps coordinates as weather forecasts API parameters, API might return a different location name (comparing to target destinations)
        So we rename weather forecast destination values with dest_coordinates's destination values mapped to destination_id. In addition we add destination_id column in order to have same destination names / ids accross all datasets<br>
        Convert dt column to datetime
        """
        destination_id_to_name_mapping = dict(zip(dest_coordinates_dtf['destination_id'],dest_coordinates_dtf['destination'] ))
        weather_forecasts_dtf['destination']= weather_forecasts_dtf['destination_id'].map(destination_id_to_name_mapping)
        weather_forecasts_dtf['dt'] = pd.to_datetime(weather_forecasts_dtf['dt'], utc=True, unit='s')
        # remove dt_txt column
        weather_forecasts_dtf.drop(['dt_txt'], axis=1, inplace=True)
        return weather_forecasts_dtf
    
    def compute_weather_forecast_date_range(self,weather_forecasts_dtf:pd.DataFrame) -> Tuple[datetime,datetime]:
        weather_forecast_start_date = weather_forecasts_dtf['dt'].min()
        weather_forecast_end_date = weather_forecasts_dtf['dt'].max()
        return (weather_forecast_start_date,weather_forecast_end_date)
    

    
    def compute_destination_score_period_dtf(self,weather_forecasts_dtf:pd.DataFrame) -> pd.DataFrame:
        """
        for each weather forecast (row) we define an arbitrary score based on weather_main considering Clear sky is the best score
        then 2 aggregations are defined for each destination
        1. median score (weather_median_score)
        2. average temperature (avg_temp)
        Then we compute a two-levels ranking based on 1 and 2 
        """
        weather_main_score_mapping = {'Clear':10, 'Clouds':6, 'Mist':4, 'Snow':4, 'Rain':4, 'Thunderstorm':2}
        weather_forecasts_dtf_copy = weather_forecasts_dtf.copy()
        weather_forecasts_dtf_copy['weather_score'] = weather_forecasts_dtf_copy['weather_main'].map(weather_main_score_mapping).astype(int)
        scores_by_destination_dtf = (
            weather_forecasts_dtf_copy
            .groupby(['destination_id', 'destination'])
            .agg(
                weather_median_score=('weather_score', 'median'),
                avg_temp=('temp', 'mean')
            )
            .reset_index()
        )

        scores_by_destination_dtf['weather_rank'] = (
            scores_by_destination_dtf
            .sort_values(['weather_median_score', 'avg_temp'], ascending=[False, False])
            .groupby(['weather_median_score', 'avg_temp'])
            .ngroup()
            .rank(method='dense', ascending=False)
            .astype(int)
        )
        (weather_forecast_start_date,weather_forecast_end_date) = self.compute_weather_forecast_date_range(weather_forecasts_dtf)
        scores_by_destination_dtf['start_date'] = weather_forecast_start_date
        scores_by_destination_dtf['end_date'] = weather_forecast_end_date
        return scores_by_destination_dtf

    def get_days_offset(self,start_date_time, end_date_time):
        return (end_date_time - start_date_time).days

    def make_hotel_search_common_param(self,start_date_time:datetime,end_date_time:datetime) -> pd.DataFrame:
        import uuid
        search_id = uuid.uuid4()
        #search_id = 'a09f8dcc-ddff-4f84-9407-9f736a1fe0b8'
        checkin_date = start_date_time.date()
        checkout_date = checkin_date + timedelta(days=self.get_days_offset(start_date_time,end_date_time))

        search_param_dict  = {'search_id': search_id,'checkin_date': checkin_date,'checkout_date':checkout_date
                                ,'destination_country':'France', 'destination_type':'city'
                                                    ,'group_adults':2, 'group_children':0 }

        #output_file_path = get_hotel_search_params_file_name(weather_forecast_dates_range_str)
        #output_file_path = OUTPUT_DIR / output_file_path
        #remove_file_if_exists(output_file_path)
        return pd.DataFrame([search_param_dict])
    

    def create_hotel_search_queries(self, dest_coordinates_dtf:pd.DataFrame
                                    , hotel_search_param_dtf:pd.DataFrame) -> List[DestinationBookingQueryParameters]:
        booking_queries = list()
        common_params = hotel_search_param_dtf.iloc[0].to_dict()
        for _,row in dest_coordinates_dtf.iterrows():
            destination_query_parameters = row[['destination_id', 'destination']].to_dict()
            destination_query_parameters.update(common_params)
            booking_queries.append(destination_query_parameters)
        return booking_queries
    
    async def scrap_destinations_hotels(self, hotel_search_queries:List[DestinationBookingQueryParameters]
                                  , output_file_path:Path):
        import asyncio

        logger = self.logger.getChild("hotels-scraping")
        deferred = hotelsearch.scrap(hotel_search_queries, output_file_path=output_file_path, logger=logger)
        async def _run_scrapy():
            loop = asyncio.get_running_loop()
            await deferred.asFuture(loop)
        try:
            asyncio.run(_run_scrapy())
        except RuntimeError:
            # cas notebook (event loop déjà actif)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(deferred.asFuture(loop))

        self.logger.info(f"Results saved to: {output_file_path}")

    def load_destinations_hotels_backup(self,hotel_search_queries:List[DestinationBookingQueryParameters]) -> pd.DataFrame:
        """
            Since Booking is now blocking queries, scraping in no longer working as it is.
            So load former scraping result from backup (when it was working)
        """
        output_file_path = self.output_dir.parent
        backup_file_path = output_file_path/"backup"/f'{FileNaming.get_hotel_search_results_filename(None,None)}'
        destination_hotels_dtf = pd.read_csv(backup_file_path, encoding='utf-8',sep=',')
        destination_hotels_dtf['search_id'] = hotel_search_queries[0]['search_id']
        return destination_hotels_dtf

    def run(self) -> IngestionPipelineOutputs:
        self.logger.info("Starting ingestion pipeline")
        outputs = IngestionPipelineOutputs()
        # destination coordinates 
        #dest_coordinates_dtf = self.load_destination_coordinates()
        dest_coordinates_dtf = self.load_destination_coordinates_backup()
        output = self.save_as_csv(dest_coordinates_dtf, FileNaming.get_destination_gps_coordinates_filename(), replace=True)
        outputs.destination_coordinates_output_filepath=output

        # weather forecasts
        weather_forecast_dtf = self.post_process_weather_forecast_dtf(self.load_weather_forecasts(dest_coordinates_dtf), dest_coordinates_dtf)
        weather_forecast_start_date, weather_forecast_end_date = self.compute_weather_forecast_date_range(weather_forecast_dtf)
        self.logger.info(f'weather_forecast_start_date : {weather_forecast_start_date}')
        self.logger.info(f'weather_forecast_end_date : {weather_forecast_end_date}')
        #dates_range_suffix = IngestionPipeline.compute_weather_forecast_dates_range_suffix(weather_forecast_start_date,weather_forecast_end_date)
        output = self.save_as_csv(weather_forecast_dtf
                                  , FileNaming.get_destination_weather_forecast_filename(weather_forecast_start_date,weather_forecast_end_date)
                                  , replace=True)
        outputs.weather_forecast_output_filepath = output

        DAYS_OFFSET_MAX = (weather_forecast_end_date - weather_forecast_start_date).days
        self.logger.info(f'DAYS_OFFSET_MAX : {DAYS_OFFSET_MAX}')

        # destination weather score
        dtf = self.compute_destination_score_period_dtf(weather_forecast_dtf)
        output = self.save_as_csv(dtf
                                  , FileNaming.get_destination_weatherscores_filename(weather_forecast_start_date, weather_forecast_end_date))
        outputs.destination_weather_score_period_file_path = output

        # hotels scraping
        hotel_search_param_dtf = self.make_hotel_search_common_param(weather_forecast_start_date, weather_forecast_end_date)
        output = self.save_as_csv(hotel_search_param_dtf
                                  ,FileNaming.get_hotel_search_params_filename(weather_forecast_start_date, weather_forecast_end_date))
        outputs.hotel_search_param_file_name = output

        '''
        output_file_path = self.build_output_file_path(FileNaming.get_hotel_search_results_filename(
            weather_forecast_start_date, weather_forecast_end_date)
            )
        '''
        #self.scrap_destinations_hotels(self.create_hotel_search_queries(dest_coordinates_dtf,hotel_search_param_dtf),output_file_path)
        dtf = self.load_destinations_hotels_backup(self.create_hotel_search_queries(dest_coordinates_dtf,hotel_search_param_dtf))
        output = self.save_as_csv(dtf,FileNaming.get_hotel_search_results_filename(
            weather_forecast_start_date, weather_forecast_end_date)
            )
        outputs.hotel_search_result_file_path=output
        return outputs
