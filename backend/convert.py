import markdown
import re

def convert_to_html(mk):
    converted = markdown.markdown(mk)
    converted.replace("\n", "<br>")
    converted.replace('"', " ")
    return converted

def check_link(link):
    link_pattern = "(https://|http://)(www.|)+[a-zA-Z0-9-]+\.+[a-zA-Z]*+[a-zA-Z0-9/-]*" # Regex. AAAAAAHHHH
    return re.search(string=link, pattern=link_pattern)



