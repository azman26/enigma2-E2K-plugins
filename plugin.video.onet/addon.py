# -*- coding: utf-8 -*-

import e2kodi__init__ # aby zainicjowac sciezki i nie musiec zmieniac czegos w kodzie

import sys
import json
import re
from urllib.parse import urlencode, parse_qsl

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

#from resources.lib.yt_live import play_yt, epgData

# --- Ustawienia globalne i stałe ---
BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
PARAMS = dict(parse_qsl(sys.argv[2][1:]))

ADDON = xbmcaddon.Addon(id='plugin.video.onet')
PATH = ADDON.getAddonInfo('path')
PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

FANART = f'{PATH}/resources/img/fanart.jpg'
ICON = f'{PATH}/icon.png'

if not xbmcvfs.exists(PROFILE_PATH):
    xbmcvfs.mkdir(PROFILE_PATH)

# --- Stałe dla API ---
VOD_LATEST_API_URL = 'https://service-feed.vmedia.pl/feed/video-sg/all' 
VOD_PLAYER_API_URL = 'https://player-api.dreamlab.pl/'
AUDIO_API_URL = 'https://app.audio.onet.pl/api'
YT_CHANNEL_ID = 'UC_vMDcmkuEvw0N-gaP35wTA'

USER_AGENT_WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
USER_AGENT_AUDIO = 'Dalvik/2.1.0 (Linux; U; Android 10; Mobile) Onet Audio/1.11.4'

HEADERS_WEB = {'User-Agent': USER_AGENT_WEB, 'Referer': 'https://video.onet.pl/'}
HEADERS_AUDIO = {'User-Agent': USER_AGENT_AUDIO, 'Accept': 'application/json'}
HEADERS_PLAYER = {'User-Agent': USER_AGENT_WEB, 'Referer': 'https://pulsembed.eu/'}

# --- Funkcje pomocnicze ---

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"[OnetVOD] {msg}", level)

def api_request(url, headers, params=None, json_payload=None, verify_ssl=True, allow_redirects=True):
    """Centralna funkcja do zapytań API."""
    try:
        if json_payload:
            response = requests.post(url, headers=headers, json=json_payload, timeout=15, verify=verify_ssl, allow_redirects=allow_redirects)
        else:
            response = requests.get(url, headers=headers, params=params, timeout=15, verify=verify_ssl, allow_redirects=allow_redirects)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log(f"Błąd sieciowy podczas zapytania do API {url}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Błąd Onet VOD", "Problem z połączeniem z serwerem.")
        return None
    except json.JSONDecodeError as e:
        log(f"Błąd parsowania JSON z API {url}: {e}", xbmc.LOGERROR)
        log(f"Surowa odpowiedź z serwera: {response.text}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Błąd Onet VOD", "Otrzymano nieprawidłowe dane z serwera.")
        return None

def build_url(query):
    return f'{BASE_URL}?{urlencode(query)}'

def add_item(url, name, image, mode, is_folder=False, is_playable=False, info=None):
    if info is None:
        info = {}
    
    li = xbmcgui.ListItem(label=name)
    li.setInfo('video', info)
    li.setProperty("IsPlayable", 'true' if is_playable else 'false')
    li.setArt({'thumb': image, 'icon': image, 'poster': image, 'fanart': FANART})

    params = {'mode': mode, 'url': url, 'title': name}
    built_url = build_url(params)
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=built_url, listitem=li, isFolder=is_folder)

# --- Główne widoki ---

