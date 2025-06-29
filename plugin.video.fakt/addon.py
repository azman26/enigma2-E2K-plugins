# -*- coding: utf-8 -*-
import e2kodi__init__ # aby zainicjowac sciezki i nie musiec zmieniac czegos w kodzie
import os
import sys

import requests
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import re
import json
from html import unescape
from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl
#from resources.lib.yt_live import play_yt, epgData

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.fakt')
PATH=addon.getAddonInfo('path')
img_empty=PATH+'/resources/empty.png'
PATH_profile=xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not xbmcvfs.exists(PATH_profile):
    xbmcvfs.mkdir(PATH_profile)

img_empty=PATH+'/resources/img/empty.png'
fanart=PATH+'/resources/img/fanart.jpg'

baseurl=''
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'

hea={
    'User-Agent':UA,
}

def build_url(query):
    return base_url + '?' + urlencode(query)

def addItemList(url, name, setArt, medType=False, infoLab={}, isF=True, isPla='false', contMenu=False, cmItems=[]):
    li=xbmcgui.ListItem(name)
    li.setProperty("IsPlayable", isPla)
    if medType:
        kodiVer=xbmc.getInfoLabel('System.BuildVersion')
        if kodiVer.startswith('19.'):
            li.setInfo(type=medType, infoLabels=infoLab)
        else:
            types={'video':'getVideoInfoTag','music':'getMusicInfoTag'}
            if medType!=False:
                setMedType=getattr(li,types[medType])
                vi=setMedType()
            
                labels={
                    'year':'setYear', #int
                    'episode':'setEpisode', #int
                    'season':'setSeason', #int
                    'rating':'setRating', #float
                    'mpaa':'setMpaa',
                    'plot':'setPlot',
                    'plotoutline':'setPlotOutline',
                    'title':'setTitle',
                    'originaltitle':'setOriginalTitle',
                    'sorttitle':'setSortTitle',
                    'genre':'setGenres', #list
                    'country':'setCountries', #list
                    'director':'setDirectors', #list
                    'studio':'setStudios', #list
                    'writer':'setWriters',#list
                    'duration':'setDuration', #int (in sec)
                    'tag':'setTags', #list
                    'trailer':'setTrailer', #str (path)
                    'mediatype':'setMediaType',
                    'cast':'setCast', #list        
                }
                
                if 'cast' in infoLab:
                    if infoLab['cast']!=None:
                        cast=[xbmc.Actor(c) for c in infoLab['cast']]
                        infoLab['cast']=cast
                
                for i in list(infoLab):
                    if i in list(labels):
                        setLab=getattr(vi,labels[i])
                        setLab(infoLab[i])
    li.setArt(setArt) 
    if contMenu:
        li.addContextMenuItems(cmItems, replaceItems=False)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isF)

def main_menu():
    items=[
        ['VIDEO','video','DefaultAddonVideo.png'],
        ['Transmisje na żywo (YT)','live','DefaultTVShows.png']
    ]
    
    for i in items:
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': i[2], 'fanart':fanart}
        url = build_url({'mode':i[1]})
        if i[1]=='live':
            cm=True
            cmItems=[('[B]Szczegóły[/B]','RunPlugin(plugin://plugin.video.fakt?mode=epg)')]
            plot='[B]Transmisje okazjonalne[/B]\n [I]Planowane transmisje dostępne z poziomu menu kontekstowego (szczegóły)[/I]'
            isFolder=False
            isPlayable='true'
        else:
            cm=False
            cmItems=[]
            plot=''
            isFolder=True
            isPlayable='false'
        iL={'plot':plot}
        addItemList(url, i[0], setArt, 'video', iL, isFolder, isPlayable, cm, cmItems)

    xbmcplugin.endOfDirectory(addon_handle)
    
def epList(p):
    url='https://www.fakt.pl/wideo'
    if p!='1':
        url+='?page='+p
    resp=requests.get(url,headers=hea).text
    resp1=resp.split('streamLead-leadItem')[1].split('\"pagination\"')[0].split('\"list-item\"')
    for r in resp1:
        if 'list-item-link' in r:
            link=re.compile('list-item-link\" href=\"([^\"]+?)\"').findall(r)[0]
            img=re.compile('src=\"([^\"]+?)\"').findall(r)[0]
            title=re.compile('list-item-title\">([^<]+?)<').findall(r)[0]
            title=title.replace('\n','')
            desc=re.compile('list-item-lead\">([^<]+?)<').findall(r)[0]
    
            iL={'plot':unescape(desc)}
            setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':fanart}
            url = build_url({'mode':'playVid','link':link})
            addItemList(url, unescape(title), setArt, 'video', iL, False, 'true')
    
    if '?page='+str(int(p)+1) in resp:
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
        url = build_url({'mode':'epList','page':str(int(p)+1)})
        addItemList(url, '[B][COLOR=yellow]>>> następna strona[/COLOR][/B]', setArt, 'video')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
def playVid(l):
    resp=requests.get(l,headers=hea).text
    resp1=resp.split('pulsembed_embed')[1]
    embURL=re.compile('<a href=\"([^\"]+?)\"').findall(resp1)[0]
    vid=embURL.split('/')[-1]
    
    url='https://player-api.dreamlab.pl/?body[method]=get&body[id]='+vid+'&body[jsonrpc]=2.0&body[params][mvp_id]='+vid+'&body[params][version]=2.0&x-onet-app=player.front.onetapi.pl&content-type=application/jsonp'
    hea_pla={
        'User-Agent':UA,
        'Referer':'https://pulsembed.eu/'
    }
    respPla=requests.get(url,headers=hea_pla).json()
    try:
        stream_url=respPla['result']['formats']['video']['hls'][0]['url'] #to do: sortowanie wg rozdzielczości int ['vertical_resolution']
    except:
        stream_url='' #TO DO: mp4 ---> tablica z jakościami ---> select
    if stream_url!='':
        playerType=addon.getSetting('playerType')
        if playerType=='ISA':
            import inputstreamhelper
            PROTOCOL = 'hls'
            is_helper = inputstreamhelper.Helper(PROTOCOL)
            if is_helper.check_inputstream():
                play_item = xbmcgui.ListItem(path=stream_url)
                play_item.setMimeType('application/xml+dash')
                play_item.setContentLookup(False)
                play_item.setProperty('inputstream', is_helper.inputstream_addon)
                play_item.setProperty("IsPlayable", "true")
                play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                play_item.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+UA)
                play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+UA)
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
        else:
            stream_url+='|User-Agent='+UA
            play_item = xbmcgui.ListItem(path=stream_url)
            play_item.setProperty("IsPlayable", "true")
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    else:
        xbmcgui.Dialog().notification('FAKT', 'Brak źródeł', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
    
        
mode = params.get('mode', None)

if not mode:
    main_menu()
else:
    if mode=='video':
        epList('1')
    
    if mode=='epList':
        page=params.get('page')
        epList(page)
        
    if mode=='playVid':
        link=params.get('link')
        playVid(link)
    
    if mode=='live':
        playerType=addon.getSetting('playerType')
        play_yt('UCR06R8uZqcwfBOlWf-3OWoA',playerType)
        
    if mode=='epg':
        epgData('UCR06R8uZqcwfBOlWf-3OWoA')