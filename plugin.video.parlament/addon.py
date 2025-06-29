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
#import base64
import json
#import random
import time
import datetime
from html import unescape
from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.parlament')
PATH=addon.getAddonInfo('path')
img_path=PATH+'/resources/img/'
img_empty=img_path+'empty.png'
img_senat=img_path+'senat.png'
fanart=img_path+'fanart.jpg'
mainIcon=PATH+'icon.png'

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
hea={
    'User-Agent':UA,
}

apiSenat='https://av8.senat.pl/fo-api/'
senatBaseurl='https://www.senat.gov.pl/'

#SSL
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
class CustomCipherAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers="DEFAULT:!DHE:!SHA1:!SHA256:!SHA384")
        context.set_ecdh_curve("prime256v1")
        kwargs['ssl_context'] = context
        return super(CustomCipherAdapter, self).init_poolmanager(*args, **kwargs)

sess = requests.Session()
sess.mount("https://", CustomCipherAdapter())

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
    
def ISAplayer(protocol,stream_url):
    import inputstreamhelper
    
    PROTOCOL = protocol
    DRM = 'com.widevine.alpha'
    is_helper = inputstreamhelper.Helper(PROTOCOL)
    
    if is_helper.check_inputstream():
        play_item = xbmcgui.ListItem(path=stream_url)                     
        play_item.setMimeType('application/xml+dash')
        play_item.setContentLookup(False)
        play_item.setProperty('inputstream', is_helper.inputstream_addon)        
        play_item.setProperty("IsPlayable", "true")
        play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+UA)        
        play_item.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent='+UA)
        play_item.setProperty('inputstream.adaptive.manifest_config','{\"timeshift_bufferlimit\":86400}')
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def directPlayer(stream_url) :
    stream_url+='|User-Agent='+UA
    play_item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def cleanTags(x):
    f=re.compile('<.*?>') 
    return re.sub(f, '', x)
    
def addZero(x):
    result= '0'+x.strip() if int(x)<=9 else x
    return result

def main_menu():
    menu=[
        ['SEJM','sejmCateg','sejm.png'],
        ['SENAT','senatCateg','senat.png']
    ]
    
    for m in menu:
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_path+m[2], 'fanart':fanart}
        url = build_url({'mode':m[1]})
        addItemList(url, m[0], setArt)
    xbmcplugin.endOfDirectory(addon_handle)

def sejmCateg():
    categs=[
        ['TRANSMISJE','trans'],
        ['ARCHIWUM - X kadencja','arch10'],
        ['ARCHIWUM - IX kadencja','arch9'],
    ]
    
    for c in categs:
        setArt={'thumb': '', 'poster': img_path+'sejm.png', 'banner': '', 'icon': 'OverlayUnwatched.png', 'fanart':fanart}
        url = build_url({'mode':'sejmSubcategs','categ':c[1]})
        addItemList(url, c[0], setArt)
    xbmcplugin.endOfDirectory(addon_handle)

def sejmSubcategs(c):
    items=[
        ['Wszystkie',''],
        ['Posiedzenie sejmu','posiedzenie'],
        ['Posiedzenia komisji','komisja'],
        ['Posiedzenia podkomisji','podkomisja'],
        ['Konferencje','konferencja'],
        ['Inne','inne']
    ]
    
    if c=='trans':
        k='10'
    else:
        k=c.replace('arch','')
        c='arch'
        items.append(['Wyszukiwarka','search'])
    
    for i in items:
        icon='OverlayUnwatched.png' if i[1]!='search' else 'DefaultAddonsSearch.png'
        setArt={'thumb': '', 'poster': img_path+'sejm.png', 'banner': '', 'icon': icon, 'fanart':fanart}
        url = build_url({'mode':'sejmItemsList','categ':c,'subcateg':i[1],'page':'1','kad':k})
        addItemList(url, i[0], setArt)
    xbmcplugin.endOfDirectory(addon_handle)


