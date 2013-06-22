from __future__ import print_function
import sys, time, re
import email      # Import the email modules we'll need
import email.parser
import email.utils
import email.mime.application
import email.Header
import smtplib    # Import smtplib for the actual sending function
import mimetypes  # For guessing MIME type
import threading
import imaplib
from Crypto.Cipher import AES
from Crypto import Random
# these are all needed to get Google's contact
import atom,gdata.contacts.data,gdata.contacts.client

# these are kevin-specific
developerEmail = "easy-email-developer@gmail.com"
# this should be pulled from config file
specialList = "afamily"

class MessageInfo:

  def __init__(self):
    self.frm=None
    self.subj=None
    self.to=None
    self.cc=None
    self.replyto=None
    self.payloads=list()
    self.payloadtypes=list()
    self.date=None
    self.attachments=list()

  def setnum(self,num):
    self.num=num

  def setlist(self,l):
    self.containingList = l

  def setfrm(self,frm):
    self.frm=frm

  def setsubj(self,sub):
    self.subj=sub

  def setto(self,to):
    if to is not None:
      if len(to) == 0:
        self.to = None
      else:
        self.to=to
    else:
      self.to=to

  def setcc(self,cc):
    if cc is not None:
      if len(cc) == 0:
        self.cc = None
      else:
        self.cc=cc
    else:
      self.cc=cc

  def setreplyto(self,replyto):
    self.replyto=replyto

  def addpayload(self,pay,type):
    self.payloads.append(pay)
    self.payloadtypes.append(type)

  def setdate(self,date):
    self.date=date

  def addattach(self,content,type,filename):
    self.attachments.append([content,type,filename])

  def delete(self):
    self.containingList.imap.store(self.num,'+FLAGS','\\Deleted')
    self.containingList.imap.expunge()

  def dump(self,fp):
    print("\tFrom: %s" % (self.frm,),file=fp)
    print("\tSubject: %s" % (self.subj,),file=fp)
    print("\tTo: %s" % (self.to),file=fp)
    print("\tDate: %d-%d-%d" % self.date,file=fp)
    print("\tPayloads:",file=fp)
    for p in range(len(self.payloads)):
      print("\t\t%s" % (self.payloadtypes[p],),file=fp)
    print("\tAttachments:",file=fp)
    for p in range(len(self.attachments)):
      attachtype = self.attachments[p][1]
      attachfile = self.attachments[p][2]
      print("\t\t%s,%s" % (attachtype,attachfile),file=fp)
    print("\n",file=fp)


