# -*- coding: utf-8 -*-
import os
import sys

import requests
from emukodi import xbmc
from emukodi import xbmcgui
from emukodi import xbmcplugin
from emukodi import xbmcaddon
from emukodi import xbmcvfs
import re
import json
import random
import datetime,time
from base64 import b64decode as getData
from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.polsat_news')
PATH=addon.getAddonInfo('path')
img_empty=PATH+'/resources/img/empty.png'
fanart=PATH+'/resources/img/fanart.jpg'
PATH_profile=xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not xbmcvfs.exists(PATH_profile):
    xbmcvfs.mkdir(PATH_profile)


baseurl='https://polsatnews.pl/'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'

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

def directPlayer(u):
    u+='|User-Agent='+UA
    play_item = xbmcgui.ListItem(path=u)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def code_gen(x):
    base='0123456789abcdef'
    code=''
    for i in range(0,x):
        code+=base[random.randint(0,15)]
    return code

def getTime(x):#WP
    diff=(datetime.datetime.now()-datetime.datetime.utcnow())
    t_utc=datetime.datetime(*(time.strptime(x,'%Y-%m-%dT%H:%M:%SZ')[0:6]))
    t_loc=t_utc+diff+datetime.timedelta(seconds=1)
    return t_loc
    
def timeToStr(x,y):#WP
    return x.strftime(y)

def strToTime(x):#WP
    return datetime.datetime(*(time.strptime(x,'%Y-%m-%d')[0:6]))

t='Wwp7J25hbWUnOidQb2xzYXQgTmV3cycsJ3Byb3RvY29sJzonaGxzJywnc3JjJzonaHR0cDovL2hscy5yZWRlZmluZS5wbC8wNDdBQjY1QS8yOTQ2My8wL3R2L3R2L2xpc3QubTN1OCcsJ2lkJzo0MzF9LAp7J25hbWUnOidQb2xzYXQnLCdwcm90b2NvbCc6J21wZCcsJ3NyYyc6J2h0dHBzOi8vbGl2ZS1pcGxhLWUyLTMyLnBsdXNjZG4ucGwvdDMvMjQxMDIvMC9kYXNoX3JlbF9tcC9ERjA2RjNEQi9saXZlLm1wZCcsJ2lkJzo1fSwKeyduYW1lJzonVFY0JywncHJvdG9jb2wnOidtcGQnLCdzcmMnOidodHRwczovL2xpdmUtaXBsYS1lMi0zMi5wbHVzY2RuLnBsLy90My8yNDE4MC8wL2Rhc2hfcmVsX21wLzYzMjEyMDMwL2xpdmUubXBkJywnaWQnOjE4fSwKeyduYW1lJzonVFYgT2themplJywncHJvdG9jb2wnOidtcGQnLCdzcmMnOidodHRwOi8vY2RuLXMtbGIyLnBsdXNjZG4ucGwvY2gvMTUyMzUzMi8zNjYvZGFzaC8yY2YzODNiYi9saXZlLm1wZCcsJ2lkJzozNX0KXQ=='

def main_menu():    
    url='https://www.polsatnews.pl/wideo-lista/'
    resp=requests.get(url,headers=hea).text
    categs=re.compile('<a class=\"section__link\" href=\"([^\"]+?)\">([^<]+?)</a').findall(resp)
    for c in categs:
        mod='itemList'
        if c[1]=='Nasze programy':
            mod='programList'
        addon.setSetting('referer',baseurl)
        
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultAddonVideo.png', 'fanart':fanart}
        url = build_url({'mode':mod,'link':c[0]})
        addItemList(url, cleanText(c[1]), setArt, 'video')
    
    menu_plus=[
        ['Reportaże Interwencji','inter','DefaultAddonVideo.png'],
        ['Materiały Polsat Sport','categs','DefaultAddonVideo.png'],
        ['Wydarzenia24 (shorty)','w24','DefaultAddonVideo.png'],
        ['Halo, tu Polsat','htp','DefaultAddonVideo.png'],
        ['Wyszukiwarka','SEARCH','DefaultAddonsSearch.png'],
        ['Na żywo','liveTV','DefaultTVShows.png'],
        ['Transmisje','live','DefaultTVShows.png'],
        ['Ulubione','favList','DefaultMusicRecentlyAdded.png'],
    ]
    for m in menu_plus:
        iL={}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': m[2], 'fanart':fanart}
        url = build_url({'mode':m[1]})
        addItemList(url,m[0], setArt, 'video', iL)
    
    xbmcplugin.endOfDirectory(addon_handle)

