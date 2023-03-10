import PyKCS11

# PyKCS11 does not include a PKCS11 library. We'll use opensc
#lib = '/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so' # Mint location using apt install opensc-pkcs11
lib = '/usr/lib64/pkcs11/opensc-pkcs11.so' # Fedora location using dnf install opensc

class SmartCardSession():
    """Smart Card Session Utilities"""

    # static method for creating session object
    @classmethod
    def create(cls, pin : str) -> None:
        """Generates a PyKCS11 session, required Citizen Card PIN code"""

        session = SmartCardSession()
        session.pkcs11 = PyKCS11.PyKCS11Lib()
        
        # load PKCS11 library
        try:
            session.pkcs11.load(lib)
        except:
            print(f"[ERROR] Could not find valid PKCS11 library at '{lib}'.")
            return None

        try:
            slot = session.pkcs11.getSlotList(tokenPresent=True)[0]
        except:
            print("[ERROR] No smartcard / smartcard reader detected. Failed to create session.")
            return None

        session.session = session.pkcs11.openSession(slot, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)

        # attempt to login using pin
        try:
            session.session.login(pin)
        except PyKCS11.PyKCS11Error as e:
            if "Incorrect PIN" in str(e):
                print("[ERROR] Incorrect PIN. Too many incorrect guesses will block the card.")
                return None
            else:
                print("[ERROR] An error occurred while creating a session. This smartcard might be blocked.")
                return None

        session.pubKey = session.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PUBLIC_KEY)])[0]

    def getPublicKey(self) -> tuple[bytes, bytes]:
        """Returns the modulus and pubExponent corresponding to the smart card's public key as bytes"""
        modulus, pubexp = self.session.getAttributeValue(
                self.pubKey, [PyKCS11.CKA_MODULUS, PyKCS11.CKA_PUBLIC_EXPONENT]
        )

        return bytes(modulus),bytes(pubexp)

    def sign(self,message: bytes) -> bytes:
        """Signs a message and returns the signature"""

        signature = self.session.sign(
                self.session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY)])[0], message, PyKCS11.Mechanism(PyKCS11.CKM_SHA256_RSA_PKCS, None)
            )

        return signature

    def close(self) -> None:
        """Closes the PyKCS11 session"""
        self.session.logout()
        self.session.closeSession()