class MessageInfoList:

  def __init__(self):
    self.imap = None
    self.parser = None
    self.MessageList = None

  def ListFolders(self):
    print('Mailbox folders:')
    for folderinfo in self.imap.list()[1]:
      print("\t"+folderinfo)
      print(' ')

  def DeleteMessage(self,num):
    self.imap.store(num,'+FLAGS','\\Deleted')
    self.imap.expunge()

  def ArchiveMessage(self,num):
    self.imap.copy(num,'Archive')
    self.DeleteMessage(num,self.imap)

  def GetMessage(self,num):
    messinfo = MessageInfo()
    messinfo.setnum(num)
    messinfo.setlist(self) # a pointer back to containing list

    # reading emails/parsing
    typ,data = self.imap.fetch(num,'(RFC822)')
    N = email.message_from_string(data[0][1])

    # "from" header
    frm,encoding = email.Header.decode_header(N.get("FROM"))[0]
    # try to catch a special case - MORE WORK NEEDED
    if frm.startswith('"=utf-8?Q?'):
      print(frm)
      # this still needs more decoding - stubborn thing
      frm2 = re.sub('"','',frm)
      frm3,encoding = email.Header.decode_header(frm2)[0]
      frm4,encoding = email.Header.decode_header(frm2)[1]
      frm = frm3+" "+frm4
      print(frm)
    messinfo.setfrm(frm)

    to,encoding = email.Header.decode_header(N.get("TO"))[0]
    if type(to) == type([]) or type(to) == type(()):
      to = ' '.join(to)
    messinfo.setto(to)

    cc,encoding = email.Header.decode_header(N.get("CC"))[0]
    if cc is not None and len(cc) > 0: 
      if type(cc) == type([]) or type(cc) == type(()):
        comma = ","
        cc = comma.join(cc)
    else:
      cc = ''
    messinfo.setcc(cc)

    # reply to:
    replyto,encoding = email.Header.decode_header(N.get("REPLY-TO"))[0]
    if replyto is None:
      replyto = frm
    messinfo.setreplyto(replyto)

    subj,encoding = email.Header.decode_header(N.get("SUBJECT"))[0]

    messinfo.setsubj(subj)

    datetup = email.utils.parsedate(N.get("DATE"))
    messinfo.setdate(datetup[0:3])

    if len(N.defects) > 0: print("\tDEFECTS: %s" % (N.defects,))

    # Now traverse the payloads of the message
    toptype = N.get_content_type()

    if N.is_multipart():
      walkit = True
    else:
      walkit = True # just cause it often gets abused.
      if toptype == "text/html" or toptype == "text/plain":
        walkit = False

    if walkit:

      statestack=list()

      for sub in N.walk():

        subtype = sub.get_content_type()

        if subtype == "multipart/alternative":
          statestack.append(subtype)
          continue

        elif subtype.startswith("multipart/"):
          statestack.append(subtype)
          continue

        elif subtype == "text/plain":

          if len(statestack) > 1 and statestack[-2] == "multipart/alternative" \
             and statestack[-1] == "text/html":
            statestack.pop()
            statestack.pop()
            continue

          if len(statestack) > 0 and statestack[-1] == "multipart/alternative":
            statestack.append(subtype) # wait for text/html
            continue

          # otherwise, better get this payload
          payload = sub.get_payload(None,True)
          messinfo.addpayload(payload,subtype)
          continue

        elif subtype == "text/html":

          if len(statestack) > 0 and statestack[-1] == "multipart/mixed":
            statestack.pop()
            payload = sub.get_payload(None,True)
            if payload is not None:

              messinfo.addpayload(payload,subtype)
              continue

          elif len(statestack) > 1 and \
               statestack[-2] == "multipart/alternative" and \
               statestack[-1] == "text/plain":
            statestack.pop()
            statestack.pop()
            payload = sub.get_payload(None,True)
            if payload is not None:

              messinfo.addpayload(payload,subtype)
              continue

          elif len(statestack) > 0 and statestack[-1] == "multipart/alternative":
            statestack.append(subtype) # wait for text/html
            payload = sub.get_payload(None,True)
            if payload is not None:
              
              messinfo.addpayload(payload,subtype)
              continue

              # get this payload, since didn't get others
              payload = sub.get_payload(None,True)
              if payload is not None:
                messinfo.addpayload(payload,subtype)
                continue

        # OK, now other types besides multipart/* or text/*
        cd = sub.get("Content-Disposition", "")
        if cd != "":
          if (cd.startswith("attachment") or cd.startswith("inline")):
            messinfo.addattach(sub.get_payload(None,True),subtype,\
                               sub.get_filename())
          else:
            pass # error message SHOULD BE EMITTED
        else:
          if subtype.startswith('image/'):
            messinfo.addattach(sub.get_payload(None,True),subtype,\
                                   sub.get_filename())
          elif subtype == "message/rfc822":
            messinfo.addattach(sub.get_payload(None,True),subtype,\
                                   sub.get_filename())
          else:
            pass # error message

    else: # not walking the message, hopefully the message is just text/plain or
          # text/html

      if toptype == "text/plain":
        payload = N.get_payload(None,True)
        if payload is not None:
          messinfo.addpayload(payload,toptype)

      elif toptype == "text/html":
        payload = N.get_payload(None,True)
        if payload is not None:
          messinfo.addpayload(payload,toptype)

    return messinfo



  # Sets up and starts thread to load contacts
  def GetContacts(self):
    thrd = threading.Thread(target = self.GetContactsThread)
    thrd.start()


  # This is Gmail - Specific!
  # Run in a separate thread to load contacts
  def GetContactsThread(self):
    self.contacts = list()
    self.specialList = list()
    client = gdata.contacts.client.ContactsClient(source='email assistant')
    client.ClientLogin(self.user,self.passwd,client.source)

    if re.search(developerEmail,self.user,re.I):
      limit = 20
    else:
      limit = -1
    feed = client.GetGroups()
    for i, entry in enumerate(feed.entry):
      if entry.title.text == specialList:
        specialListid = entry.id.text
    feed = client.GetContacts()
    cntr = 1
    while feed:
      if cntr == limit: break
      for entry in feed.entry:
        cntr += 1
        if cntr == limit: break
        afam = False
        for group in entry.group_membership_info:
          if group.href == specialListid:
            afam = True
        for contactEmail in entry.email:
          if contactEmail.primary:
            if entry.title.text is not None:
              fmted = email.utils.formataddr((entry.title.text, \
                                                contactEmail.address))
            else:
              fmted = contactEmail.address
            self.contacts.append(fmted)
            if afam:
              self.specialList.append(fmted)
      nextfeed = feed.GetNextLink()
      feed = None
      if nextfeed:
        feed = client.GetContacts(uri=nextfeed.href)
    feed = None
    client = None

    self.callbackContacts(self.contacts,self.specialList)



  def Send(self,subject,recipients,body,bodytype):
    # Create a text/plain message
    msg = email.mime.Multipart.MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = self.user
    msg['To'] = recipients

    # The main body is just another attachment
    if bodytype == "text/plain":
      subtype = "plain"
    elif bodytype == "text/html":
      subtype = "html"
    else:
      return 0
    sys.stdout.flush()
    ebody = email.mime.Text.MIMEText(body,subtype)
    msg.attach(ebody)
    s = smtplib.SMTP('smtp.gmail.com',587)
    s.starttls()
    s.login(self.user, self.passwd)
    s.sendmail(self.user,recipients,msg.as_string())
    s.quit()
    return 0


  def SignOn(self):
    key = b'Superdupertwoper'
    fp = open('EmailProgram.cfg')
    ciphertext = fp.readline()
    fp.close()
    iv = ciphertext[0:16]
    cipher = AES.new(key, AES.MODE_CFB, iv)
    plaintext = cipher.decrypt(ciphertext)
    plaintext = plaintext[16:]

    parts = plaintext.split(';')

    self.user   = parts[0]
    self.passwd = parts[1]
    server = parts[2]
    port   = parts[3]

    self.imap = imaplib.IMAP4_SSL(server,port)
    self.imap.login(self.user, self.passwd)

    num_messages = self.imap.select() # Must select some mailbox - default "Inbox"

    typ, data = self.imap.search(None, 'ALL')
    numliststr = data[0]
    numlist = numliststr.split(' ')
    return numlist



  def SignOff(self):
    self.imap.close()
    self.imap.logout()



  def CreateList(self,splash,align,color,callbackContacts):

    self.callbackContacts = callbackContacts

    self.numlist = self.SignOn()
    self.GetContacts()

    self.parser = email.parser.Parser()
    self.MessageList=list()
    if self.user == developerEmail:
      limit = 40
    else:
      limit = 20 # keep it to 20 messages for now

    if len(self.numlist) > limit:  
      self.numlist = self.numlist[(-1*limit):]
    self.numlist.reverse()
    cnt = 1
    maxo = len(self.numlist)
    for num in self.numlist:
      splash.showMessage("loading message %d of %d" % (cnt,maxo),align,color) 
      self.MessageList.append(self.GetMessage(num))
      cnt += 1

  def DumpList(self):
    fp = open("dump.txt","w")
    for m in self.MessageList:
      if m is None:
        print("None on message list")
      else:
        m.dump(fp)
    fp.close()

  def Generator(self):
    index = 0
    while index < len(self.MessageList):
      yield self.MessageList[index]
      index += 1

  def Message(self,index):
    return self.MessageList[index]