def categs(): #PS
    url='https://www.polsatsport.pl/wideo/'
    resp=requests.get(url,headers=hea).text
    categs=re.compile('<a class=\"section__link\" href=\"([^\"]+?)\">([^<]+?)</a').findall(resp)
    for c in categs:
        mod='itemList'
        if c[1]=='Nasze programy':
            mod='programList'
        addon.setSetting('referer',url)
        
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultAddonVideo.png', 'fanart':fanart}
        url = build_url({'mode':mod,'link':c[0]})
        addItemList(url, cleanText(c[1]), setArt, 'video')
    xbmcplugin.endOfDirectory(addon_handle)    

def itemList(l):
    hea.update({'Referer':addon.getSetting('referer')})
    resp=requests.get(l,headers=hea).text
    resp1=resp.split('class=\"news-list ')[1].split('</section')[0].split('</article>')
    vids=[]
    for r in resp1:
        if 'href' in r:
            link=re.compile('href=\"([^\"]+?)\"').findall(r)[0]
            img=re.compile('data-src=\"([^\"]+?)\"').findall(r)[0]
            name=re.compile('alt=\"([^\"]+?)\"').findall(r)[0]
            date=re.compile('datetime=\"([^\"]+?)\"').findall(r)[0]
            vids.append([name,link,img,date])
    for v in vids:
        img=v[2]
        plot='[B]Data: [/B]'+v[3]
                
        iL={'title': '','sorttitle': '','plot': plot}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
        url = build_url({'mode':'playVid','link':v[1]})
        addItemList(url, cleanText(v[0]), setArt, 'video', iL, False, 'true')
            
    if '>pokaż więcej<' in cleanText(resp):
        nextPageLink=re.compile('data-url=\"([^\"]+?)\"').findall(resp)[0]
        addon.setSetting('referer',l)
                
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
        url = build_url({'mode':'itemListNext','link':nextPageLink})
        addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt)
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def itemListNext(l):
    hea.update({'Referer':addon.getSetting('referer')})
    resp=requests.get(l,headers=hea).json()
    for i in resp['items']:
        img=i['img']['midi']
        plot='[B]Data: [/B]'+datetime.datetime.fromtimestamp(i['timestamp']/1000).strftime('%Y-%m-%d %H:%M')
               
        iL={'title': '','sorttitle': '','plot': plot}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
        url = build_url({'mode':'playVid','link':i['url']})
        addItemList(url, cleanText(i['title']), setArt, 'video', iL, False, 'true')
    
    if 'button' in resp:
        if 'data-url=' in resp['button']: 
            nexturl=re.compile('data-url=\'([^\']+?)\'').findall(resp['button'])[0]
            addon.setSetting('referer',l)
            
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'itemListNext','link':nexturl})
            addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt, 'video')
        elif '/wyszukiwarka/' in resp['button']:
            urlSea=re.compile('href=\"([^\"]+?)\"').findall(resp['button'])[0]
            x=dict(parse_qsl(urlSea.split('?')[-1]))
            query=''
            if 'text' in x:
                query=x['text']
                        
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'search','query':query,'page':'1'})
            addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt, 'video')
            
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def programList(l):   
    def getList(x):
        progs=[]
        for r in x:
            if 'href' in r:
                link=re.compile('href=\"([^\"]+?)\"').findall(r)[0]
                img=re.compile('data-src=\"([^\"]+?)\"').findall(r)[0]
                name=re.compile('alt=\"([^\"]+?)\"').findall(r)[0]
                progs.append([name,link,img])
        return progs
    
    hea.update({'Referer':addon.getSetting('referer')})
    resp=requests.get(l,headers=hea).text
    resp1=resp.split('<section')[1].split('</section')[0].split('</article>')#class=\"news-list 
    for r in getList(resp1):
        name=cleanText(r[0])
        img=r[2]
        iL={'plot':cleanText(r[0])}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
        url = build_url({'mode':'episList','link':r[1],'page':'1'})
        cmItems=[('[B]Dodaj do ulubionych[/B]','RunPlugin(plugin://plugin.video.polsat_news?mode=favAdd&url='+quote(url)+'&name='+quote(name)+'&art='+quote(str(setArt))+'&iL='+quote(str(iL))+')')]
        addItemList(url, name, setArt, 'video', iL, contMenu=True, cmItems=cmItems)
    
    try:
        resp2=resp.split('<section')[2].split('</section')[0].split('</article>')#class=\"news-list 
        for ra in getList(resp2):
            name2=cleanText(ra[0])
            img=ra[2]
            iL={'plot':cleanText(ra[0])}
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
            url = build_url({'mode':'episList','link':ra[1],'page':'1'})
            cmItems=[('[B]Dodaj do ulubionych[/B]','RunPlugin(plugin://plugin.video.polsat_news?mode=favAdd&url='+quote(url)+'&name='+quote(name2)+'&art='+quote(str(setArt))+'&iL='+quote(str(iL))+')')]
            addItemList(url, '[Archiwalny] '+name2, setArt, 'video', iL, contMenu=True, cmItems=cmItems)
    except:
        pass
    
    xbmcplugin.endOfDirectory(addon_handle)
    
