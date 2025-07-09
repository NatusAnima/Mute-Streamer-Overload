import os
import webbrowser
import threading
import http.server
import urllib.parse
import requests
import json
import time
import logging
import socket
from mute_streamer_overload.utils.config import get_config, set_config, save_config

logger = logging.getLogger(__name__)

# Use a proper client ID from dev.twitch.tv that supports localhost redirects
# This client ID is configured to allow localhost redirects for development
CLIENT_ID = "zhum65yhnitmerei9d2jvn15yhnubg"  # Replace with your actual client ID from dev.twitch.tv
SCOPES = "chat:edit chat:read user:write:chat"

def find_available_port(start_port=17563, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")

# Use a different port to avoid conflicts
OAUTH_PORT = find_available_port(17564)  # Start from 17564 instead of 17563
REDIRECT_URI = f"http://localhost:{OAUTH_PORT}/twitch_oauth_callback"

logger.info(f"Using OAuth port: {OAUTH_PORT}")

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info(f"OAuth Server: {format % args}")
    
    def do_GET(self):
        logger.info(f"Received GET request: {self.path}")
        logger.info(f"Full URL: {self.requestline}")
        
        if self.path.startswith("/twitch_oauth_callback"):
            # Parse the fragment from the URL (access_token is in the fragment)
            html = """
            <html>
            <head>
                <title>Twitch Authorization Complete</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #0e0e10; color: #efeff1; }
                    .container { max-width: 400px; margin: 0 auto; }
                    .success { color: #00ff00; }
                    .error { color: #ff0000; }
                    .info { color: #9147ff; }
                    button { background: #9147ff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
                    button:hover { background: #7c3aed; }
                    .debug { font-size: 12px; color: #666; margin-top: 20px; text-align: left; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Twitch Authorization</h2>
                    <div id="status">Processing authorization...</div>
                    <br>
                    <button onclick="window.close()">Close Window</button>
                </div>
                <div class="debug" id="debug"></div>
                <script>
                    // Debug: Log the current URL and all parameters
                    document.getElementById('debug').innerHTML = 'URL: ' + window.location.href;
                    document.getElementById('debug').innerHTML += '<br>Hash: ' + window.location.hash;
                    
                    // Parse the access token from the URL fragment
                    var hash = window.location.hash.substring(1);
                    var params = {};
                    if (hash) {
                        hash.split('&').forEach(function(part) {
                            var item = part.split('=');
                            if (item.length === 2) {
                                params[item[0]] = decodeURIComponent(item[1]);
                            }
                        });
                    }
                    
                    var accessToken = params['access_token'];
                    var error = params['error'];
                    var errorDescription = params['error_description'];
                    
                    document.getElementById('debug').innerHTML += '<br>Params: ' + JSON.stringify(params);
                    
                    if (accessToken) {
                        document.getElementById('status').innerHTML = '<span class="success">✓ Access token received! Processing...</span>';
                        
                        // Send token to our server
                        var xhr = new XMLHttpRequest();
                        xhr.open('POST', '/twitch_token', true);
                        xhr.setRequestHeader('Content-Type', 'application/json');
                        xhr.onreadystatechange = function() {
                            if (xhr.readyState === 4) {
                                if (xhr.status === 200) {
                                    document.getElementById('status').innerHTML = '<span class="success">✓ Authorization successful! You can now close this window.</span>';
                                } else {
                                    document.getElementById('status').innerHTML = '<span class="error">✗ Failed to save authorization. Please try again.</span>';
                                }
                            }
                        };
                        xhr.send(JSON.stringify({access_token: accessToken}));
                    } else if (error) {
                        var errorMsg = '✗ Authorization failed: ' + error;
                        if (errorDescription) {
                            errorMsg += ' - ' + errorDescription;
                        }
                        document.getElementById('status').innerHTML = '<span class="error">' + errorMsg + '</span>';
                    } else {
                        document.getElementById('status').innerHTML = '<span class="info">No access token received. This might be normal if you cancelled the authorization.</span>';
                    }
                </script>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == "/":
            # Root path - redirect to callback
            self.send_response(302)
            self.send_header('Location', '/twitch_oauth_callback')
            self.end_headers()
        else:
            logger.warning(f"Unknown path requested: {self.path}")
            self.send_error(404)

    def do_POST(self):
        logger.info(f"Received POST request: {self.path}")
        
        if self.path == "/twitch_token":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode('utf-8'))
                access_token = params.get('access_token')
                
                logger.info(f"Received access token: {'Yes' if access_token else 'No'}")
                
                if access_token:
                    try:
                        # Get user info from Twitch API
                        headers = {
                            'Authorization': f'Bearer {access_token}',
                            'Client-Id': CLIENT_ID
                        }
                        resp = requests.get('https://api.twitch.tv/helix/users', headers=headers)
                        
                        if resp.ok:
                            data = resp.json()
                            if data['data']:
                                user_info = data['data'][0]
                                username = user_info['login']
                                display_name = user_info['display_name']
                                
                                # Save to config
                                set_config('twitch.access_token', access_token)
                                set_config('twitch.username', username)
                                set_config('twitch.display_name', display_name)
                                set_config('twitch.client_id', CLIENT_ID)
                                save_config()
                                
                                logger.info(f"Successfully authenticated as {display_name} ({username})")
                            else:
                                logger.error("No user data received from Twitch API")
                        else:
                            logger.error(f"Failed to get user info: {resp.status_code} - {resp.text}")
                            
                    except Exception as e:
                        logger.error(f"Error processing Twitch authentication: {e}")
                else:
                    logger.error("No access token received in POST request")
                    
            except Exception as e:
                logger.error(f"Error processing POST request: {e}")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_error(404)

def start_twitch_oauth_flow(parent=None):
    """Start the Twitch OAuth flow by opening the authorization URL."""
    try:
        # Check if client ID is configured
        if CLIENT_ID == "your_client_id_here":
            logger.error("Client ID not configured. Please set up a Twitch application at dev.twitch.tv")
            return
        
        # Create OAuth URL with state parameter for security
        import secrets
        state = secrets.token_urlsafe(16)
        
        oauth_url = (
            f"https://id.twitch.tv/oauth2/authorize"
            f"?response_type=token"
            f"&client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
            f"&scope={urllib.parse.quote(SCOPES)}"
            f"&state={state}"
        )
        
        logger.info(f"OAuth URL: {oauth_url}")
        logger.info(f"Using redirect URI: {REDIRECT_URI}")
        
        def run_server():
            try:
                server = http.server.HTTPServer(('localhost', OAUTH_PORT), OAuthHandler)
                logger.info(f"Starting OAuth callback server on localhost:{OAUTH_PORT}")
                
                # Handle multiple requests (GET for callback page, POST for token)
                request_count = 0
                max_requests = 2  # Expect GET then POST
                
                while request_count < max_requests:
                    try:
                        server.handle_request()
                        request_count += 1
                        logger.info(f"Handled request {request_count}/{max_requests}")
                    except Exception as e:
                        logger.error(f"Error handling request {request_count + 1}: {e}")
                        break
                
                server.server_close()
                logger.info("OAuth callback server stopped")
                
                # Refresh the parent UI if provided - use Qt's signal mechanism
                if parent and hasattr(parent, 'load_current_config'):
                    # Use QTimer to schedule the UI update on the main thread
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, parent.load_current_config)
                    
            except Exception as e:
                logger.error(f"Error in OAuth server: {e}")
        
        # Start the callback server in a background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Give the server a moment to start
        time.sleep(1.0)
        
        # Open the browser
        logger.info("Opening Twitch authorization page in browser")
        webbrowser.open(oauth_url)
        
    except Exception as e:
        logger.error(f"Failed to start Twitch OAuth flow: {e}")

def send_message_to_twitch_chat(message):
    """Send a message to the user's own Twitch channel."""
    twitch = get_config('twitch', {})
    access_token = twitch.get('access_token')
    username = twitch.get('username')
    
    if not access_token or not username:
        logger.error("Missing Twitch credentials. Please log in first.")
        return False
    
    try:
        # Get user info (this includes the user's channel ID)
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': CLIENT_ID
        }
        
        resp = requests.get('https://api.twitch.tv/helix/users', headers=headers)
        if not resp.ok:
            logger.error(f"Failed to get user info: {resp.status_code}")
            return False
            
        data = resp.json()
        if not data.get('data'):
            logger.error("No user data received")
            return False
            
        user_info = data['data'][0]
        user_id = user_info['id']
        user_login = user_info['login']
        
        # Send message to the user's own channel
        chat_url = 'https://api.twitch.tv/helix/chat/messages'
        payload = {
            'broadcaster_id': user_id,  # Send to user's own channel
            'sender_id': user_id,
            'message': message
        }
        
        resp = requests.post(chat_url, headers=headers, json=payload)
        
        if resp.ok:
            logger.info(f"Message sent to Twitch chat in #{user_login}: {message}")
            return True
        else:
            logger.error(f"Failed to send message: {resp.status_code} - {resp.text}")
            # Log more details for debugging
            if resp.status_code == 403:
                logger.error("Access denied. Make sure you have the 'chat:edit' scope.")
            elif resp.status_code == 400:
                logger.error("Bad request. Check if the message format is valid.")
            return False
            
    except Exception as e:
        logger.error(f"Error sending message to Twitch chat: {e}")
        return False

def is_twitch_authenticated():
    """Check if user is authenticated with Twitch."""
    twitch = get_config('twitch', {})
    return bool(twitch.get('access_token') and twitch.get('username'))

def get_twitch_user_info():
    """Get current Twitch user information."""
    twitch = get_config('twitch', {})
    return {
        'username': twitch.get('username'),
        'display_name': twitch.get('display_name'),
        'authenticated': is_twitch_authenticated()
    }

def logout_twitch():
    """Clear Twitch authentication data."""
    set_config('twitch.access_token', None)
    set_config('twitch.username', None)
    set_config('twitch.display_name', None)
    save_config()
    logger.info("Twitch authentication cleared") 