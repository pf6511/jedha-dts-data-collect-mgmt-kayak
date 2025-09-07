import pandas as pd
import requests

import os
from pathlib import Path
import sys

class GetDestinationCoordinates:

    def __init__(self,user_agent:str='Edg/129.0.2792.79'):
        self.user_agent=user_agent
        self.headers = {'User-Agent' : self.user_agent}

    current_dir = os.path.dirname(os.path.realpath(__file__))

    URL_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
    RESP_DEST_ADDRESSTYPE_DICT_KEY = 'addresstype'
    RESP_DEST_NAME_DICT_KEY = 'name'
    RESP_DEST_LONGITUTE_DICT_KEY = 'lon'
    RESP_DEST_LATITUTE_DICT_KEY = 'lat'

    INPUT_DEST_DICT_KEY = 'destination_key'

    def response_json(self,parameters:dict) -> list:
        """
        Request url_endoint with input parameters
        Return respon in json format
        """
        try:
            search_resp = requests.get(url=GetDestinationCoordinates.URL_ENDPOINT, params=parameters, headers=self.headers)
            print('Response Status code : {}, parameters : {}'.format(search_resp.status_code, parameters))
            return search_resp.json()
        except Exception as e:
            print("Request failed, ", e)

    @staticmethod
    def filter_response_json_by_addresstype(destinations_response_json:list, destination_key:str, address_type:str) -> dict:
        """
        Return 
        """
        #print(destinations_response_json)
        lst = list(filter(lambda d: (d[GetDestinationCoordinates.RESP_DEST_ADDRESSTYPE_DICT_KEY] == address_type),destinations_response_json))
        if(len(lst)==1):
                lst = lst[0]
        elif (len(destinations_response_json) >= 1):
            print("No entry matching address_type for destination key : ", destination_key)
            print("take first entry, addesstype : ", destinations_response_json[0][GetDestinationCoordinates.RESP_DEST_ADDRESSTYPE_DICT_KEY])
            lst = destinations_response_json[0]
        else :
            print("No matching entry for destination key : ", destination_key)
        return lst
       #raise Exception("More than one element in list")  

    @staticmethod
    def get_destination_request_parameters(destination_q_param:str)->dict:
        parameters = {'format':'jsonv2'}
        parameters['q']=destination_q_param
        return parameters

    @staticmethod
    def get_destination_request_q_param(destination:str,destinations_input_info_list:list)->str:
        lst = list(filter(lambda d:d[GetDestinationCoordinates.INPUT_DEST_DICT_KEY] == destination,destinations_input_info_list ))
        return lst[0]['destination_q']

    @staticmethod
    def get_destination_input_addresstype(destination:str,destinations_input_info_list:list)->str:
        lst = list(filter(lambda d:d[GetDestinationCoordinates.INPUT_DEST_DICT_KEY] == destination,destinations_input_info_list ))
        if(len(lst)==1):
            return lst[0]['address_type']
        else:
            return None
    @staticmethod
    def get_destination_resp_coordinates(destination_resp_attributes:dict) -> dict:
        return {'gps_long':destination_resp_attributes[GetDestinationCoordinates.RESP_DEST_LONGITUTE_DICT_KEY]
                , 'gps_lat':destination_resp_attributes[GetDestinationCoordinates.RESP_DEST_LATITUTE_DICT_KEY]}

    def get_destination_resp_name(destination_resp_attributes:dict) -> dict:
        return {'destination':destination_resp_attributes[GetDestinationCoordinates.RESP_DEST_NAME_DICT_KEY]}
                                  
    def get_destinations_gpscoordinates(self,destinations_input_info_list:list) -> list:
        destination_list = list()
        for destination_key in [dest_dico[GetDestinationCoordinates.INPUT_DEST_DICT_KEY] for dest_dico in destinations_input_info_list]:
            destination_summary_dict = {'destination_key': destination_key}
            destination_request_params = GetDestinationCoordinates.get_destination_request_parameters(GetDestinationCoordinates.get_destination_request_q_param(destination_key,destinations_input_info_list))
            destinations_response_json = self.response_json(destination_request_params)
            destination_resp_attributes = GetDestinationCoordinates.filter_response_json_by_addresstype(destinations_response_json, destination_key
                                                                                                        , GetDestinationCoordinates.get_destination_input_addresstype(destination_key,destinations_input_info_list)) 
            if(len(destination_resp_attributes)==0):
                continue
            destination_summary_dict |= GetDestinationCoordinates.get_destination_resp_coordinates(destination_resp_attributes)
            destination_summary_dict |= GetDestinationCoordinates.get_destination_resp_name(destination_resp_attributes)
            destination_list.append(destination_summary_dict)
        return destination_list

    @staticmethod
    def create_output_dataframe() -> pd.DataFrame:
        schema ={'destination_key':str, 'destination':str, 'gps_long':float, 'gps_lat':float}
        return pd.DataFrame(columns=schema).astype(schema)

    def get_destination_gpscoordinates_dataframe(self,destinations_input_info_list:list) -> pd.DataFrame:
        '''
            Return destinations GPS coordinates. DataFrame columns
            destination_key, destination_name, gps_long, gps_lat
        '''
        schema ={'destination_id':int,'destination_key':str, 'destination':str, 'gps_long':float, 'gps_lat':float}
        dest_coordinates_dtf = pd.DataFrame(columns=schema).astype(schema)
        destination_coordinates_list = self.get_destinations_gpscoordinates(destinations_input_info_list)
        for index,dest in enumerate(destination_coordinates_list):
            dest_coordinates_dtf.loc[len(dest_coordinates_dtf)]=[index+1,dest["destination_key"], dest["destination"], dest["gps_long"],dest["gps_lat"]]
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
        instance = GetDestinationCoordinates(user_agent)
        dest_coordinates_dtf =  instance.get_destination_gpscoordinates_dataframe(destinations_input_info_list)
        print(dest_coordinates_dtf.head(20))

@staticmethod
def test():
    GetDestinationCoordinates.test_get_destination_gpscoordinates_dataframe()

#test()