def itemList(j,k,s=None):
    jl=json.loads(j)

    if 'params' in jl: #manifest mpd/hls
        params=jl['params']
        
        icon='DefaultTVShows.png' if jl['status']=='VIDEO_PLAYING' else 'DefaultAddonVideo.png'
        unid=jl['unid']
        srcType='hls'
        

    elif jl['videoFile'] !='': #plik mp4
        unid=jl['videoFile']
        srcType='mp4'
        icon='DefaultAddonVideo.png'
        
    desc=unescape(jl['desc']).replace('<br/>','\n') #przedmiot posiedzenia
    title=jl['title'] #np. rodzaj komisji
    try:
        plot='[B]'+title+'[/B]\n'+desc+'\n'+'[B]Rozpoczęcie: [/B]'+params['start']+'\n'+'[B]Zakończenie: [/B]'+params['stop']
        TITLE=title + ' | ' + params['start']
    except:
        plot='[B]'+title+'[/B]\n'+desc+'\n'+'[B]Rozpoczęcie: [/B]'+jl['start']+'\n'+'[B]Zakończenie: [/B]-'
        TITLE=title + ' | ' + jl['start']
    
    cmItems=[]
    if s=='posiedzenie':
        ts=dateToTmp(jl['params']['start'])
        te=dateToTmp(jl['params']['stop'])
        cmItems=[
            ('[B]Harmonogram: wystąpienia[/B]','Container.Update(plugin://plugin.video.parlament?mode=sejmSchedule&type=osoby&ts='+ts+'&te='+te+'&link='+unid+'&srcType='+srcType+'&kad='+k+')'),
            ('[B]Harmonogram: sprawy[/B]','Container.Update(plugin://plugin.video.parlament?mode=sejmSchedule&type=sprawy&ts='+ts+'&te='+te+'&link='+unid+'&srcType='+srcType+'&kad='+k+')'),
        ]
    
    iL={'title': TITLE,'sorttitle': TITLE,'plot': plot}
    setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': icon, 'fanart':fanart}
    url = build_url({'mode':'sejmPlay','link':unid,'srcType':srcType,'kad':k})
    addItemList(url, TITLE, setArt, 'video', iL, False, 'true', True, cmItems)
    
def sejmItemsList(c,s,p,k,y):
    s='' if s==None else s
    y='' if y==None else y   
        
    if c=='trans':
        url='https://sejm.gov.pl/Sejm'+k+'.nsf/transmisje.xsp#'
    else:
        url='https://sejm.gov.pl/Sejm'+k+'.nsf/transmisje_arch.xsp?page='+str(p)
        if s!='':
            url+='&type='+s
        if y!='':
            url+='&rok='+y

    resp=sess.get(url,headers=hea).text
    resp1=''
    if c=='trans':
        try:
            tr_block=resp.split('listaTransmisji')[1].split('</ul>')[0]
            tr=tr_block.split('</li>')
            for t in tr:
                if s!='':
                    if 'class=\"'+s+'\"' in t:
                        resp1 +=t
                else:
                    resp1 +=t
        except:
            pass
    else:
        resp1=resp
    
    jsn=re.compile('json hidden\">([^<]+?)<').findall(resp1)
    for j in jsn:
        itemList(j,k,s)

    if  c=='arch': # sprawdzić czy transmisje nie mają stron 
        if 'aria-label=\"Nast&#281;pna strona\"' in resp:
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'sejmItemsList','categ':c,'subcateg':s,'page':str(int(p)+1),'kad':k,'year':y})
            addItemList(url, '[B][COLOR=yellow]>>> Następna strona[/B][/COLOR]', setArt)
        else:
            def getYear(y,years,k):
                i=years[k].index(y)
                result=years[k][i+1] if i+1<=len(years[k])-1 else None
                return result
            
            years={'10':['2024','2023'],'9':['2022','2021','2020','2019']}
            year=years[k][0] if y=='' else getYear(y,years,k)
            if year!=None:
                setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultYear.png', 'fanart':fanart}
                url = build_url({'mode':'sejmItemsList','categ':c,'subcateg':s,'page':'1','kad':k,'year':year})
                addItemList(url, 'Rok [B]%s[/B]'%(year), setArt)
                
                
        xbmcplugin.setContent(addon_handle, 'videos')
    
    xbmcplugin.endOfDirectory(addon_handle)


