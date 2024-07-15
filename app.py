from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from download_pdfs import get_pdf_urls, download_pdfs_to_zip
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Nécessaire pour utiliser flash messages

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Récupérer l'année courante du système et utiliser le mois de juin (mois 6) pour le test
        now = datetime.now()
        year = now.year
        month = now.month  # Tester pour le mois de juin
        base_url = f'http://www.sgg.gov.ma/BulletinOfficiel.aspx'
        zip_filename = 'bulletins_officiels.zip'

        pdf_urls = get_pdf_urls(base_url, year, month)
        
        if not pdf_urls:
            flash("Aucun PDF trouvé pour ce mois.", 'error')
        else:
            download_pdfs_to_zip(pdf_urls, zip_filename)
            flash("Les fichiers PDF du mois ont été téléchargés avec succès!", 'success')
            return redirect(url_for('download_zip'))

    return render_template('index.html')

@app.route('/download')
def download_zip():
    zip_filename = 'bulletins_officiels.zip'
    if os.path.exists(zip_filename):
        return send_file(zip_filename, as_attachment=True)
    else:
        flash("Le fichier zip n'existe pas.", 'error')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