def episList(l,p):
    hea.update({'Referer':addon.getSetting('referer')})
    resp=requests.get(l,headers=hea).text
    if '\"pagination\"' in resp:
        resp1=resp.split('class=\"news-list ')[1].split('\"pagination\"')[0].split('</article>')  #.split('</div')[0]
    else:
        resp1=resp.split('class=\"news-list ')[1].split('</main>')[0].split('</article>') 
    vids=[]
    for r in resp1:
        if 'href' in r:
            link=re.compile('href=\"([^\"]+?)\"').findall(r)[0]
            img=re.compile('data-src=\"([^\"]+?)\"').findall(r)[0]
            name=re.compile('alt=\"([^\"]+?)\"').findall(r)[0]
            vids.append([name,link,img])
    for v in vids:
        img=v[2]

        iL={'plot':cleanText(v[0])}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
        url = build_url({'mode':'playVid','link':v[1]})
        addItemList(url, cleanText(v[0]), setArt, 'video', iL, False, 'true')
    
    nextPageLink=re.compile('href=\"([^\"]+?)\" class=\"pagination__link\">'+str(int(p)+1)+'<').findall(resp)
    if len(nextPageLink)==1:
        nexturl=nextPageLink[0]
        addon.setSetting('referer',l)
                
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
        url = build_url({'mode':'episList','link':nexturl,'page':str(int(p)+1)})
        addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt, 'video')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def playVid(l):
    resp=requests.get(l,headers=hea).text
    try:
        url_stream=re.compile('<source data-src=\"([^\"]+?)\"').findall(resp)[0]
    except:
        url_stream=''
    print(url_stream)
    if url_stream!='' and 'mp4' in url_stream:
        url_stream+='|User-Agent='+UA+'&Referer='+baseurl
        play_item = xbmcgui.ListItem(path=url_stream)
        play_item.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    else:
        xbmcgui.Dialog().notification('Polsat News', 'Brak źródła', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())

