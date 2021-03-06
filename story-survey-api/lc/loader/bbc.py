import json, datetime, re
from .core import Core
import urllib, socket
from bs4 import BeautifulSoup

class BBC(Core):
    
    def __init__(self, format = "json"):
        super().__init__()
        self.html = ''
        return
    
    def getDate(self, item):
        return datetime.datetime.strptime(item['pubDate'][5:16], '%d %b %Y')
    
    def getContent(self, item):
        content = self.getPageContent(item['link'])
        if not content:
            return '';
        return item['title'] + '. ' + content
    
    def getTitle(self, item):
        return item['title']
    

    def getShortDescription(self, item):
        return item['description']
    
    def fetchPage(self, link):
        try:
            fp = urllib.request.urlopen(link, timeout = self.timeout)
            mybytes = fp.read()
            page = mybytes.decode("utf8")
            fp.close()
        except socket.timeout as e:
            print(type(e))
            print(link)
            print("There was an error: %r" % e)
            return None  
        except urllib.error.HTTPError as e:
            print(type(e))
            print(link)
            print("There was an error: %r" % e)
            return None
        except urllib.error.URLError as e:
            print(type(e))
            print(link)
            print("There was an error: %r" % e)
            return None 
        
        self.html = ''
        soup = BeautifulSoup(page, features="html.parser")
        title = soup.find('title');
        description = soup.find("meta", {"name": "description"}).attrs['content']
        date = soup.find('time');
        item = {
            'title': re.sub(' - BBC News$', '', title.text),
            'description': description,
            'pubDate': date.get('datetime'),
            'link': link,
            'content': self.getPageContent(soup),
            'content_html': self.html
        }
        return item
    
    
    def getPageContent(self, soup):
        divs = soup.findAll('div', attrs={"class":"story-body__inner"})
        if divs:
            self.html = self.getDivText(divs)
            return self.html.strip()
 
        text = ''
        articles = soup.findAll('article')
        for article in articles:
            for item in article.findChildren(recursive=False):
                if not self.shouldIncludeItem(item):
                    continue
                text += self.getAndAppendValue(item)
                
        self.html = text
        text = re.sub('<[^<]+?>', '', text)
        text = re.sub('\s+', ' ', text)
        return text
    
    def shouldIncludeItem(self, item):
        if item.name not in ['p', 'ul', 'li', 'ol', 'div', 'h2', 'h3', 'a', 'h3']:
            return False
        
        if item.attrs and 'class' in item.attrs.keys():
            for cssClass in item.attrs['class']:
                if cssClass.find('RichText') != -1:
                    return True
        
        return False
        
    
    def getDivText(self, divs):
        text = ''
        for div in divs:
            for item in div.findChildren(recursive=False):
                text += self.getAndAppendValue(item)
        return text
    
    def getAndAppendValue(self, item):
        if item.name not in ['p', 'ul', 'li', 'ol', 'h2', 'h3', 'div', 'b']:
            return '';
        value = ''
        if item.name in ['p', 'li']:
            value = self.cleanText(item.text.strip())
        elif item.findChildren():
            for childItem in item.findChildren(recursive=False):
                value += self.getAndAppendValue(childItem)
        else:
            value = self.cleanText(item.text)
            
        if value:
            value = '<' + item.name + '>' + value + ' </' + item.name + '>'
        return value
        
    
    def cleanText(self, text):
        value = re.sub('<[^<]+?>', '', str(text))
        text = re.sub(r'Follow [a-zA-Z]+ on Twitter', r'', text)
        text = re.sub(r'^.*PODCAST:.+$', r'', text)
        text = re.sub(r'^.*DOWNTIME SYMPHONY:.+$', r'', text)
        ignoreTexts = [
            "Do you work in the civil service? Share your views and experiences by emailing haveyoursay@bbc.co.uk.",
            "Please include a contact number if you are willing to speak to a BBC journalist. You can also get in touch in the following ways:",
            "Do you live in one of the areas where restrictions are being reintroduced? How will you be affected? Share your views and experiences by emailing haveyoursay@bbc.co.uk.",
            "WhatsApp: +44 7756 165803. Tweet: @BBC_HaveYourSay. Please read our terms & conditions and privacy policy. ",
            "Use the form below to send us your questions and we could be in touch.",
            "In some cases your question will be published, displaying your name, age and location as you provide it, unless you state otherwise. Your contact details will never be published. Please ensure you have read the terms and conditions.",
            "If you are reading this page on the BBC News app, you will need to visit the mobile version of the BBC website to submit your question on this topic.",
            "Find BBC News: East of England on Facebook, Instagram and Twitter. If you have a story suggestion email eastofenglandnews@bbc.co.uk"
        ]
        for ignoreText in ignoreTexts:
            text = text.replace(ignoreText, '')
            
        return text

    
