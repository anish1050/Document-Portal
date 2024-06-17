from flask import Flask, request, redirect, url_for, render_template
import PyPDF2
from PyPDF2 import PdfReader, PdfFileWriter
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] ={ 'pdf' }

def allowed_file(filename):
    return'.'in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=['POST'])
def upload_file():

    if 'pdf' not in request.files:
        print("No file part")
        return 'No Files Part'
    file = request.files['pdf']
    if file.filename == '':
        print("No selected file")
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print("File uploaded and saved")
        return redirect(url_for('display_pdf', filename=filename))
    print("Invalid file format")
    return 'Invalid file Format'

def extract_text_from_pdf(pdf_path, page_number):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        if page_number >= 1 and page_number <= len(reader.pages):
            text = reader.pages[page_number - 1].extract_text()
            return text
        else:
            return 'Invalid page number'

@app.route("/display/<filename>")
def display_pdf(filename):
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"],filename)
    page_number = 1
    text = extract_text_from_pdf(pdf_path, page_number)
    return render_template("display.html", text=text)


if __name__ == "__main__":
    app.run(debug=True)