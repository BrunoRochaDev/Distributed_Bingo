import PyKCS11
import binascii
from asn1crypto import pem, x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from src.crypto import Crypto
from cryptography.hazmat.primitives import hashes
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa


lib = '/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'

class SmartCardSession():
    """Smart Card Session Utilities"""

    def __init__(self,loginCred: str):
        """Generates a PyKCS11 session, required Citizen Card PIN code"""
        self.pkcs11 = PyKCS11.PyKCS11Lib()
        self.pkcs11.load(lib)

        slot = self.pkcs11.getSlotList(tokenPresent=True)[0]

        self.session = self.pkcs11.openSession(slot, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)
        self.session.login(loginCred)

        self.pubKey =self.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY)])[0]
        


    def getPublicPEM(self):
        """Returns the PEM corresponding to the smart card's public key as bytes"""
        key = self.session.getAttributeValue(self.pubKey, [PyKCS11.CKA_VALUE])
        keyBytes = bytes(key[0])
        

        cert = serialization.load_der_public_key(keyBytes, backend=default_backend())
        pem = cert.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


        return pem

    def sign(self,message: bytes):


        sha256 = hashes.SHA256()
        signed_data_hash = hashes.Hash(sha256, default_backend())
        signed_data_hash.update(str(message).encode('utf-8'))
        digest=signed_data_hash.finalize()

        # sha256 digestInfo
        binaryData2 =b'\x30\x31\x30\x0d\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20'+digest

        mechanism = PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, None)
        signature = self.session.sign(self.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY)])[0],binaryData2,mechanism)
        
        return signature

    def close(self):
        self.session.logout()
        self.session.closeSession()

        return



if __name__ == '__main__':
    
    smart = SmartCardSession("1111") 
    result = smart.getPublicPEM()
    print(result.decode("ascii"))

