import sys, os, re
from PyQt4 import QtCore, QtGui, QtWebKit
from datetime import date
from AttachDialog import Ui_MainWindow
from os.path import abspath as abspath

class StartAttachDialog(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # button connections
        self.ui.btn_open.clicked.connect(self.open)
        self.ui.checkall.stateChanged.connect(self.ckall)
	self.ui.btn_close.clicked.connect(self.close)


    def show(self,attach_files):
        # attach files is a list of lists containing: 
        #   filename, type, and full path

        self.pathlist = list() # initialize - for callback

        # create table model
        self.tablemodel = QtGui.QStandardItemModel(10,2)
        header1 = QtGui.QStandardItem(QtCore.QString('Type'))
        header1.setTextAlignment(QtCore.Qt.AlignLeft)
        self.tablemodel.setHorizontalHeaderItem(0, header1)
        header2 = QtGui.QStandardItem(QtCore.QString('Filename'))
        header2.setTextAlignment(QtCore.Qt.AlignLeft)
        self.tablemodel.setHorizontalHeaderItem(1, header2)
        self.ui.tableView.setModel(self.tablemodel)
        vheader = self.ui.tableView.verticalHeader()
        vheader.hide()
        # cause a cell click to select whole row
        self.ui.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        # for going off Mime type
        #reimg = re.compile('^image/',re.IGNORECASE)
        #bigpat = '^(application/(pdf|vnd.ms-powerpoint|msword)|'
        #bigpat += '(text/(plain|html|rtf|richtext|xml))'
        #redoc = re.compile(bigpat,re.IGNORECASE)

        # go off extension
        reimgext = re.compile('\.(gif|jpg|jpeg|png|bmp)$',re.IGNORECASE)
        redocext = re.compile('\.(htm|html|txt|doc|docx|rtf|xml|pps|pdf)$',\
                                  re.IGNORECASE)
        # setup for population of table
        row = 0
        openmethod = 2 # this is the careful method, by default
        Ty = 'Unsure'

        for filename,typ,path in attach_files:
            if reimgext.search(filename):
                openmethod = 1
                Ty = 'Image'
            elif redocext.search(filename):
                openmethod = 1
                Ty = 'Document'
            
            self.pathlist.append((openmethod,path))
            
            cell = QtGui.QStandardItem(QtCore.QString(Ty))
            cell.setEditable(False)
            self.tablemodel.setItem(row,0,cell)
            cell = QtGui.QStandardItem(QtCore.QString(filename))
            cell.setEditable(False)
            self.tablemodel.setItem(row,1,cell)
            row += 1

        self.ui.tableView.resizeColumnsToContents()
        self.maxRow = row
        self.showMaximized()

    def open(self):
        print('open'); sys.stdout.flush()
        cautious = list()
        print("selected rows:")
        print(self.ui.tableView.selectionModel().selectedRows().__str__())
        for r in self.ui.tableView.selectionModel().selectedRows():
            rr = r.row()
            if rr < 0 or rr >= len(self.pathlist):
                print("r.row()=%d is outside of range of pathlist (0-%d)" \
                          % (rr,len(self.pathlist)))
                if r.row() < 0: print('less than 0')
                if r.row() > len(self.pathlist): print('greater than ...')
                continue

            open_method = self.pathlist[r.row()][0]
            path = abspath(self.pathlist[r.row()][1])
            if open_method == 1:
                os.system('cmd /c "%s"' % (path,))
            else:
                cautious.append(path)
        if cautious:
            # display dialog to confirm, cautious = list to populate dialog
            title = "Being Cautious"
            msg = """Some attachments you want to open may have some risks to
you and your computer. These are listed below. You can choose to open them
anyway, send them to Kevin for evaluation or do nothing. Click the appropriate
button below.
"""
            for f in cautious:
                msg += "\t%s\n" % (f,)
            
            dialog = QtGui.QMessageBox()
            dialog.setWindowTitle(title)
            dialog.setText(msg)
            buttonOpen = dialog.addButton("Open Anyway")
            buttonSend = dialog.addButton("Send to Kevin")
            buttonNothing = dialog.addButton("Do Nothing")
            dialog.exec_()
            if dialog.clickedButton() == buttonOpen:
                for f in cautious:
                    os.system('cmd /c %s' % (f,))
            elif dialog.clickedButton() == buttonSend:
                print("create an email containing:")
                for f in cautious:
                    print(f)

        self.ui.tableView.clearSelection()

    def ckall(self):
        if self.ui.checkall.isChecked():
            # check all lines
            print('check all lines'); sys.stdout.flush()
            self.ui.tableView.selectAll()
        else:
            # uncheck all lines
            print('uncheck all lines'); sys.stdout.flush()
            self.ui.tableView.clearSelection()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = StartAttachDialog()
    filelist = [ 
        ( 'Example-attach-a.pdf','application/pdf',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-a.pdf' ), 
        ( 'Example-attach-b.bmp','image/bmp',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-b.bmp' ), 
        ( 'Example-attach-c.png','image/png',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-c.png' ), 
        ( 'Example-attach-d.DOC','application/msword',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-d.DOC' ), 
        ( 'Example-attach-e.docx','application/msword',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-e.docx' ), 
        ( 'Example-attach-f.text','text/plain',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-f.txt' ), 
        ( 'Example-attach-g.xml','text/xml',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-g.xml' ), 
        ( 'Example-attach-h.htm','text/html',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-h.htm' ), 
        ( 'Example-attach-i',    'text/plain',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-i' ), 
        ( 'Example-attach-j.bat','application/exe',
          'c:/users/buchs/Documents/src/MomEmail/Example-attachments/Example-attach-j.bat' ) ]

    MainWindow.show(filelist)
    sys.exit(app.exec_())

