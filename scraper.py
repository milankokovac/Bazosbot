import requests
from bs4 import BeautifulSoup
import os

# Konfiguracia
BASE_URL = "https://mobil.bazos.sk/{page}?hledat=5g&Submit=H%C4%BEada%C5%A5&rubriky=mobil&category=0&hlokalita=81101&humkreis=125&cenaod=30&cenado=5005&order=&crp=&kitx=ano"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATA_FILE = "videne_inzeraty.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Status odoslania: {r.status_code}")

def scrape():
    videne = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            videne = f.read().splitlines()
    
    print(f"Pocet uz videnych inzeratov v subore: {len(videne)}")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
    nove_inzeraty_count = 0
    
    for start in [0, 20, 40]:
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        response = requests.get(current_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        inzeraty = soup.find_all('div', class_='listintele')
        
        print(f"Na strane {int(start/20)+1} som nasiel {len(inzeraty)} inzeratov.")
        
        for inz in inzeraty:
            link_tag = inz.find('h2', class_='nadpis').find('a')
            if not link_tag: continue
            
            title = link_tag.text
            url = "https://www.bazos.sk" + link_tag['href']
            price_div = inz.find('div', class_='listicena')
            cena = price_div.text if price_div else "N/A"
            inz_id = url.split('/')[-2]

            if inz_id not in videne:
                msg = f"📱 Nový inzerát (Strana {int(start/20)+1})!\n{title}\nCena: {cena}\n{url}"
                send_telegram(msg)
                videne.append(inz_id)
                nove_inzeraty_count += 1

    print(f"Ukladam {len(videne)} inzeratov do suboru.")
    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))
    print("Hotovo.")

if __name__ == "__main__":
    scrape()
