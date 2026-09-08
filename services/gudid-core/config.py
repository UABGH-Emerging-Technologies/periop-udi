import os
import socket
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def get_local_ip():
    """
    Get the local IP address of this machine.
    In Docker, use HOST_IP environment variable.
    """
    # First check if HOST_IP is set (required for Docker)
    host_ip = os.getenv("HOST_IP")
    if host_ip and host_ip != "your_local_ip_here":
        return host_ip
    
    # Try to auto-detect local IP (works when running locally, not in Docker)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", ""}


def get_base_url(app_base_url, local_ip, port):
    """
    Browser-reachable origin for this app, used for QR code contents and for the
    `base_url` passed to templates.

    A QR code is scanned by a phone, so the URL inside it has to be reachable
    from another device. Two deployments, two answers:

      * Deployed (Azure Container Apps, or any host behind TLS) — APP_BASE_URL is
        the public https origin. Use it verbatim. The LAN-IP form is wrong there
        on all three counts: the autodetected address is container-internal, the
        scheme is https not http, and the port is the proxy's, not PORT.
      * Local development — APP_BASE_URL is unset or loopback, which no phone can
        reach. Fall back to http://<HOST_IP>:<PORT>, which is what HOST_IP in
        .env.example exists for.
    """
    if app_base_url:
        try:
            host = urlparse(app_base_url).hostname or ""
        except ValueError:
            host = ""
        if host.lower() not in _LOOPBACK_HOSTS:
            return app_base_url.rstrip("/")
    return f"http://{local_ip}:{port}"


class Config:
    """Flask application configuration."""
    
    # Security
    # Signs the Flask session cookie. A stable value is REQUIRED for SMART App
    # Launch — the OAuth2 state / PKCE verifier / session handle live in the
    # session across the authorize redirect. The default is public in this repo,
    # so a deployment that keeps it can have its sessions forged; see the
    # startup check in app.py, which refuses to boot on it in production.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEFAULT_SECRET_KEYS = {
        "dev-secret-key-change-in-production",
        "dev-secret-key",
        "change-this-to-a-random-secret-key",
    }

    # ---- Access gate (auth.py) ----
    # Enforced by default; turn off only for local development.
    REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() not in ("0", "false", "no")
    # Shared passcode for the synthetic-data deployment. No passcode set means
    # local sign-in is unavailable and SMART launch is the only way in.
    DEMO_PASSCODE = os.getenv("DEMO_PASSCODE", "")
    SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", 12 * 3600))

    # Cookie hardening. SECURE_COOKIES should be on wherever the app is served
    # over HTTPS, which is anywhere it is publicly reachable.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"  # Lax, not Strict: the SMART callback is a
                                     # cross-site redirect back into the app and
                                     # must carry the session cookie.
    SESSION_COOKIE_SECURE = os.getenv("SECURE_COOKIES", "false").lower() in (
        "1", "true", "yes",
    )

    # ---- SMART App Launch v2 (services/gudid-core/smart_launch.py) ----
    # Public client, PKCE, no secret. Tested against the SMART Health IT
    # sandbox launcher (https://launch.smarthealthit.org).
    SMART_CLIENT_ID = os.getenv("SMART_CLIENT_ID", "periop-udi")
    SMART_SCOPES = os.getenv(
        "SMART_SCOPES",
        "launch openid fhirUser profile "
        "patient/Patient.read patient/Device.read patient/Device.write "
        "patient/Procedure.read",
    )
    # Scopes for a standalone launch (no EHR "launch" param): swap the EHR
    # "launch" scope for "launch/patient" so the auth server shows a patient picker.
    SMART_STANDALONE_SCOPES = os.getenv(
        "SMART_STANDALONE_SCOPES",
        "launch/patient openid fhirUser profile "
        "patient/Patient.read patient/Device.read patient/Device.write "
        "patient/Procedure.read",
    )
    # FHIR base used for a standalone launch (the EHR supplies its own on an EHR launch).
    SMART_DEFAULT_ISS = os.getenv(
        "SMART_DEFAULT_ISS", "https://launch.smarthealthit.org/v/r4/fhir"
    )
    # Public base URL of THIS app, for building the OAuth redirect_uri.
    APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")

    # The SMART Health IT sandbox always decodes the `launch` parameter as
    # base64url JSON, so a conformant standalone launch (which sends no `launch`)
    # fails against it. Send its simulation options for these hosts only; any
    # other server gets a standard standalone launch. Set empty to disable.
    SMART_SIM_HOSTS = os.getenv("SMART_SIM_HOSTS", "launch.smarthealthit.org")
    SMART_SIM_LAUNCH_TYPE = os.getenv("SMART_SIM_LAUNCH_TYPE", "provider-standalone")

    
    # OpenAI API Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")  # Custom URL support
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default model
    
    # Server settings
    HOST = "0.0.0.0"  # Listen on all interfaces
    PORT = int(os.getenv("PORT", 8080))
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"
    
    # Network settings for QR codes
    LOCAL_IP = get_local_ip()
    BASE_URL = get_base_url(APP_BASE_URL, LOCAL_IP, PORT)
    
    # File paths
    QR_CODE_DIR = "static/qr_codes"
    DEVICES_FILE = "data/devices.json"
    
    # GUDID API settings (FIXED: v2 -> v3)
    GUDID_BASE_URL = "https://accessgudid.nlm.nih.gov/api/v3"
    GUDID_TIMEOUT = 10  # seconds