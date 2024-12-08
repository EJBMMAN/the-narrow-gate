# import libraries
import os
print(os.getcwd())
# from dotenv import load_dotenv
import datetime
import requests
# from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

import plotly.express as px
import plotly.io as pio
pio.templates.default = 'plotly' 
from geopy.distance import geodesic
import googlemaps
import time
from pathlib import Path
from utils.scrape import  *
from utils.finder import  *


# load_dotenv()
GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

st.set_page_config(page_title="Mass Finder Demo", page_icon="🌍")
st.markdown("# Mass Finder Demo")
# st.sidebar.header("Mass Finder Demo")

conn = st.connection("gsheets", type=GSheetsConnection)

churches = conn.read(
    spreadsheet='https://docs.google.com/spreadsheets/d/1onhJrQ7bp2NWQX3DABR-YrzSQLiXrpF1XmZjesE01Hg/edit?usp=sharing'
    worksheet="churches",
)
masses = conn.read(
    spreadsheet='https://docs.google.com/spreadsheets/d/1onhJrQ7bp2NWQX3DABR-YrzSQLiXrpF1XmZjesE01Hg/edit?usp=sharing'
    worksheet="masses",
)

# sample_address = 'Skyway Twin Towers Condominium Capt. Javier st. Brgy Oranbo Pasig city'
# search_range = 10
# target_sched = '6:00 PM'
current_datetime = datetime.datetime.now()
sample_address = st.text_input("Your current location")
search_range = st.number_input("Search radius(km)", value=5, step=1)
target_sched = st.time_input("Target Schedule", step=1800).strftime('%I:%M %p')

# st.table(churches.head(3))
# st.table(masses.head(3))
# st.markdown(target_sched)

if st.button('Search'):
    try:
        church_results, mass_results = find_mass(churches, masses, sample_address, search_range, target_sched, current_datetime)

        fig = px.scatter_map(church_results[church_results.church_name.isin(mass_results.church_name)],
                            lat="lat",
                            lon="long",
                            hover_name="church_name", # display church name on hover
                            text="church_name"
                            )
        sample_geocode = gmaps.geocode(sample_address)
        fig.add_scattermap(lon=[sample_geocode[0]['geometry']['location']['lng']],
                        lat=[sample_geocode[0]['geometry']['location']['lat']],
                        name='my location'
                        )
        st.plotly_chart(fig)
        st.table(mass_results[['schedule','church_name','church_address','Travel Time(Mins)','Arrival Time']])
    except Exception as e:
        st.markdown(e)