def search(q,p):
    if q==None:
        q=''
    url='https://www.polsatnews.pl/wyszukiwarka/?text='+q+'&type=vod'
    if p!='1':
        url+='&page='+p
    resp=requests.get(url,headers=hea).text
    if 'search__info-no-results' not in resp:
        resp1=resp.split('\"searchwrap\"')[1].split('\"pagination\"')[0].split('</article')
        vids=[]
        for r in resp1:
            if 'news--video' in r:
                link=re.compile('href=\"([^\"]+?)\"').findall(r)[0]
                img=re.compile('data-src=\"([^\"]+?)\"').findall(r)[0]
                name=re.compile('"news__title\">([^<]+?)<').findall(r)[0]
                try:
                    date=re.compile('datetime=\"([^\"]+?)\"').findall(r)[0]
                except:
                    date=''
                vids.append([name,link,img,date])
        for v in vids:
            img=v[2]
            plot='[B]Data: [/B]'+v[3]
            
            iL={'title': '','sorttitle': '','plot':plot}
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
            url = build_url({'mode':'playVid','link':v[1]})
            addItemList(url, cleanText(v[0]), setArt, 'video', iL, False, 'true')
            
        if 'pagination__link">'+str(int(p)+1)+'<' in resp:
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'search','guery':q,'page':str(int(p)+1)})
            addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt, 'video')
    else:
        xbmcgui.Dialog().notification('Polsat News', 'Brak wyników', xbmcgui.NOTIFICATION_INFO)
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def liveTV():
    chans=eval(getData(t).decode('utf-8'))
    for c in chans:
        iL={'plot':'EPG dostępne z poziomu menu kontekstowego'}
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultTVShows.png', 'fanart':fanart}
        url = build_url({'mode':'playTV','cid':str(c['id'])})
        cmItems=[('[B]EPG[/B]','RunPlugin(plugin://plugin.video.polsat_news?mode=epg&cid='+str(c['id'])+')')]
        addItemList(url, c['name'], setArt, 'video', iL, False, 'true', True, cmItems)
    xbmcplugin.endOfDirectory(addon_handle)

def playTV(cid):
    chans=eval(getData(t).decode('utf-8'))
    chan=[c for c in chans if c['id']==int(cid)][0]
    
    playerType=addon.getSetting('playerType')
    if playerType=='ISA':
        import inputstreamhelper
        PROTOCOL = chan['protocol']
        is_helper = inputstreamhelper.Helper(PROTOCOL)
        if is_helper.check_inputstream():
            play_item = xbmcgui.ListItem(path=chan['src'])
            play_item.setMimeType('application/xml+dash')
            play_item.setContentLookup(False)
            play_item.setProperty('inputstream', is_helper.inputstream_addon)
            play_item.setProperty("IsPlayable", "true")
            if PROTOCOL=='mpd':
                play_item.setProperty('resumeTime','86400')
                play_item.setProperty('totalTime','1')
            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            play_item.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+UA)
            play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+UA)
                      
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    else:
        directPlayer(chan['src'])
    
def epg(cid):
    today=datetime.datetime.now()
    yest=datetime.datetime.now()-datetime.timedelta(days=1)
    t=timeToStr(today,'%Y-%m-%d')
    y=timeToStr(yest,'%Y-%m-%d')
    progs=[]
    url='https://tv.wp.pl/api/v1/program/'+y+'/'+cid
    h={
       'User-Agent':UA,
    }
    resp=requests.get(url,headers=h).json()
    progs=resp['data'][0]['entries']
    url='https://tv.wp.pl/api/v1/program/'+t+'/'+cid
    resp=requests.get(url,headers=h).json()
    progs+=resp['data'][0]['entries']
    epg=''
    for r in progs:
        if getTime(r['end'])>datetime.datetime.now():
            title=r['title']
            if 'episode_title' in r:
                title+=' - ' + r['episode_title']
            if 'genre' in r:
                title+=' [I]('+ r['genre']+')[/I]'
            ts=timeToStr(getTime(r['start']),'%H:%M')
            epg+='[B]%s[/B] %s\n'%(ts,title)
    
    if epg=='':
        epg='Brak danych'
    
    dialog = xbmcgui.Dialog()
    dialog.textviewer('EPG', epg)
    
