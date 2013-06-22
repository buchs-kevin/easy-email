import sys, os
from PyQt4 import QtCore, QtGui
from SendEditor import Ui_MainWindow

class StartSendEditor(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # buttons
        QtCore.QObject.connect(self.ui.btn_send,
                               QtCore.SIGNAL("clicked()"), self.send)
        QtCore.QObject.connect(self.ui.btn_quit,
                               QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.btn_close,
                               QtCore.SIGNAL("clicked()"), self.close)
        # give it a nice healthy cursor
        self.ui.body.setCursorWidth(5)

    def activate(self,sendCallback,sendTo=None,subj=None,body=None,
                 typ=None,quotee=None,focus=None,attachments=None):

        self.sendCallback = sendCallback
        if sendTo is not None: 
            self.ui.to.setText(sendTo)
        else:
            self.ui.to.setText('')
        if subj is not None:
            self.ui.subject.setText(subj)
        else:
            self.ui.subject.setText('')
        if typ is not None:
            self.typ = typ
        else:
            self.typ = "text/plain"

        if body is not None:
            if self.typ == "text/plain":
                repbody = "\n\n\n------ %s wrote: ------\n%s" % (quotee,body)
                self.ui.body.setPlainText(repbody)
            elif self.typ == "text/html":
                repbody = "<br><br>\n<p>------ %s wrote: ------<p>%s" \
                           % (quotee,body)
                self.ui.body.setHtml(repbody)
            else:
                print("Really? Really?, type is %s" % (typ,))
                return 0
        self.ui.body.setPlainText('')
        self.showMaximized()
        if focus is not None:
            if focus == "body":
                self.ui.body.setFocus()


    def send(self):
        # let the user know we are busy
        self.hide()
        if self.typ == "text/plain":
            sendBody = self.ui.body.toPlainText().toUtf8().data()
        elif self.typ == "text/html":
            sendBody = self.ui.body.toHtml().toUtf8().data()
        else:
            print("Oh, no; type=%s" % (self.typ,))
            self.hide()
            return 0
        self.sendCallback(self.ui.subject.text().toUtf8().data(),
                          self.ui.to.text().toUtf8().data(),
                          sendBody, self.typ)
        print("send completed")
 
