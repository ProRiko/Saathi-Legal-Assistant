from flask import Flask
from app.routes.ai import ai_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(ai_bp)

    @app.get('/health')
    def health():
        return {
            'status': 'healthy',
            'service': 'saathi-ai-python',
        }

    return app


app = create_app()
