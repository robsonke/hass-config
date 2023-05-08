import requests
import sys
from bs4 import BeautifulSoup

# highly specific scrape script for pool monitoring system
# hopefully replaced by an API later
# usage: python3 scrape-pool.py scrapeUrl username password whattoscrape
args = [arg for arg in sys.argv[1:]]
login_url = args[0]
login = args[1]
password = args[2]
value = args[3]

selector = ""

# use the copy selector options in devtools
if value == "ph":
  selector = "#content-wrapper > div.container-xl.mt-2.ml-lg-5.mr-lg-5.px-0 > div.row.mt-4.m-2 > div:nth-child(2) > div > div > div > div.col.mr-2 > div.col-auto > div"
elif value == "redox":
  selector = "#content-wrapper > div.container-xl.mt-2.ml-lg-5.mr-lg-5.px-0 > div.row.mt-4.m-2 > div:nth-child(3) > div > div > div > div.col.mr-2 > div.col-auto > div"
elif value == "flow":
  selector = "#content-wrapper > div.container-xl.mt-2.ml-lg-5.mr-lg-5.px-0 > div.row.mt-4.m-2 > div:nth-child(4) > div > div > div > div.col.mr-2 > div.col-auto > div"


with requests.session() as s:
  req = s.get(login_url).text
  html = BeautifulSoup(req, "html.parser")
  
  s.get(login_url)
  token = s.cookies['csrftoken']


  payload = {
    "csrfmiddlewaretoken": token,
    "username": login,
    "password": password
  }

  headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-GB,en;q=0.5",
    "Cookie": "csrftoken="+token,
    "Referer": login_url,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
  }


  # and login
  res = s.post(login_url, data = payload, headers = headers)
  soup = BeautifulSoup (res.content, "html.parser")

  scrapedValue = soup.select(selector)

  # return the first hit
  print(scrapedValue[0].text)
