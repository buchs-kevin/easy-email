import sys, os, re
from PyQt4 import QtCore, QtGui, QtWebKit
from datetime import date
from ReadWindow import Ui_MainWindow
import threading


class StartReaderDialog(QtGui.QMainWindow):

    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings = self.ui.body.settings() 
        self.settings.setFontFamily(QtWebKit.QWebSettings.StandardFont,\
                                    'Arial')

        # button connections
        QtCore.QObject.connect(self.ui.btn_reply,QtCore.SIGNAL("clicked()"),\
                                   self.reply)
        QtCore.QObject.connect(self.ui.btn_replyall,QtCore.SIGNAL("clicked()"),\
                                   self.replyall)
        QtCore.QObject.connect(self.ui.btn_forward,QtCore.SIGNAL("clicked()"),\
                                   self.forward)
        QtCore.QObject.connect(self.ui.btn_delete,QtCore.SIGNAL("clicked()"),\
                                   self.delete)
        QtCore.QObject.connect(self.ui.btn_attachs,QtCore.SIGNAL("clicked()"),\
                                   self.show_attachments)
        QtCore.QObject.connect(self.ui.btn_close,QtCore.SIGNAL("clicked()"),\
                                   self.close)


    def showMax(self):
        self.ui.btn_attachs.hide()
        self.ui.pointer.hide()
        self.showMaximized()


    def showMaxAttach(self):
        self.ui.btn_attachs.show()
        self.ui.pointer.show()
        self.showMaximized()
        self.animate()


    def animate(self):
        self.animation = QtCore.QPropertyAnimation(self.ui.pointer,"geometry")
        geometry3 = self.ui.pointer.geometry()
        (x,y,w,h) = geometry3.getRect()
        geometry2 = QtCore.QRect(x-100,y,w,h)
        geometry1 = QtCore.QRect(x-200,y,w,h)
        
        self.animation.setKeyValueAt(0, geometry1);
        self.animation.setKeyValueAt(0.5, geometry2);
        self.animation.setKeyValueAt(1, geometry3);

        self.animation.setLoopCount(1000)
        self.animation.setDuration(2000) # ms in loop
        self.animation.start()


    def reply(self):
        replySubject = re.sub('^(RE: )?','Re: ',
                     self.chosenMessage.subj,flags=re.IGNORECASE)
        self.mainobj.sender_ui.activate(self.mainobj.mlist.Send,
             self.chosenMessage.frm,
             replySubject,self.body,self.typ,
             self.chosenMessage.frm,"body")

    def replyall(self):

        replySubject = re.sub('^(RE: )?','Re: ',self.chosenMessage.subj,
                              flags=re.IGNORECASE)
        print("toCc=%s" % (self.toCc.__str__(),))
        print("frm=%s" % (self.chosenMessage.frm,))
        sys.stdout.flush()
        self.mainobj.sender_ui.activate(self.mainobj.mlist.Send,
             self.chosenMessage.frm + "," + self.toCc,
             replySubject,self.body,self.typ,
             self.chosenMessage.frm, "body")

    def forward(self):

        # pick addresses to which to forward the message
        timer = threading.Condition()
        timer.acquire()
        while not self.mainobj.contactsCompleted:
            print("waiting for contacts to be loaded")
            timer.wait(1)
        sys.stdout.flush()
        self.mainobj.addressbook_ui.show(self.forwardContinued)


    def forwardContinued(self,resultsList):
        if resultsList is not None:
            if len(resultsList) > 0:
                if resultsList.index('(special list)') > -1:
                    pass
                    # Here is the hook to add in the special list to the
                    # address book
                comma = ", "
                addr = comma.join(resultsList)
                fwdSubject = re.sub('^((RE|FWD): *)*','Fwd: ',
                                    self.chosenMessage.subj,
                                    flags=re.IGNORECASE)
                print("fwdSubject=")
                print(fwdSubject)
                self.mainobj.sender_ui.activate( self.mainobj.mlist.Send,
                          addr,fwdSubject,self.body,self.typ,
                          self.chosenMessage.frm, "body", self.attach_files )


    def delete(self):

        msg = """Are you sure you wish to delete this message from '%s'
with the subject '%s' ?""" % (self.chosenMessage.frm,self.chosenMessage.subj)
        ans = QtGui.QMessageBox.question(None,"Delete, Really?",msg,
                                         QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
        if ans == QtGui.QMessageBox.Yes:
            self.chosenMessage.delete()
            self.mainobj.deleted(self.guirow)
            self.close()

    def show_attachments(self):

        # fill up attachment list
        self.attach_ui.show(self.attach_files)


    def setChosenMsg(self,chosenMessage,guirow,mainobj):

        self.mainobj = mainobj
        self.chosenMessage = chosenMessage
        self.guirow = guirow
        self.ui.date.setText(QtCore.QString(
                      self.relevantDate(self.chosenMessage.date)))

        if self.chosenMessage.cc == "None":
            self.chosenMessage.cc = None

        if self.chosenMessage.cc is None:
            if self.chosenMessage.to is None:
                self.toCc = None
            else:
                self.toCc = self.chosenMessage.to
        else:
            if self.chosenMessage.to is None:
                self.toCc = self.chosenMessage.cc
            else:
                self.toCc = self.chosenMessage.to + ', ' + \
                    self.chosenMessage.cc

        self.ui.frm.setText(QtCore.QString(self.chosenMessage.frm))
        self.ui.subject.setText(QtCore.QString(self.chosenMessage.subj))
        self.returnStatus = "nothing"

        # body
        usePayload = 0
        if len(self.chosenMessage.payloads) > 1:
            usePayload = -1
            if 'text/html' in self.chosenMessage.payloadtypes:
                usePayload = self.chosenMessage.payloadtypes.index('text/html')
            elif 'text/plain' in self.chosenMessage.payloadtypes:
                usePayload = self.chosenMessage.payloadtypes.index('text/plain')
            else:
                dialog = QtGui.QMessageBox()
                dialog.setWindowTitle('Payloads irregular')
                dialog.setText('''This message has unusual payloads that do not
match what is expected: %s''' % (self.chosenMessage.payloadtypes.__str__(),))
                dialog.exec_()
                
        elif len(self.chosenMessage.payloads) == 0:
            print("What? No payloads on this message!")
            sys.stdout.flush()
            return
        
        self.body = self.chosenMessage.payloads[usePayload]
        self.typ = self.chosenMessage.payloadtypes[usePayload]
        self.ui.body.setContent(self.body, QtCore.QString(self.typ))

        if self.typ == "text/plain":
            self.settings.setFontSize(QtWebKit.QWebSettings.DefaultFixedFontSize,40)

        elif self.typ == "text/html":
            self.settings.setFontSize(QtWebKit.QWebSettings.DefaultFontSize,20)

        else:
            # I don't know what to do - display error message
            print("I'm not really sure what to do with message payload = "+self.typ)
            sys.stdout.flush()
    

        # attachments
        if len(self.chosenMessage.attachments) > 0:
            self.attach_files = list()
            dire = "%s-%d" % (self.attach_folder_date, self.attach_folder_counter)
            os.mkdir(dire)
            self.attach_folder_counter += 1

            for content,type,filename in self.chosenMessage.attachments:
                if filename == '':
                    print('NO FILENAME!')
                else:
                    full_filename = dire + "/" + filename
                    fp = open(full_filename,'wb')
                    fp.write(content)
                    fp.close()
                    self.attach_files.append([filename,type,full_filename])

            self.showMaxAttach()

        else:

            self.attach_files = None
            self.showMax()

        return self.returnStatus

 
    def relevantDate(self,datelist): # returns only minimal string to determine date (just month/day for last 12 months.
        diff = date.today() - date(datelist[0],datelist[1],datelist[2])
        if diff.days > 364:
            if datelist[0] >= 2000:
                year = datelist[0] - 2000
            else:
                year = datelist[0] - 1900
                return "%d/%d/%02d" % (datelist[1],datelist[2],year)
        else:
            return "%d/%d" % (datelist[1],datelist[2])
