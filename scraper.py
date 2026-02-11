import requests
from bs4 import BeautifulSoup
import os

# Konfiguracia - Tvoja URL (upravena pre strankovanie)
BASE_URL = "https://mobil.bazos.sk/{page}?hledat=5g&hlokalita=&humkreis=25&cenaod=30&cenado=250&order="
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATA_FILE = "videne_inzeraty.txt"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        print(f"Status odoslania na Telegram: {r.status_code}")
    except Exception as e:
        print(f"Chyba pri odosielani: {e}")

def scrape():
    videne = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            videne = f.read().splitlines()
    
    print(f"Pocet videnych inzeratov v archive: {len(videne)}")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
    
    # Prechadzame prve 3 strany (0, 20, 40)
    for start in [0, 20, 40]:
        page_param = f"{start}/" if start > 0 else ""
        current_url = BASE_URL.format(page=page_param)
        
        print(f"Kontrolujem stranu {int(start/20)+1}: {current_url}")
        
        response = requests.get(current_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Bazoš pouziva rozne triedy, skusime najst vsetky bezne typy
        inzeraty = soup.find_all('div', class_=['listin', 'listintele'])
        
        print(f"Najdenych inzeratov na strane: {len(inzeraty)}")
        
        for inz in inzeraty:
            # Hladame nadpis a link
            nadpis_tag = inz.find('h2', class_='nadpis')
            if not nadpis_tag:
                continue
            
            link_tag = nadpis_tag.find('a')
            if not link_tag:
                continue
            
            title = link_tag.text.strip()
            link = "https://mobil.bazos.sk" + link_tag['href']
            
            # Cena
            cena_tag = inz.find('div', class_='listicena')
            cena = cena_tag.text.strip() if cena_tag else "N/A"
            
            # ID inzeratu z URL
            try:
                inz_id = link.split('/')[-2]
            except:
                continue

            if inz_id not in videne:
                msg = f"📱 Nový inzerát (Strana {int(start/20)+1})!\n{title}\nCena: {cena}\n{link}"
                send_telegram(msg)
                videne.append(inz_id)

    # Ulozime aktualizovany zoznam
    with open(DATA_FILE, "w") as f:
        f.write("\n".join(videne))
    print("Ukladanie dokoncene.")

if __name__ == "__main__":
    scrape()
