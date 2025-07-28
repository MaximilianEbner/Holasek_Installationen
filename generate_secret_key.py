#!/usr/bin/env python3
"""
Generiert eine sichere SECRET_KEY für Railway
"""
import secrets
import string

def generate_secret_key(length=64):
    """Generiert eine sichere SECRET_KEY"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print("🔑 Sichere SECRET_KEY generiert:")
    print(f"SECRET_KEY={secret_key}")
    print("\n📋 Kopiere diese in Railway Environment Variables:")
    print(f"Key: SECRET_KEY")
    print(f"Value: {secret_key}")
