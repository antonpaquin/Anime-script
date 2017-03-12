import requests
from bs4 import BeautifulSoup
from urllib import parse

import sys
from os import getcwd
import re
import traceback

identity = {}
with open('/home/anton/.passwords/ohayo') as pass_f:
  for line in pass_f.readlines():
    key = line.split('=')[0].strip()
    val = line.split('=')[1].strip()
    identity[key] = val

def run():
    args = parseArgs()

    if '-h' in args:
        doHelp()

    elif '-l' in args:
        doList(args['target'])

    else:
        doPlay(args['target'])


def doList(target):
    if len(target) == 0:
        listShows()
    else:
        if 'show' in target:
            if 'season' in target:
                if 'episode' in target:
                    listEpisode(target['show'], target['season'], target['episode'])
                else:
                    listSeason(target['show'], target['season'])
            else:
                listShow(target['show'])
        else:
            doHelp()


def doHelp():
    print('''
    Usage:
    anime (-l | -h)? (showName (season)? (episode)? )?
    ''')


def doPlay(target):
    if not ('show' in target and 'season' in target and 'episode' in target):
        doList(target)
        return

    url = parse.quote(
        'ohayo.antonpaquin.me/Anime/{}/{}/{}'.format(
            target['show'],
            target['season'],
            target['episode']
        )
    )
    header = 'http://' + identity['user'] + ':' + identity['password'] + '@'

    print('mpv ' + header + url)


###


def listShows():
    print('Anime/')
    print('--------------------')
    for show in getShows():
        print(show)


def listShow(showName):
    seasons = getSeasons(showName)
    if len(seasons) == 1:
        listSeason(showName, 'Season 01')
    else:
        print('Anime/' + showName + '/')
        print('--------------------')
        for season in seasons:
            print(season)


def listSeason(showName, season):
    episodes = getEpisodes(showName, season)
    print('Anime/' + showName + '/' + season + '/')
    print('--------------------')
    for episode in episodes:
        print(episode)


def listEpisode(showName, season, episode):
    print('Why do you want this? unimplemented.')


###


def parseArgs():
    try:
        args = sys.argv[1:]

        if len(args) == 0:
            return {'-h': True}

        if args[0] == '-l':
            return {'-l': True, 'target': parseShow(args[1:])}

        if args[0] == '-h':
            return {'-h': True}

        targs = [a for a in args if a[0] != '-']
        return {'target': parseShow(targs)}

    except Exception as e:
        print('Error in parsing arguments')
        print(e)
        print('This file is located in: ' + getcwd())
        return {'-h': True}


def getShows():
    return listApache('http://ohayo.antonpaqu.in/Anime/')


def getSeasons(show):
    return listApache('http://ohayo.antonpaqu.in/Anime/' + show + '/')


def getEpisodes(show, season):
    return listApache('http://ohayo.antonpaqu.in/Anime/' + show + '/' + season + '/')


def getEpisode(show, season, episodeNumber):
    episodes = getEpisodes(show, season)
    epSearch = 'e' + padNumber(episodeNumber)
    for episode in episodes:
        if re.search(epSearch, episode):
            return episode


def parseShowName(name):
    validNames = getShows()

    # First, by exact copy
    if name in validNames:
        return name

    # Try with ignoring case
    lowNames = list(map(lambda x: x.lower(), validNames))
    for lowname, fullname in zip(lowNames, validNames):
        if name.lower() == lowname:
            return fullname

    # Try abbreviations
    shortNames = list(map(lambda x: x[:len(name)], lowNames))
    for shortname, fullname in zip(shortNames, validNames):
        if name.lower() == shortname:
            return fullname

    # Try substrings
    for lowname, fullname in zip(lowNames, validNames):
        if lowname.find(name.lower()) != -1:
            return fullname

    # Fallback to edit distance
    minDist = 10000
    res = ''
    for lowname, fullname in zip(lowNames, validNames):
        d = editDistance(lowname, name.lower())
        if d < minDist:
            minDist = d
            res = fullname

    return res


def parseShow(args):
    res = {}

    try:
        if len(args) > 3:
            raise dead

        if len(args) == 0:
            return {}

        # The first argument better be some kind of show name
        res['show'] = parseShowName(args[0])
        if len(args) == 1:
            return res

        if len(args) == 3:
            sNum = re.search('[0-9]+', args[1]).group(0)
            res['season'] = 'Season ' + padNumber(sNum)
            eNum = re.search('[0-9]+', args[2]).group(0)
            res['episode'] = getEpisode(res['show'], res['season'], eNum)
            return res

        if len(args) == 2:
            numSeasons = len(getSeasons(res['show']))
            mNums = re.findall('[0-9]+', args[1])
            if numSeasons == 1 and len(mNums) == 1:
                res['season'] = 'Season 01'
                eNum = re.search('[0-9]+', args[1]).group(0)
                res['episode'] = getEpisode(res['show'], res['season'], eNum)
                return res
            else:
                mNums = re.findall('[0-9]+', args[1])
                if len(mNums) >= 1:
                    res['season'] = 'Season ' + padNumber(mNums[0])
                if len(mNums) >= 2:
                    res['episode'] = getEpisode(res['show'], res['season'], mNums[1])
                return res
    except Exception as e:
        traceback.print_exc()
        return res


###


def padNumber(num):
    n = int(num)
    return ('0' + str(n))[-2:]


def editDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


webcache = {}
def httpGet(url):
    if url in webcache:
        return webcache[url]

    auth = requests.auth.HTTPBasicAuth(identity['user'], identity['password'])
    html = requests.get(url, auth=auth).text
    soup = BeautifulSoup(html, 'lxml')
    webcache[url] = soup
    return soup


def listApache(url):
    soup = httpGet(url)
    links = soup.find_all('a')[5:]
    def f(x):
        if x.text[-1] == '/':
            return x.text[:-1]
        else:
            return x.text
    shows = map(f, links)
    return list(shows)


run()
