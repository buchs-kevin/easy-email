# -*- coding: utf-8 -*-
import sys, os, threading
from datetime import date
from PyQt4 import QtCore, QtGui, QtWebKit
from FullInterface import Ui_MainWindow
from ReaderInterface import StartReaderDialog
from AttachInterface import StartAttachDialog
from SendInterface import StartSendEditor
from AddressInterface import StartAddressBook
import ImapParse

class StartQT4(QtGui.QMainWindow):


  ContactsReadySignal = QtCore.pyqtSignal()


  def __init__(self, parent=None):

    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)

    # This signal utilized when the thread loading the contacts completes
    # and the address book may be started
    self.ContactsReadySignal.connect(self.StartAddressBk)
    self.contactsCompleted = False

    self.attach_folder_location = "C:/Users/buchs/Documents/EmailProgram/Attachments/"
    self.setup_attach_folder()

    # First load up messages from the server
    # display a info message during this operation
    splashpixmap = QtGui.QPixmap("splash.png")
    splash = QtGui.QSplashScreen(splashpixmap)
    splash.show()
    print('Downloading messages...')
    sys.stdout.flush()
    self.mlist = ImapParse.MessageInfoList()
    self.mlist.CreateList(splash,
         QtCore.Qt.AlignHCenter|QtCore.Qt.AlignBottom,QtCore.Qt.cyan,
                          self.ContactsComplete)
    splash.close() 
    print('Done downloading messages')
    sys.stdout.flush()


    # button connections
    QtCore.QObject.connect(self.ui.btn_afamily,QtCore.SIGNAL("clicked()"), self.afamily)
    QtCore.QObject.connect(self.ui.btn_read,QtCore.SIGNAL("clicked()"), self.read)
    QtCore.QObject.connect(self.ui.btn_send,QtCore.SIGNAL("clicked()"), self.send)
    QtCore.QObject.connect(self.ui.btn_close,QtCore.SIGNAL("clicked()"), self.close)

    # create table model
    self.tablemodel = QtGui.QStandardItemModel(10,3)
    header1 = QtGui.QStandardItem(QtCore.QString('Date'))
    header1.setTextAlignment(QtCore.Qt.AlignLeft)
    self.tablemodel.setHorizontalHeaderItem(0, header1)
    header2 = QtGui.QStandardItem(QtCore.QString('From'))
    header2.setTextAlignment(QtCore.Qt.AlignLeft)
    self.tablemodel.setHorizontalHeaderItem(1, header2)
    header3 = QtGui.QStandardItem(QtCore.QString('Subject'))
    header3.setTextAlignment(QtCore.Qt.AlignLeft)
    self.tablemodel.setHorizontalHeaderItem(2, header3)
    self.ui.tableView.setModel(self.tablemodel)
    vheader = self.ui.tableView.verticalHeader()
    vheader.hide()
    # cause a cell click to select whole row
    self.ui.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.ui.tableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

    # population of table
    row = 0
    self.messageLoad = list()
    for msg in self.mlist.Generator():

      self.populateTable(row,0,self.relevantDate(msg.date))
      self.populateTable(row,1,msg.frm)
      self.populateTable(row,2,msg.subj)
      self.messageLoad.append(row) # seems trivial now but offers room for future growth
      row += 1

    self.ui.tableView.resizeColumnsToContents()

    # Ready the Reader UI
    self.reader = StartReaderDialog()
    self.reader.attach_folder_date = self.attach_folder_date
    self.reader.attach_folder_counter = self.attach_folder_counter

    # Ready the Attachment UI
    self.attach_ui = StartAttachDialog()

    # Ready the Send Editor UI
    self.sender_ui = StartSendEditor()

    # Create a condition lock that can be used as a timer
    self.timer = threading.Condition()
    self.timer.acquire()
    # now: just need   self.timer(4.2) to pause for 4.2 seconds


  # This will be called by another thread
  def ContactsComplete(self,contacts,special):

    self.contacts = contacts
    self.specialContacts = special
    self.ContactsReadySignal.emit()
    

  # This slot gets connected to a signal emitted from the prior function.
  # The cross-thread communication happens through the signal.
  def StartAddressBk(self):

    self.addressbook_ui = StartAddressBook(self.contacts)
    self.contactsCompleted = True
    if isinstance(self.specialContacts,list) or \
          isinstance(self.specialContacts,tuple):
      comma = ","
      sc = comma.join(self.specialContacts)
      self.specialContacts = sc




  def populateTable(self,row,col,value):
    if type(value) == type([]) or type(value) == type(()):
      newvalue = ' '.join(value)
      value = newvalue
    cell = QtGui.QStandardItem(QtCore.QString(value))
    cell.setEditable(False)
    self.tablemodel.setItem(row,col,cell)


  def send(self):

    while not self.contactsCompleted:
      self.timer.wait(1)

    self.addressbook_ui.show(self.sendContinue)


  def sendContinue(self, resultsList):
    addr = ""
    if resultsList is not None:
      if len(resultsList) > 0:
        comma = ","
        addr = comma.join(resultsList)
        
      self.sender_ui.activate ( self.mlist.Send, addr )


  def afamily(self):

    while not self.contactsCompleted:
      self.timer.wait(1)
      
    self.sender_ui.activate ( self.mlist.Send, self.specialContacts )


  def read(self):
    sel = self.ui.tableView.selectedIndexes()  # will be just one index
    chosenMsg = self.mlist.Message( self.messageLoad[ sel[0].row() ])
    self.reader.setChosenMsg(chosenMsg, sel[0].row(),self)


  def deleted(self,row):
    # while the message was being read, it was deleted
    self.ui.tableView.hideRow(row)
    

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


  def setup_attach_folder(self):
    dirlist = [self.attach_folder_location,]
    doomed = False
    while not os.path.exists(dirlist[-1]) and not doomed:
      dirlist.append(os.path.dirname(dirlist[-1]))
      if dirlist[-1] == dirlist[-2]: doomed = True
    if doomed: 
      print("Error, root of attachment folder, %s, does not exist" % (dirlist[-1]))
      # exit
    else:
      d = dirlist.pop()
      while d:
        if not os.path.exists(d):
          os.mkdir(d)
        if len(dirlist) > 0:
          d = dirlist.pop()
        else:
          d = ''

      self.attach_folder_date = "%sattachments-%s" % \
          (self.attach_folder_location,date.today().__str__())
      self.attach_folder_counter = 0
      while ( os.path.exists("%s-%d" % (self.attach_folder_date, \
                                          self.attach_folder_counter)) ):
        self.attach_folder_counter += 1
    

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  app.setFont(QtGui.QFont('Arial 14'))  # set default font
  myapp = StartQT4()
  myapp.showMaximized()
  sys.exit(app.exec_())
