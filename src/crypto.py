import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding  
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec 

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
        """Generates a new Asymetric key pair"""
        
        private_key = ec.generate_private_key(
            ec.SECP384R1()
        )
        
        return (private_key, private_key.public_key())

 