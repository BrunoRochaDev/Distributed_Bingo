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
    def sym_encrypt(cls, data: bytes, key: bytes, nonce: bytes) -> bytes:
        """Encrypts data given with given AESGCM key"""

        cypher = AESGCM(key) 
        ct = cypher.encrypt(nonce, data, None)

        #print("\n[Encypted] msg: " + str(data) + ", to: "+ str(ct)) 
        return ct 

    @classmethod
    def sym_decrypt(cls, crypted_data: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypts encrypted data given with given AESGCM key"""
        
        cypher = AESGCM(key) 
        data = cypher.decrypt(nonce, crypted_data, None)

        #print("\n[Decrypted] ct: " + str(crypted_data) + ", to: "+ str(data)) 
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
    def asym_encrypt(cls, public_key, data: bytes) -> bytes:
        """Encrypts data using given key"""
        
        ciphertext = public_key.encrypt(data,
            
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
                )
        )

        return ciphertext

    @classmethod
    def asym_decrypt(cls, private_key, crypted_data: bytes) -> bytes:
        """Encrypts data using given key"""
        
        data = private_key.decrypt(crypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return data

    @classmethod
    def sign(cls, private_key, data: bytes) -> bytes:
        """Encrypts data using given key"""
          
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
    def verify(cls, public_key, message: bytes, signature: bytes) -> bool:
        """Encrypts data using given key"""
          
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