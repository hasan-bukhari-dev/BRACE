"""Loopback port only. The default remains the documented 8765."""
import os
def local_port():
    value=os.environ.get('BRACE_PORT','8765')
    if not value.isdecimal() or not 1024<=int(value)<=65535:
        raise ValueError('BRACE_PORT must be an integer from 1024 to 65535; host stays 127.0.0.1')
    return int(value)
