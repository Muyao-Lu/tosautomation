import markdown

def convert_to_html(mk):
    converted = markdown.markdown(mk)
    print(converted)
    return converted

