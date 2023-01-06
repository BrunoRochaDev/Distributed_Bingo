import PyKCS11
import binascii
from asn1crypto import pem, x509


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
        
        self.prikey =  self.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY)])[0]

    def getKeys(self):
        """Retuns Public and Private keys"""


        return (self.session.findObjects([
                  (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY), 
                  ])[0], self.session.findObjects([
                  (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY), 
                  ])[0])


    def getPublicPEM(self):

        dict = self.pubKey.to_dict()
        cka_value = dict.get("CKA_VALUE")
        cert_der = bytes(cka_value)


        return pem.armor('PUBLIC KEY', cert_der)

        

