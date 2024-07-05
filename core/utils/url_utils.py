from courlan import check_url, is_navigation_page, is_not_crawlable, clean_url, validate_url

def check_url_is_valid(url:str, accept_navigation:bool = False):
    url = clean_url(url)
    try:
        if is_navigation_page(url) and not accept_navigation:
            raise
        if is_not_crawlable(url):
            raise
        if not validate_url(url)[0]: 
            raise
    except:
        return None
    return url
