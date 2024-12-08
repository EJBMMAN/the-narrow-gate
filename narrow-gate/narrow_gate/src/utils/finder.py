import os
# from dotenv import load_dotenv
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from geopy.distance import geodesic
import googlemaps
import time
from pathlib import Path
from src.utils.scrape import  *
from src.utils.finder import  *
import streamlit as st

# load_dotenv()
 
GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def calculate_distance(x, geocode_in):
    return geodesic(x, (geocode_in[0]['geometry']['location']['lat'], geocode_in[0]['geometry']['location']['lng']))

def time_diff(start_time, end_time):
    """Calculates the time difference between two time strings in HH:MM am/pm format.

    Args:
        start_time: The start time string.
        end_time: The end time string.

    Returns:
        A datetime.timedelta object representing the time difference.
    """

    # Parse the time strings into datetime objects
    start_datetime = datetime.datetime.strptime(start_time, '%I:%M %p')
    end_datetime = datetime.datetime.strptime(end_time, '%I:%M %p')

    # Calculate the time difference
    time_difference = end_datetime - start_datetime

    return time_difference

def find_mass(churches, masses, sample_address, search_range, target_sched, current_datetime):
  sample_geocode = gmaps.geocode(sample_address)
  churches['relative_dist'] = churches.apply(lambda x: calculate_distance((x['lat'],x['long']), sample_geocode).km, axis=1)
  church_results = churches[churches.relative_dist<=5]
  church_results.sort_values(by='relative_dist', inplace=True)

  print(church_results.shape)
  print(target_sched.lstrip('0'))

  masses['mass_start'] = masses['schedule'].apply(lambda x: x.split(' - ')[0])
  masses['mass_end'] = masses['schedule'].apply(lambda x: x.split(' - ')[1])
  mass_results = masses[(masses.mass_start==target_sched.lstrip('0')) & 
                        (masses.church_address.isin(church_results.address)) &
                        (masses.day_of_week==current_datetime.weekday())]

  print(masses.mass_start.unique())
  print(target_sched)
  print(mass_results.shape)

  church_results = church_results[church_results.address.isin(mass_results.church_address)]
  church_results['Travel Time(mins)'] = church_results.address.apply(lambda x: gmaps.distance_matrix(sample_address, x, mode="driving", departure_time=datetime.datetime.now()))
  church_results['Travel Time(mins)'] = church_results['Travel Time(mins)'].apply(lambda x: x['rows'][0]['elements'][0]['duration']['value'] / 60)

  travel_times = church_results[['church_name','Travel Time(mins)']].set_index('church_name').to_dict()['Travel Time(mins)']
  addresses = church_results[['church_name','address']].set_index('church_name').to_dict()['address']

  mass_results['Travel Time(Mins)'] = mass_results.church_name.replace(travel_times)
  #mass_results['Address'] = mass_results.church_name.replace(addresses)
  mass_results = mass_results.sort_values(by='Travel Time(Mins)').drop_duplicates(subset=['church_name']).head()
  mass_results['Arrival Time'] = mass_results['Travel Time(Mins)'].apply(lambda x: (datetime.datetime.now() + datetime.timedelta(minutes=x)).strftime("%I:%M %p"))

  return church_results, mass_results