def sejmSchedule(t,ts,te,l,st,k):
    url='https://sejm.c.blueonline.tv/api/events/?start='+ts+'&stop='+te
    resp=sess.get(url,headers=hea).json()
    ct='speakers' if t=='osoby' else 'agenda'
    for r in resp[ct]:
        title=r['text']
        s=str(r['start_time'])
        e=str(r['stop_time'])
        dur=int((int(e)-int(s))/1000)
        
        iL={'title': title,'sorttitle': title,'plot': title,'duration':dur} #to do: duration
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultAddonVideo.png', 'fanart':fanart}
        url = build_url({'mode':'sejmPlay','link':l,'srcType':st,'kad':k,'ts':s,'te':e})
        addItemList(url, title, setArt, 'video', iL, False, 'true')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)    

def dateToTmp(x,f='%Y-%m-%d %H:%M:%S'): #2024-06-10 09:59:38
    return str(int(datetime.datetime(*(time.strptime(x,f)[0:6])).timestamp()*1000))
    

def sejmPlay(u,st,k,ts,te):
    stream_url=''
    if st=='mp4':
        stream_url='https://itv.sejm.gov.pl/kadencja'+k+'/mp4/'+u+'.mp4'
        directPlayer(stream_url)
    elif st=='hls':
        url='https://sejm.gov.pl/Sejm'+k+'.nsf/VideoFrame.xsp/'+u
        resp=sess.get(url,headers=hea).text
        baseStream=re.compile('api_url: \"([^"]+?)\"').findall(resp)[0]
        camera=re.compile('cameras: \[([^]]+?)\]').findall(resp)[0]
        camera=eval('[%s]'%(camera))#[0]
        period=re.compile('timeShift: {([^}]+?)}').findall(resp)[0]
        
        if len(camera)>1:
            select=xbmcgui.Dialog().select('Kamera', camera)
            if select > -1:
                cam=camera[select]
            else:
                cam=camera[0]
        else:
            cam=camera[0]

        if 'blueonline' in baseStream:
            stream_url=baseStream+'/stream/'+cam+'/'+u+'/manifest.mpd'
            if ts==None:
                if 'start' in period:
                    start=re.compile('start: \"([^"]+?)\"').findall(period)
                    if len(start)>0:
                        stream_url+='?start='+dateToTmp(start[0])
                if 'stop' in period:
                    stop=re.compile('stop: \"([^"]+?)\"').findall(period)
                    if len(stop)>0:
                        stream_url+='&stop='+dateToTmp(stop[0])
            else: #from schedule
                stream_url+='?start='+ts+'&stop='+te
        
        if stream_url!='':
            print(stream_url)
            ISAplayer('mpd',stream_url)
        else:
            xbmcgui.Dialog().notification('Parlament', 'Brak źródła', xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
            

def searchSejm(s,p,k):
    filtry=eval(addon.getSetting('filtry'))
    filters=[
        ['Dowolne słowa','phrase'],
        ['Typ transmisji','trType'],
        ['Data (od)','since'],
        ['Data (do)','till']
    ]
    for f in filters:
        fLabel='[COLOR=cyan][B]%s[/B][/COLOR]: %s'%(f[0],filtry[f[1]])
        
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultTags.png', 'fanart':fanart}
        url = build_url({'mode':'filtersSejm','type':f[1]})
        addItemList(url, fLabel, setArt, isF=False)
    
    setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
    url = build_url({'mode':'searchResultSejm', 'kad':k, 'page':p })
    addItemList(url, '[B][COLOR=yellow]>>> SZUKAJ[/COLOR][/B]', setArt)
    
    xbmcplugin.endOfDirectory(addon_handle)

def filtersSejm(t):
    def dateVerify(s):
        res=False
        try:
            d=datetime.datetime(*(time.strptime(s, "%Y-%m-%d")[0:6])).timestamp()
            res=True if d<time.time() else False
        except:
            pass
        return res
    
    filtry=eval(addon.getSetting('filtry'))
    if t=='phrase':
        p=xbmcgui.Dialog().input(u'Szukaj, Fraza:', type=xbmcgui.INPUT_ALPHANUM)
        if p:
            filtry['phrase']=p
    
    elif t=='trType':
        types=['wszystkie','posiedzenia Sejmu','posiedzenia komisji','posiedzenia podkomisji','konferencje prasowe','brefingi Marszałka Sejmu']
        select=xbmcgui.Dialog().select('Typ transmisji', types)
        if select > -1:
            filtry['trType']=types[select]
    
    elif t=='since':
        p=xbmcgui.Dialog().input(u'Szukaj, Data (od) w formacie yyyy-mm-dd:', type=xbmcgui.INPUT_ALPHANUM)
        if p and dateVerify(p):
            filtry['since']=p
    
    elif t=='till':
        p=xbmcgui.Dialog().input(u'Szukaj, Data (do) w formacie yyyy-mm-dd:', type=xbmcgui.INPUT_ALPHANUM)
        if p and dateVerify(p):
            filtry['till']=p
        
    addon.setSetting('filtry',str(filtry))
    xbmc.executebuiltin('Container.Refresh')

def searchResultSejm(k,p,Sess,sessID):
    filtry=eval(addon.getSetting('filtry'))
    url='https://sejm.gov.pl/Sejm'+k+'.nsf/transmisje_arch.xsp?view=S'
    if Sess==None and sessID==None:
        resp=sess.get(url,headers=hea).text
        Sess=re.compile('id1__VUID\" value=\"([^"]+?)\"').findall(resp)[0]
        sessID=re.compile('SessionID=([^"]+?)\"').findall(resp)[0]
    dateFil='='
    if filtry['since']!='' and filtry['till']!='':
        dateFil='<>'
    elif filtry['since']!='' and filtry['till']=='':
        dateFil='>'
    elif filtry['since']=='' and filtry['till']!='':
        dateFil='<'
    types={'wszystkie':'','posiedzenia Sejmu':'posiedzenia','posiedzenia komisji':'komisje','posiedzenia podkomisji':'podkomisje','konferencje prasowe':'konferencje','brefingi Marszałka Sejmu':'brifingi'}
    trType='' if filtry['trType']=='' else types[filtry['trType']]
    ids={'10':['_id100:_id101:_id104','_id100:_id101:_id139'],'9':['_id101:_id102:_id105','_id101:_id102:_id140']} 
    files={
        'view:_id1:_id3:facetMain:'+ids[k][0]+':edtSearch': (None, filtry['phrase']),#phrase
        'view:_id1:_id3:facetMain:'+ids[k][0]+':cusTransmRodzaj': (None, trType),#type
        'view:_id1:_id3:facetMain:'+ids[k][0]+':cdrData:cbData': (None, dateFil),#
        'view:_id1:_id3:facetMain:'+ids[k][0]+':cdrData:dtpData1': (None, filtry['since']),#since
        'view:_id1:_id3:facetMain:'+ids[k][0]+':cdrData:dtpData2': (None, filtry['till']),#till
        '$$viewid': (None, Sess),
        '$$xspsubmitid': (None, 'view:_id1:_id3:facetMain:'+ids[k][1]),
        '$$xspexecid': (None, ''),
        '$$xspsubmitvalue': (None, ''),
        '$$xspsubmitscroll': (None, '0|0'),
        'view:_id1': (None, 'view:_id1'),
    }
    if p!='1':
        url+='&page='+p
    hea.update({'referer':url})
    cookies={'SessionID':sessID}
    resp=sess.post(url,headers=hea,cookies=cookies,files=files).text
    jsn=re.compile('json hidden\">([^<]+?)<').findall(resp)
    for j in jsn:
        itemList(j,k)
    
    if 'page='+str(int(p)+1) in resp:
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
        url = build_url({'mode':'searchResultSejm', 'kad':k, 'page':str(int(p)+1),'sess':Sess,'sessID':sessID })
        addItemList(url, '[B][COLOR=yellow]>>> Następna strona[/B][/COLOR]', setArt)
    
    xbmcplugin.setContent(addon_handle, 'videos')   
    xbmcplugin.endOfDirectory(addon_handle)

#SENAT    
def senatCateg():
    categs=[
        ['TRANSMISJE','senatItemsList','trans'],
        ['ARCHIWUM','senatItemsList','arch'],
        ['Wyszukiwarka posiedzeń Senatu','searchSenatFilters','ps'],
        ['Wyszukiwarka posiedzeń komisji','searchSenatFilters','pk'],
    ]
    
    for c in categs:
        img='DefaultAddonsSearch.png' if 'Wyszukiwarka' in c[0] else 'OverlayUnwatched.png'
        setArt={'thumb': '', 'poster': img_path+'senat.png', 'banner': '', 'icon': img, 'fanart':fanart}
        url = build_url({'mode':c[1],'categ':c[2]})
        addItemList(url, c[0], setArt)
    xbmcplugin.endOfDirectory(addon_handle)

def senatItemsList(c):
    if c=='trans':
        url=apiSenat+'transmissions/current'
        icon='DefaultTVShows.png'
    elif c=='arch':
        url=apiSenat+'transmissions/archival'
        icon='DefaultAddonVideo.png'

    resp=sess.get(url,headers=hea).json()
    ct='vodTransmissions' if c=='arch' else 'liveTransmissions'

    for t in resp[ct]:
        title=t['title']
        link=t['transmissionShortName']['value']
        iL={'plot': title}
        if c=='arch':
            ts=dateToTmp(t['since'],'%Y-%m-%dT%H:%M:%S.000+00:00')
            te=dateToTmp(t['till'],'%Y-%m-%dT%H:%M:%S.000+00:00')
            dur=int((int(te)-int(ts))/1000)
            iL['duration']=dur
        
        cmItems=[('[B]Harmonogram[/B]','Container.Update(plugin://plugin.video.parlament?mode=senatSchedule&link='+link+')')]
        
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': icon, 'fanart':fanart}
        url = build_url({'mode':'senatPlay','link':link,'categ':c})
        addItemList(url, title, setArt, 'video', iL, False, 'true', True, cmItems)
    
    if c=='arch':
        xbmcplugin.setContent(addon_handle, 'videos')
    
    xbmcplugin.endOfDirectory(addon_handle)

def senatSchedule(l):
    url=apiSenat+'transmissions/'+l+'/board-messages'
    resp=sess.get(url,headers=hea).json()
    if 'messages' in resp:
        for r in resp['messages']:
            title=r['content'].replace('\n',' ')
            ts=str(r['createdAt']*1000)
            
            iL={'plot':title}
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultAddonVideo.png', 'fanart':fanart}
            url = build_url({'mode':'senatPlay','link':link,'categ':'arch','ts':ts})
            addItemList(url, title, setArt, 'video', iL, False, 'true')
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)    

