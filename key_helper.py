#!/usr/bin/env python3
"""
Walmart API Key Helper

This script helps you work with your Walmart API RSA keys.
"""

import base64
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def save_public_key_from_base64(base64_key: str, filename: str = "walmart_provided_public_key.pem"):
    """Save the provided base64 public key to a PEM file"""
    try:
        # Decode the base64 key
        key_bytes = base64.b64decode(base64_key)
        
        # Load as public key
        public_key = serialization.load_der_public_key(key_bytes, backend=default_backend())
        
        # Convert to PEM format
        pem_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Save to file
        with open(filename, 'wb') as f:
            f.write(pem_bytes)
        
        print(f"✅ Public key saved to: {filename}")
        print("📄 Content:")
        print(pem_bytes.decode('utf-8'))
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing public key: {str(e)}")
        return False

def main():
    print("🔑 Walmart API Key Helper")
    print("=" * 40)
    
    # Your provided public key
    your_public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0PXJ1Uel3jjxG5Zg0lfRypu4qtqGohEYlQ9J1ddLrWpPnC49OGE1QppTFxVWuPxR46nF7414RWwzwztMzLtMyrCGJ7DEYiOO1gHIoucf2ky7Xa+vcxA7gOcPqEIe++zho+GgD5x+VhYT33HbePKymK3+6f+KmW3wg6WADebOUkCrESVFefVltGQsRJnXU2MmuJfZ1nUjsdvljQ3yrDicsKBz0bviKHb9NOYpMaS3q8kaCn3iRo9AyT3m1e9HYqX5VqHjsGuaJadyijk9wPr+cigLGY8N8U9f+Ohk+ZsM8M7P6qTQDPKzK1+VPwtgQOrgZyckt5T6z1aQFeU9xmZ/AwIDAQAB"
    
    print("📝 Processing your provided public key...")
    
    if save_public_key_from_base64(your_public_key, "your_walmart_public_key.pem"):
        print("\n🎯 Next Steps:")
        print("1. ✅ Your public key has been saved to 'your_walmart_public_key.pem'")
        print("2. 🔍 You need to find the PRIVATE key that corresponds to this public key")
        print("3. 📁 The private key file usually has a name like:")
        print("   - walmart_private_key.pem")
        print("   - private_key.pem") 
        print("   - id_rsa (if generated with ssh-keygen)")
        print("   - Or any .pem/.key file you created when generating the key pair")
        print("\n4. 🔧 Once you find your private key file, update .env:")
        print("   WALMART_PRIVATE_KEY_PATH=/path/to/your/private_key.pem")
        print("\n5. 🧪 Then run: python quick_test.py")
        
        print("\n💡 If you can't find your private key:")
        print("   - Check where you originally generated the key pair")
        print("   - Look for .pem, .key files in your downloads or documents")
        print("   - If lost, you'll need to generate a new key pair and upload the new public key to Walmart")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())