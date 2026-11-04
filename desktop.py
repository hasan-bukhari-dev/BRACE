"""Native lifecycle controller for the unchanged local BRACE web application.

Packaged builds store generated research data outside their read-only resources.
The --headless switch is for reproducible binary checks and managed operation.
"""
from __future__ import annotations
import argparse
import logging
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser

VERSION = '1.0.0-v6'


def data_directory(environ=None, platform=None, home=None):
    env = os.environ if environ is None else environ
    system = sys.platform if platform is None else platform
    user = Path.home() if home is None else Path(home)
    if env.get('BRACE_DATA_DIR'):
        return Path(env['BRACE_DATA_DIR']).expanduser().resolve()
    if system == 'win32':
        return Path(env.get('LOCALAPPDATA', str(user/'AppData/Local')))/'BRACE'
    if system == 'darwin':
        return user/'Library/Application Support/BRACE'
    return Path(env.get('XDG_DATA_HOME', str(user/'.local/share')))/'BRACE'


def configure_runtime():
    root = data_directory()
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('BRACE_RUNS_DIR', str(root/'runs'))
    (root/'logs').mkdir(exist_ok=True)
    # Windowed executables have no console streams; Uvicorn's logging needs one.
    stream = (root/'logs/desktop.log').open('a', encoding='utf-8', buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    logging.basicConfig(filename=root/'logs/desktop.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    return root


def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(str(path))
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def native_controller(root, self_test=False):
    import tkinter as tk
    from tkinter import ttk, messagebox
    import uvicorn
    from launch import reserve_port

    window = tk.Tk()
    window.title('BRACE · Research Workbench')
    window.geometry('560x310')
    window.minsize(460, 290)
    window.configure(background='#f6f7fa')
    icon = Path(__file__).with_name('brace.ico')
    if sys.platform == 'win32' and icon.exists():
        window.iconbitmap(str(icon))
    panel = ttk.Frame(window, padding=24)
    panel.pack(fill='both', expand=True)
    ttk.Label(panel, text='BRACE', font=('Segoe UI', 24, 'bold')).pack(anchor='w')
    ttk.Label(panel, text='Biological Reliability Assessment\nacross Cohorts and Experiments').pack(anchor='w', pady=(2, 14))
    status = tk.StringVar(value='Starting the local workbench…')
    address = tk.StringVar(value='Your browser will open when the server is ready.')
    ttk.Label(panel, textvariable=status, wraplength=490).pack(anchor='w')
    ttk.Label(panel, textvariable=address, wraplength=490).pack(anchor='w', pady=(5, 16))
    buttons = ttk.Frame(panel)
    buttons.pack(fill='x')
    opened = ttk.Button(buttons, text='Open workbench', state='disabled')
    opened.pack(side='left')
    folder = ttk.Button(buttons, text='Open data folder', command=lambda: open_folder(root))
    folder.pack(side='left', padx=8)
    stop = ttk.Button(buttons, text='Stop & close')
    stop.pack(side='right')
    ttk.Label(panel, text='Research only. Closing this window stops the local server.',
              wraplength=490).pack(anchor='w', pady=(18, 0))
    state = {'server': None, 'listener': None, 'error': None, 'ready': False,
             'stopping': False, 'address': None}

    def serve():
        try:
            listener, port = reserve_port()
            state['listener'] = listener
            os.environ['BRACE_PORT'] = str(port)
            state['address'] = 'http://127.0.0.1:'+str(port)
            config = uvicorn.Config('brace_app.server:app', host='127.0.0.1', port=port,
                                    log_level='warning', access_log=False)
            server = uvicorn.Server(config)
            state['server'] = server
            if state['stopping']:
                return
            server.run(sockets=[listener])
        except BaseException as exc:
            state['error'] = str(exc)
            logging.exception('Local server stopped unexpectedly')
        finally:
            if state['listener'] is not None:
                state['listener'].close()

    thread = threading.Thread(target=serve, name='BRACE-local-server')

    def close():
        state['stopping'] = True
        status.set('Stopping safely; waiting for active requests to finish…')
        opened.configure(state='disabled')
        stop.configure(state='disabled')
        if state['server']:
            state['server'].should_exit = True

    def poll():
        if state['stopping'] and not thread.is_alive():
            window.destroy()
            return
        server = state['server']
        if server and server.started and not state['ready'] and not state['stopping']:
            state['ready'] = True
            status.set('Running locally · '+VERSION)
            address.set(state['address'])
            opened.configure(state='normal', command=lambda: webbrowser.open(state['address']))
            if self_test:
                (root/'launcher-self-test.json').write_text(
                    '{"status":"PASS","ready":true,"native_window":true}', encoding='utf-8')
                window.after(500, close)
            elif os.environ.get('BRACE_NO_BROWSER') != '1':
                webbrowser.open(state['address'])
        if not thread.is_alive() and not state['stopping']:
            status.set('BRACE could not start. Open the data folder to inspect logs/desktop.log.')
            address.set(state['error'] or 'The local server stopped unexpectedly.')
            stop.configure(text='Close', command=window.destroy)
            if self_test:
                window.destroy()
                raise RuntimeError(state['error'] or 'Native launcher did not start')
            return
        window.after(100, poll)

    stop.configure(command=close)
    window.protocol('WM_DELETE_WINDOW', close)
    thread.start()
    window.after(100, poll)
    window.mainloop()
    if thread.is_alive():
        close()
        thread.join()
    if self_test and not state['ready']:
        raise RuntimeError('Native launcher readiness was not verified')


def main():
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description='BRACE local research workbench')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--headless', action='store_true', help='Run the local server without the native controller')
    parser.add_argument('--launcher-self-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = configure_runtime()
    if args.headless:
        os.environ['BRACE_NO_BROWSER'] = '1'
        from launch import main as launch
        launch()
    else:
        native_controller(root, args.launcher_self_test)


if __name__ == '__main__':
    main()