def senatPlay(l,c,ts,te=None):
    links=l.split('|')
    if len(links)>1:
        select=xbmcgui.Dialog().select('Części:', links)
        if select>-1:
            l=links[select]
        else:
            l=links[0]
        
    url=apiSenat+'transmissions/'+l+'/player-configuration'
    hea={
        'User-Agent':UA,
    }
    resp=sess.get(url,headers=hea).json()
    url_stream=resp['player']['playlist']['dash']
    if not url_stream.startswith('http'):
        url_stream='https:'+ url_stream
        
    if c=='arch':
        if ts==None:
            urlVOD=apiSenat+'transmissions/'+l
            resp=sess.get(urlVOD,headers=hea).json()
            ts=resp['markerSince']
            te=resp['markerTill']
        
        corr=978307200000
        t_start=int(ts)-corr
        url_stream +='&startTime='+str(t_start)
        if te!=None:
            t_stop=int(te)-corr
        else:
            t_stop=int(ts)+3600000-corr
        url_stream +='&stopTime='+str(t_stop)
                
    ISAplayer('mpd',url_stream)

senKads=['11','10','9','8']
senFilters={
    'kad':{'type':'select','labels':senKads,'default':'11','labelType':'Kadencja'},
    'since':{'type':'date','default':'','labelType':'Od [yyyy-mm-dd]'},
    'till':{'type':'date','default':'','labelType':'Do [yyyy-mm-dd]'},
    'no':{'type':'number','default':'','labelType':'Nr posiedzenia'}
}


