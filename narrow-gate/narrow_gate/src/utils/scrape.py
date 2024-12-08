# import libraries
import os
from dotenv import load_dotenv
import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from geopy.distance import geodesic
import googlemaps
import time
from pathlib import Path

URL = 'https://www.mass-schedules.com'
header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"}

def get_page(url):
  page = requests.get(url, headers=header)
  s1 = BeautifulSoup(page.content,'html.parser')
  s2 = BeautifulSoup(s1.prettify(),'html.parser')
  return s2

def get_map(s2):
  loc_map = {}
  tables = s2.find_all('table')
  for a in tables[0].find_all('a', href=True):
    city = a.contents[0].strip()
    s2 = get_page(URL+a['href']) # get churches for specific city
    tables = s2.find_all('table') # get all churches
    loc_map[city] = [(x.find('span', {'class':'list_church_name'}).contents[0].strip(), x['href']) for x in tables[0].find_all('a', href=True)]
  return loc_map

def cell_parse(cell, tag, filter):
  if cell.find(tag, filter):
    return cell.find(tag, filter).contents[0].strip()
  else:
    return ''

def get_church_info(x):
  church_info = {}
  for li in get_page(x).find('ul', id='church_info1').find_all('li'):
    try:
      church_info[li.find('label').contents[0].strip()[:-1]] = li.find('p').contents[0].strip()
    except:
      pass

  return church_info

def get_mass_schedule(x):
  mass_schedule = []
  for row in get_page(x).find_all("tr"):
    for idx, cell in enumerate(row.find_all("td")):
      temp = {}
      temp['day_of_week'] = idx
      temp['schedule'] = cell_parse(cell, 'p', {'class':'schedule'})
      temp['language'] = cell_parse(cell, 'p', {'class':'language'})
      temp['comment'] = cell_parse(cell, 'p', {'class':'comment'})
      if temp['schedule']!='':
        mass_schedule.append(temp)

  return mass_schedule

def compile_churches(city):
  churches = []
  for x in city:
    print(x)
    temp = {}
    temp['church_name'] = x[0]
    temp.update(get_church_info(URL+x[1]))
    churches.append(temp)

  return pd.DataFrame(churches)

def compile_schedules(city):
  schedules = []
  for x in city:
    temp = pd.DataFrame(get_mass_schedule(URL+x[1]))
    temp['church_name'] = x[0]
    temp['address'] = get_church_info(URL+x[1])['address']
    schedules.append(temp)

  return pd.concat(schedules)

def build_church_dataset(city_map):
  churches = pd.concat([compile_churches(city_map[c]) for c in list(city_map.keys())])
  churches['coords'] = churches.address.apply(lambda x: gmaps.geocode(x)[0]['geometry']['location'])
  churches['long'] = churches.coords.apply(lambda x: x['lng'])
  churches['lat'] = churches.coords.apply(lambda x: x['lat'])
  #churches.to_csv('churches.csv')
  return churches

def refresh_dataset():
  s2 = get_page(URL+"/philippine-locations.html")
  tables = s2.find_all('table') # get all cities
  city_map = get_map(s2)
  
  # note: figure out how to handle confessions
  churches = build_church_dataset(city_map)
  print(churches.shape)
  masses = pd.concat([compile_schedules(city_map[c]) for c in list(city_map.keys())])
  masses['day_of_week'] = abs(masses['day_of_week'] - 6)
  print(masses.shape)
  churches.to_csv('./data/churches.csv')
  masses.to_csv('./data/masses.csv')