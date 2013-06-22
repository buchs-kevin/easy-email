import sys, os, re
from PyQt4 import QtCore, QtGui, QtWebKit
from AddressBook import Ui_AddressBook

class StartAddressBook(QtGui.QMainWindow):

    def __init__(self, contactList, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_AddressBook()
        self.ui.setupUi(self)

        self.manualString = "(Manually Enter Address)"

        # button connections
        self.ui.btn_ok.clicked.connect(self.OK)
        self.ui.btn_close.clicked.connect(self.NotOK)

        # create table model
        self.tablemodel = QtGui.QStandardItemModel(10,1)
        header1 = QtGui.QStandardItem(QtCore.QString('Addressee'))
        header1.setTextAlignment(QtCore.Qt.AlignLeft)
        self.tablemodel.setHorizontalHeaderItem(0, header1)
        self.ui.tableView.setModel(self.tablemodel)
        vheader = self.ui.tableView.verticalHeader()
        vheader.hide()
        # cause a cell click to select whole row
        self.ui.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        # load contacts into table, manual one first
        row = 0
        cell = QtGui.QStandardItem(QtCore.QString(self.manualString))
        cell.setEditable(False)
        self.tablemodel.setItem(row,0,cell)
        row += 1
        for aContact in contactList:
            cell = QtGui.QStandardItem(QtCore.QString(aContact))
            cell.setEditable(False)
            self.tablemodel.setItem(row,0,cell)
            row += 1

        self.ui.tableView.resizeColumnsToContents()


    def show(self,callback):
        self.callback = callback
        self.showMaximized()


    def OK(self):
        resultsList = list()
        for r in self.ui.tableView.selectionModel().selectedRows():
            addr = r.data().toString().toUtf8().data()
            if addr != self.manualString:
                resultsList.append(addr)
        self.callback(resultsList)
        self.hide()
        self.ui.tableView.clearSelection()



    def NotOK(self):
        self.callback(None)
        self.hide()
        self.ui.tableView.clearSelection()



    def testCallback(self,resultList):
        print("Results are:")
        print(resultList)
        self.close()



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    dummyContacts = list()
    for i in range(50):
        dummyContacts.append("Contact %d" % (i,))
    MainWindow = StartAddressBook(dummyContacts)
    MainWindow.show(MainWindow.testCallback)
    print("showing...")
    sys.exit(app.exec_())

