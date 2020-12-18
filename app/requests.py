import urllib.request,json
from .models import Quote

base_url = None
def configure_request(app):
    global base_url
    base_url ='http://quotes.stormconsultancy.co.uk/random.json'
def getQuotes():
    with urllib.request.urlopen('http://quotes.stormconsultancy.co.uk/random.json') as url:
        quotesResponse = url.read()
        word = json.loads(quotesResponse)
        print(word)
        read = []
        id = word.get('id')
        author = word.get('author')
        quote = word.get('quote')
        quoteObject = Quote(id,author,quote)
        read.append(quoteObject)
        return read