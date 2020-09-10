import base64
import hashlib
import hmac
import logging

from .env import ENV


def verify_git_hook_sha1(payload: bytes, sig: str) -> bool:
    digester = hmac.new(ENV.GIT_SECRET, payload, digestmod=hashlib.sha1)
    calced_sig = digester.hexdigest().encode("utf-8")
    return hmac.compare_digest(b"sha1=" + calced_sig, sig.encode("utf-8"))
