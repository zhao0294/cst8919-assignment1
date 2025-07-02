import os
import logging
import json
from flask import Flask, redirect, render_template, session, url_for, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "your_default_key")
app.config['DEBUG'] = True

# Configure structured logging for Azure Monitor
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

oauth = OAuth(app)

AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')

oauth.register(
    name="auth0",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url=f"https://{AUTH0_DOMAIN}",
    access_token_url=f"https://{AUTH0_DOMAIN}/oauth/token",
    authorize_url=f"https://{AUTH0_DOMAIN}/authorize",
    userinfo_endpoint=f"https://{AUTH0_DOMAIN}/userinfo",
    jwks_uri=f"https://{AUTH0_DOMAIN}/.well-known/jwks.json",
    client_kwargs={"scope": "openid profile email"},
)

def log_user_activity(activity_type, user_info=None, details=None):
    """Log user activity in structured format for Azure Monitor"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "activity_type": activity_type,
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', ''),
        "details": details or {}
    }
    
    if user_info:
        log_data.update({
            "user_id": user_info.get('sub', ''),
            "email": user_info.get('email', ''),
            "name": user_info.get('name', '')
        })
    
    app.logger.info(f"USER_ACTIVITY: {json.dumps(log_data)}")

@app.route("/")
def home():
    user = session.get('user')
    log_user_activity("home_page_access", 
                     user_info=user.get('userinfo') if user else None)
    return render_template("home.html", user=user)

@app.route("/login")
def login():
    log_user_activity("login_initiated")
    return oauth.auth0.authorize_redirect(redirect_uri=url_for("callback", _external=True))

@app.route("/callback")
def callback():
    try:
        # Get authorization code from URL
        code = request.args.get('code')
        if not code:
            raise Exception("No authorization code received")
        
        # Exchange code for token
        token = oauth.auth0.authorize_access_token()
        
        # Get user info
        userinfo = oauth.auth0.get('userinfo', token=token).json()
        
        # Store only essential user info to avoid large cookies
        session['user'] = {
            'userinfo': {
                'sub': userinfo.get('sub'),
                'email': userinfo.get('email'),
                'name': userinfo.get('name'),
                'picture': userinfo.get('picture')
            }
        }
        
        # Log successful login
        log_user_activity("login_successful", 
                         user_info=userinfo,
                         details={"redirect_target": "/protected"})
        
        return redirect("/protected")
    except Exception as e:
        # Log failed login attempt
        log_user_activity("login_failed", 
                         details={"error": str(e), "callback_url": request.url})
        app.logger.error(f"OAuth callback failed: {e}")
        return f"Login failed: {str(e)}", 400

@app.route("/logout")
def logout():
    user = session.get('user')
    user_info = user.get('userinfo') if user else None
    
    log_user_activity("logout", 
                     user_info=user_info)
    
    session.clear()
    # For local development, redirect directly to home
    # For production, use Auth0 logout
    if os.getenv('FLASK_ENV') == 'development' or 'localhost' in request.host or '3000' in request.host:
        return redirect(url_for('home'))
    else:
        return redirect(f"https://{AUTH0_DOMAIN}/v2/logout?returnTo={url_for('home', _external=True)}")

@app.route("/protected")
def protected():
    user = session.get('user')
    
    if not user or not user.get('userinfo'):
        # Log unauthorized access attempt
        log_user_activity("unauthorized_access_attempt", 
                         details={"target_route": "/protected", "reason": "no_valid_session"})
        return redirect("/login")
    
    # Log successful access to protected route
    log_user_activity("protected_route_access", 
                     user_info=user['userinfo'],
                     details={"route": "/protected"})
    
    return render_template("protected.html", user=user['userinfo'])

# Add a health check endpoint for monitoring
@app.route("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}, 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))