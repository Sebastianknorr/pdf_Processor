from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from main import PDFProcessor
import shutil
import logging
import zipfile
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'input')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Ingen fil valgt'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Ingen fil valgt'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"File uploaded successfully: {filename}")
            return jsonify({'message': 'Fil lastet opp', 'filename': filename})
        
        return jsonify({'error': 'Ugyldig filtype. Kun PDF-filer er tillatt'}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'Feil ved opplasting av fil'}), 500

@app.route('/process', methods=['POST'])
def process_files():
    try:
        processor = PDFProcessor()
        processor.process_files()
        
        # Get the list of processed files
        output_files = []
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            if filename.startswith('Prosessert_'):
                output_files.append(filename)
        
        logger.info(f"Files processed successfully. Found {len(output_files)} processed files.")
        logger.info(f"Processed files: {output_files}")
        
        return jsonify({
            'message': 'Filer behandlet',
            'files': output_files
        })
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        return jsonify({'error': 'Feil ved behandling av filer'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Check if the filename already has the prefix
        if not filename.startswith('Prosessert_'):
            filepath = os.path.join(app.config['OUTPUT_FOLDER'], f'Prosessert_{filename}')
        else:
            filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return jsonify({'error': 'Fil ikke funnet'}), 404
            
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Feil ved nedlasting av fil'}), 500

@app.route('/files')
def list_files():
    try:
        output_files = []
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            if filename.startswith('Prosessert_'):
                output_files.append(filename)
        return jsonify({'files': output_files})
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': 'Feil ved henting av filer'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port) 