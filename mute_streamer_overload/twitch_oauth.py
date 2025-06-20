import os
import webbrowser
import threading
import http.server
import urllib.parse
import requests
import json
import time
from mute_streamer_overload.utils.config import get_config, set_config, save_config

def get_twitch_client_info():
    twitch = get_config('twitch', {})
    client_id = twitch.get('client_id')
    client_secret = twitch.get('client_secret')
    if client_id and client_secret:
        return client_id, client_secret
    # Fallback to twitch_secret.json
    try:
        with open(os.path.join(os.path.dirname(__file__), '../../twitch_secret.json'), 'r') as f:
            secret_data = json.load(f)
        return secret_data['client_id'], secret_data['client_secret']
    except Exception:
        return None, None

CLIENT_ID, CLIENT_SECRET = get_twitch_client_info()
REDIRECT_URI = "http://localhost:17563/twitch_oauth_callback"
SCOPES = "chat:edit chat:read"
OAUTH_URL = (
    f"https://id.twitch.tv/oauth2/authorize?response_type=token"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
)

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/twitch_oauth_callback"):
            # Parse the fragment from the URL (access_token is in the fragment)
            html = """
            <html><body>
            <script>
            // Parse the access token from the URL fragment
            var hash = window.location.hash.substring(1);
            var params = {};
            hash.split('&').forEach(function(part) {
                var item = part.split('=');
                params[item[0]] = item[1];
            });
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/twitch_token', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(params));
            document.write('<h2>You may now close this window.</h2>');
            </script>
            </body></html>
            """
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/twitch_token":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            access_token = params.get('access_token')
            if access_token:
                # Get user info
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Client-Id': CLIENT_ID
                }
                resp = requests.get('https://api.twitch.tv/helix/users', headers=headers)
                username = None
                if resp.ok:
                    data = resp.json()
                    if data['data']:
                        username = data['data'][0]['login']
                set_config('twitch.access_token', access_token)
                set_config('twitch.username', username)
                save_config()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_error(404)

def start_twitch_oauth_flow(parent=None):
    import urllib.parse
    client_id, _ = get_twitch_client_info()
    if not client_id:
        print("[Twitch] No client ID set.")
        return
    REDIRECT_URI = "http://localhost:17563/twitch_oauth_callback"
    SCOPES = "chat:edit chat:read"
    oauth_url = (
        f"https://id.twitch.tv/oauth2/authorize?response_type=token"
        f"&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    def run_server():
        server = http.server.HTTPServer(('localhost', 17563), OAuthHandler)
        # Handle only one request (the callback)
        server.handle_request()
        server.server_close()
        if parent:
            parent.load_current_config()
    threading.Thread(target=run_server, daemon=True).start()
    webbrowser.open(oauth_url)

def send_message_to_twitch_chat(message):
    twitch = get_config('twitch', {})
    access_token = twitch.get('access_token')
    client_id = twitch.get('client_id') or CLIENT_ID
    channel = twitch.get('channel') or twitch.get('username')
    if not (access_token and client_id and channel):
        print("[Twitch] Missing credentials or channel.")
        return False
    # Get broadcaster/user ID
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': client_id
    }
    resp = requests.get('https://api.twitch.tv/helix/users', headers=headers)
    if not resp.ok or not resp.json().get('data'):
        print("[Twitch] Failed to get user info.")
        return False
    user_id = resp.json()['data'][0]['id']
    # Send message
    chat_url = f'https://api.twitch.tv/helix/chat/messages'
    payload = {
        'broadcaster_id': user_id,
        'sender_id': user_id,
        'message': message
    }
    resp = requests.post(chat_url, headers=headers, json=payload)
    if resp.ok:
        print("[Twitch] Message sent to chat.")
        return True
    else:
        print(f"[Twitch] Failed to send message: {resp.text}")
        return False 