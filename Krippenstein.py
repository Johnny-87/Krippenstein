# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 13:23:29 2021

@author: Johannes
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import seaborn as sns
from matplotlib.lines import Line2D
import time
import pandas as pd
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import numpy as np




#speicherort der csv dateik
csv_filepath = "Krippenstein_daten.csv"

#speicherort windrose:
wind_rose_filepath = 'Windrose.jpg'

#wpeicherort für liniendiagramm wind
wind_line_filepath = 'Wind_line.jpg'

#speicherort für logging
logging_filepath = "Krippenstein.log"

#speicherort temperatur jpg
temperatur_filepath = "Temperatur.jpg"

#bestimmt die max anzahl an observationen bei der windrose 180 = ~3h
wind_rose_observation = 180

#bestimmt max datenpunkte für wind_line und temperatur plot mehr als 800 wird unübersichtlich
wind_line_observation = 800

#max länge des datensatzes 4400 = ca 3 tage
csv_max_lenght = 4400

#logging parameter
logging.basicConfig(format="{asctime} {levelname:<8} {message}",
                    filename=logging_filepath,
                    style='{', filemode='w')


#option von webdriver wird geändert damit kein browserfenster geöffnet wird
option = webdriver.ChromeOptions()
option.add_argument('headless')

#dict zur umrechnung der Windrichtungen
Windrichtung_Grad = {"N": 0,
                     "NNO": 22.5,
                     "NO": 45, 
                     "ONO": 67.5,
                     "O": 90, 
                     "OSO":112.5,
                     "SO": 135,
                     "SSO": 157.5,
                     "S": 180, 
                     "SSW": 202.5,
                     "SW": 225, 
                     "WSW": 247.5,
                     "W": 270,
                     "WNW": 292.5,
                     "NW": 315,
                     "NNW": 337.5}

# generiere Pandas Dataframe
columns = ["Wind","Wind-max", "Windrichtung", "Temperatur", "Zeit"]
df = pd.DataFrame(columns=columns)

while True:
    try:
        # Im folgenden Code wird die Info über Windwerte abgerufen und in df gespeichert
        browser = webdriver.Chrome(options=option)

        browser.get("http://kaboom.weti.net:3000/locationviewdetailed/84?item%5Bid%5D=84&item%5Bname%5D=Dachstein-Krippenstein&item%5BlogoUrl%5D=https%3A%2F%2Frailway-profile-images.s3-eu-west-1.amazonaws.com%2Fgerhard.zauner%40weti.net%2Fkrippenstein.png")

        nav = browser.find_element(By.ID, "react-root")

        krippenstein_info = nav.text
        logging.debug(f"krippenstein_info: {krippenstein_info}")
        # Werte aus der Krippenstein_info auslesen
        wind_aktuell = float(krippenstein_info.split()[8])
        wind_max = float(krippenstein_info.split()[10])
        windrichtung_aktuell = krippenstein_info.split()[12]
        temp_aktuell = float(krippenstein_info.split()[13])

        dateninput = {"Wind":wind_aktuell,"Wind-max":wind_max, "Windrichtung":windrichtung_aktuell, 
                  "Temperatur":temp_aktuell, "Zeit": datetime.now()}

        #dateninput an den Dataframe anhängen
        df = df.append(dateninput, ignore_index=True)
        
        #generierung der Spalte df["Windrichtung_Grad"]
        df["Windrichtung_Grad"] = df["Windrichtung"].map(Windrichtung_Grad)
        
        #den df auf 4400 kürzen (ca.3 Tage) um zu große daten zu vermeiden
        if len(df)>csv_max_lenght:
            df=df.head(csv_max_lenght)
            
        #speichern des df als csv
        df.to_csv(csv_filepath)
        
        
        
        
