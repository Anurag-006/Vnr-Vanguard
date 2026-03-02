import os
import logging
from flask import Flask
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes.main import main_bp, cache

load_dotenv()

def create_app():
    app = Flask(__name__)

    # 1. Configuration
    app.config['CACHE_TYPE'] = 'FileSystemCache'
    app.config['CACHE_DIR'] = 'flask_cache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 86400  # 24 Hours
    app.secret_key = os.getenv("MY_SECRET_KEY", "vnr_secret_2026")

    # 2. Initialize Cache
    cache.init_app(app)

    # 3. Initialize Rate Limiter
    # 'memory://' is used for the storage backend as it's fast and 
    # suitable for the single-instance deployments like Render's free tier.
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["100 per day", "30 per hour"],
        storage_uri="memory://",
    )
    
    # Store limiter on app so blueprints can access it if needed via current_app
    app.limiter = limiter

    # 4. Setup Professional Logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = logging.FileHandler('logs/vnr_engine.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('VNR Vanguard Engine Startup with Rate Limiting')

    # 5. Register the Main Routes Blueprint
    app.register_blueprint(main_bp)

    # 6. Global Rate Limit Error Handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('error.html', 
                               title="Rate Limit Exceeded", 
                               message="Whoa there! You're making too many requests. Please wait a minute."), 429

    return app

app = create_app()

if __name__ == '__main__':
    # Using 0.0.0.0 for local network access (PC + Phone testing)
    app.run(host='0.0.0.0', port=5000, debug=True)