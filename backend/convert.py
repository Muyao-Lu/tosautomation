import markdown
import re

def convert_to_html(mk):
    converted = markdown.markdown(mk)
    converted.replace("\n", "<br>")
    converted.replace('"', " ")
    return converted

def check_link(link):
    link_pattern = "(https://|http://)(www.|)[0-9a-zA-Z\-]{1,}\.+[a-zA-Z]{2,}[a-zA-Z0-9\?\=\/\?\.\-]*" # Regex. AAAAAAHHHH
    print(re.search(string=link, pattern=link_pattern))
    return re.search(string=link, pattern=link_pattern)



