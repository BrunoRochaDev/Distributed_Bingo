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

    def getCert(self):
        result = []
        cert_pem = []
        certs = self.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)])
        for cert in certs:
            cka_value, cka_id = self.session.getAttributeValue(cert, [PyKCS11.CKA_VALUE, PyKCS11.CKA_ID])
            cert_der = bytes(cka_value)
            cert = x509.Certificate.load(cert_der)
            # Write out a PEM encoded value
            cert_pem = pem.armor('CERTIFICATE', cert_der)
            result.append(cert)
        
        return cert_pem





if __name__ == '__main__':
    smart = SmartCardSession("1111") 



    result = smart.getCert()
    print(result.decode())