import requests
from bs4 import BeautifulSoup
import os
import time

# TESTOVACIA KONFIGURACIA (Zmenil som na iPhone, aby sme videli, ci to vobec nieco najde)
BASE_URL = "https://mobil.bazos.sk/{page}?hledat=iphone&hlokalita=&humkreis=25&cenaod=100&cenado=1000&order="
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
    
    # Maximalne maskovanie za realny Windows prehliadac
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'sk-SK,sk;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
    }

    for start in [0]: # Na test skusime len prvu stranu
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        print(f"--- START TESTU ---")
        print(f"Skusam nacitat: {current_url}")
        
        try:
            response = requests.get(current_url, headers=headers, timeout=15)
            
            # TOTO JE KLUC_ K DIAGNOSTIKE:
            print(f"Odpoved servera (Status Code): {response.status_code}")
            
            if response.status_code != 200:
                print("⚠️ Pozor! Bazos vratil chybu. Skusime vypisat zaciatok stranky:")
                print(response.text[:500]) # Vypise prvych 500 znakov kodu
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Skusime najst vsetky mozne typy inzeratov
            inzeraty = soup.find_all('div', class_=['listin', 'listintele'])
            
            print(f"Najdenych inzeratov na strane: {len(inzeraty)}")
            
            for inz in inzeraty:
                link_tag = inz.find('h2', class_='nadpis').find('a') if inz.find('h2', class_='nadpis') else None
                if not link_tag: continue
                
                title = link_tag.text.strip()
                link = "https://mobil.bazos.sk" + link_tag['href']
                
                price_tag = inz.find('div', class_='listicena')
                price = price_tag.text.strip() if price_tag else "N/A"
                
                inz_id = link.split('/')[-2] if '/' in link else title

                if inz_id not in videne:
                    msg = f"📱 TEST BOT: {title}\nCena: {price}\n{link}"
                    send_telegram(msg)
                    videne.append(inz_id)

        except Exception as e:
            print(f"Chyba pripojenia: {e}")

    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))
    print("--- KONIEC TESTU ---")

if __name__ == "__main__":
    scrape()
