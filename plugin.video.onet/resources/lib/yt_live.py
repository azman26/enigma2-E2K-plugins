# -*- coding: utf-8 -*-
import os
import sys

import urllib
import requests
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import urllib3
import re
import json
import datetime
from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl
from urllib.request import Request, urlopen

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.onet')
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
hea={
    'User-Agent':UA
}

def build_url(query):
    return base_url + '?' + urlencode(query)

def get_url_stream(cid):
    
    def isLive(x): #helper
        result=False
        labels=x['richItemRenderer']['content']['videoRenderer']['thumbnailOverlays']
        for l in labels:
            if 'thumbnailOverlayTimeStatusRenderer' in l:
                if l['thumbnailOverlayTimeStatusRenderer']['style']=='LIVE':
                    result=True
        
        return result
    
    liveList=[]
    stream_url=''
    
    '''Sprawdzenie ilości live streams'''
    url='https://youtube.com/channel/'+cid+'/streams'
    resp = urllib.request.urlopen(Request(url,headers=hea))
    rf = resp.read().decode('utf-8')
    
    jsn=re.compile('ytInitialData = (.*);</script>').findall(rf)[0]
    jsn=jsn.split(';</script')[0]
    j=json.loads(jsn)
    sections=j['contents']['twoColumnBrowseResultsRenderer']['tabs']
    streamSect0=[s for s in sections if 'tabRenderer' in s]
    streamSect=[s['tabRenderer']['content']['richGridRenderer']['contents'] for s in streamSect0 if s['tabRenderer']['title']=='Na żywo']
    if len(streamSect)==1:
        liveItems=streamSect[0]
        for i in liveItems:
            if 'richItemRenderer' in i:
                if isLive(i):
                    vidID=i['richItemRenderer']['content']['videoRenderer']['videoId']
                    vidTitle=i['richItemRenderer']['content']['videoRenderer']['title']['runs'][0]['text']
                    liveList.append([vidID,vidTitle])
                
    '''Wybór transmisji (użytkownik)'''
    if len(liveList)>1:
        liveLabels=[l[1] for l in liveList]
        select=xbmcgui.Dialog().select('Transmisje', liveLabels)
        if select>-1:
            url='https://www.youtube.com/watch?v='+liveList[select][0]
            resp = urllib.request.urlopen(Request(url,headers=hea))
            rf = resp.read().decode('utf-8')
            u=re.compile('\"hlsManifestUrl\":\"([^\"]+?)\"').findall(rf)
            if len(u)>0:
                stream_url=u[0]
    
            
    '''Z zakładki live'''
    if stream_url=='':
        url='https://youtube.com/channel/'+cid+'/live'
        resp = urllib.request.urlopen(Request(url,headers=hea))
        rf = resp.read().decode('utf-8')
        u=re.compile('\"hlsManifestUrl\":\"([^\"]+?)\"').findall(rf)
        if len(u)>0:
            stream_url=u[0]
    return stream_url

def ISAplayer(u):
    import inputstreamhelper
    PROTOCOL = 'hls'
    is_helper = inputstreamhelper.Helper(PROTOCOL)
    if is_helper.check_inputstream():
        play_item = xbmcgui.ListItem(path=u)
        play_item.setMimeType('application/xml+dash')
        play_item.setContentLookup(False)
        play_item.setProperty('inputstream', is_helper.inputstream_addon)
        play_item.setProperty("IsPlayable", "true")
        play_item.setProperty('inputstream.adaptive.play_timeshift_buffer', 'false')
        play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+UA)
        play_item.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+UA) #K21
        play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def directPlayer(u):
    play_item = xbmcgui.ListItem(path=u)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def play_yt(cid,playerType):
    url_stream = get_url_stream(cid)
    if url_stream!='':
        if playerType=='ISA':
            ISAplayer(url_stream)
        elif playerType=='ffmpeg':
            url_stream+='|User-Agent='+UA
            directPlayer(url_stream)    
    else:
        xbmcgui.Dialog().notification('YT Live', 'Emisja na żywo nie jest obecnie prowadzona.', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())

def epgData(cid):
    plot=''
    url='https://youtube.com/channel/'+cid+'/streams'
    page_ch = urllib.request.urlopen(Request(url,headers=hea))
    rf = page_ch.read().decode('utf-8')
    jsn=re.compile('ytInitialData = (.*);</script>').findall(rf)[0]
    jsn=jsn.split(';</script>')[0]
    j=json.loads(jsn)
    categs=j['contents']['twoColumnBrowseResultsRenderer']['tabs']
    items=[]
    for c in categs:
        if 'tabRenderer' in c:
            if c['tabRenderer']['title']=='Na żywo': #ver. ang 'Live' "Na żywo"
                vids=c['tabRenderer']['content']['richGridRenderer']['contents']
                for v in vids:
                    if 'richItemRenderer' in v:
                        vid= v['richItemRenderer']['content']['videoRenderer']
                        if 'upcomingEventData' in vid:
                            tmstmp=int(vid['upcomingEventData']['startTime'])
                            date=datetime.datetime.fromtimestamp(tmstmp).strftime('%Y-%m-%d %H:%M')
                            name=vid['title']['runs'][0]['text']
                            items.append([tmstmp,date,name])
                        else:
                            icon=vid['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['style']
                            if icon=='LIVE':
                                name=vid['title']['runs'][0]['text']
                                date='TRWA'
                                tmstmp=0
                                items.append([tmstmp,date,name])
    def sortFN(i):
        return i[0]
    items.sort(key=sortFN,reverse=False)
    for i in items:
        plot+='[B]'+i[1]+'[/B]  '+i[2]+'\n'
    
    dialog = xbmcgui.Dialog()
    if plot=='':
        plot='Brak informacji'
    dialog.textviewer('Planowane transmisje', plot) 
            