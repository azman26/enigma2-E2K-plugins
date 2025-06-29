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
import base64
import unicodedata
import json

from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl
'''
import locale
locale.setlocale(locale.LC_COLLATE, "pl_PL")#pl_PL.UTF-8
'''

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.esesja')
PATH=addon.getAddonInfo('path')
PATH_profile=xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not xbmcvfs.exists(PATH_profile):
    xbmcvfs.mkdir(PATH_profile)
img_empty=PATH+'/resources/empty.png'
img_addon=PATH+'/icon.png'

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
baseurl='https://esesja.tv/'
hea={
    'User-Agent':UA,
    'Referer':baseurl
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
    
def ISAplayer(protocol, stream_url, subt):
    subActive=False
    mimeType={'hls':'application/x-mpegurl','mpd':'application/xml+dash'}
    import inputstreamhelper
    PROTOCOL = protocol
    is_helper = inputstreamhelper.Helper(PROTOCOL)
    if is_helper.check_inputstream():
        play_item = xbmcgui.ListItem(path=stream_url)
        play_item.setMimeType(mimeType[protocol])
        play_item.setContentLookup(False)
        play_item.setProperty('inputstream', is_helper.inputstream_addon)
        play_item.setProperty("IsPlayable", "true")
        play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        play_item.setProperty('inputstream.adaptive.stream_headers', urlencode(hea))
        play_item.setProperty('inputstream.adaptive.manifest_headers', urlencode(hea)) #K21
        if subt!='':
            play_item.setSubtitles([baseurl[:-1]+subt])
            subActive=True
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
               
        if subActive==True:
            while not xbmc.Player().isPlaying():
                xbmc.sleep(100)
            xbmc.Player().showSubtitles(True)
        

def directPlayer(stream_url,subt):
    subActive=False
    
    play_item = xbmcgui.ListItem(path=stream_url+'|'+urlencode(hea))
    play_item.setProperty("IsPlayable", "true")
    if subt!='':
        play_item.setSubtitles([baseurl[:-1]+subt])
        subActive=True
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
    if subActive==True:
        while not xbmc.Player().isPlaying():
            xbmc.sleep(100)
        xbmc.Player().showSubtitles(True)

def main_menu():
    sources=[
        ['Na żywo','live','DefaultTVShows.png'],
        ['Archiwum','archive','DefaultYear.png'],
        ['Transmisje wg miejscowości','countries','DefaultCountry.png'],
        ['ULUBIONE','favList','DefaultMusicRecentlyAdded.png']
    ]
    for s in sources:
        setArt={'icon': s[2]}
        url = build_url({'mode':s[1]})       
        addItemList(url, s[0], setArt)
        
    if addon.getSetting('videoContView')=='true':
        xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def getCountry(x):
    r=['Urząd Miasta i Gminy', 'Rada Miasta i Gminy', 'Metropolitalny Związek Komunikacyjny', 'Związek Celowy Gmin MG-6', 'Związek Gmin', 'Rada Dzielnicy', 'Rada Miejska', 'Rada Miasta', 'Rada Powiatu', 'Rada Gminy', 'Sejmik Województwa', 'Starostwo Powiatowe', 'Urząd Gminy', ' w ']
    for rr in r:
        x=x.replace(rr,'')
    
    return x.lstrip()

def getLive(): #helper
    resp=requests.get(baseurl,headers=hea).text
    ssid=re.compile('checkliveapps\(\'([^\']+?)\'\)').findall(resp)[0]
    
    url=baseurl+'ajax/appslive_json'
    data={
        'ssid':ssid,
    }
    resp=requests.post(url,headers=hea,data=data).json()
    return resp
    
def addLive(r,label=False): #helper
    name=r['channel']
    if label:
        name+=' [COLOR=yellow][transmisja na żywo][/COLOR]'
    img=r['image']
    link=r['url']
    viewers=r['viewers']
    startTime=r['time']
    
    plot='[B]%s[/B]\n\n'%(name)
    plot+='[B]Rozpoczęto:[/B] %s\n'%(startTime)
    plot+='[B]Oglądający:[/B] %s'%(viewers)
    
    setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':''}
    iL={'title': name,'plot':plot,'mediatype':'video'}
    URL=build_url({'mode':'playVid','link':link})
    addItemList(URL, name, setArt, 'video', iL, False, 'true')
    

def live():
    liveData=getLive()['live']
    
    def sortFN(i):
        #return locale.strxfrm(getCountry(i['channel']))
        return getCountry(i['channel'])

    liveData.sort(key=sortFN,reverse=False)
    
    for r in liveData:
        addLive(r)

    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
        
def archive(p,u=None):
    url=baseurl if u==None else baseurl[:-1]+u
    #live
    if p==None and u!=None:
        liveData=getLive()['live']
        liveTrans=[l for l in liveData if l['channel_url']==u]
        if len(liveTrans)>0:
            live=liveTrans[0]
            addLive(live,label=True)
                
    if p!=None:
        url+=p
    
    resp=requests.get(url,headers=hea).content
    resp=resp.decode()
    resp1=resp.split('id=\"transmisje\"')[1].split('<ul')[0].split('class=\'transmisja\'')
    vids=[]
    for r in resp1:
        if 'publisher' in r:
            link,title=re.compile('\'title\'><a href=\"([^\"]+?)\">([^<]+?)</a').findall(r)[0] #link bez baseurl
            img=re.compile('class=\'img\'.*:url\(\"([^"]+?)\"\)').findall(r)[0]
            try:
                date=re.compile('calendar\'></i>([^<]+?)<').findall(r)[0]
            except:
                date=re.compile('clock\'></i>([^<]+?)<').findall(r)[0]
            views=re.compile('views\'></i>([^<]+?)<').findall(r)[0]
            
            plot='[B]%s[/B]\n\n'%(title)
            plot+='[B]Dodano:[/B] %s\n'%(date)
            plot+='[B]Odsłon:[/B] %s'%(views)
            
            setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':''}
            iL={'title': title,'plot':plot,'mediatype':'video'}
            URL=build_url({'mode':'playVid','link':link})
            cmItems=[('[B]Dodaj do ulubionych[/B]','RunPlugin(plugin://plugin.video.esesja?mode=favAdd&url='+quote(URL)+'&title='+quote(title)+'&iL='+quote(str(iL))+'&setart='+quote(str(setArt))+')')]
            addItemList(URL, title, setArt, 'video', iL, False, 'true', True, cmItems)
            
    page=p if p!=None else '1'
    resp2=resp.split('\'pager\'')[1].split('</ul')[0]
    if '>następne<' in resp2:
        next_page=str(int(page)+1)
        u='' if u==None else u
        
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':''}
        url = build_url({'mode':'archive','page':next_page,'link':u})
        addItemList(url, '[B][COLOR=yellow]>>> Następna strona[/COLOR][/B]', setArt, 'video')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def countries():
    url=baseurl+'assets/autocomplete.js'
    resp=requests.get(url,headers=hea).text
    data=re.compile('var countries = ([^;]+?);').findall(resp)[0]
    data=data.replace('data','\"data\"').replace('value','\"value\"').replace('\'','\"')
    urzedy=json.loads(data)
    for u in urzedy:
        name=u['value']
        link='/transmisje_z_obrad/'+u['data']+'.htm'
        img=img_addon
        
        iL={'title':name,'plot':name}
        setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':''}
        URL=build_url({'mode':'archive','link':link})
        cmItems=[('[B]Dodaj do ulubionych[/B]','RunPlugin(plugin://plugin.video.esesja?mode=favAdd&url='+quote(URL)+'&title='+quote(name)+'&iL='+quote(str(iL))+'&setart='+quote(str(setArt))+')')]
        addItemList(URL, name, setArt, 'video', iL, contMenu=True, cmItems=cmItems)
        
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def playVid(l):
    url=baseurl[:-1]+l
    if 'transmisja_na_zywo' not in url:
        url+='?hd=1'
    resp=requests.get(url,headers=hea).text
    stream_url=''
    subtitles=''
    if 'videourl=' in resp:
        stream_url=re.compile('videourl=\'([^\']+?)\'').findall(resp)[0]
        subt=re.compile('kind=\"subtitles\" src=\"([^"]+?)\" ').findall(resp)
        if len(subt)==1:
            subtitles=subt[0]
            
    if stream_url!='':
        if '.m3u' in stream_url:
            ISAplayer('hls',stream_url,subtitles)
        else:
            directPlayer(stream_url,subtitles)
        
    else:
        xbmcgui.Dialog().notification('eSesja.tv', 'Brak źródła lub transmisja nie jest prowadzona', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())

    
#FAV            
def openJSON(u):
    try:
        f=open(u,'r',encoding = 'utf-8')
    except:
        f=open(u,'w+',encoding = 'utf-8')
    cont=f.read()
    f.close()
    try:
        js=eval(cont)
    except:
        js=[]
    return js
    
def saveJSON(u,j):
    with open(u, 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=4)

def favList():
    fURL=PATH_profile+'ulubione.json'
    js=openJSON(fURL)
    for j in js:
        if 'playVid' in j[0]:
            isPlayable='true'
            isFolder=False
        else:
            isPlayable='false'
            isFolder=True

        contMenu=True
        cmItems=[
            ('[B]Usuń z ulubionych[/B]','RunPlugin(plugin://plugin.video.esesja?mode=favDel&url='+quote(j[0])+')'),
        ]
        setArt=eval(j[3])
        iL=eval(j[2])
        addItemList(j[0], j[1], setArt, 'video', iL, isFolder, isPlayable, contMenu, cmItems)
        
    xbmcplugin.setContent(addon_handle, 'videos')     
    xbmcplugin.endOfDirectory(addon_handle)

def favDel(c):
    fURL=PATH_profile+'ulubione.json'
    js=openJSON(fURL)
    for i,j in enumerate(js):
        if  j[0]==c:
            del js[i]
    saveJSON(fURL,js)
    xbmc.executebuiltin('Container.Refresh()')

def favAdd(u,t,iL,art):
    fURL=PATH_profile+'ulubione.json'
    js=openJSON(fURL)
    duplTest=False
    for j in js:
        if j[0]==u:
            duplTest=True
    if not duplTest:
        js.append([u,t,iL,art])
        xbmcgui.Dialog().notification('eSesja.tv', 'Dodano do ulubionych', xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcgui.Dialog().notification('eSesja.tv', 'Materiał jest już w ulubionych', xbmcgui.NOTIFICATION_INFO)
    saveJSON(fURL,js)

mode = params.get('mode', None)

if not mode:        
    main_menu()

else:

    if mode=='live':
        live()
    
    if mode=='archive':
        page=params.get('page')
        link=params.get('link')
        archive(page,link)
  
    if mode=='countries':
        countries()
    
    if mode=='playVid':
        link=params.get('link')
        playVid(link)
    
    #FAV    
    if mode=='favList':
        favList()
        
    if mode=='favDel':
        u=params.get('url')
        favDel(u)
        
    if mode=='favAdd':
        u=params.get('url')
        t=params.get('title')
        iL=params.get('iL')
        setart=params.get('setart')
        favAdd(u,t,iL,setart)
