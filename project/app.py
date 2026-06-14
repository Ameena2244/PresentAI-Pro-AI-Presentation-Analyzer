import os
import json
import tempfile
from flask import Flask, request, jsonify, render_template, send_file, abort
from werkzeug.utils import secure_filename

from utils.pdf_parser import extract_text_from_pdf
from utils.docx_parser import extract_text_from_docx
from utils.gemini_analyzer import GeminiAnalyzer, GeminiError
from utils.report_generator import generate_pdf_report, generate_docx_report

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {'.pdf', '.docx', '.txt'}

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

analyzer = None


def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    filename = secure_filename(f.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(save_path)
    # extract text
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == '.pdf':
            text = extract_text_from_pdf(save_path)
        elif ext == '.docx':
            text = extract_text_from_docx(save_path)
        else:
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
    except Exception as e:
        return jsonify({'error': 'Failed to extract text', 'details': str(e)}), 500

    if not text.strip():
        return jsonify({'error': 'Uploaded file contains no extractable text'}), 400

    # return extracted text so frontend can immediately analyze without extra roundtrip
    return jsonify({'filename': filename, 'text_length': len(text), 'text': text})


@app.route('/read_uploaded_text', methods=['POST'])
def read_uploaded_text():
    data = request.get_json() or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.pdf':
            text = extract_text_from_pdf(path)
        elif ext == '.docx':
            text = extract_text_from_docx(path)
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': 'Failed to read file', 'details': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    text = data.get('text')
    if not text or not text.strip():
        return jsonify({'error': 'No text provided'}), 400
    try:
        # lazy initialize analyzer so app works even if GEMINI env isn't configured yet
        global analyzer
        if analyzer is None:
            try:
                analyzer = GeminiAnalyzer()
            except GeminiError as ge:
                return jsonify({'error': 'Gemini configuration missing', 'details': str(ge)}), 503
        result = analyzer.analyze_presentation(text)
        return jsonify(result)
    except GeminiError as ge:
        return jsonify({'error': 'AI analysis failed', 'details': str(ge)}), 502
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@app.route('/generate_viva', methods=['POST'])
def generate_viva():
    data = request.get_json() or {}
    text = data.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        global analyzer
        if analyzer is None:
            try:
                analyzer = GeminiAnalyzer()
            except GeminiError as ge:
                return jsonify({'error': 'Gemini configuration missing', 'details': str(ge)}), 503
        viva = analyzer.generate_viva(text)
        return jsonify(viva)
    except GeminiError as ge:
        return jsonify({'error': 'AI viva generation failed', 'details': str(ge)}), 502
    except Exception as e:
        return jsonify({'error': 'Viva generation failed', 'details': str(e)}), 500


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    payload = request.get_json() or {}
    report = payload.get('report')
    if not report:
        return jsonify({'error': 'No report data provided'}), 400
    fd, path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    try:
        generate_pdf_report(report, path)
        return send_file(path, as_attachment=True, download_name='presentaipro_report.pdf')
    finally:
        try: os.remove(path)
        except: pass


@app.route('/download_docx', methods=['POST'])
def download_docx():
    payload = request.get_json() or {}
    report = payload.get('report')
    if not report:
        return jsonify({'error': 'No report data provided'}), 400
    fd, path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    try:
        generate_docx_report(report, path)
        return send_file(path, as_attachment=True, download_name='presentaipro_report.docx')
    finally:
        try: os.remove(path)
        except: pass


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
