import os

secret_key = os.getenv("SECRET_KEY")

if secret_key:
    print("Secret key retrieved successfully:", secret_key)
else:
    print("Secret key not found in environment variables.")