#!/usr/bin/env python3
"""Serve the self-contained synthetic demo on loopback; Python standard library only."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'web/dist')
    parser.add_argument('--port', type=int, default=8504)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / 'index.html').is_file():
        parser.error('Built app missing. Run tools/build_web.py or use the complete demo package.')
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError:
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    url = 'http://127.0.0.1:' + str(server.server_address[1]) + '/'
    print('TrialTrace synthetic demo: ' + url, flush=True)
    print('Keep this terminal open. Press Control-C to stop. Use synthetic records only.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
