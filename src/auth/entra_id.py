from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
import urllib.request
import json
from src.config import settings

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/oauth2/v2.0/token",
)

def get_jwks():
    """Fetch JSON Web Key Set from Microsoft Entra ID."""
    jwks_url = f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/discovery/v2.0/keys"
    try:
        with urllib.request.urlopen(jwks_url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return {"keys": []}

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate the Entra ID JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        unverified_header = jwt.get_unverified_header(token)
        jwks = get_jwks()
        
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
                
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.ENTRA_CLIENT_ID,
                issuer=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/v2.0"
            )
            return payload
    except JWTError:
        raise credentials_exception
        
    raise credentials_exception
