import os
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, Optional

import jwt

AUDIENCE = "authenticated"
JWKS_PATH = "/auth/v1/.well-known/jwks.json"
ASYMMETRIC_ALGORITHMS = ["ES256", "RS256"]


class AuthError(Exception):
    status_code = 401


class NotOperator(AuthError):
    status_code = 403


class AuthNotConfigured(AuthError):
    status_code = 503


TokenDecoder = Callable[[str], Dict]


def hs256_decoder(secret: str) -> TokenDecoder:
    def decode(token: str) -> Dict:
        return jwt.decode(token, secret, algorithms=["HS256"], audience=AUDIENCE, options={"require": ["exp", "sub"]})

    return decode


def jwks_decoder(supabase_url: str) -> TokenDecoder:
    client = jwt.PyJWKClient(supabase_url.rstrip("/") + JWKS_PATH)

    def decode(token: str) -> Dict:
        key = client.get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=ASYMMETRIC_ALGORITHMS, audience=AUDIENCE,
                          options={"require": ["exp", "sub"]})

    return decode


def parse_operator_emails(raw: str) -> FrozenSet[str]:
    return frozenset(e.strip().lower() for e in (raw or "").split(",") if e.strip())


@dataclass
class OperatorAuth:
    decoder: Optional[TokenDecoder]
    operator_emails: FrozenSet[str]

    def operator_email(self, authorization: Optional[str]) -> str:
        if self.decoder is None or not self.operator_emails:
            raise AuthNotConfigured("Operator sign-in is not configured on this backend.")
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Sign in as an operator to make changes.")
        try:
            claims = self.decoder(token.strip())
        except jwt.PyJWTError as exc:
            raise AuthError("Session is invalid or expired. Sign in again.") from exc
        email = str(claims.get("email") or "").lower()
        if email not in self.operator_emails:
            raise NotOperator("This account is not an operator.")
        return email


def auth_from_env() -> OperatorAuth:
    secret = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    url = os.getenv("SUPABASE_URL", "").strip()
    decoder = hs256_decoder(secret) if secret else jwks_decoder(url) if url else None
    return OperatorAuth(decoder, parse_operator_emails(os.getenv("OPERATOR_EMAILS", "")))
