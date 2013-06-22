import os, getpass
from Crypto.Cipher import AES
from Crypto import Random

filename = 'EmailProgram.cfg'
key = b'Superdupertwoper'

defacct = ""
defserver = ""
defport = ""
defsmtpserver = ""
defsmtpport = ""

# does the file already exist? Then read it for defaults
if os.path.exists(filename):
    fp = open('EmailProgram.cfg','rb')
    ciphertext = fp.readline()
    fp.close()
    iv = ciphertext[0:16]
    cipher = AES.new(key, AES.MODE_CFB, iv)
    plaintext = cipher.decrypt(ciphertext)
    plaintext = plaintext[16:]  # subtract the IV
    parts = plaintext.split(';')
    defacct = parts[0]
    if len(parts) > 2: defserver = parts[2]
    if len(parts) > 3: defport = parts[3]
    if len(parts) > 4: defsmtpserver = parts[4]
    if len(parts) > 5: defsmtpport = parts[5]

if defport == "": defport = '993'
if defsmtpport == "": defsmtpport = '587'

acct = raw_input("Enter email account [%s]: " % (defacct,))
if len(acct) == 0: acct = defacct
print("Enter account password: ")
password = getpass.getpass()
server = raw_input("Enter IMAP server [%s]: " % (defserver,))
if len(server) == 0: server = defserver
port = raw_input("Enter IMAP port [%s]: " % (defport,))
if len(port) == 0: port = defport
smtpserver = raw_input("Enter SMTP server [%s]: " % (defsmtpserver,))
if len(smtpserver) == 0: smtpserver = defsmtpserver
smtpport = raw_input("Enter SMTP port [%s]: " % (defsmtpport,))
if smtpport == "": smtpport = defsmtpport

plaintext = ";".join((acct,password,server,port,smtpserver,smtpport,'                 '))
trimlen = int( len(plaintext)/16.0 ) * 16
plaintext = plaintext[0:trimlen]

iv = Random.new().read(AES.block_size)
cipher = AES.new(key, AES.MODE_CFB, iv)
ciphertext = iv + cipher.encrypt(plaintext)

fp = open("EmailProgram.cfg","wb")
fp.write(ciphertext)
fp.close()
