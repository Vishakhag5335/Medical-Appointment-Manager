import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from config import config
from app.extensions import db, migrate, login_manager, csrf, mail


def create_app(config_name=None):
    """Application factory for Flask app."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Configure logging
    setup_logging(app)

    # Register blueprints
    from app.routes import main_bp, auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)


    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    # Teardown database session after each request context
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # Register error handlers
    register_error_handlers(app)



    return app


def setup_logging(app):
    """Configures application logging."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/medical_app.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Medical Appointment Manager Startup')


def register_error_handlers(app):
    """Register HTTP error handlers."""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
