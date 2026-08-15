from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Configure LoginManager defaults
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """User loader callback for Flask-Login."""
    from app.models.user import User
    db.session.expire_all()
    return db.session.get(User, int(user_id))




