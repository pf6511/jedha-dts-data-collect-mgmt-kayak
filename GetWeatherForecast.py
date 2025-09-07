import os
import requests
import pandas as pd
from typing import TypedDict, List
from pathlib import Path

class DestinationForecastInput(TypedDict):
    destination_id: int
    destination: str
    lon: float
    lat: float


class GetWeatherForecast:
    URL_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, user_agent: str = "Edg/129.0.2792.79"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("❌ OPENWEATHER_API_KEY not set in environment")

    def response_json(self, parameters: dict) -> dict:
        try:
            search_resp = requests.get(
                url=self.URL_ENDPOINT, params=parameters, headers=self.headers
            )
            parameters_print = parameters.copy()
            parameters_print.pop("appid", None)  # hide API key in logs
            print(
                f"Response Status code : {search_resp.status_code}, parameters : {parameters_print}"
            )
            return search_resp.json()
        except Exception as e:
            print("Request failed:", e)
            return {}

    def get_location_parameters(self, lon: float, lat: float) -> dict:
        return {"units": "metric", "lon": lon, "lat": lat, "appid": self.api_key}

    def create_output_dataframe(self) -> pd.DataFrame:
        schema = {
            "destination_id": int,
            "destination": str,
            "dt_txt": str,
            "dt": int,
            "temp": float,
            "temp_min": float,
            "temp_max": float,
            "pressure": int,
            "humidity": int,
            "weather_main": str,
            "weather_descr": str,
            "clouds_info_dict": object,
            "pop": int,
        }
        return pd.DataFrame(columns=schema).astype(schema)

    def add_destination_forecasts_to_dataframe(
        self,
        destination_input: DestinationForecastInput,
        destination_pred_json_output: dict,
        output_dtf: pd.DataFrame,
    ) -> pd.DataFrame:
        """Fill dataframe with weather forecasts for a single destination"""
        for days_data_lst in destination_pred_json_output.get("list", []):
            day_row_dtf = pd.DataFrame(
                {
                    "destination_id": destination_input["destination_id"],
                    "destination": [destination_pred_json_output["city"]["name"]],
                    "dt_txt": [days_data_lst["dt_txt"]],
                    "dt": [days_data_lst["dt"]],
                    "temp": [days_data_lst["main"]["temp"]],
                    "temp_min": [days_data_lst["main"]["temp_min"]],
                    "temp_max": [days_data_lst["main"]["temp_max"]],
                    "pressure": [days_data_lst["main"]["pressure"]],
                    "humidity": [days_data_lst["main"]["humidity"]],
                    "weather_main": [days_data_lst["weather"][0]["main"]],
                    "weather_descr": [days_data_lst["weather"][0]["description"]],
                    "clouds_info_dict": [days_data_lst["clouds"]],
                    "pop": [days_data_lst["pop"]],
                },
                columns=output_dtf.columns,
            )
            output_dtf = pd.concat([output_dtf, day_row_dtf], ignore_index=True)
        return output_dtf

    def get_destination_weatherforecasts(self, lon: float, lat: float) -> dict:
        return self.response_json(self.get_location_parameters(lon, lat))

    def get_weather_forecasts(
        self, destination_input_list: List[DestinationForecastInput]
    ) -> pd.DataFrame:
        """Return DataFrame with forecasts for multiple destinations"""
        output_dtf = self.create_output_dataframe()
        for dest_input in destination_input_list:
            output_dtf = self.add_destination_forecasts_to_dataframe(
                dest_input,
                self.get_destination_weatherforecasts(dest_input["lon"], dest_input["lat"]),
                output_dtf,
            )
        return output_dtf

    @classmethod
    def test(cls):
        destinations_coordinates = [
            {"destination_id": 1, "destination": "Aix-en-Provence", "lon": 5.4474738, "lat": 43.5298424}
        ]

        user_agent = "Edg/129.0.2792.79"
        weather_forecasts_dtf = cls(user_agent).get_weather_forecasts(destinations_coordinates)

        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        destination_name = destinations_coordinates[0]["destination"].replace(" ", "-").lower()
        output_file = output_dir / f"destination_weatherforecasts_{destination_name}.csv"

        weather_forecasts_dtf.to_csv(output_file, encoding="utf-8", sep=",", index=False)

        print(f"✅ Forecasts saved to {output_file}")
        return weather_forecasts_dtf