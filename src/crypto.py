import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding  
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes

class Crypto:
    """Cryptographic utilities"""

    @classmethod
    def sym_gen(cls):
        """Generates a new AESGCM key"""
        return (AESGCM.generate_key(bit_length=128), os.urandom(12))

    @classmethod
    def sym_encrypt(cls, data, key, nonce):
        """Encrypts data given with given AESGCM key"""

        cypher = AESGCM(key) 
        ct = cypher.encrypt(nonce, data, None)

        #print("\n[Encypted] msg: " + str(data) + ", to: "+ str(ct)) 
        return ct 

    @classmethod
    def sym_decrypt(cls, crypted_data, key, nonce):
        """Decrypts encrypted data given with given AESGCM key"""
        
        cypher = AESGCM(key) 
        data = cypher.decrypt(nonce, crypted_data, None)

        #print("\n[Decrypted] ct: " + str(crypted_data) + ", to: "+ str(data)) 
        return data 

    @classmethod
    def do_hash(cls, data: bytes):
        """Returns an hash of a given data"""
        
        digest = hashes.Hash(hashes.SHA256()) 
        digest.update(data)    
        hash = digest.finalize().hex()
        
        return hash 
 

 

""" HOW TO USE: 

msg_ = b'uwu'  

(key,nonce) = Crypto.sym_gen()
msg = Crypto.sym_decrypt(Crypto.sym_encrypt(msg_, key, nonce), key, nonce)

print("\n")
    
"""