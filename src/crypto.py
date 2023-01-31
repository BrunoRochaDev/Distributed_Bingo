import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding  
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64  
from cryptography.hazmat.backends import default_backend
from binascii import a2b_hex, b2a_hex 
import hashlib 

class Crypto:
    """Cryptographic utilities""" 
 
    @classmethod
    def sym_gen(cls) -> tuple:
        """Generates a new AESGCM (key, nonce) tuple""" 
        key= os.urandom(32)
        return (base64.b64encode(key).decode('ascii'), os.urandom(12))

    @classmethod
    def sym_encrypt(cls, key: bytes, data) -> bytes:
        """Encrypts data given with given AESGCM key"""
 
        key=base64.b64decode(key.encode('ascii'))
        data=bytes(str(data), 'ascii')

        cipher = Cipher(algorithms.AES(key), modes.ECB()) 

        # Set up padder
        padder = sym_padding.PKCS7(128).padder()
        
        # Add padding to the bites
        padded_data = padder.update(data) + padder.finalize() 

        # create encryptor
        encryptor = cipher.encryptor()

        # encrypt the message
        ct = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(ct).decode('ascii')

    @classmethod
    def sym_decrypt(cls, key: bytes, crypted_data) -> bytes:
        """Decrypts encrypted data given with given AESGCM key"""
        
        crypted_data=base64.b64decode(crypted_data.encode('ascii'))
        key=base64.b64decode(key.encode('ascii'))

        cipher = Cipher(algorithms.AES(key), modes.ECB())
       # Set up unpadder
        unpadder = sym_padding.PKCS7(128).unpadder() 

        # create decrepter
        decryptor = cipher.decryptor()

        # dencrypt the message
        data = decryptor.update(crypted_data) + decryptor.finalize()  

        # Remove padding from the bites
        data = unpadder.update(data) + unpadder.finalize() 
         
        return data.decode('ascii')

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
        
        return ( Crypto.serialize_private_key(private_key), Crypto.serialize_public_key(private_key.public_key()))

    @classmethod
    def asym_encrypt(cls, public_key: str, data) -> bytes:
        """Encrypts data using given public key"""
        
        public_key = Crypto.load_public_key(public_key)

        data=bytes(str(data), 'utf-8')
        ciphertext = public_key.encrypt(data,
            
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
                )
        )

        return ciphertext

    @classmethod
    def asym_decrypt(cls, private_key: str, crypted_data) -> bytes:
        """Encrypts data using given private key"""

        private_key = Crypto.load_private_key(private_key)
        
        crypted_data=bytes(str(crypted_data), 'utf-8')
        data = private_key.decrypt(crypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return data

    @classmethod
    def sign(cls, private_key: str, data) -> bytes:
        """Returns Signature of given data signed with given private key"""
          
        private_key = Crypto.load_private_key(private_key)

        data=bytes(str(data), 'utf-8')
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
    def verify(cls, public_key: str, message, signature: bytes) -> bool:
        """Verifies if given message matches with given signature"""
          
        public_key = Crypto.load_public_key(public_key)

        message =message.encode()
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


    @classmethod
    def verifyFromCard(cls, modulus: bytes, pubexp: bytes, message: bytes, signature: bytes) -> bool:
        """Verifies if given message matches with given signature"""

        public_key = Crypto.load_public_key_from_SC(modulus,pubexp)

        try:  
            public_key.verify(
                bytes(signature), message, padding.PKCS1v15(), hashes.SHA256()
            )
        except InvalidSignature:
            return False
        except:
            print("Unidentified Error")
            return False

        return True


    @classmethod
    def load_public_key_from_SC(cls,modulus,pubexp):

        n = modulus
        e = pubexp
        key = rsa.RSAPublicNumbers(
            e=int(b2a_hex(e), 16), n=int(b2a_hex(n), 16)
        )
        key = key.public_key(backend=default_backend())
        return key

    @classmethod
    def load_private_key(cls, key_string: str):
        """ """ 
        key_object = serialization.load_pem_private_key(key_string.encode(), password=b'mypassword')
        return  key_object
    @classmethod
    def load_public_key(cls, key_string: str):
        """ """  
        key_object = serialization.load_pem_public_key(key_string.encode())
        return  key_object
    @classmethod
    def serialize_public_key(cls, key_object) -> str:
        """ """ 
        key_string = key_object.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ) 
        return key_string.decode() 
    @classmethod
    def serialize_private_key(cls, key_object) -> str:
        """ """ 
        key_string = key_object.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'mypassword')
        )
        return key_string.decode()  

    # Fisher-Yates Algorithm https://favtutor.com/blogs/shuffle-list-python
    @classmethod
    def deterministic_shuffle(cls, ls : list, seed : str):
        """Deterministically shuffles a list given a seed using the Fisher-Yates Algorithm""" 

        rng = [] # array of 16 random numbers as generated from a MD5 hash
        nonce = 0 # nonce for generating the hash in case the original rng pool runs out
        for i in range(len(ls)-1, 0, -1):

            # if the random number pool is empty, generate more numbers 
            if rng == []:
                digest = hashlib.md5((seed+str(nonce)).encode()).digest() # MD5 hash of the seed + the nonce as a source of uniqueness
                rng = [x for x in digest] # convert bytes to array of ints
                nonce += 1 # increase the nonce so that the next digest is different

            # selects a random index using the random number
            j = rng.pop() % i
            ls[i],ls[j] = ls[j], ls[i] # swaps two items
        
        return ls

    # https://crypto.stackexchange.com/q/78309
    @classmethod
    def deterministic_unshuffle(cls, shuffled_ls : list, seed : str):
        """Reverses the deterministic shuffle and returns the original list"""
        n = len(shuffled_ls)
        # perm is [1, 2, ..., n]
        perm = [i for i in range(1, n + 1)]
        # apply sigma to perm
        shuffled_perm = cls.deterministic_shuffle(perm, seed)
        # zip and unshuffle
        zipped_ls = list(zip(shuffled_ls, shuffled_perm))
        zipped_ls.sort(key=lambda x: x[1])
        return [a for (a, b) in zipped_ls]
