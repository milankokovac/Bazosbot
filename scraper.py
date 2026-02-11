import requests
from bs4 import BeautifulSoup
import os
import time

# Konfiguracia - Mobilna verzia Bazosu pre lepsie obchadzanie ochrany
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
    
    # Simulujeme realny mobilny prehliadac (iPhone)
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'sk-SK,sk;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    for start in [0, 20, 40]:
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        print(f"Skusam nacitat: {current_url}")
        
        try:
            response = requests.get(current_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Chyba: Bazos vratil kod {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hladame vsetky inzeraty podla hlavnej struktury
            inzeraty = soup.find_all('div', class_='listin')
            
            # Ak listin nefunguje, skusime univerzalnejsie hladanie cez nadpisy
            if not inzeraty:
                inzeraty = soup.select('.listintele, .listin, .mainclanek')

            print(f"Najdenych inzeratov na strane {int(start/20)+1}: {len(inzeraty)}")
            
            for inz in inzeraty:
                nadpis_tag = inz.find('h2', class_='nadpis')
                if not nadpis_tag: continue
                
                link_tag = nadpis_tag.find('a')
                if not link_tag: continue
                
                title = link_tag.text.strip()
                link = "https://mobil.bazos.sk" + link_tag['href']
                
                price_tag = inz.find('div', class_='listicena')
                price = price_tag.text.strip() if price_tag else "N/A"
                
                inz_id = link.split('/')[-2] if '/' in link else title

                if inz_id not in videne:
                    msg = f"📱 Nový inzerát!\n{title}\nCena: {price}\n{link}"
                    send_telegram(msg)
                    videne.append(inz_id)
            
            # Kratka pauza, aby sme nevyzerali ako bot
            time.sleep(2)
            
        except Exception as e:
            print(f"Chyba pri spracovani strany: {e}")

    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))
    print("Hotovo.")

if __name__ == "__main__":
    scrape()
