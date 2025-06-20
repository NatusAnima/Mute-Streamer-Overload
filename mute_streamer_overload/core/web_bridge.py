from flask_socketio import SocketIO

# This variable will be set by the web server at startup.
# It acts as a bridge to allow other parts of the application to send
# data to the web clients without creating circular dependencies.
socketio: SocketIO | None = None

def web_update_message(text: str):
    """Emits a 'text_update' event to all connected web clients."""
    if socketio:
        socketio.emit('text_update', {'text': text})

def web_update_animation(settings: dict):
    """Emits an 'animation_update' event to all connected web clients."""
    if socketio:
        socketio.emit('animation_update', {'settings': settings}) 