def main_menu():
    categories = [
        {'mode': 'list_vod_latest', 'title': 'Najnowsze wideo', 'icon': 'DefaultAddonVideo.png', 'folder': True, 'url': '1'},
        {'mode': 'list_audio_main', 'title': 'Podcasty Onet Audio', 'icon': 'DefaultMusicSongs.png', 'folder': True},
        {'mode': 'play_live_yt', 'title': 'Transmisje na żywo (Onet News)', 'icon': 'DefaultTVShows.png', 'playable': True},
        {'mode': 'play_radio', 'title': 'Radio Onet', 'icon': 'DefaultMusicSongs.png', 'playable': True},
    ]
    for cat in categories:
        info = {'plot': cat['title']}
        context_menu = []
        if cat['mode'] == 'play_live_yt':
            info['plot'] = '[B]Transmisje okazjonalne[/B]\n[I]Planowane transmisje dostępne z poziomu menu kontekstowego.[/I]'
            context_menu = [('[B]Szczegóły (EPG)[/B]', f'RunPlugin({build_url({"mode": "show_epg"})})')]

        li = xbmcgui.ListItem(cat['title'])
        li.setInfo('video', info)
        li.setArt({'icon': cat['icon'], 'fanart': FANART})
        li.setProperty('IsPlayable', 'true' if cat.get('playable') else 'false')
        if context_menu:
            li.addContextMenuItems(context_menu)
        
        xbmcplugin.addDirectoryItem(
            handle=ADDON_HANDLE,
            url=build_url({'mode': cat['mode'], 'url': cat.get('url', '')}),
            listitem=li,
            isFolder=cat.get('folder', False)
        )
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

# --- Sekcja VOD ---

def list_vod_latest(page='1'):
    """Listuje najnowsze materiały VOD z publicznego API service-feed."""
    data = api_request(VOD_LATEST_API_URL, HEADERS_WEB, verify_ssl=False, allow_redirects=False)
    
    if not data or 'items' not in data:
        log("Nie otrzymano poprawnych danych z API 'service-feed'.", xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    for item in data['items']:
        url_str = item.get('url', '')
        match = re.search(r',(\w+)\.html', url_str)
        if match:
            mvp_id = match.group(1)
            add_item(
                url=mvp_id,
                name=item.get('title', 'Brak tytułu'),
                image=item.get('image', {}).get('url') or ICON,
                mode='play_video',
                is_playable=True,
                info={'plot': item.get('lead', item.get('title')), 'duration': item.get('duration')}
            )

    xbmcplugin.setContent(ADDON_HANDLE, 'videos')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def play_video(mvp_id):
    """Odtwarza wideo Onetu."""
    payload = {"jsonrpc": "2.0", "method": "get", "id": mvp_id, "params": {"mvp_id": mvp_id, "version": "2.0"}}
    data = api_request(VOD_PLAYER_API_URL, HEADERS_PLAYER, json_payload=payload)
    if not data or 'result' not in data:
        xbmcgui.Dialog().notification('Onet VOD', 'Brak źródła wideo.')
        return xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
    try:
        stream_url = data['result']['formats']['video']['hls'][0]['url']
        li = xbmcgui.ListItem(path=stream_url)
        li.setProperty('inputstream', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'hls')
        li.setMimeType('application/vnd.apple.mpegurl')
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=li)
    except (KeyError, IndexError):
        xbmcgui.Dialog().notification('Onet VOD', 'Nie znaleziono strumienia HLS.')
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())

# --- Sekcja Onet Audio ---

