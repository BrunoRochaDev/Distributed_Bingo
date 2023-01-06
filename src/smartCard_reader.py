import PyKCS11
import binascii

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

    def getKeys(self):
        """Retuns Public and Private keys"""




        return (self.session.findObjects([
                  (PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY), 
                  ])[0], self.session.findObjects([
                  (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY), 
                  ])[0])


        