def live():
    urls=['https://www.polsatnews.pl/wideo-lista/','https://www.polsatsport.pl/wideo/']
    
    '''polsatsport.pl TRANSMISJA'''
    hea.update({'Referer':''})
    resp=requests.get('https://polsatsport.pl',headers=hea).text
    x=re.compile('<article(?:(?!</article>).)*?</article>').findall(resp)
    for xx in x:
        if '>TRANSMISJA<' in xx:
            link=re.compile('href=\"([^\"]+?)\"').findall(xx)[0]
            if link not in urls:
                urls.append(link)
    
    for u in urls:
        hea.update({'Referer':u})
        resp=requests.get(u,headers=hea).text
        if '<iframe class=\"embed' in resp:
            u_ifr=re.compile('<iframe class=\"embed[^=]+?data-src=\"([^\"]+?)\"').findall(resp)
            for ui in u_ifr:
                respI=requests.get(ui,headers=hea).text
                if 'playerDataUrl' in respI:
                    cont_url=re.compile('playerDataUrl: \"([^\"]+?)\"').findall(respI)[0]
                    mediaID=re.compile('mediaId: \"([^\"]+?)\"').findall(respI)[0]
                    cont_url=cont_url.replace('MEDIA_ID',mediaID)
                    respS=requests.get(cont_url,headers=hea).json()
                    if 'error' not in respS:
                        item=respS['mediaItem']
                        title=item['displayInfo']['title']
                        def sortFN(c):
                            return c['size']['width']
                        imgs=item['displayInfo']['thumbnails']
                        imgs.sort(key=sortFN,reverse=True)
                        img=imgs[0]['src']
                        
                        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':img}
                        url = build_url({'mode':'playLive','link':cont_url})
                        addItemList(url, title, setArt, 'video', {}, False, 'true')
    xbmcplugin.endOfDirectory(addon_handle)                    

