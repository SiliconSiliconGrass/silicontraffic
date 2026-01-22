import threading

_port_factory = 8831
_lock = threading.Lock()

def get_unique_port():
    global _port_factory
    with _lock:
        if _port_factory > 65535: # normally not possible to happen
            print("[get_unique_port] Warning: port factory exceeds 65535, reset to 8831")
            _port_factory = 8831
        _port_factory += 1
    return _port_factory
