#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

HTML = open('web_ui_simple_final.html', 'r', encoding='utf-8').read()

@app.route('/')
def index():
    return HTML

@app.route('/api/status')
def status():
    from nfo_to_vsmeta_webui_state import _state
    return {
        'is_running': _state['is_running'],
        'progress': _state['progress']
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=True)
