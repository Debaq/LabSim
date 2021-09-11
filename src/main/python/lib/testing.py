#import pyAesCrypt
#password = "DFG/8$94lks3=="#"
# encrypt
#pyAesCrypt.encryptFile("test.json", "test.asim", password)
# decrypt
#pyAesCrypt.decryptFile("data.txt.aes", "dataout.txt", password)

import pycrypt

print(pycrypt.__name__ + ", Version " + pycrypt.__version__)
print("Made by " + pycrypt.__author__ + "\n\n")

# Encrypts a message with the caesar cipher and the key 12
print("Encrypted Message:")
print(pycrypt.caesar.encrypt("[eddf:{}te]]", 5))

# Decrypts a message with the caesar cipher and the key 12
print("Decrypted Message:")
print(pycrypt.caesar.decrypt("[jiikyj]]", 5))