def searchSenatFilters(t,page=None):
    if t=='pk':
        kad=addon.getSetting('sen_kad')
        kad='11' if kad=='' else kad
        #filtr:kad
        tit='[COLOR=cyan][B]Kadencja: [/B][/COLOR]%s.'%(kad)
        setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultGenre.png', 'fanart':fanart}
        url = build_url({'mode':'setSenFilter','filter':'kad'})
        addItemList(url, tit, setArt, isF=False)
        
        url=senatBaseurl+'prace/komisje-senackie/?kadencja='+kad
        resp=sess.get(url,headers=hea).text
        resp1=resp.split('ul class=\"row\"')[1].split('</ul')[0].split('\"nazwa-komisji\"')
        for r in resp1:
            if 'a href' in r:
                link=re.compile('<a href=\"([^"]+?)\"').findall(r)[0]
                kid=link.split(',')[-2]
                kname=link.split(',')[-1]
                img=senatBaseurl[:-1]+re.compile('<img src=\"([^"]+?)\"').findall(r)[0]
                name=re.compile('\"pseudo-link\">([^<]+?)</span>').findall(r)[0]
                                
                setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':fanart}
                url = build_url({'mode':'senatKomList','kid':kid,'kname':kname})
                addItemList(url, name, setArt)
                
        
    elif t=='ps':
        p=page if page!=None else '1'
        
        for f in senFilters:
            v=addon.getSetting('sen_%s'%(f))
            senFilters[f]['value']=v if v!='' else senFilters[f]['default']
        
        #filtry
        if page==None:
            for f in senFilters:
                fltData=senFilters[f]
                tit='[COLOR=cyan][B]%s: [/B][/COLOR]%s'%(fltData['labelType'],fltData['value'])
                setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': 'DefaultGenre.png', 'fanart':fanart}
                url = build_url({'mode':'setSenFilter','filter':f})
                addItemList(url, tit, setArt, isF=False)
        
        url=senatBaseurl+'prace/posiedzenia/'
        if page!=None:
            url+='page,%s.html'%(p)
        paramsUrl={
            'k':senFilters['kad']['value'],
            'q':senFilters['no']['value'],
            'od':senFilters['since']['value'],
            'do':senFilters['till']['value'],
            'pp':'52'
        }
        resp=sess.get(url,headers=hea,params=paramsUrl).text
        resp1=resp.split('<div class=\"archive\">')[1].split('pager-bottom')[0].split('container-posiedzenia')
        for r in resp1:
            if 'Zapis video' in r:
                link=re.compile('<a href=\"([^"]+?)\">Zapis video</a>').findall(r)[0]
                r1=r.replace('\n','').replace('<BR>','').replace('<br>','').replace('<br>','')
                title=re.compile('headline-anchor\">([^"]+?)</a>').findall(r1)[0]
                date=re.compile('date-container\">((?:(?!</div>).)*?)</div>').findall(r1)[0]
                tit='%s (%s)'%(title.strip(),cleanTags(date).strip())
                
                img=img_senat
                iL={'title':tit, 'plot':tit}
                setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':fanart}
                url = build_url({'mode':'senatVideos','link':link})
                addItemList(url, tit, setArt, 'video', iL)
        
        if '>Następna strona<' in resp:
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'searchSenatFilters','categ':t,'page':str(int(p)+1)})
            addItemList(url, '[COLOR=cyan][B]>>> następna strona[/B][/COLOR]', setArt)
    
    xbmcplugin.endOfDirectory(addon_handle)

