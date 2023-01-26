import PyKCS11
import binascii
from asn1crypto import pem, x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


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
        """Returns the PEM corresponding to the smart card's public key"""
        key = self.session.getAttributeValue(self.pubKey, [PyKCS11.CKA_VALUE])
        keyBytes = bytes(key[0])
        

        cert = serialization.load_der_public_key(keyBytes, backend=default_backend())
        pem = cert.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


        return pem

    def close(self):
        self.session.logout()
        self.session.closeSession()

        return



if __name__ == '__main__':
    
    smart = SmartCardSession("1111") 
    result = smart.getPublicPEM()
    print(result)