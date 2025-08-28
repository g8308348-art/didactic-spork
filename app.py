from __future__ import annotations

# Entry point to run the Flask app with Waitress on Windows (or any OS)
# Listens on 0.0.0.0:8088
# Note: Waitress does not terminate TLS itself. Use a reverse proxy (IIS, Nginx, Caddy)
# to provide HTTPS, forwarding requests to this server. ProxyFix makes Flask
# respect X-Forwarded-* headers set by the proxy.

from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_server import app

# Honor X-Forwarded-* headers from a trusted reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


def main() -> None:
    serve(app, host="0.0.0.0", port=8088, threads=8)


if __name__ == "__main__":
    main()
