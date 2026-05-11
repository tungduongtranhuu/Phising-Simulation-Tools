from flask import Flask, render_template, redirect
from database.db import init_db
from routes.campaign_routes import campaign_bp
from routes.dashboard_routes import dashboard_bp
from routes.tracking_routes import tracking_bp
from routes.user_routes import user_bp
from routes.api_routes import api_bp
from config import DevelopmentConfig

app = Flask(__name__)

# Load configuration
app.config.from_object(DevelopmentConfig)

# Register Blueprints
app.register_blueprint(campaign_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(tracking_bp)
app.register_blueprint(user_bp)
app.register_blueprint(api_bp)


@app.route("/")
def home():
    # Rediriger vers le dashboard au lieu de render directement
    # pour éviter les erreurs de variables manquantes
    return redirect("/dashboard")


@app.route("/landing")
def landing():
    return render_template("landing.html")


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run the application
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )
