import sqlite3
import os
import re
import requests
from bs4 import BeautifulSoup
from contextlib import redirect_stdout
from feedgen.feed import FeedGenerator

scriptDir = os.path.dirname(os.path.realpath(__file__))
db_connection = sqlite3.connect(scriptDir + '/sponsr.sqlite')
db = db_connection.cursor()
db.execute('CREATE TABLE IF NOT EXISTS rsssponsr (dataid integer, topic TEXT,  url TEXT, mp3_path TEXT, filename TEXT)')

data = {
    'email':        '', #insert here your email and password
    'password':         '', #and password
         }
podcasturl = '' #and link to podcast
yourdomainurl = '' #and your domain for rss link
#get html page from sponsr.ru with your cred
def gethtml():
  url = 'https://sponsr.ru/signin/'
  file_exist = os.path.exists('sponsr.html')

  session = requests.Session()
  req = session.get(url)


  sendauth = session.post(url, data=data, headers=dict(Referer=url))
  getdata = session.get(podcasturl)

  if file_exist is False:
    with open('sponsr.html', 'w') as file:
      with redirect_stdout(file):
        print(getdata.text)
  else:
    input('File exist, delete old file to get update, or i will show you an old data')
gethtml()

#get all from database
def get_podcasts():
    with db_connection:
        db.execute("SELECT * FROM rsssponsr")
        records=db.fetchall()


#check if record exist
def check_podcast_in_db(dataid, url):
    db.execute("SELECT * from rsssponsr WHERE dataid=? AND url=?", (dataid, url))
    if not db.fetchall():
        return True
    else:
        return False

def add_podcast_to_db(dataid, topic,  url, mp3_path, filename):
    db.execute("INSERT INTO rsssponsr VALUES (?,?,?,?,?)", (dataid, topic,  url, mp3_path, filename))
    db_connection.commit()

def getmp3(filename,url):
  authurl = 'https://sponsr.ru/signin/'
  file_exist = os.path.exists(filename)

  session = requests.Session()
  req = session.get(authurl)

  sendauth = session.post(authurl, data=data, headers=dict(Referer=url))
  getdata = session.get(url)

  if file_exist is False:
    open(filename, "wb").write(getdata.content)  

  #else:
  #  print('File already exist')

#parse html file
def checkin_parse():
  f = open("sponsr.html", "r")
  contents = f.read()
  soup = BeautifulSoup(contents, 'html.parser')
  mainsearch = soup.findAll('div', attrs={'class':'post-con'})
#parsing sponsr.html and write podcast id, name, url and path to mp3 to database
  for div in mainsearch:
    url = div.find('a')['href']
    topic = div.find('a').contents[0]
    dataid = div.find('label')['data-id']
    url = 'https://sponsr.ru' + url
    script_path = div.find('div', {'class': 'post-podcast-box'})
    content = str(script_path)
    reg = re.compile(r"\(\'(?P<filename>\S+\.mp3)\'\,\s+\'(?P<mp3_path>\S+)\'\,\s+\'\S+\'\)\;")
    parse = reg.search(content)
    if(parse is not None):
      mp3_path = 'https://sponsr.ru' + parse.group('mp3_path')
      filename = parse.group('filename')
      getmp3(filename,mp3_path)
    else:
      mp3_path = ''
    #votings with empty mp3 url  
    if str(mp3_path) != '':
      if check_podcast_in_db(dataid,url):
        add_podcast_to_db(dataid,topic,url,mp3_path,filename)

  f.close()

checkin_parse()

def podcastdata():
  f = open("sponsr.html", "r")
  contents = f.read()
  soup = BeautifulSoup(contents, 'html.parser')
  title = soup.find("meta",property="og:title")
  img = soup.find("meta",property="og:image")
  description = soup.find("div", {"class": "project-desc-wrapper"})
  podcastdata.description = description.text
  podcastdata.title = title["content"]
  podcastdata.img = img["content"]

podcastdata()

#generate rss.xml from sqlite
def get_podcasts():
  with db_connection:
    db.execute("SELECT * FROM rsssponsr ORDER by dataid DESC;")
    rows=db.fetchall()
  
  fg = FeedGenerator()
  fg.id(podcasturl)
  fg.title(podcastdata.title)
  fg.link( href=  podcasturl, rel='self' )
  fg.logo(podcastdata.img)
  fg.subtitle(podcastdata.description)
  fg.language('ru')

  for row in rows:
    fe = fg.add_entry()
    fe.id(row[2])
    fe.title(row[1])
    fe.link(href=row[2])
    fe.enclosure(yourdomainurl + row[4],0,'audio/mpeg')
    rssfeed  = fg.rss_str(pretty=True)
  fg.rss_file('rss.xml')
get_podcasts()

os.remove('sponsr.html')    
db_connection.close()