def setSenFilter(f): #helper
    fltData=senFilters[f]
    flt=addon.getSetting('sen_%s'%(f))
    flt=flt if flt!='' else fltData['default']
    
    if fltData['type']=='select':
        select=xbmcgui.Dialog().select('%s:'%(fltData['labelType']), fltData['labels'])
        if select>-1:
            new_flt=fltData['labels'][select]
        else:
            new_flt=flt
    
    elif fltData['type']=='date':
        d=xbmcgui.Dialog().input('%s:'%(fltData['labelType']))#,type=xbmcgui.INPUT_DATE
        new_flt=d

    elif fltData['type']=='number':
        n=xbmcgui.Dialog().input('%s:'%(fltData['labelType']))#type=xbmcgui.INPUT_NUMERIC
        new_flt=n
    
    if new_flt!=flt:
        addon.setSetting('sen_%s'%(f),new_flt)
        xbmc.executebuiltin('Container.Refresh()')
    

def senatVideos(l):
    url=senatBaseurl[:-1]+l
    resp=sess.get(url,headers=hea).text
    resp1=resp.split('modul-posiedzenia')[1].split('<hr>')[0]
    vids=re.compile('href=\"([^"]+?)\">([^<]+?)</a').findall(resp1)
    for v in vids:
        if 'av' in v[0]:
            vid=v[0].split('/')[-1]
            title=v[1]
            
            img=img_senat
            iL={'title':title, 'plot':title}
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':fanart}
            url = build_url({'mode':'senatPlay','link':vid,'categ':'arch'})
            addItemList(url, title, setArt, 'video', iL, False, 'true')
        
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
    
