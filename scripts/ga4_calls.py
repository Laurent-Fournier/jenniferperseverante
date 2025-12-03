#!/usr/bin/env python
"""
Documentation
https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
https://analytics.google.com/analytics/web/

Installation
pip install google-analytics-data

Quality
flake8 /home/laurent/projects/ga4-scripts/ga4-calls.py

Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/deliver.py --target=UAT
python scripts/deliver.py --target=PROD

Execution
Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/ga4_calls.py --website=jenniferperseverante
python scripts/ga4_calls.py --website=transbeaute
"""

import argparse
import json
import os
import sys
import time
import mysql.connector

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric, MetricType, RunReportRequest)

from dotenv import load_dotenv

class GA4:
    def __init__(self):

        load_dotenv()  # load variables from .env
        
        # Get the current script's directory path
        self.current_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        self.connexion = mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            password = os.getenv('DB_PASSWORD'),
            database = os.getenv('DB_NAME'),
        )
        self.cursor = self.connexion.cursor(dictionary=True)
    
    # ----------------------------
    # Process all GA4 API calls
    # ----------------------------
    def process_calls(self, website):
        """
        Processes all configured GA4 API calls for a specific website.
        :param website: The identifier of the website whose data should be processed.
        """
        print(f"Start Processing GA4 calls for website '{website}'")
        print(f"Current path : {self.current_path}")
        
        # 1°) Load GA4 Calls setup file
        ga4_calls_file = f'{self.current_path}/conf/ga4_calls.json'
        print(f"GA4 calls file: {ga4_calls_file}")
        with open(ga4_calls_file, 'r') as file:
            self.ga4_calls = json.load(file)        

        # 2°) Load website-specific configuration
        website_config_file = f'{self.current_path}/conf/{website}.json'
        with open(website_config_file, 'r') as config_file:
            config_data = json.load(config_file)
            self.account_id = config_data["account_id"]
            self.site_name = config_data["site_name"]
            self.site_url = config_data["site_url"]
            self.ga4_property_id = config_data["ga4_property_id"]
            self.ga4_credential_filename = config_data["ga4_credential_filename"]

        # Set GA4 API credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{self.current_path}/conf/{self.ga4_credential_filename}'
        client = BetaAnalyticsDataClient()
            
        print('✅ GA4 processed successfully!') 

    
    # -----------
    # Run !!
    # -----------
    def run(self):
        """
        Main function to execute GA4 API calls for traffic data.
        This function handles logging setup, argument parsing, and processes the specified website configuration.
        """
        # Start time tracking for execution duration
        start_time = time.time()

        # Parse script arguments
        parser = argparse.ArgumentParser(
            description="run GA4 API calls",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("-w", "--website", default="UNKNOWN", help="Website config filename")
        args = parser.parse_args()

        # Check if a valid website config filename is provided
        if args.website == 'UNKNOWN':
            print('[ERROR] Need a config filename')
            quit()
        else:
            self.process_calls(args.website)  # process GA4 calls

        # Calculate and log the total execution time
        interval = time.time() - start_time
        print(f'Total time execution: {round(interval / 60, 1)} minutes')



if __name__ == "__main__":
    GA4().run()