def playLive(l):
    stream_url=''
    hea.update({'Referer':''})
    l+='?dev=pc&os=windows&player=html&app=firefox&build=2190000'
    resp=requests.get(l,headers=hea).json()
    if 'error' not in resp:
        streams=[[s['url'],s['quality'],s] for s in resp['mediaItem']['playback']['mediaSources'] if s['format']=='200' and len(s['drmTypes'])==0] #HLS
        drm=False
        if len(streams)==0:
            streams=[[s['url'],s['quality'],s] for s in resp['mediaItem']['playback']['mediaSources'] if s['format']=='300' and 'widevine' in s['drmTypes']]
            if len(streams)>0:
                drm=True
            
        if len(streams)!=0:    
            qlts=[s[1] for s in streams]
            select = xbmcgui.Dialog().select('Źródła', qlts)
            if select > -1:
                stream_url=streams[select][0]
                stream_data=streams[select][2]
            else:
                stream_url=streams[0][0]
                stream_data=streams[0][2]
    
    if stream_url!='':
        if drm:
            licURL=stream_data['authorizationServices']['widevine']['getWidevineLicenseUrl']
            deviceid=code_gen(32)+'_'   #'03a06979619f27f43122ddc0f9fce171_'
            keyId=stream_data['keyId']
            mediaid=resp['mediaItem']['playback']['mediaId']['id']
            cpid=resp['mediaItem']['playback']['mediaId']['cpid']
            sourceId=stream_data['id']
            portal=resp['reporting']['gastream']['portal']
            data_lic=quote('{"id":1,"jsonrpc":"2.0","method":"getWidevineLicense","params":{"cpid":'+str(cpid)+',"deviceId":{"type":"other","value":"'+deviceid+'"},"keyId":"'+keyId+'","mediaId":"'+mediaid+'","object":"b{SSM}","sourceId":"'+sourceId+'","userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":2190000,"portal":"'+portal+'","player":"html","widevine":true}}}')
            hea_lic=urlencode({'User-Agent':UA})
            protocol='mpd'
        else:
            protocol='hls'
        
        playerType=addon.getSetting('playerType')
        if playerType=='ISA' or drm:
        
            import inputstreamhelper
            PROTOCOL = protocol
            DRM = 'com.widevine.alpha'
            if drm:
                is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
            else:
                is_helper = inputstreamhelper.Helper(PROTOCOL)
            if is_helper.check_inputstream():
                play_item = xbmcgui.ListItem(path=stream_url)           
                play_item.setMimeType('application/xml+dash')
                play_item.setContentLookup(False)
                play_item.setProperty('inputstream', is_helper.inputstream_addon)
                play_item.setProperty("IsPlayable", "true")
                play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                play_item.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+UA) #K21
                play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+UA)
                play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                play_item.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                play_item.setProperty('resumeTime','86400')
                play_item.setProperty('totalTime','1')
                if drm:
                    play_item.setProperty('inputstream.adaptive.license_type', DRM)
                    play_item.setProperty('inputstream.adaptive.license_key', licURL+'|'+hea_lic+'|'+data_lic+'|JBlicense')
                
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
        
        else:
            directPlayer(stream_url)
 
        
    else:
        xbmcgui.Dialog().notification('Polsat News', 'Brak źródła', xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        
def inter(p):
    h=addon.getSetting('hash')
    if h=='' or h==None:
        addon.setSetting('hash',code_gen(32))
        h=addon.getSetting('hash')
    if p==None:
        p='1'
    url='https://interwencja.polsatnews.pl/search/search?hash='+h+'&platform=1&cfg=interwencja&resultsPerPage=24&text=&src=form&pageNumber='+p+'&pagedType=event&extra_text='
    hea.update({'Referer':'https://interwencja.polsatnews.pl/wyszukiwarka/'})
    resp=requests.get(url,headers=hea).text
    resp1=resp.split('</article>')
    for r in resp1:
        if 'news__link' in r:
            title=re.compile('news__title\">([^<]+?)<').findall(r)[0]
            img=re.compile('data-src=\"([^\"]+?)\"').findall(r)[0]
            plot=re.compile('datetime=\"([^\"]+?)\"').findall(r)[0]
            link=re.compile('href=\"([^\"]+?)\"').findall(r)[0]
            
            iL={'plot':plot}
            setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':fanart}
            url = build_url({'mode':'playVid','link':link})
            addItemList(url, title, setArt, 'video', iL, False, 'true')
            
    if 'pagination__button--next' in resp:
        nextPage=re.compile('pagination__button--next.* href=\"([^\"]+?)\"').findall(resp)[0].split('page=')[1]
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
        url = build_url({'mode':'inter','page':nextPage})
        addItemList(url, '[COLOR=yellow]>>> Następna strona[/COLOR]', setArt)
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
def w24(vid):
    if vid==None:
        vid='0'
    url='https://reels-api.interia.pl/reels/wydarzenia24?lastReelId='+vid+'&packSize=10'
    hea.update({'Referer':'https://www.wydarzenia24.pl/'})
    resp=requests.get(url,headers=hea).json()
    img=PATH+'/resources/img/w24.png'
    for r in resp:
        title=r['name']
        aId=r['attachmentId']
        aExt=r['attachmentExtension']
        
        iL={'plot':title}
        setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':fanart}
        url = build_url({'mode':'playW24','aid':aId,'aext':aExt})
        addItemList(url, title, setArt, 'video', iL, False, 'true')
    
    setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
    url = build_url({'mode':'w24','vid':str(resp[-1]['id'])})
    addItemList(url, '[B][COLOR=yellow]>>> kolejne[/COLOR][/B]', setArt, 'video')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
def playW24(a,e):
    stream_url='https://interia-v.pluscdn.pl/msg-rollup/%s-V1.%s'%(a,e)
    stream_url+='|User-Agent='+UA+'&Referer=https://www.wydarzenia24.pl/'
    
    play_item = xbmcgui.ListItem(path=stream_url)
    play_item.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
def htp():
    url='https://polsathbbtv.pl/polsat_api/halo_tu_polsat/halo_tu_polsat.php'
    h={'User-Agent':UA}
    resp=requests.get(url,headers=h).json()
    for r in resp['items']:
        title=r['video_title']
        img=r['video_image']
        vid=r['video_url']
        
        iL={'plot':title,'title':title}
        setArt={'thumb': img, 'poster': img, 'banner': img, 'icon': img, 'fanart':fanart}
        url = build_url({'mode':'playHtp','vid':vid})
        addItemList(url, title, setArt, 'video', iL, False, 'true')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

        

def cleanText(x):
    rep=[['Å»','Ż'],['Åº','ź'],['Ä','ę'],['Ä','ą'],['Ã³','ó'],['Å¼','ż'],['Å','ł'],['Å','ś'],['Ä','ć'],['&quot;','\"'],['Å','ń'],['Å','Ś'],['\r',''],['\n','']]
    for r in rep:
        x=x.replace(r[0],r[1])
    return x

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
        isPlayable='false'
        isFolder=True
        URL=j[0]
        if 'mode=play' in URL:
            isPlayable='true'
            isFolder=False

        cmItems=[
            ('[B]Usuń z ulubionych[/B]','RunPlugin(plugin://plugin.video.polsat_news?mode=favDel&url='+quote(j[0])+')'),
        ]
        setArt=eval(j[2])
        iL=eval(j[3])
        addItemList(URL, j[1], setArt, 'video', iL, isFolder, isPlayable, True, cmItems)
    
    xbmcplugin.setContent(addon_handle, 'videos')     
    xbmcplugin.endOfDirectory(addon_handle)

def favDel(u):
    fURL=PATH_profile+'ulubione.json'
    js=openJSON(fURL)
    for i,j in enumerate(js):
        if  j[0]==u:
            del js[i]
    saveJSON(fURL,js)
    xbmc.executebuiltin('Container.Refresh()')

def favAdd(u,n,a,i):
    fURL=PATH_profile+'ulubione.json'
    js=openJSON(fURL)
    duplTest=False
    for j in js:
        if j[0]==u:
            duplTest=True
    if not duplTest:
        js.append([u,n,a,i])
        xbmcgui.Dialog().notification('Polsat News&Sport', 'Dodano do ulubionych', xbmcgui.NOTIFICATION_INFO)
    else:
        xbmcgui.Dialog().notification('Polsat News&Sport', 'Materiał jest już w ulubionych', xbmcgui.NOTIFICATION_INFO)
    saveJSON(fURL,js)



mode = params.get('mode', None)

if not mode:
    main_menu()
else:
    if mode=='itemList':
        link=params.get('link')
        itemList(link)
    
    if mode=='itemListNext':
        link=params.get('link')
        itemListNext(link)
    
    if mode=='programList':
        link=params.get('link')
        programList(link)
        
    if mode=='episList':
        link=params.get('link')
        page=params.get('page')
        episList(link,page)
    
    if mode=='playVid':
        link=params.get('link')
        playVid(link)
    
    if mode=='SEARCH':
        query=xbmcgui.Dialog().input(u'Szukaj, Podaj frazę:', type=xbmcgui.INPUT_ALPHANUM)
        if query:
           search(query,'1')
        else:
            xbmcplugin.endOfDirectory(addon_handle)
        main_menu()
    
    if mode=='search':
        query=params.get('query')
        page=params.get('page')
        search(query,page)

    if mode=='liveTV':
        liveTV()
        
    if mode=='playTV':
        cid=params.get('cid')
        playTV(cid)
    
    if mode=='epg':
        cid=params.get('cid')
        epg(cid)
    
    if mode=='inter':
        page=params.get('page')
        inter(page)
        
    if mode=='w24':
        vid=params.get('vid')
        w24(vid)
        
    if mode=='playW24':
        aid=params.get('aid')
        aext=params.get('aext')
        playW24(aid,aext)
        
    if mode=='htp':
        htp()
    
    if mode=='playHtp':
        vid=params.get('vid')
        directPlayer(vid)
        
    if mode=='categs':
        categs()
    
    if mode=='live':
        live()
        
    if mode=='playLive':
        link=params.get('link')
        playLive(link)
    
    #FAV
    if mode=='favList':
        favList()
        
    if mode=='favDel':
        url=params.get('url')
        favDel(url)
        
    if mode=='favAdd':
        u=params.get('url')
        n=params.get('name')
        a=params.get('art')
        i=params.get('iL')
        favAdd(u,n,a,i)
    