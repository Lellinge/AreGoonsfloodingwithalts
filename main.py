#!/usr/bin/python3

import requests
import json
import datetime
import time
from ratelimit import limits, sleep_and_retry

number_time_in_corp_under_90_days = 0
number_new_characters_without_corp_history = 0
number_new_characters_without_zkill_history = 0
number_no_corp_or_zkill_history = 0
number_age_below_90_days = 0
quit = 0
number_of_characters_processed = 0

member_count = 0

position = -1

data_esi = {}
headers = {
    'User-Agent': '', #Insert a way to contact you here
    'Accept-Encoding': 'gzip'
}
url_evewho = "https://evewho.com/api/allilist/1354830081"

url_zkb = "https://zkillboard.com/api/kills/characterID/"

starttime = datetime.datetime.now()

def get_time_in_corp(data):
    jointime = data[0]['start_date']
    jointime_as_datetime = datetime.datetime.strptime(jointime, '%Y-%m-%dT%H:%M:%SZ')  #for example 2019-12-30T00:24:00Z
    now = datetime.datetime.now()
    duration = now - jointime_as_datetime
    return duration.days

def get_corps_in_history(data):
    counter = 0
    for i in data:
        counter += 1
    return counter

def get_zkill_history(character_id):
    try:

        data_zkillboard = get_zkill_data(character_id)
        counter = 0
        for i in data_zkillboard:
            counter += 1
        return counter
    except:
        print("Something didnt work")
        return 0




@sleep_and_retry
@limits(calls=1, period= 1)
def get_zkill_data(character_id):
    url_final = "https://zkillboard.com/api/kills/characterID/" + str(character_id) + "/"
    response_zkill = requests.get(url_final, headers)
    if(response_zkill.status_code != 200):
        raise Exception('Request to zkillboard failed')
    data_parsed = json.loads(response_zkill.text)
    return data_parsed



def get_character_age(data):
    counter = -1 # array starts at 0
    for i in data: #finds the first corp the character ever was in
        counter += 1
    character_creation_date = data[counter]['start_date']
    character_creation_date_as_datetime = datetime.datetime.strptime(character_creation_date, '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.datetime.now()
    duration = now - character_creation_date_as_datetime
    return duration.days

def get_id(url):
    quit = 0
    position = -1
    url = url + "/"
    while (quit == 0):
        position = position - 1
        if url[position] == "/":
            quit = 1
    position = position + 1
    id = url[position:-1]
    return id

def get_membercount(url_used):
    member_count = 0
    id = get_id(url_used)
    url_corplist = "https://esi.evetech.net/latest/alliances/" + str(id) + "/corporations/"
    corp_list = requests.get(url_corplist, headers)
    data = json.loads(corp_list.text)
    for corp in data:
        url = "https://esi.evetech.net/latest/corporations/" + str(corp) + "/"
        data = requests.get(url, headers)
        data_parsed = json.loads(data.text)
        member_count += data_parsed["member_count"]
    return member_count

def get_list_of_corps(url_used):
    id = get_id(url_used)
    url_corplist = "https://esi.evetech.net/latest/alliances/" + str(id) + "/corporations/"
    corp_list = requests.get(url_corplist, headers)
    data = json.loads(corp_list.text)
    return data

def get_alliance_name(id):
    url_alliance = "https://esi.evetech.net/latest/alliances/" + str(id) + "/"
    data = requests.get(url_alliance, headers)
    data_parsed = json.loads(data.text)
    name = data_parsed['name']
    return name


id = get_id(url_evewho)
list_of_corps = get_list_of_corps(url_evewho)


response = requests.get(url_evewho, headers=headers)
data_evewho = json.loads(response.text)
#gets an json array of every character in alliance

for name in data_evewho['characters']:
    tries = 0
    done = False
    character_id = str(name['character_id'])
    url_esi = "https://esi.evetech.net/latest/characters/" + character_id + "/corporationhistory/"
    while(done == False and tries <= 5):
        try:
            response_corphistory = requests.get(url_esi, headers)
            if (response_corphistory.status_code == 200):
                data_esi = json.loads(response_corphistory.text)
                try: # sometimes data_esi is empty No idea why
                    if(data_esi[0]['corporation_id'] in list_of_corps): #Evewho reports some characters that already left the alliance as still in it.
                        number_of_characters_processed += 1
                        days_in_corp = get_time_in_corp(data_esi)
                        if(days_in_corp <= 90):
                            number_time_in_corp_under_90_days += 1
                            number = get_corps_in_history(data_esi)

                            if(number <= 5):
                                number_new_characters_without_corp_history += 1

                            number = get_zkill_history(character_id)
                            if (number < 5):
                                number_new_characters_without_zkill_history += 1
                            number = get_character_age(data_esi)
                            if (number <= 90):
                                number_age_below_90_days += 1
                except:
                    print("Something happened")
                done = True
            else:
                tries += 1
                if (response_corphistory.status_code == 429):
                    print(response_corphistory.text)
                    print(response_corphistory.content)
                    print(response_corphistory.headers)
                    time.sleep(5)
                else:
                    time.sleep(2)
                    print("The connection to esi failed, retrying")
        except:
            print("requests couldn't do the connection, cant fix that")

member_count = get_membercount(url_evewho)

name = get_alliance_name(id)
endtime = datetime.datetime.now()
runtime = endtime - starttime

print("Alliance")
print(name)
print("Number of characters in corp for less than 90 days")
print(number_time_in_corp_under_90_days)
print("Number of new characters without corp history")
print(number_new_characters_without_corp_history)
print("Number of new characters without zkillboard history")
print(number_new_characters_without_zkill_history)
print("Number of charcters created within the last 90 days")
print(number_age_below_90_days)
print("Numebr of characters processed")
print(number_of_characters_processed)
print("Number of characters in alliance")
print(member_count)
print("Coverage")
print(number_of_characters_processed / member_count)
print("Runtime:")
print(runtime)
