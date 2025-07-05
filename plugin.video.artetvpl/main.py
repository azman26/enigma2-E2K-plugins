# -*- coding: UTF-8 -*-

import e2kodi__init__ # aby zainicjowac sciezki i nie musiec zmieniac czegos w kodzie

# -*- coding: utf-8 -*-
import sys
import json
import re
from urllib.parse import urlencode, parse_qsl

import requests
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

# --- Ustawienia globalne i stałe ---
BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
PARAMS = dict(parse_qsl(sys.argv[2][1:]))

ADDON = xbmcaddon.Addon(id='plugin.video.artetvpl')
PATH = ADDON.getAddonInfo('path')
PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
RESOURCES_PATH = f'{PATH}/resources/'

FANART = f'{RESOURCES_PATH}/../fanart.jpg'
ICON = f'{RESOURCES_PATH}/../icon.png'
ICON_NEXT = f'{RESOURCES_PATH}/right.png'
CATEGORIES_FILE = f'{RESOURCES_PATH}/categ.json'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'

API_TOKEN_EMAC = 'MWZmZjk5NjE1ODgxM2E0MTI2NzY4MzQ5MTZkOWVkYTA1M2U4YjM3NDM2MjEwMDllODRhMjIzZjQwNjBiNGYxYw'
API_TOKEN_PLAYER = 'MzYyZDYyYmM1Y2Q3ZWRlZWFjMmIyZjZjNTRiMGY4MzY4NzBhOWQ5YjE4MGQ1NGFiODJmOTFlZDQwN2FkOTZjMQ'

HEADERS_EMAC = {
    'User-Agent': 'arte/214402057',
    'Authorization': f'Bearer {API_TOKEN_EMAC}',
}
HEADERS_PLAYER = {
    'User-Agent': USER_AGENT,
    'Authorization': f'Bearer {API_TOKEN_PLAYER}',
}

# --- Funkcje pomocnicze ---

def log(msg, level=xbmc.LOGINFO):
    """Logowanie wiadomości do dziennika Kodi."""
    xbmc.log(f"[ArteTV-PL] {msg}", level)

def api_request(url, api_type='emac'):
    """Centralna funkcja do wykonywania zapytań do API Arte."""
    headers = HEADERS_EMAC if api_type == 'emac' else HEADERS_PLAYER
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log(f"Błąd sieciowy podczas zapytania do API {url}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Błąd ArteTV", "Problem z połączeniem z serwerem.")
        return None
    except json.JSONDecodeError as e:
        log(f"Błąd parsowania JSON z API {url}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Błąd ArteTV", "Otrzymano nieprawidłowe dane z serwera.")
        return None

def build_url(query):
    """Buduje URL dla wtyczki."""
    return f'{BASE_URL}?{urlencode(query)}'

def add_item(url, name, image, mode, is_folder=False, is_playable=False, info=None, fanart=FANART):
    """Nowoczesna funkcja do dodawania elementów."""
    if info is None:
        info = {'title': name, 'plot': name}

    li = xbmcgui.ListItem(label=name)
    li.setProperty("IsPlayable", 'true' if is_playable else 'false')
    li.setInfo(type="video", infoLabels=info)
    li.setArt({'thumb': image, 'icon': image, 'poster': image, 'fanart': fanart})

    built_url = build_url({'mode': mode, 'url': url, 'title': name, 'image': image})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=built_url, listitem=li, isFolder=is_folder)

# --- Widoki (Główne funkcje) ---

