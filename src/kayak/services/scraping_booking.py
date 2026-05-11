import os 
import logging

# Import scrapy and scrapy.crawler 
import scrapy
from scrapy.crawler import CrawlerProcess
#from twisted.internet import reactor, defer
#from scrapy.crawler import CrawlerRunner

#from twisted.internet import reactor
from urllib.parse import urlencode,unquote_plus
from pathlib import Path
import re

from datetime import date, datetime, timezone
from typing import TypedDict, List


class DestinationBookingQueryParameters(TypedDict):
    search_id:str
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

    # Name of your spider
    name = "booking"

    # Url to start your spider from 
    start_urls = [
        
    ]

    ROOT_URL = 'https://www.booking.com/searchresults.fr.html'
    filename = "booking_hotels.csv"
    MAX_ROWS_PER_QUERY_RESULT = 20

    def __init__(self, queries:List[DestinationBookingQueryParameters],logger=None):
        self.queries = queries
        import logging
        self.logger = logger or logging.getLogger(__name__)


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

    def start_requests(self):
        for query in self.queries:
            url = self.to_url(query)

            self.logger.info(f"Start scraping: {url}")

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"query": query}
            )

    

    # Callback function that will be called when starting your spider
    # iterate on each hotels in the searchresult page (containerlist), collect hotel name, hotel url and destination_id into a dict
    # then provide callback to follow at hotel_url to gather more informations that will be added to dict (meta)
    def parse(self, response):
        print("GOT RESPONSE")
        query = response.meta["query"]

        hotel_container_list = response.xpath("*//div[contains(@data-testid,'property-card') and contains(@role,'listitem')]")
        self.logger.info("Found %d hotel containers on %s", len(hotel_container_list), response.url)
        print("Found %d hotel containers on %s", len(hotel_container_list), response.url)
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
                    'search_id': query["search_id"],
                    'destination_id':query["destination_id"]
                    #,'nb_results':len(hotel_container_list)
                    #,'i':i
                    ,'hotel_name' : hotel_name
                    ,'url':hotel_url
                    ,"scraped_at": datetime.utcnow().isoformat()
                    }
                  yield response.follow(hotel_url, callback=self.parse_hotel, meta={'item':hotel_item,'query':query})
            except Exception as e:
                self.logger.error('Hotel not found, go to next')
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
                score = self.extract_first_number(score)
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
            self.logger.error(f"An error occured : {e}")
            raise
            #self.logger.error('Error parsing response: %s', e)

    @staticmethod
    def extract_first_number(txt:str):
        match = re.search(r"\d+(?:[.,]\d+)?", txt)
        if match:
            return match.group(0).replace(",", ".")
        return None




def scrap(booking_queries: List[DestinationBookingQueryParameters], output_file_path: Path, logger=None):
    import os
    import logging
    from scrapy.crawler import CrawlerRunner
    import asyncio

    # If file exists, remove it so Scrapy starts fresh
    if os.path.exists(output_file_path):
        print("remove file : ", output_file_path)
        os.remove(output_file_path)
    print("START SCRAP")
    runner = CrawlerRunner(
        settings={
            "USER_AGENT": "Chrome/97.0",
            "LOG_LEVEL": logging.INFO,
            "FEEDS": {str(output_file_path): {"format": "csv"}},
            "CONCURRENT_REQUESTS": 8,
            "DOWNLOAD_TIMEOUT": 15,
        }
    )

    deferred = runner.crawl(
        BookingSpider,
        queries=booking_queries,
        logger=logger
    )

    return deferred


def test_scrapping():
    import requests
    url =" https://www.booking.com/searchresults.fr.html?ss=Mont+Saint-Michel%2CFrance&lang=fr&dest_type=city&checkin=2026-04-03&checkout=2026-04-10&group_adults=2&group_children=0&rows=20"
    requests.get(url).status_code

