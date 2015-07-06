# Introduction #

This is the home page for the easy-email project. Its goal is the provide an extremely simple email client, providing a bare bones GUI. It was created for my 92-year-old mother. Once Outlook Express went away, everything else was too complicated.


# Details #

## Stuff You Need to Run This - Libraries ##

This is written for Python 2.7, but I bet it works well with 3.**You need [PyQt4](http://www.riverbankcomputing.com/software/pyqt), [pycrypto-2.6](https://www.dlitz.net/software/pycrypto/), and [gdata](https://code.google.com/p/gdata-python-client/)**

## Set Up ##

Start by running EmailSetup.py. It will prompt you for the email account parameters. This will create an encrypted file: EmailProgram.cfg. That is done one time. Then run EmailProgram.py for the regular problem.

## Limitations ##

The program currently only works with Google contacts for the address book.