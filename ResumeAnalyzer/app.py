import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from services.parser import ResumeParser
from services.extractor import SkillExtractor
from services.matcher import ResumeMatcher
from services.scorer import ScoreCalculator
from services.suggestions import SuggestionEngine

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

parser = ResumeParser()
extractor = SkillExtractor()
matcher = ResumeMatcher()
scorer = ScoreCalculator()
suggestion_engine = SuggestionEngine()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results')
def results():
    return render_template('results.html')


@app.route('/api/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF and DOCX are supported.'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    return jsonify({
        'success': True,
        'filename': unique_filename,
        'original_name': filename,
        'file_path': file_path
    })


@app.route('/api/parse', methods=['POST'])
def parse_resume():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'error': 'Filename is required'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        parsed_data = parser.parse(file_path)
        return jsonify({'success': True, 'data': parsed_data})
    except Exception as e:
        return jsonify({'error': f'Parsing failed: {str(e)}'}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    filename = data.get('filename')
    job_description = data.get('job_description', '')

    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    if not job_description or len(job_description.strip()) < 20:
        return jsonify({'error': 'Job description must be at least 20 characters'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Resume file not found'}), 404

    try:
        parsed_resume = parser.parse(file_path)
        resume_skills = extractor.extract_skills(parsed_resume.get('raw_text', ''))
        jd_skills = extractor.extract_skills(job_description)

        match_result = matcher.match(parsed_resume, job_description, resume_skills, jd_skills)
        score_result = scorer.calculate(match_result)
        suggestions = suggestion_engine.generate(match_result, score_result, parsed_resume)

        response = {
            'success': True,
            'candidate': {
                'name': parsed_resume.get('name', 'Not Found'),
                'email': parsed_resume.get('email', 'Not Found'),
                'phone': parsed_resume.get('phone', 'Not Found'),
            },
            'parsed_resume': parsed_resume,
            'resume_skills': resume_skills,
            'jd_skills': jd_skills,
            'match_result': match_result,
            'scores': score_result,
            'suggestions': suggestions
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Resume Analyzer API is running'})


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
