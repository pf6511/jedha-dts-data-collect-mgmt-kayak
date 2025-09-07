import os 
import logging

# Import scrapy and scrapy.crawler 
import scrapy
from scrapy.crawler import CrawlerProcess
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner

from twisted.internet import reactor
from urllib.parse import urlencode,unquote_plus
import re

from datetime import date, datetime, timedelta
from typing import TypedDict, List

class DestinationBookingQueryParameters(TypedDict):
    destination_id:int
    destination: str
    destination_country: str
    destination_type: str
    checkin_date: date
    checkout_date: date
    group_adults:int
    group_children:int


class BookingSpider(scrapy.Spider):

    custom_settings = {
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36',
    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    },
    }


    ROOT_URL = 'https://www.booking.com/searchresults.fr.html'
    destination_id_mapping = dict()
    filename = "booking_hotels.csv"
    MAX_ROWS_PER_QUERY_RESULT = 20

    def add_query_start_url(self,destination_query_parameters:DestinationBookingQueryParameters)->str:
        self.destination_id_mapping.update({destination_query_parameters['destination']: destination_query_parameters['destination_id']})
        url = self.to_url(destination_query_parameters)
        print('url : ' , url)
        self.start_urls.append(url)
        return url


    def to_url(self, destination_query_parameters:DestinationBookingQueryParameters)->str:
        booking_destination_query_parameters_str = BookingSpider.ROOT_URL + "?" + urlencode({'ss':destination_query_parameters['destination'] + "," + destination_query_parameters['destination_country']
                                                ,'lang':'fr', 'dest_type':destination_query_parameters['destination_type']
                                                ,'checkin':destination_query_parameters['checkin_date'].strftime('%Y-%m-%d')
                                                ,'checkout':destination_query_parameters['checkout_date'].strftime('%Y-%m-%d')
                                                ,'group_adults':str(destination_query_parameters['group_adults'])
                                                , 'group_children':str(destination_query_parameters['group_children'])
                                                , 'rows' : str(BookingSpider.MAX_ROWS_PER_QUERY_RESULT)
                                                })
        return booking_destination_query_parameters_str

    def get_matching_destination_id_from_url(self, url) ->str:
        str = ''
        if(url is None):
            return str
        try:
            url = unquote_plus(url)
            str = url[url.index('ss=')+3:url.index('&')]
            str = str[0:str.rfind(',')]
            str = self.destination_id_mapping[str]
        except Exception as e:
            print('no matching destination_id for : ', str)
        return str
    
    def __init__(self, queries:List[DestinationBookingQueryParameters], filename:str):
        self.start_urls = []
        for query in queries:
            self.add_query_start_url(query)
        BookingSpider.filename = filename

    # Name of your spider
    name = "booking"

    

    # Url to start your spider from 
    start_urls = [
        
    ]

    # Callback function that will be called when starting your spider
    # iterate on each hotels in the searchresult page (containerlist), collect hotel name, hotel url and destination_id into a dict
    # then provide callback to follow at hotel_url to gather more informations that will be added to dict (meta)
    def parse(self, response):
        hotel_container_list = response.xpath("*//div[contains(@data-testid,'property-card') and contains(@role,'listitem')]")
        self.logger.info("Found %d hotel containers on %s", len(hotel_container_list), response.url)
        i=0
        for hotel_container in hotel_container_list:
            i=i+1
            try:               
                  hotel_name=hotel_container.xpath("*//div[contains(@data-testid,'title')]/text()").get()
                  hotel_url=hotel_container.xpath("*//a[contains(@data-testid,'title-link')]/@href").get()
                  '''
                  if (i>5):
                    break
                  '''
                  if(hotel_name is None):
                       continue                
                  hotel_item= {
                    'destination_id':self.get_matching_destination_id_from_url(response.url)
                    #,'nb_results':len(hotel_container_list)
                    #,'i':i
                    ,'hotel_name' : hotel_name
                    ,'url':hotel_url
                    }
                  yield response.follow(hotel_url, callback=self.parse_hotel, meta={'item':hotel_item})
            except Exception as e:
                logging.info('Hotel not found, go to next')
                continue
            
    def parse_hotel(self, response):
        try:
            hotel_item = response.meta['item']
            gps_coord_node = response.xpath('*//a[contains(@data-atlas-latlng,"")]/@data-atlas-latlng')
            gps_coord_str = str(gps_coord_node.get())
            gps_lat, gps_lng = None, None
            if gps_coord_str and "," in gps_coord_str:
                parts = gps_coord_str.split(",")
                if len(parts) == 2:
                     gps_lat, gps_lng = parts

            #address = response.xpath('*//a[contains(@data-atlas-latlng,"")]/following-sibling::span[1]/div[1]/text()').get()
            address = response.xpath('*//a[contains(@data-atlas-latlng,"")]/following-sibling::div[1]//span//button//div/text()').get()


            score = response.xpath('*//div[contains(@data-testid,"review-score-right-component")]/div[1]/text()').get()
            if(score is not None):
                score = BookingSpider.extract_first_number(score)
            description = response.xpath('*//div[@class="hp-description"]//following::p[contains(@data-testid,"property-description")]/text()').get()
            hotel_item.update({
                'gps_lat': gps_lat
                ,'gps_long':gps_lng
                ,'score':score
                ,'description': description
                ,'address':address
            })
            yield hotel_item
        except Exception as e:
            logging.error(f"An error occured : {e}")
            #self.logger.error('Error parsing response: %s', e)

    def extract_first_number(txt:str):
        match = re.search(r"\d+(?:[.,]\d+)?", txt)
        if match:
            return match.group(0).replace(",", ".")
        return None

# Name of the file where the results will be saved

current_dir = os.path.dirname(os.path.realpath(__file__))
output_subdir = os.path.join(current_dir,"data","output")
os.makedirs(output_subdir, exist_ok=True)
print("output_subdir : ", output_subdir)


def get_outputfile_path(filename: str) -> str:
    return os.path.join(output_subdir, filename)




def scrap(booking_queries: List[DestinationBookingQueryParameters], filename: str):
    filepath = get_outputfile_path(filename)

    # If file exists, remove it so Scrapy starts fresh
    if os.path.exists(filepath):
        print("remove file : ", filepath)
        os.remove(filepath)

    process = CrawlerProcess(
        settings={
            "USER_AGENT": "Chrome/97.0",
            "LOG_LEVEL": logging.INFO,
            "FEEDS": {filepath: {"format": "csv"}},
        }
    )
    process.crawl(BookingSpider, queries=booking_queries, filename=filename)
    process.start() 
    return filepath


