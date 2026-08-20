"""Authentication management for Google Search Console API."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow

from search_cli.config import (
    get_config_dir,
    get_config_value,
    get_token_path,
    load_config,
    save_config,
    set_config_value,
)

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/webmasters",
]


class AuthError(Exception):
    """Raised when authentication fails or credentials are missing."""
    pass


def get_stored_credentials_path() -> Path:
    """Return default path for stored client secrets."""
    return get_config_dir() / "client_secrets.json"


def login_oauth(
    client_secrets_path: Optional[Path] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    port: int = 0,
    open_browser: bool = True,
) -> OAuthCredentials:
    """Run OAuth 2.0 Authorization Code flow and save credentials."""
    # 1. Direct Client ID & Client Secret
    c_id = client_id or os.environ.get("SEARCH_CLI_CLIENT_ID") or get_config_value("client_id")
    c_secret = client_secret or os.environ.get("SEARCH_CLI_CLIENT_SECRET") or get_config_value("client_secret")

    if c_id and c_secret:
        client_config = {
            "installed": {
                "client_id": c_id,
                "client_secret": c_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        set_config_value("client_id", c_id)
        set_config_value("client_secret", c_secret)
    else:
        # 2. File-based credentials
        secrets_file: Optional[Path] = None

        if client_secrets_path and Path(client_secrets_path).exists():
            secrets_file = Path(client_secrets_path)
        elif os.environ.get("SEARCH_CLI_CLIENT_SECRETS"):
            env_path = Path(os.environ["SEARCH_CLI_CLIENT_SECRETS"])
            if env_path.exists():
                secrets_file = env_path
        elif get_config_value("client_secrets_path"):
            cfg_path = Path(get_config_value("client_secrets_path"))
            if cfg_path.exists():
                secrets_file = cfg_path
        elif get_stored_credentials_path().exists():
            secrets_file = get_stored_credentials_path()

        if not secrets_file or not secrets_file.exists():
            raise AuthError(
                "OAuth credentials not found!\n"
                "Please authenticate using one of the following methods:\n"
                "  1. Pass client secrets file:  search-cli auth login --credentials /path/to/client_secrets.json\n"
                "  2. Pass Client ID & Secret:   search-cli auth login --client-id <ID> --client-secret <SECRET>\n"
                f"  3. Place credentials file at: {get_stored_credentials_path()}\n"
                "  4. Set environment variables: SEARCH_CLI_CLIENT_ID and SEARCH_CLI_CLIENT_SECRET (or SEARCH_CLI_CLIENT_SECRETS)"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(secrets_file),
            scopes=SCOPES,
        )
        set_config_value("client_secrets_path", str(secrets_file.resolve()))

    creds = flow.run_local_server(
        port=port,
        open_browser=open_browser,
        prompt="consent",
    )

    # Save token
    token_path = get_token_path()
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    # Update config
    set_config_value("auth_type", "oauth")

    return creds



def set_service_account(service_account_path: Path) -> ServiceAccountCredentials:
    """Configure search-cli to use a Google Cloud service account key."""
    sa_path = Path(service_account_path).resolve()
    if not sa_path.exists():
        raise AuthError(f"Service account file not found: {sa_path}")

    # Validate file format
    try:
        creds = ServiceAccountCredentials.from_service_account_file(
            str(sa_path),
            scopes=SCOPES,
        )
    except Exception as e:
        raise AuthError(f"Invalid service account key file: {e}")

    set_config_value("auth_type", "service_account")
    set_config_value("service_account_path", str(sa_path))

    return creds


def get_credentials(
    service_account_file: Optional[str] = None,
    client_secrets_file: Optional[str] = None,
) -> Any:
    """Load valid credentials (Service Account or OAuth2), refreshing if expired."""
    # 1. Explicit Service Account flag or env var
    sa_path_str = (
        service_account_file
        or os.environ.get("SEARCH_CLI_SERVICE_ACCOUNT")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )
    if not sa_path_str and get_config_value("auth_type") == "service_account":
        sa_path_str = get_config_value("service_account_path")

    if sa_path_str:
        sa_path = Path(sa_path_str).resolve()
        if not sa_path.exists():
            raise AuthError(f"Configured service account file not found: {sa_path}")
        try:
            return ServiceAccountCredentials.from_service_account_file(
                str(sa_path),
                scopes=SCOPES,
            )
        except Exception as e:
            raise AuthError(f"Error loading service account credentials: {e}")

    # 2. OAuth2 Cached Token
    token_path = get_token_path()
    if token_path.exists():
        try:
            creds = OAuthCredentials.from_authorized_user_file(
                str(token_path),
                scopes=SCOPES,
            )
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                return creds
        except Exception as e:
            # Token might be invalid or revoked
            pass

    # 3. Try to prompt OAuth login if client secrets file is explicitly provided
    if client_secrets_file:
        return login_oauth(Path(client_secrets_file))

    # 4. Check if client secrets file exists in default config
    if get_stored_credentials_path().exists() or get_config_value("client_secrets_path"):
        # We have secrets but no valid token, need login
        raise AuthError(
            "Authentication required or expired.\n"
            "Please run: search-cli auth login"
        )

    raise AuthError(
        "No authentication credentials found.\n"
        "Please authenticate using either:\n"
        "  1. OAuth flow: search-cli auth login --credentials <client_secrets.json>\n"
        "  2. Service account: search-cli auth service-account --key <service_account.json>"
    )


def logout() -> None:
    """Remove cached tokens and authentication configurations."""
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()
    
    config = load_config()
    config.pop("auth_type", None)
    save_config(config)


def get_auth_status() -> Dict[str, Any]:
    """Inspect and return current authentication status."""
    auth_type = get_config_value("auth_type")
    token_path = get_token_path()
    sa_path = get_config_value("service_account_path")

    status: Dict[str, Any] = {
        "authenticated": False,
        "type": auth_type or "None",
        "details": {},
    }

    if auth_type == "service_account" and sa_path and Path(sa_path).exists():
        try:
            with open(sa_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            status["authenticated"] = True
            status["details"] = {
                "client_email": data.get("client_email"),
                "project_id": data.get("project_id"),
                "key_path": str(sa_path),
            }
            return status
        except Exception:
            pass

    if token_path.exists():
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            status["authenticated"] = True
            status["type"] = "oauth"
            status["details"] = {
                "client_id": data.get("client_id", "")[:12] + "...",
                "expiry": data.get("expiry"),
                "has_refresh_token": bool(data.get("refresh_token")),
                "token_path": str(token_path),
            }
            return status
        except Exception:
            pass

    return status