def home():
    """Główne menu wtyczki."""
    add_item('HOME', 'Strona główna', ICON, "list_zones", is_folder=True)
    add_item('MOST_VIEWED', 'Popularne', ICON, "list_content", is_folder=True)
    add_item('MOST_RECENT', 'Najnowsze', ICON, "list_content", is_folder=True)
    add_item('LAST_CHANCE', 'Ostatnia szansa', ICON, "list_content", is_folder=True)
    add_item('MAGAZINES', 'Magazyny', ICON, "list_content", is_folder=True)
    add_item('CATEGORIES', 'Kategorie', ICON, "list_categories", is_folder=True)
    add_item('', '[COLOR lightblue]Szukaj[/COLOR]', 'DefaultAddonsSearch.png', "search", is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_categories():
    """Wyświetla kategorie z lokalnego pliku JSON."""
    try:
        with xbmcvfs.File(CATEGORIES_FILE, 'r') as f:
            content = f.read()
            categories_data = json.loads(content)
    except Exception as e:
        log(f"Nie udało się wczytać pliku kategorii: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Błąd ArteTV", "Błąd pliku z kategoriami.")
        return

    for category in categories_data:
        title = category.get("label", "Brak tytułu")
        plot = category.get("description", "")
        info = {'title': title, 'plot': plot}
        add_item(category.get('code'), title, ICON, "list_subcategories", info=info, is_folder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_subcategories(category_code, category_title):
    """Wyświetla podkategorie dla wybranej kategorii."""
    try:
        with xbmcvfs.File(CATEGORIES_FILE, 'r') as f:
            content = f.read()
            categories_data = json.loads(content)
    except Exception as e:
        log(f"Nie udało się wczytać pliku kategorii: {e}", xbmc.LOGERROR)
        return

    for category in categories_data:
        if category.get('code') == category_code:
            for subcategory in category.get("subcategories", []):
                title = subcategory.get("label", "Brak tytułu")
                plot = subcategory.get("description", "")
                url = f"{category_code}|{subcategory.get('code')}"
                info = {'title': title, 'plot': plot}
                add_item(url, title, ICON, "list_content", info=info, is_folder=True)
            break
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_zones(page_code):
    """Wyświetla "strefy" ze strony głównej (np. "Kino", "Odkrycia")."""
    url = f'https://api.arte.tv/api/emac/v3/pl/app/{page_code}?authorizedAreas=ALL,SAT'
    data = api_request(url)
    if not data:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return

    for zone in data.get("zones", []):
        title = zone.get("title")
        if not title or not zone.get("data") or "Top teaser" in title or "Banner" in title:
            continue
        
        url_param = f"{page_code}|{title}"
        add_item(url_param, title, ICON, "list_zone_content", is_folder=True)
        
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def process_and_add_video(video_data):
    """Przetwarza dane o pojedynczym wideo i dodaje je do listy."""
    program_id = video_data.get('programId')
    if not program_id:
        return

    title = video_data.get('title', 'Brak tytułu')
    plot = video_data.get('shortDescription', title)
    duration = video_data.get('duration')
    
    images = video_data.get('images', {})
    img = ''
    if images:
        for key in ['landscape', 'portrait', 'banner', 'teaser']:
            if images.get(key) and images[key].get('url'):
                img = images[key]['url']
                break
    if img:
        img = re.sub(r'(\d+x\d+)', '1920x1080', img)

    info = {'title': title, 'plot': plot, 'duration': duration}
    
    is_collection = program_id.startswith('RC-')
    mode = "list_content" if is_collection else "play_video"
    url = f"https://api.arte.tv/api/emac/v3/pl/app/{program_id}" if is_collection else program_id

    add_item(url, title, img, mode, is_folder=is_collection, is_playable=not is_collection, info=info)

def list_zone_content(url_param):
    """Wyświetla zawartość konkretnej strefy."""
    page_code, zone_title = url_param.split('|')
    url = f'https://api.arte.tv/api/emac/v3/pl/app/{page_code}?authorizedAreas=ALL,SAT'
    data = api_request(url)
    if not data:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return
        
    found_zone = None
    for zone in data.get("zones", []):
        if zone.get("title") == zone_title:
            found_zone = zone
            break
            
    if found_zone:
        for video_data in found_zone.get("data", []):
            process_and_add_video(video_data)
        
        next_page_url = found_zone.get("nextPage")
        if next_page_url:
            add_item(next_page_url, ">> Następna strona >>", ICON_NEXT, "list_content", is_folder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def list_content(url):
    """Uniwersalna funkcja do listowania zawartości z różnych endpointów API."""
    if '|' in url:
        category_code, subcategory_code = url.split('|')
        api_url = f'https://api.arte.tv/api/emac/v3/pl/app/MOST_RECENT?category={category_code}&subcategories={subcategory_code}'
    elif not url.startswith('https://'):
        api_url = f'https://api.arte.tv/api/emac/v3/pl/app/{url}'
    else:
        api_url = url
        
    data = api_request(api_url, api_type='emac')
    if not data:
        xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=False)
        return

    next_page_url = None
    if 'zones' in data:
        for zone in data.get("zones", []):
            for video_data in zone.get("data", []):
                process_and_add_video(video_data)
            if zone.get("nextPage"):
                next_page_url = zone.get("nextPage")
    else:
        for video_data in data.get("data", []):
            process_and_add_video(video_data)
        next_page_url = data.get("nextPage")

    if next_page_url:
        next_page_url = re.sub(r'limit=\d+', 'limit=20', next_page_url)
        add_item(next_page_url, ">> Następna strona >>", ICON_NEXT, "list_content", is_folder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)
    
def play_video(program_id):
    """Pobiera strumienie i odtwarza wideo."""
    url = f'https://api.arte.tv/api/player/v2/config/pl/{program_id}'
    data = api_request(url, api_type='player')
    
    if not data:
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return

    streams = data.get("data", {}).get("attributes", {}).get("streams", [])
    if not streams:
        xbmcgui.Dialog().notification("ArteTV", "Nie znaleziono strumieni dla tego wideo.")
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return

    versions = []
    for stream in streams:
        for version in stream.get('versions', []):
            label = version.get('label', 'Nieznana wersja')
            stream_url = stream.get('url')
            if label and stream_url:
                versions.append({'label': label, 'url': stream_url})
    
    if not versions:
        xbmcgui.Dialog().notification("ArteTV", "Brak dostępnych wersji językowych.")
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return

    if len(versions) > 1:
        labels = [v['label'] for v in versions]
        dialog = xbmcgui.Dialog()
        select = dialog.select("Wybierz wersję:", labels)
        if select == -1:
            xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
            return
        final_url = versions[select]['url']
    else:
        final_url = versions[0]['url']
   
    play_item = xbmcgui.ListItem(path=final_url)
    play_item.setProperty('inputstream', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setMimeType('application/vnd.apple.mpegurl')
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)

def search():
    """Funkcja wyszukiwania."""
    dialog = xbmcgui.Dialog()
    query = dialog.input('Szukaj w Arte.tv', type=xbmcgui.INPUT_ALPHANUM)
    if query:
        encoded_query = urlencode({'query': query})
        search_url = f'https://api.arte.tv/api/emac/v3/pl/app/SEARCH?{encoded_query}'
        list_content(search_url)

# --- Główny router wtyczki ---

def router():
    """Główny router, który wywołuje odpowiednią funkcję na podstawie 'mode'."""
    mode = PARAMS.get('mode')
    url = PARAMS.get('url')
    title = PARAMS.get('title')
    
    routes = {
        'list_zones': lambda: list_zones(url),
        'list_zone_content': lambda: list_zone_content(url),
        'list_categories': list_categories,
        'list_subcategories': lambda: list_subcategories(url, title),
        'list_content': lambda: list_content(url),
        'play_video': lambda: play_video(url),
        'search': search,
    }

    if mode is None:
        home()
    elif mode in routes:
        routes[mode]()
    else:
        log(f"Nieznany tryb (mode): {mode}", xbmc.LOGWARNING)

if __name__ == '__main__':
    router()