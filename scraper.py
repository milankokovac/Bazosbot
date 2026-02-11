import requests
from bs4 import BeautifulSoup
import os
import time

# Konfiguracia - Upravena URL na najjednoduchsi format
BASE_URL = "https://mobil.bazos.sk/{page}?hledat=5g&hlokalita=&humkreis=25&cenaod=30&cenado=250&order="
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATA_FILE = "videne_inzeraty.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def scrape():
    videne = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            videne = f.read().splitlines()
    
    # Maximalne maskovanie - kopia realneho Chrome prehliadaca
    headers = {
        'authority': 'mobil.bazos.sk',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'sk-SK,sk;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    # Skusime len prvu stranu na test, aby sme nevyvolali podozrenie
    for start in [0, 20]:
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        print(f"Skusam nacitat: {current_url}")
        
        try:
            # Pridany session pre udrzanie cookies (vyzera to ludskejsie)
            session = requests.Session()
            response = session.get(current_url, headers=headers, timeout=15)
            
            if "Pridané inzeráty" not in response.text and "Hľadať" not in response.text:
                print("⚠️ Varovanie: Stranka sa pravdepodobne nenacitala spravne (Anti-bot ochrana).")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Skusime najst inzeraty cez velmi vseobecny selector
            inzeraty = soup.select('div.listin') or soup.select('.listintele')
            
            print(f"Najdenych inzeratov na strane: {len(inzeraty)}")
            
            for inz in inzeraty:
                link_tag = inz.select_one('h2.nadpis a')
                if not link_tag: continue
                
                title = link_tag.text.strip()
                link = "https://mobil.bazos.sk" + link_tag['href']
                
                price_tag = inz.select_one('.listicena b')
                price = price_tag.text.strip() if price_tag else "N/A"
                
                inz_id = link.split('/')[-2] if '/' in link else title

                if inz_id not in videne:
                    msg = f"📱 Nový inzerát!\n{title}\nCena: {price}\n{link}"
                    send_telegram(msg)
                    videne.append(inz_id)
            
            time.sleep(3) # Dlhšia pauza
            
        except Exception as e:
            print(f"Chyba: {e}")

    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))
    print("Hotovo.")

if __name__ == "__main__":
    scrape()
