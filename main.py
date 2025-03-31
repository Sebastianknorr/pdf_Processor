from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from pdf_processor.processor import PDFProcessor
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
import zipfile
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DATA_DIR = os.path.join(BASE_DIR, 'data')

app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)

# Add ProxyFix middleware to handle HTTPS properly
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response

app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'input')
app.config['OUTPUT_FOLDER'] = os.path.join(DATA_DIR, 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure data directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Create a single PDFProcessor instance
pdf_processor = PDFProcessor(
    input_dir=app.config['UPLOAD_FOLDER'],
    output_dir=app.config['OUTPUT_FOLDER']
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Ingen filer valgt'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'Ingen filer valgt'}), 400
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filename)
                logger.info(f"File uploaded successfully: {filename}")
            else:
                return jsonify({'error': f'Ugyldig filtype: {file.filename}. Kun PDF-filer er tillatt'}), 400
        
        return jsonify({
            'message': f'{len(uploaded_files)} fil(er) lastet opp',
            'files': uploaded_files
        })
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        return jsonify({'error': 'Feil ved opplasting av filer'}), 500

@app.route('/process', methods=['POST'])
def process_files():
    try:
        pdf_processor.process_files()
        
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

@app.route('/download-all')
def download_all_files():
    try:
        # Create a BytesIO object to store the ZIP file
        memory_file = io.BytesIO()
        
        # Create the ZIP file
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all processed files to the ZIP
            for filename in os.listdir(app.config['OUTPUT_FOLDER']):
                if filename.startswith('Prosessert_'):
                    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                    zf.write(filepath, filename)
        
        # Seek to the beginning of the BytesIO object
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='processed_files.zip'
        )
    except Exception as e:
        logger.error(f"Error creating ZIP file: {str(e)}")
        return jsonify({'error': 'Feil ved nedlasting av filer'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port) 