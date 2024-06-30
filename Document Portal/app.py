from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        print("No file part")
        return 'No file part'
    file = request.files['pdf']
    if file.filename == '':
        print("No selected file")
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print("File uploaded and saved")
        return redirect(url_for('display_pdf', filename=filename))
    print("Invalid file format")
    return 'Invalid file format'

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def convert_pdf_to_images(pdf_path, upload_folder):
    images = convert_from_path(pdf_path)
    image_paths = []
    for i, image in enumerate(images):
        image_filename = f'page_{i + 1}.png'
        image_path = os.path.join(upload_folder, image_filename)
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths

def extract_images_from_pdf(pdf_path, upload_folder):
    extracted_images = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if page.images:
                for img_num, img in enumerate(page.images):
                    image = page.within_bbox((img['x0'], img['top'], img['x1'], img['bottom'])).to_image()
                    image_filename = f'extracted_image_{i + 1}_{img_num + 1}.png'
                    image_path = os.path.join(upload_folder, image_filename)
                    image.save(image_path, format="PNG")
                    extracted_images.append(url_for('uploaded_file', filename=image_filename))
    return extracted_images

def extract_tables_from_images(image_paths):
    tables = []
    for image_path in image_paths:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if w > 50 and h > 50 and 0.2 < aspect_ratio < 5:  # Filtering out non-table-like structures
                table = image[y:y+h, x:x+w]
                table_filename = f'table_{os.path.basename(image_path)}_{len(tables) + 1}.png'
                table_path = os.path.join(app.config['UPLOAD_FOLDER'], table_filename)
                cv2.imwrite(table_path, table)
                tables.append(url_for('uploaded_file', filename=table_filename))
    return tables

def extract_flowcharts_from_images(image_paths):
    flowcharts = []
    for image_path in image_paths:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        edges = cv2.Sobel(image, cv2.CV_8U, 1, 1, ksize=3)
        _, thresh = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 10000:  # Filtering based on contour area
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                if len(approx) > 5:  # Assuming flowcharts have more complex shapes
                    x, y, w, h = cv2.boundingRect(contour)
                    flowchart = image[y:y+h, x:x+w]
                    flowchart_filename = f'flowchart_{os.path.basename(image_path)}_{len(flowcharts) + 1}.png'
                    flowchart_path = os.path.join(app.config['UPLOAD_FOLDER'], flowchart_filename)
                    cv2.imwrite(flowchart_path, flowchart)
                    flowcharts.append(url_for('uploaded_file', filename=flowchart_filename))
    return flowcharts

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/display/<filename>")
def display_pdf(filename):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text = extract_text_from_pdf(pdf_path)
    image_paths = convert_pdf_to_images(pdf_path, app.config['UPLOAD_FOLDER'])
    extracted_images = extract_images_from_pdf(pdf_path, app.config['UPLOAD_FOLDER'])
    tables = extract_tables_from_images(image_paths)
    flowcharts = extract_flowcharts_from_images(image_paths)
    
    return render_template("display.html", text=text, images=extracted_images, tables=tables, flowcharts=flowcharts)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)