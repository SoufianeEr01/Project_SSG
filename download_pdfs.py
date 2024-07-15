import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import zipfile
import os
from datetime import datetime


# Configuration de Selenium et des options du navigateur
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optionnel: exécute le navigateur en mode headless (sans interface graphique)

def get_pdf_urls(base_url, year, month):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(base_url)
    
    # Attendre que la page soit complètement chargée
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pdf_urls = []
    
    # Parcourir les lignes du tableau
    for row in soup.select('tr'):
        date_cell = row.select('td:nth-child(2) center')
        if date_cell:
            date_text = date_cell[0].text.strip()
            date_parts = date_text.split('-')
            if len(date_parts) == 3 and int(date_parts[0]) == year and int(date_parts[1]) == month:
                pdf_link = row.select('td a')
                if pdf_link:
                    pdf_url = pdf_link[0]['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(base_url, pdf_url)
                    pdf_urls.append(pdf_url)
    
    driver.quit()
    return pdf_urls

def resolve_final_pdf_url(pdf_url):
    try:
        response = requests.get(pdf_url, allow_redirects=True)
        response.raise_for_status()
        return response.url  # Retourne l'URL finale après redirection
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la résolution de {pdf_url}: {e}")
        return None

def download_pdfs_to_zip(pdf_urls, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for url in pdf_urls:
            final_url = resolve_final_pdf_url(url)
            if final_url:
                try:
                    response = requests.get(final_url)
                    response.raise_for_status()
                    pdf_data = response.content
                    pdf_name = final_url.split('/')[-1]
                    zipf.writestr(pdf_name, pdf_data)
                    print(f"Téléchargé et ajouté à l'archive : {pdf_name}")
                except requests.exceptions.RequestException as e:
                    print(f"Erreur lors du téléchargement de {final_url}: {e}")

if __name__ == "__main__":
    base_url = 'http://www.sgg.gov.ma/BulletinOfficiel.aspx'
    zip_filename = 'bulletins_officiels.zip'
    now = datetime.now()
    pdf_urls = get_pdf_urls(base_url, now.year, 6)  # Tester pour le mois de juin
    
    if not pdf_urls:
        print("Aucun PDF trouvé, rien à faire.")
    else:
        download_pdfs_to_zip(pdf_urls, zip_filename)
        print(f"Tous les fichiers PDF ont été compressés dans {zip_filename}")
