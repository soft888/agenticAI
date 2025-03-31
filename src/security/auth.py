import logging
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Key Vault setup
key_vault_name = "mcp-keyvault"
key_vault_uri = f"https://{key_vault_name}.vault.azure.net/"

# Get credentials from Key Vault
credential = ClientSecretCredential(
    tenant_id="TENANT_ID",  # Replace with your tenant ID
    client_id="CLIENT_ID",  # Replace with your client ID
    client_secret="CLIENT_SECRET"  # Replace with your client secret
)

secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

# Get the secret for JWT signing
try:
    jwt_secret = secret_client.get_secret("JwtSecret").value
except Exception as e:
    logger.error(f"Error retrieving JWT secret: {str(e)}")
    jwt_secret = "placeholder-secret"  # Use a default for development

def authenticate_request(token: str = Depends(oauth2_scheme)):
    """Validate the JWT token and return the user information."""
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        if payload.get("exp") < datetime.now().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a new JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm="HS256")
    return encoded_jwt