#============================================================================
        #Graphische aufbereitung:
        # WINDROSE

        
        #länge der datenreihe für die windrose 180 = ca 3 h
        if len(df)> wind_rose_observation:
            head = wind_rose_observation
        else:
            head = len(df)
            
        speed = df["Wind"].head(wind_rose_observation)
        direction = df["Windrichtung_Grad"].head(wind_rose_observation)
        observation = np.arange(0,len(df.head(wind_rose_observation)))
        observation = observation[::-1]
        
        dir_rad = np.radians(np.array(direction))
        speed = np.array(speed)
        observation = np.array(observation)
        
        fig, ax = plt.subplots(ncols=1, figsize=(10, 4), subplot_kw={"projection": "polar"})
        cmap = 'inferno_r'
        
        img = ax.scatter(dir_rad, speed, c=observation, cmap=cmap, vmin=0, vmax=max(observation) * 1.01)
        ax.set_title(f'Windobservation past ~{wind_rose_observation} minutes')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.annotate("~Minutes past", xy=(1,1), xycoords="axes fraction",
                    xytext=(125,-70), textcoords="offset points",
                    ha="left", va="top",rotation=90, size=14)
        plt.colorbar(img, ax=ax, pad=0.12)
        plt.savefig(wind_rose_filepath,
                    format='jpeg',
                    dpi=200,
                    bbox_inches='tight')
        # Clear the current axes.
        plt.cla() 
        # Clear the current figure.
        plt.clf() 
        # Closes all the figure windows.
        plt.close('all')  
#==============================================================================             
        # Wind line graph
        
        # falls man die nächsten 2 lines 
        # laufen lässt gibt es keine vertikalen linien in den plots 
        #plt.rcParams["axes.grid.axis"] ="y"
        #plt.rcParams["axes.grid"] = True
        
        #bestimmt die größe der sns plots wind_line und temperatur
        sns.set(rc={'figure.figsize':(18,8)})
        
        if len(df)> wind_line_observation:
            tail = wind_line_observation
        else:
            tail = len(df)
        
        #set legend labels
        a = Line2D([], [], color="blue", label="Windgeschwindigkeit")
        b = Line2D([], [], color="red", label="Wind_10min_max")
        
        sns.set_style("whitegrid")
        fig,ax = plt.subplots()
        sns.lineplot(x=df["Zeit"].tail(tail),y=df["Wind"])
        sns.lineplot(x=df["Zeit"].tail(tail),y=df["Wind-max"], color="r")
        ax.tick_params(labelrotation=90)
        ax.set_ylabel("Wind (km/h)", fontsize=14)
        ax.set_xlabel("Zeit (Monat-Tag Stunde)", fontsize=14)
        plt.legend(handles=[a, b],loc = 2, fontsize=20, bbox_to_anchor = (0,-0.15))
        ax2 = plt.twinx()
        ax2.set_ylabel("Windrichtung in Grad",color="green",fontsize=14)
        ax2.set_ylim([0, 360])
        sns.scatterplot(x=df["Zeit"].tail(tail), y=df["Windrichtung_Grad"], color="g")
        ax2.grid(None)
    
        plt.legend(labels=["Windrichtung"],loc = 2, fontsize=20, bbox_to_anchor = (0.3,-0.15))
        fig.savefig(wind_line_filepath,
                    format='jpeg',
                    dpi=400,
                    bbox_inches='tight')
        # Clear the current axes.
        plt.cla() 
        # Clear the current figure.
        plt.clf() 
        # Closes all the figure windows.
        plt.close('all')   
        
 #=============================================================================
        #Temperatur jpg
        
        
        fig,ax = plt.subplots()
        sns.lineplot(x=df["Zeit"].tail(tail), y=df["Temperatur"])
        ax.set_ylabel("Temperatur", fontsize=14)
        ax.set_xlabel("Zeit (Monat-Tag Stunde)", fontsize=14)
        fig.savefig(temperatur_filepath,
                    format='jpeg',
                    dpi=400,
                    bbox_inches='tight')
        
        
        
        # Clear the current axes.
        plt.cla() 
        # Clear the current figure.
        plt.clf() 
        # Closes all the figure windows.
        plt.close('all')   
        
# =============================================================================
      
    except IndexError:
        # Output expected IndexErrors.
        logging.error("Index_Error" )
        
    except NoSuchElementException:
        logging.error("NoSuchElement")
    
    except ValueError:
        logging.error("ValueError")
        
        
    
    time.sleep(50) # delay für 50 sec