
from datetime import datetime
from pathlib import Path

class FileNaming:

    DESTINATION_GPS = "destination_gps_coordinates"
    DESTINATION_WEATHER_FORECAST = "destination_weather_forecast"
    DESTINATION_WEATHER_SCORE = "destination_weather_scores"
    HOTEL_SEARCH_PARAM = "hotel_search_param"
    HOTEL_SEARCH_RESULT = "hotel_search_results"

    ISO_DATETIME_FORMAT ='%Y%m%dT%H%M'
    EXTENSION = ".csv"

    @classmethod
    def detect_type(cls, file_name: str) -> str:
        for prefix in [
            cls.DESTINATION_GPS,
            cls.DESTINATION_WEATHER_FORECAST,
            cls.DESTINATION_WEATHER_SCORE,
            cls.HOTEL_SEARCH_PARAM,
            cls.HOTEL_SEARCH_RESULT,
        ]:
            if file_name.startswith(prefix):
                return prefix
        return "unknown"

    @classmethod
    def _build_suffix(cls, start: datetime, end: datetime) -> str:
        return f"{start.strftime(cls.ISO_DATETIME_FORMAT)}_{end.strftime(cls.ISO_DATETIME_FORMAT)}"
    
    @classmethod
    def _add_suffix(cls, base: str, start: datetime = None, end: datetime = None) -> str:
        if start and end:
            return f"{base}_{cls._build_suffix(start, end)}"
        return base
    
    @classmethod
    def _add_csv_extension(cls,base:str) -> str:
        if not (".csv" in base):
            return f"{base}{cls.EXTENSION}"
        return base
    
    @staticmethod
    def _build_with_period(base: str, start, end) -> str:
        return f"{base}_{start}_{end}{FileNaming.EXTENSION}"
    

    @classmethod
    def get_destination_gps_coordinates_filename(cls) -> str:
        return f"{cls.DESTINATION_GPS}{cls.EXTENSION}"

    @classmethod
    def get_destination_weather_forecast_filename(cls, start:datetime, end:datetime) -> str:
        return f"{cls._add_suffix(cls.DESTINATION_WEATHER_FORECAST,start,end)}{cls.EXTENSION}"

    @classmethod    
    def get_destination_weatherscores_filename(cls, start:datetime, end:datetime) -> str:
        return f"{cls._add_suffix(cls.DESTINATION_WEATHER_SCORE,start,end)}{cls.EXTENSION}"

    @classmethod
    def get_destination_weatherscores_filename(cls, start:datetime, end:datetime) -> str:
        return f"{cls._add_suffix(cls.DESTINATION_WEATHER_SCORE,start,end)}{cls.EXTENSION}"

    @classmethod   
    def get_hotel_search_params_filename(cls, start:datetime, end:datetime) -> str:
        return f"{cls._add_suffix(cls.HOTEL_SEARCH_PARAM,start,end)}{cls.EXTENSION}"

    @classmethod   
    def get_hotel_search_results_filename(cls, start:datetime, end:datetime) -> str:
        return f"{cls._add_suffix(cls.HOTEL_SEARCH_RESULT,start,end)}{cls.EXTENSION}"