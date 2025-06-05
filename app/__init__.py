import os
from flask import Flask
from flask_cors import CORS
from werkzeug.utils import secure_filename

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_mapping(
        UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER', 'uploads'),
        MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    )
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes.business import bp as business_bp
    app.register_blueprint(business_bp, url_prefix='/api')
    
    return app 