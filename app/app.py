import os
import logging
import hashlib
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes.main import main_bp, cache

load_dotenv()

def create_app():
    app = Flask(__name__)

    # 1. Absolute Path Configuration
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 🛠️ THE FIX: Auto-create the cache folder so Windows doesn't crash
    cache_dir = os.path.join(base_dir, 'flask_cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    app.config['CACHE_TYPE'] = 'FileSystemCache'
    app.config['CACHE_DIR'] = cache_dir
    app.config['CACHE_DEFAULT_TIMEOUT'] = 86400  # 24 Hours
    app.secret_key = os.getenv("MY_SECRET_KEY", "vnr_secret_2026")

    # 2. Initialize Cache
    cache.init_app(app)

    # 3. Initialize Rate Limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    app.limiter = limiter

    # 4. Professional Logging
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(log_dir, 'vnr_engine.log'))
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('VNR Vanguard Engine Startup | Subdirectory Mode')

    # 5. Register Blueprints
    app.register_blueprint(main_bp)

    # 6. Global Rate Limit Error Handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('dashboard.html', 
                               students=None,
                               error="Rate limit exceeded. Please wait a moment before scraping again."), 429

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)