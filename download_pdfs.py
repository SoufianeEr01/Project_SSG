import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
from datetime import datetime
import pdfplumber
import shutil
import json
import zipfile

chrome_options = Options()
chrome_options.add_argument("--headless")

def get_pdf_urls(base_url, year, month):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.get(base_url)
    
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pdf_urls = []
    
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
        return response.url
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

def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ''
    return text

def save_text_from_pdfs(pdf_urls, directory='pdf_texts', json_filename='pdf_texts.json'):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    
    if os.path.exists(json_filename):
        os.remove(json_filename)
    
    texts = {}
    for url in pdf_urls:
        final_url = resolve_final_pdf_url(url)
        if final_url:
            try:
                response = requests.get(final_url)
                response.raise_for_status()
                pdf_data = response.content
                pdf_name = final_url.split('/')[-1]
                pdf_path = os.path.join(directory, pdf_name)
                
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_data)
                
                text = extract_text_from_pdf(pdf_path)
                text_filename = f"{os.path.splitext(pdf_name)[0]}.txt"
                with open(os.path.join(directory, text_filename), 'w', encoding='utf-8') as f:
                    f.write(text)
                
                texts[pdf_name] = text
                print(f"Texte extrait et sauvegardé pour : {pdf_name}")
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors du téléchargement de {final_url}: {e}")
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(texts, f)

def load_text_from_json(json_filename='pdf_texts.json'):
    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    base_url = 'http://www.sgg.gov.ma/BulletinOfficiel.aspx'
    zip_filename = 'bulletins_officiels.zip'
    
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    
    now = datetime.now()
    pdf_urls = get_pdf_urls(base_url, now.year, now.month)
    
    if not pdf_urls:
        print("Aucun PDF trouvé, rien à faire.")
    else:
        download_pdfs_to_zip(pdf_urls, zip_filename)
        save_text_from_pdfs(pdf_urls)
        print(f"Tous les fichiers PDF ont été compressés dans {zip_filename}")
