import pandas as pd
import requests

import os
from pathlib import Path
import sys
import time

class GetGPSCoordinates:

    def __init__(self,user_agent:str='Edg/129.0.2792.79', logger=None):
        self.user_agent=user_agent
        self.headers = {'User-Agent' : self.user_agent}
        import logging
        self.logger = logger or logging.getLogger(__name__)

    current_dir = os.path.dirname(os.path.realpath(__file__))

    URL_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
    RESP_DEST_ADDRESSTYPE_DICT_KEY = 'addresstype'
    RESP_DEST_NAME_DICT_KEY = 'name'
    RESP_DEST_LONGITUTE_DICT_KEY = 'lon'
    RESP_DEST_LATITUTE_DICT_KEY = 'lat'

    INPUT_DEST_DICT_KEY = 'destination_key'
    TIME_SLEEP_BETWEEN_REQUEST = 1

    def response_json(self,parameters:dict) -> list:
        """
        Request url_endoint with input parameters
        Return response in json format
        """
        try:
            search_resp = requests.get(url=GetGPSCoordinates.URL_ENDPOINT, params=parameters, headers=self.headers)
            self.logger.info('Response Status code : {}, parameters : {}'.format(search_resp.status_code, parameters))
            search_resp.raise_for_status()
            return search_resp.json()
        except Exception as e:
            self.logger.error("Request failed, ", e)
            raise

    def filter_response_json_by_addresstype(self,destinations_response_json:list, destination_key:str, address_type:str) -> dict:
        """
        Return 
        """
        #print(destinations_response_json)
        lst = list(filter(lambda d: (d[GetGPSCoordinates.RESP_DEST_ADDRESSTYPE_DICT_KEY] == address_type),destinations_response_json))
        if(len(lst)==1):
                lst = lst[0]
        elif (len(destinations_response_json) >= 1):
            self.logger.info("No entry matching address_type for destination key : %s", destination_key)
            self.logger.info("Take first entry, addesstype : %s", str(destinations_response_json[0][GetGPSCoordinates.RESP_DEST_ADDRESSTYPE_DICT_KEY]))
            lst = destinations_response_json[0]
        else :
            self.logger.info("No matching entry for destination key : %s", destination_key)
        return lst
       #raise Exception("More than one element in list")  

    def get_destination_request_parameters(self,destination_q_param:str)->dict:
        parameters = {'format':'jsonv2'}
        parameters['q']=destination_q_param
        return parameters

    def get_destination_request_q_param(self,destination:str,destinations_input_info_list:list)->str:
        lst = list(filter(lambda d:d[GetGPSCoordinates.INPUT_DEST_DICT_KEY] == destination,destinations_input_info_list ))
        return lst[0]['destination_q']


    def get_destination_input_addresstype(self,destination:str,destinations_input_info_list:list)->str:
        lst = list(filter(lambda d:d[GetGPSCoordinates.INPUT_DEST_DICT_KEY] == destination,destinations_input_info_list ))
        if(len(lst)==1):
            return lst[0]['address_type']
        else:
            return None
    
    def get_destination_resp_coordinates(self,destination_resp_attributes:dict) -> dict:
        return {'gps_long':destination_resp_attributes[GetGPSCoordinates.RESP_DEST_LONGITUTE_DICT_KEY]
                , 'gps_lat':destination_resp_attributes[GetGPSCoordinates.RESP_DEST_LATITUTE_DICT_KEY]}

    def get_destination_resp_name(self,destination_resp_attributes:dict) -> dict:
        return {'destination':destination_resp_attributes[GetGPSCoordinates.RESP_DEST_NAME_DICT_KEY]}
                                  
    def get_destinations_gpscoordinates(self,destinations_input_info_list:list) -> list:
        destination_list = list()
        for destination_key in [dest_dico[self.INPUT_DEST_DICT_KEY] for dest_dico in destinations_input_info_list]:
            destination_summary_dict = {'destination_key': destination_key}
            destination_request_params = self.get_destination_request_parameters(
                self.get_destination_request_q_param(destination_key,destinations_input_info_list)
            )
            destinations_response_json = self.response_json(destination_request_params)
            time.sleep(GetGPSCoordinates.TIME_SLEEP_BETWEEN_REQUEST)
            destination_resp_attributes = self.filter_response_json_by_addresstype(
                destinations_response_json, destination_key
                , self.get_destination_input_addresstype(destination_key,destinations_input_info_list)) 
            if(len(destination_resp_attributes)==0):
                continue
            destination_summary_dict |= self.get_destination_resp_coordinates(destination_resp_attributes)
            destination_summary_dict |= self.get_destination_resp_name(destination_resp_attributes)
            destination_list.append(destination_summary_dict)
        return destination_list

    
    def create_output_dataframe(self) -> pd.DataFrame:
        schema ={'destination_key':str, 'destination':str, 'gps_long':float, 'gps_lat':float}
        return pd.DataFrame(columns=schema).astype(schema)

    def get_destination_gpscoordinates_dataframe(self,destinations_input_info_list:list) -> pd.DataFrame:
        '''
            Return destinations GPS coordinates. DataFrame columns
            destination_key, destination_name, gps_long, gps_lat
        '''
        destination_coordinates_list = self.get_destinations_gpscoordinates(destinations_input_info_list)
        schema = {
            "destination_id": "int64",
            "destination_key": "string",
            "destination": "string",
            "gps_long": "float64",
            "gps_lat": "float64"
        }
        dest_coordinates_dtf = pd.DataFrame(destination_coordinates_list)
        dest_coordinates_dtf.insert(0, "destination_id", range(1, len(dest_coordinates_dtf) + 1))
        dest_coordinates_dtf = dest_coordinates_dtf.reindex(columns=schema.keys()).astype(schema)
        return dest_coordinates_dtf

    @staticmethod
    def test_get_destination_gpscoordinates_dataframe():
        destinations_input_info_list = [{'destination_key':'Mont Saint-Michel','destination_q':'Mont Saint Michel, France, 50170', 'address_type':'tourism'}
                                ]
        destinations_input_info_list = [{'destination_key':'Bayeux','destination_q':'Bayeux, France, 14400','address_type':'city'}
                                ]
        destinations_input_info_list = [{'destination_key':'Chateau du Haut Koenigsbourg','destination_q':'Chateau du Haut Koenigsbourg, France','address_type':'historic'}
                                ]
        destinations_input_info_list = [
                                {'destination_key':'Aigues Mortes','destination_q':'Aigues Mortes, France','address_type':'tourism'}
                                ]
                                
                                
        user_agent = 'Edg/129.0.2792.79'
        from Logger import setup_logger
        root_logger = setup_logger("app", log_file="logs/kayak.log", console=False)
        coordinates_logger = root_logger.getChild("coordinates")
        instance = GetGPSCoordinates(user_agent,coordinates_logger)
        dest_coordinates_dtf =  instance.get_destination_gpscoordinates_dataframe(destinations_input_info_list)
        print(dest_coordinates_dtf.head(20))

@staticmethod
def test():
    GetGPSCoordinates.test_get_destination_gpscoordinates_dataframe()

#test()
