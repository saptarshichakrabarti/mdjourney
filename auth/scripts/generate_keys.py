from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

PRIVATE_KEY_FILE = "auth/data/jwt-private.pem"
PUBLIC_KEY_FILE = "auth/data/jwt-public.pem"

def generate_keys():
    """Generates a new RSA key pair and saves them to the specified files."""
    print("Generating new RSA key pair...")

    # Generate the private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Serialize the private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Save the private key
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(pem_private)
    os.chmod(PRIVATE_KEY_FILE, 0o600)  # Set restrictive permissions
    print(f"Private key saved to {PRIVATE_KEY_FILE}")

    # Generate and serialize the public key
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save the public key
    with open(PUBLIC_KEY_FILE, 'wb') as f:
        f.write(pem_public)
    print(f"Public key saved to {PUBLIC_KEY_FILE}")

if __name__ == "__main__":
    generate_keys()
