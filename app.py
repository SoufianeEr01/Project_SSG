from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import os
from datetime import datetime
from download_pdfs import get_pdf_urls, download_pdfs_to_zip, save_text_from_pdfs, load_text_from_json
import openai

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuration de votre serveur OpenAI local
openai.api_base = "http://localhost:1234/v1"
openai.api_key = "lm-studio"

def ask_question(question, context):
    response = openai.ChatCompletion.create(
        model="model-identifier",  # Remplacez par le modèle que vous utilisez
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

@app.route('/', methods=['GET', 'POST'])
def index():
    download_success = False
    if request.method == 'POST':
        now = datetime.now()
        year = now.year
        month = 4
        base_url = 'http://www.sgg.gov.ma/BulletinOfficiel.aspx'
        zip_filename = 'bulletins_officiels.zip'

        pdf_urls = get_pdf_urls(base_url, year, month)
        
        if not pdf_urls:
            flash("Aucun PDF trouvé pour ce mois.", 'error')
        else:
            download_pdfs_to_zip(pdf_urls, zip_filename)
            save_text_from_pdfs(pdf_urls)
            flash("Les fichiers PDF du mois ont été téléchargés et le texte a été extrait avec succès!", 'success')
            download_success = True

    return render_template('index.html', download_success=download_success)

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question')
    texts = load_text_from_json()
    context = " ".join(texts.values())
    answer = ask_question(question, context)
    return jsonify({'answer': answer})

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
