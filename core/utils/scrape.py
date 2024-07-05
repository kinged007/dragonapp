from core import log
import io, datetime
from bs4 import BeautifulSoup as bs
from requests_html import AsyncHTMLSession, HTMLSession
# from utils.datetime import datetime, timedelta
import time, json, asyncio
from courlan import get_hostinfo
import re

from models.proxy import prepare_headers
from models.file import find_file, save_file

async def get_cached_html(url:str):
    """ Attempts to fetch the HTML for a given URL """
    try:
        log.debug("Looking for cached HTML")
        # Clean url using regex
        clean_url = re.sub(r'\W+', '', url)
        # Find file
        file = await find_file(clean_url + ".html")
        if file:
            # Read file
            with open(file, 'r') as f:
                html = f.read()
                log.debug("Retrieved Cached HTML")
                return html
        
    except Exception as e:
        log.error(e)
        
    # try:
    #     file = await UrlCache.select(UrlCache.html_file).where(UrlCache.url == url).first()
    #     if file:
    #         bufferedFile = await MEDIA_RAW_HTML.get_file(file['html_file'])
    #         # decode binary string
    #         html = bufferedFile.read().decode('utf-8')
    #         log.debug("Retrieved Cached HTML")
    #         return html

    # except Exception as e:
    #     log.error(e)

    return None

async def save_cached_html(url:str,html:str,search_term = ''):
    """ Attempts to cache the HTML for a given URL """
    try:
        log.debug("Saving Cached HTML")
        # Clean url using regex
        clean_url = re.sub(r'\W+', '', url)
        # Save file
        # TODO Save to database
        if await save_file(clean_url + ".html", html):
            log.debug("Saved Cached HTML")
            return True
    except Exception as e:
        log.error(e)
    
    return False
    # try:
    #     f = io.BytesIO(bytes(str(html), 'utf-8'))
    #     f_key = await MEDIA_RAW_HTML.store_file(file_name='raw.html',file=f)
    #     f_key
    #     log.debug(f_key)
    # except Exception as e:
    #     log.error(e)
    #     return False

    return


async def fetch_metadata(html:str, url:str = ''):
    soup = bs(html, 'html.parser')
    metas = soup.find_all('meta')
    urlinfo = get_hostinfo(url)
    return {
        'url' : url,
        'domain' : urlinfo[0] if urlinfo[0] else '',
        'title' : soup.title.text,
        'description' : " ".join([meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'].lower() == 'description' and 'content' in meta.attrs]),
        'og-data' : {
            meta.attrs['property']:meta.attrs['content'] for meta in metas if 'property' in meta.attrs and meta.attrs['property'].lower().startswith('og:') and 'content' in meta.attrs
        }
        
    }


async def fetch_html(url, render_js = False, use_cache = True ):
    """
    Function that scrapes the html from the url
    """
    if use_cache:
        html = await get_cached_html(url)
        if html:
            return html
    try:
        _count = 1
        # url = "https://api.myip.com/" # DEBUG 
        log.info("Scraping HTML from url: "+url)
        while True:
            if _count <= 0: break
            try:
                session = AsyncHTMLSession() # HTMLSession()
                headers = prepare_headers()
                if 'proxies' in headers:
                    session.proxies = headers['proxies']
                response = await session.get(url, headers=headers['headers'] )
                
                if render_js:
                    await response.html.arender(sleep=2, reload=False) # Reload=False is required for proxies to work
                    # # asession = AsyncHTMLSession()
                    # # response = await asession.get(url, **prepare_headers() )
                    # # TODO Detect if content is html text of PDF file. If PDF file, convert to HTML
                    # if response.headers['Content-Type'] == 'application/pdf':
                    #     # Digest PDF to plain text
                    #     log.warning("TODO: Digest PDF to plain text")
                    #     pass
                    # else:
                    #     # await response.html.arender()
                    #     print("BOO")
                    #     await response.html.arender()
                else:
                    # session = HTMLSession()
                    # response = session.get(url, **prepare_headers())
                    pass
                if response.status_code not in [200,301,302]:
                    raise Exception("Incorrect Status Code: "+str(response.status_code))
                
                log.debug(response.headers)
                
                # Success    
                log.debug("Success scraping HTML for URL " +url+ " : " + str(response.html.html[:300]).replace("\n",""))
                await save_cached_html(url, response.html.html )
                return response.html.html
                break
            except Exception as e:
                log.error(e)
                await asyncio.sleep(1)
                _count -= 1

    except Exception as e:
        log.error(e)
      
    return ""
