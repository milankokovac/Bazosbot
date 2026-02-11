import requests
from bs4 import BeautifulSoup
import os

# Konfigurácia
BASE_URL = "https://mobil.bazos.sk/{page}?hledat=5g&Submit=H%C4%BEada%C5%A5&rubriky=mobil&category=0&hlokalita=81101&humkreis=200&cenaod=30&cenado=200&order=&crp=&kitx=ano"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATA_FILE = "videne_inzeraty.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})

def scrape():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            videne = f.read().splitlines()
    else:
        videne = []

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
    
    # Prechádzame prvé 3 strany (0, 20, 40)
    for start in [0, 20, 40]:
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        response = requests.get(current_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        inzeraty = soup.find_all('div', class_='listintele')
        
        for inz in inzeraty:
            link_tag = inz.find('h2', class_='nadpis').find('a')
            if not link_tag: continue
            
            title = link_tag.text
            url = "https://www.bazos.sk" + link_tag['href']
            cena = inz.find('div', class_='listicena').text
            inz_id = url.split('/')[-2]

            if inz_id not in videne:
                msg = f"📱 Nový inzerát (Strana {int(start/20)+1})!\n{title}\nCena: {cena}\n{url}"
                send_telegram(msg)
                videne.append(inz_id)

    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))

if __name__ == "__main__":
    scrape()
