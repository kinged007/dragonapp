import markdown
import html2text
import re
import html



def html_to_markdown(html:str, ignore_links:bool = True):
    if html == None:
        return "" 
    h = html2text.HTML2Text()
    # Ignore converting links from HTML
    h.ignore_links = ignore_links
    return h.handle(html)

def markdown_to_html(text:str):
    if not text:
        return ""
    return str(markdown.markdown(str(text), extensions=['extra'], output_format='html5'))
    
def strip_html_tags(text):
    text = html.unescape(text)
    text = re.sub('<[^<]+?>', '', text)
    return text

def markdownify(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        _new_value = ""
        for _k,_v in obj.items():
            _new_value += f"\n\n### {_k}\n\n"
            if isinstance(_v, list):
                _new_value += markdownify(_v)
            else:
                _new_value += f" - {str(_v)}\n"
        return _new_value

    elif isinstance(obj, list):
        return " - " + "\n - ".join(obj) + "\n"
    elif isinstance(obj, tuple):
        return tuple(markdownify(item) for item in obj)
    else:
        return str(obj)