"""Store provider secrets in the OS credential vault, never in JSON config."""
import os
import keyring
from keyring.errors import KeyringError
from . import store

SERVICE="tend-local-assistant"
ACCOUNT="provider-api-key"

def _vault():
    backend=keyring.get_keyring()
    if getattr(backend,"priority",0)<=0:
        raise ValueError("No secure OS credential vault available. Configure an environment variable instead.")
    return backend

def get():
    override=os.environ.get("TEND_AI_API_KEY")
    if override:return override
    try:
        return _vault().get_password(SERVICE,ACCOUNT)
    except (KeyringError,ValueError):
        return None

def set_key(value):
    if not value or not value.strip():raise ValueError("API key must not be empty")
    try:_vault().set_password(SERVICE,ACCOUNT,value.strip())
    except KeyringError as exc:raise ValueError("Could not save key to OS credential vault") from None

def delete_key():
    try:
        vault=_vault()
        if vault.get_password(SERVICE,ACCOUNT):
            vault.delete_password(SERVICE,ACCOUNT)
    except KeyringError:
        raise ValueError("Could not remove key from OS credential vault") from None
