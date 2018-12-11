# Michael Lepori/Parth Singh
# CS 415
# Databases Final Project

# Web Scraper to Obtain Info about Trails

import requests
from bs4 import BeautifulSoup
import re
import csv


def spider (max_pages):

    seed = "https://www.hikingproject.com/directory/areas"

    urls = []
    visited_links = []
    urls.append(seed)
    visited = 0

    with open('trail_data.csv', mode='w') as trail_file:
        writer = csv.writer(trail_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['ID', 'Name', 'Length (miles)', 'Ascent (ft)', 'Descent (ft)', 'Dogs', 'Features', 'Ratings', 'Difficulty', 'State'])
        while visited < max_pages and urls != []:

            info = []
            links = []
            url = urls[0]
            urls = urls[1:]
            if visited_links.count(url) > 0:
                continue
            
            visited_links.append(url)
            visited = visited + 1
            print(visited)

            if "www.hikingproject.com/directory/areas" in url:
                links = parse_areas(url)

            elif "www.hikingproject.com/directory/" in url:
                links = parse_directory(url)

            elif "www.hikingproject.com/trail/" in url:
                p = re.compile(r'\d+')
                id = p.findall(url)[0]

                idx = url.rfind('/')
                name = url[idx + 1:]

                info.append(id)
                info.append(name)

                data = parse_trail(url)
                info = info + data

                writer.writerow(info)

            else:
                continue

            urls = urls + links
        

def parse_directory(url):

    new_urls = []
    webpage = requests.get(url)

    wp = BeautifulSoup(webpage.content, 'html.parser')

    tbl = wp.find('table', class_="table table-striped trail-table")
    if tbl:
        links = tbl.find_all('tr')
        for link in links:
            if link:
                new_urls.append(link.get("data-href"))

    tbl = wp.find('div', class_="list-group-item")
    if tbl:
        links = tbl.find_all('a')
        for link in links:
            if link:
                new_urls.append(link.get("href"))

    return new_urls


def parse_areas(url):

    new_urls = []
    webpage = requests.get(url)

    wp = BeautifulSoup(webpage.content, 'html.parser')

    tbl = wp.find_all('div', class_="card area-card")
    for t in tbl:
        links = t.find_all('a')
        for link in links:
            if link:
                new_urls.append(link.get("href"))

    return new_urls


def parse_trail(url):

    info = []

    webpage = requests.get(url)
    wp = BeautifulSoup(webpage.content, 'html.parser')

    tbl = wp.find_all('tr', class_="bottom-border")

    if tbl:
        for t in tbl:
            measures = t.find_all('span', class_="imperial")
            if measures:
                for m in measures:
                    info.append(parse_measures(str(m)))
            else:
                info.append('')
                info.append('')
                info.append('')
    else:
        info.append('')
        info.append('')
        info.append('')            
    
    tbl = wp.find_all("h3", class_="mb-1")
    if tbl:
        dog = 0
        feat = 0
        for t in tbl:
            if "Dog" in str(t):
                sections = t.find_all("span", class_='font-body pl-half')
                info.append(parse_dog(str(sections[0])))
                dog = 1
            if "Features" in str(t):
                sections = t.find_all("span", class_='font-body pl-half')
                info.append(parse_feats(str(sections[0])))
                feat = 1

        if dog == 0:
            info.append('')
        if feat == 0:
            info.append('')

    else:
        info.append('')
        info.append('')

    tbl = wp.find("div", class_="row hidden-xs-down")
    if tbl:
        score_info = tbl.find("span", class_="title text-muted")
        if score_info:
            score_info = parse_score(str(score_info))
            info.append(score_info)
        else: info.append('')

        titles = tbl.find_all("div", class_="title")
        if titles:
            diff = titles[1]
            diff = parse_diff(str(diff))
            info.append(diff)
        else: info.append('')
    
    else: 
        info.append('')
        info.append('')

    tbl = wp.find("ol", class_="breadcrumb")
    if tbl:
        bc = tbl.find_all("li", class_="breadcrumb-item")
        if bc:
            state = bc[1]
            state = parse_state(str(state))
            info.append(state)
        else: info.append('')
    else: info.append('')

    return info


def parse_measures(measure):
    p = re.compile(r'\d+\.?,?\d*')
    m = p.findall(measure)
    if m:
        meas = float(m[0].replace(',',''))
        return meas
    return ''


def parse_dog(dog):
    p = re.compile(r'\n[a-zA-Z -/]+')
    dog_info = p.findall(dog)
    if dog_info:
        dog_info = str(dog_info[0])
        dog_info = dog_info.strip()
        return dog_info
    return ''


def parse_feats(feats):
    feats = feats.split('\n')[1]
    feats = feats.split("·")
    cleaned_feats = []
    for feat in feats:
        feat = feat.strip()
        cleaned_feats.append(feat)
    return cleaned_feats


def parse_score(scores):
    p = re.compile(r'\<span\>\d\.\d\<\/span\>')
    sc = p.findall(scores)
    sc = float(sc[0][6:9])
    p = re.compile(r'\<span\>\d+?<\/span\>')
    num_ratings = p.findall(scores)
    num_ratings = int(num_ratings[0][6:-7])

    return [sc, num_ratings]


def parse_diff(diff):
    p = re.compile(r'\"[A-Z][a-z]+?\/?[A-Z]?[a-z]*?\"')
    d = p.findall(diff)
    if d:
        d = d[0][1:-1]
        return d
    return ''


def parse_state(state):
    return state[-19:-17]


if __name__ == "__main__":
    spider(2000)
