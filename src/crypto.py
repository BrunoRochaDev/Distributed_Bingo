import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding   
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

class Crypto:
    """Cryptographic utilities"""

    @classmethod
    def sym_gen(cls) -> tuple:
        """Generates a new AESGCM (key, nonce) tuple""" 
        return (AESGCM.generate_key(bit_length=128), os.urandom(12))

    @classmethod
    def sym_encrypt(cls, key: bytes, data, nonce: bytes=b'') -> bytes:
        """Encrypts data given with given AESGCM key"""

        data=bytes(data, 'utf-8')
        cypher = AESGCM(key) 
        ct = cypher.encrypt(nonce, data, None)
  
        return ct 

    @classmethod
    def sym_decrypt(cls, key: bytes, crypted_data, nonce: bytes=b'') -> bytes:
        """Decrypts encrypted data given with given AESGCM key"""
        
        crypted_data=bytes(crypted_data, 'utf-8')
        cypher = AESGCM(key) 
        data = cypher.decrypt(nonce, crypted_data, None)
        
        return data  

    @classmethod
    def do_hash(cls, data: bytes) -> bytes:
        """Returns an hash of a given data"""
        
        digest = hashes.Hash(hashes.SHA256()) 
        digest.update(data)    
        hash = digest.finalize().hex()
        
        return hash 

    @classmethod
    def asym_gen(cls) -> tuple:
        """Generates a new Asymetric key(Object) pair"""
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        return (private_key, private_key.public_key())

    @classmethod
    def asym_encrypt(cls, public_key, data) -> bytes:
        """Encrypts data using given public key"""
        
        data=bytes(data, 'utf-8')
        ciphertext = public_key.encrypt(data,
            
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
                )
        )

        return ciphertext

    @classmethod
    def asym_decrypt(cls, private_key, crypted_data) -> bytes:
        """Encrypts data using given private key"""
        
        crypted_data=bytes(crypted_data, 'utf-8')
        data = private_key.decrypt(crypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return data

    @classmethod
    def sign(cls, private_key, data) -> bytes:
        """Returns Signature of given data signed with given private key"""
          
        data=bytes(data, 'utf-8')
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature

    @classmethod
    def verify(cls, public_key, message, signature: bytes) -> bool:
        """Verifies if given message matches with given signature"""
          
        try:  
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            ) 
        except InvalidSignature:
            return False
        except:
            print("Unidentified Error")
            return False

        return True