def senatKomList(kid,kname,page):
    p='1' if page==None else page
    url='%sprace/komisje-senackie/posiedzenia,%s,%s,%s?pp=52'%(senatBaseurl,kid,p,kname)
    resp=sess.get(url,headers=hea).text
    if 'tabela-posiedzenia-komisji' in resp:
        resp1=resp.split('\"tabela-posiedzenia-komisji\"')[1].split('</table')[0].split('</tr>')
        for r in resp1:
            if 'retransmisja posiedzenia' in r:
                '''
                try:
                    link=re.compile('href=\"([^"]+?)\">[\s]?retransmisja posiedzenia').findall(r)
                except:
                    link=re.compile('href=\"([^"]+?)\"></transmisja').findall(r)
                link=[l.split('/')[-1] for l in link]
                '''
                link=re.compile('https://av8.senat.pl/([^"]+?)\"').findall(r)
                if len(link)>1:
                    vid='|'.join(link)
                elif len(link)==1:
                    vid=link[0]
                    r1=r.replace('\n','').replace('<BR>','').replace('<br>','').replace('<br>','')
                    data=re.compile('<td>([^<]+?)</td>').findall(r1)
                    title='Posiedzenie %s (%s)'%(data[0].strip(),data[1].strip())
                    
                    img=img_senat
                    iL={'title':title, 'plot':title}
                    setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img, 'fanart':fanart}
                    url = build_url({'mode':'senatPlay','link':vid,'categ':'arch'})
                    addItemList(url, title, setArt, 'video', iL, False, 'true')
        
        if '>Następna strona<' in resp:
            setArt={'thumb': '', 'poster': '', 'banner': '', 'icon': img_empty, 'fanart':fanart}
            url = build_url({'mode':'senatKomList','kid':kid,'kname':kname,'page':str(int(p)+1)})
            addItemList(url, '[COLOR=cyan][B]>>> następna strona[/B][/COLOR]', setArt)
    
    xbmcplugin.setContent(addon_handle, 'videos')
    xbmcplugin.endOfDirectory(addon_handle)
    
        
mode = params.get('mode', None)

if not mode:
    main_menu()
else:
    if mode=='sejmCateg':
        sejmCateg()
    
    if mode=='sejmSubcategs':
        c=params.get('categ')
        addon.setSetting('filtry',str({'phrase':'','trType':'','since':'','till':''}))
        sejmSubcategs(c)
    
    if mode=='sejmItemsList':
        c=params.get('categ')
        s=params.get('subcateg')
        p=params.get('page')
        k=params.get('kad')
        y=params.get('year')
        if s=='search':
            searchSejm(s,p,k)
        else:
            sejmItemsList(c,s,p,k,y)
    
    if mode=='filtersSejm':
        t=params.get('type')
        filtersSejm(t)
    
    if mode=='searchResultSejm':
        p=params.get('page')
        k=params.get('kad')
        Sess=params.get('sess')
        sessID=params.get('sessID')
        searchResultSejm(k,p,Sess,sessID)
    
    if mode=='sejmSchedule':
        t=params.get('type')
        ts=params.get('ts')
        te=params.get('te')
        link=params.get('link')
        st=params.get('srcType')
        k=params.get('kad')
        sejmSchedule(t,ts,te,link,st,k)
    
    if mode=='sejmPlay':
        link=params.get('link')
        st=params.get('srcType')
        k=params.get('kad')
        ts=params.get('ts')
        te=params.get('te')
        sejmPlay(link,st,k,ts,te)
        
    if mode=='senatCateg':
        senatCateg()
    if mode=='senatItemsList':
        c=params.get('categ')
        senatItemsList(c)
    if mode=='senatPlay':
        link=params.get('link')
        c=params.get('categ')
        ts=params.get('ts')
        senatPlay(link,c,ts)
    if mode=='senatSchedule':
        link=params.get('link')
        senatSchedule(link)
    
    if mode=='searchSenatFilters':
        c=params.get('categ')
        page=params.get('page')
        searchSenatFilters(c,page)
        
    if mode=='setSenFilter':
        filter=params.get('filter')
        setSenFilter(filter)
        
    if mode=='senatKomList':
        kid=params.get('kid')
        kname=params.get('kname')
        page=params.get('page')
        senatKomList(kid,kname,page)
        
    if mode=='senatVideos':
        link=params.get('link')
        senatVideos(link)
        