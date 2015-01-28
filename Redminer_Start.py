import sys
import PyQt4, PyQt4.QtGui

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Redminer import Main_Window

if __name__ == '__main__':
    app = PyQt4.QtGui.QApplication(sys.argv)
#     app.setStyle(QStyleFactory.create("plastique"))
    myapp = Main_Window.MainWindow()
    myapp.show()
    
    myapp.ui.actionRestart.triggered.disconnect()
    
    @pyqtSlot()
    def restartSlot():
        print 'Restarting App'
        global myapp
        myapp.deleteLater()
#         myapp.close()
        myapp = Main_Window.MainWindow()
        myapp.show()

        myapp.ui.actionRestart.triggered.disconnect()   
        myapp.ui.actionRestart.triggered.connect(restartSlot)        
        
        QObject.connect(myapp, SIGNAL("RESTART_REQUEST"), restartSlot)
        print 'New App started!'
    
    QObject.connect(myapp, SIGNAL("RESTART_REQUEST"), restartSlot)
    myapp.ui.actionRestart.triggered.connect(restartSlot)
    
    sys.exit(app.exec_())