def list_audio_main():
    """Główne menu dla Onet Audio."""
    items = [
        {'mode': 'list_audio_podcasts', 'title': 'Podcasty'},
        {'mode': 'list_audio_episodes', 'title': 'Najnowsze odcinki'},
        {'mode': 'list_audio_categories', 'title': 'Kategorie'},
        {'mode': 'list_audio_authors', 'title': 'Autorzy'},
        {'mode': 'search_audio', 'title': 'Szukaj w Onet Audio'},
    ]
    for item in items:
        add_item('1', item['title'], ICON, item['mode'], is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_audio_podcasts(page='1'):
    data = api_request(f"{AUDIO_API_URL}/podcasts", HEADERS_AUDIO, params={'page': page})
    if not data: return
    for item in data['data']:
        add_item(item['id'], item['name'], item.get('thumbnail') or ICON, 'list_podcast_episodes', is_folder=True, info={'plot': item.get('short_description')})
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(str(int(page) + 1), '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_audio_podcasts', is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
    
def list_podcast_episodes(podcast_id, page='1'):
    data = api_request(f"{AUDIO_API_URL}/podcasts/{podcast_id}/episodes", HEADERS_AUDIO, params={'page': page})
    if not data: return
    for item in data['data']:
        add_item(item['id'], item['name'], item.get('thumbnail') or ICON, 'play_audio', is_playable=True, info={'plot': item.get('short_description'), 'duration': item.get('duration')})
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(podcast_id, '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_podcast_episodes', is_folder=True)
    xbmcplugin.setContent(ADDON_HANDLE, 'videos')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_audio_episodes(page='1'):
    data = api_request(f"{AUDIO_API_URL}/episodes", HEADERS_AUDIO, params={'page': page})
    if not data: return
    for item in data['data']:
        add_item(item['id'], item['name'], item.get('thumbnail') or ICON, 'play_audio', is_playable=True, info={'plot': item.get('short_description'), 'duration': item.get('duration')})
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(str(int(page) + 1), '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_audio_episodes', is_folder=True)
    xbmcplugin.setContent(ADDON_HANDLE, 'videos')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_audio_categories(page='1'):
    data = api_request(f"{AUDIO_API_URL}/categories", HEADERS_AUDIO, params={'page': page})
    if not data: return
    for item in data['data']:
        filter_url = urlencode({'category_id': item['id']})
        add_item(filter_url, item['name'], ICON, 'list_filtered_podcasts', is_folder=True)
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(str(int(page) + 1), '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_audio_categories', is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_audio_authors(page='1'):
    data = api_request(f"{AUDIO_API_URL}/authors", HEADERS_AUDIO, params={'page': page})
    if not data: return
    for item in data['data']:
        filter_url = urlencode({'author_id': item['id']})
        add_item(filter_url, item['name'], item.get('avatar') or ICON, 'list_filtered_podcasts', is_folder=True)
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(str(int(page) + 1), '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_audio_authors', is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_filtered_podcasts(filter_query, page='1'):
    params = dict(parse_qsl(filter_query))
    params['page'] = page
    data = api_request(f"{AUDIO_API_URL}/podcasts", HEADERS_AUDIO, params=params)
    if not data: return
    for item in data['data']:
        add_item(item['id'], item['name'], item.get('thumbnail') or ICON, 'list_podcast_episodes', is_folder=True, info={'plot': item.get('short_description')})
    if data.get('meta', {}).get('last_page', 1) > int(page):
        add_item(filter_query, '[COLOR yellow]>> Następna strona[/COLOR]', ICON, 'list_filtered_podcasts', is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
    
def play_audio(episode_id):
    data = api_request(f"{AUDIO_API_URL}/episodes/{episode_id}", HEADERS_AUDIO)
    if data and data.get('data', {}).get('file'):
        li = xbmcgui.ListItem(path=data['data']['file'])
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=li)
    else:
        xbmcgui.Dialog().notification('Onet Audio', 'Brak źródła audio.')
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())

def search_audio():
    xbmcgui.Dialog().notification("Onet Audio", "Wyszukiwarka w budowie.")

# --- Sekcja Live i Radio ---

def play_radio():
    stream_url = 'https://stream4.nadaje.com:10023/radio'
    li = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=li)

def get_player_type():
    try:
        return ADDON.getSetting('playerType')
    except:
        return 'default'

# --- Router ---

def router():
    mode = PARAMS.get('mode')
    url = PARAMS.get('url', '1')
    
    routes = {
        'list_vod_latest': lambda: list_vod_latest(url),
        'play_video': lambda: play_video(url),
        
        'list_audio_main': list_audio_main,
        'list_audio_podcasts': lambda: list_audio_podcasts(url),
        'list_podcast_episodes': lambda: list_podcast_episodes(url),
        'list_audio_episodes': lambda: list_audio_episodes(url),
        'list_audio_categories': lambda: list_audio_categories(url),
        'list_audio_authors': lambda: list_audio_authors(url),
        'list_filtered_podcasts': lambda: list_filtered_podcasts(url),
        'play_audio': lambda: play_audio(url),
        'search_audio': search_audio,
        
        'play_live_yt': lambda: play_yt(YT_CHANNEL_ID, get_player_type()),
        'show_epg': lambda: epgData(YT_CHANNEL_ID),
        'play_radio': play_radio,
    }

    if mode is None:
        main_menu()
    elif mode in routes:
        routes[mode]()
    else:
        log(f"Nieznany tryb: {mode}", xbmc.LOGWARNING)

if __name__ == '__main__':
    router()