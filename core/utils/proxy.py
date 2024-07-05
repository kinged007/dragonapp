import os, random
from core import log
# from config.config import Settings

def prepare_headers():
    headers = {}
    proxy = random_proxy()
    if proxy:
        if proxy.startswith("http"):
            headers['proxies'] = {
                'http' : proxy,
                'https' : proxy
                }
        else:
            headers['proxies'] = {
                'http' : f'http://{proxy}',
                'https' : f'http://{proxy}'
                }
            
        # Set proxy at global environement level TODO: I dont think we need to do this. The fix was turning Reload page OFF on response.html.render()
        os.environ.update(http_proxy=headers['proxies']['http'], https_proxy=headers['proxies']['https'])
        
    ua = random_useragent()
    if ua:
        headers['headers'] = ({'User-Agent': ua,
                'Accept-Language': 'en-US, en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Accept' : 'test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.google.com/'
                })
    # log.debug("Using Proxy/UserAgents: " + str(headers))
    return headers

def random_proxy(file=None):
    
    # TODO Manage proxies through database
    file = file if file else "proxies.txt"
    
    if os.environ['ROTATING_PROXY_URL']:
        # Use rotating proxy
        return os.environ['ROTATING_PROXY_URL']
    
    elif os.path.isfile(file):
        # Use proxies file
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) == 0:
                log.warning("Proxy file is empty")
                return None
            proxy = random.choice(lines).replace('\n','').strip()
            if "@" not in proxy:
                _p = proxy.split(":")
                if len(_p) == 4:
                    proxy = f"{_p[2]}:{_p[3]}@{_p[0]}:{_p[1]}"
            return proxy

    else:
        log.warning("No proxies file found. Please create a proxy file in 'proxies.txt'")
    
    return None
        

def random_useragent():
    ua_file = os.path.join('useragents.txt')
    if not os.path.isfile(ua_file):
        log.warning("No useragents file found. Please create a text file in 'src/useragents.txt'")
        return None

    with open(ua_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) == 0:
            log.warning("Useragents file is empty")
            return None
        return random.choice(lines).replace('\n','').strip()