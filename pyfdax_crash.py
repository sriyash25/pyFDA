# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import logging
import logging.config
logger = logging.getLogger(__name__)

from PyQt4 import QtGui, QtCore

import pyfda.filterbroker as fb
from pyfda import pyfda_rc as rc
from pyfda.filter_tree_builder import FilterTreeBuilder

from pyfda.input_widgets import input_tab_widgets
from pyfda.plot_widgets import plot_tab_widgets_crash

__version__ = "0.1a5"

# get dir for this file, apppend 'pyfda' and store as base_dir in filterbroker
fb.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyfda')

class DynFileHandler(logging.FileHandler):
    """
    subclass FileHandler with a customized handler for dynamic definition of
    the logging filepath and -name
    """
    def __init__(self, *args):
        filename, mode = args
        if not os.path.isabs(filename): # path to logging file given in config_file?
            filename = os.path.join(fb.base_dir, filename) # no, use basedir
        logging.FileHandler.__init__(self, filename, mode)

# "register" custom class DynFileHandler as an attribute for the logging module
# to use it inside the logging config file and pass file name / path and mode
# as parameters:
logging.DynFileHandler = DynFileHandler
logging.config.fileConfig(os.path.join(fb.base_dir, rc.log_config_file))#, disable_existing_loggers=True)


if not os.path.exists(rc.save_dir):
    logger.warning('Specified save_dir "%s" doesn\'t exist, using "%s" instead.\n',
        rc.save_dir, fb.base_dir)
    rc.save_dir = fb.base_dir


class pyFDA(QtGui.QMainWindow):
    """
    Create the main window consisting of a tabbed widget for entering filter
    specifications, poles / zeros etc. and another tabbed widget for plotting
    various filter characteristics

    QMainWindow is used here as it is a class that understands GUI elements like
    toolbar, statusbar, central widget, docking areas etc.
    """

    def __init__(self):
        super(pyFDA, self).__init__()
        # initialize the FilterTreeBuilder class with the filter directory and
        # the filter file as parameters:         
        # read directory with filterDesigns and construct filter tree from it
        self.ftb = FilterTreeBuilder('filter_design', 'filter_list.txt', comment_char='#')                                  
        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()]
        - Plot Window [-> plotAll.plotAll()]
        """

        # Instantiate widget groups
        self.inputWidgets = input_tab_widgets.InputTabWidgets() # input widgets
        self.inputWidgets.setMaximumWidth(320) # comment out for splitter

        self.pltWidgets = plot_tab_widgets_crash.PlotTabWidgets() # plot widgets

        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups

        layHMain = QtGui.QHBoxLayout(_widget) # horizontal layout of all groups

        # comment out following 3 lines for splitter design
        layHMain.addWidget(self.inputWidgets)
        layHMain.addWidget(self.pltWidgets)
        layHMain.setContentsMargins(0, 0, 0, 0)#(left, top, right, bottom)

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')

        # Create scroll area and "monitor" _widget whether scrollbars are needed
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidget(_widget) # splitter for var. size tabs?

        #============= Set behaviour of scroll area ======================
        # scroll bars appear when the scroll area shrinks below this size:
        scrollArea.setMinimumSize(QtCore.QSize(800, 500))
#        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) #default
#        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) # default
        scrollArea.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                 QtGui.QSizePolicy.MinimumExpanding)

        # Size of monitored widget is allowed to grow:
        scrollArea.setWidgetResizable(True)


        # CentralWidget (focus of GUI?) is now the ScrollArea
        self.setCentralWidget(scrollArea)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # Here, signals about spec and design changes from lower hierarchies
        # are distributed. At the moment, only changes in the input widgets are
        # routed to the plot widgets:
        #
        # sigSpecsChanged: signal indicating that filter SPECS have changed,
        # requiring partial update of some plot widgets:
#        self.inputWidgets.sigSpecsChanged.connect(self.pltWidgets.update_view)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #  requiring full update of all plot widgets:
#        self.inputWidgets.sigFilterDesigned.connect(self.pltWidgets.update_data)
        #
        # sigReadFilters: button has been pressed to rebuild filter tree:
        self.inputWidgets.inputFiles.sigReadFilters.connect(self.ftb.init_filters)
#####        self.closeEvent.connect(self.aboutToQuit)
#        aboutAction.triggered.connect(self.aboutWindow) # open pop-up window
        logger.debug("Main routine initialized!")


#------------------------------------------------------------------------------
    def statusMessage(self, message):
        """
        Display a message in the statusbar.
        """
        self.statusBar().showMessage(message)

#------------------------------------------------------------------------------       
    def clean_up(self):
        """
        Clean up everything - only called when exiting application

        See http://stackoverflow.com/questions/18732894/crash-on-close-and-quit
        """
        for i in self.__dict__:
            item = self.__dict__[i]
            clean(item)
                
            
    def closeEvent(self, event): # reimplement QMainWindow.closeEvent von !pyFDA!
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
#            self.clean_up()
            event.accept()
        else:
            event.ignore()

#    combine with:
#    self.btnExit.clicked.connect(self.close)
#    app.aboutToQuit.connect(mainw.clean_up)        
#    app.lastWindowClosed.connect(mainw.closeEvent)


#------------------------------------------------------------------------------

def clean(item):
    """
    Clean up memory by closing and deleting item if possible
    """
    if isinstance(item, list) or isinstance(item, dict):
        for _ in range(len(item)):
            clean(item.pop())
    else:
        try:
            item.close()
        except(RuntimeError, AttributeError): # deleted or no close method
            pass
        try:
            item.deleteLater()
        except(RuntimeError, AttributeError): # deleted or no deleteLater method
            pass

#------------------------------------------------------------------------------
def main():
    """ 
    entry point for the pyfda application 
    see http://pyqt.sourceforge.net/Docs/PyQt4/qapplication.html :
    
    "For any GUI application using Qt, there is precisely *one* QApplication object,
    no matter whether the application has 0, 1, 2 or more windows at any given time.
    ...
    Since the QApplication object does so much initialization, it must be created 
    *before* any other objects related to the user interface are created."     
    """
    app = QtGui.QApplication(sys.argv) # instantiate QApplication object, passing ?
    app.setObjectName("TopApp")
    
    icon = os.path.join(fb.base_dir, 'images', 'icons', "Logo_LST_4.svg")

    app.setWindowIcon(QtGui.QIcon(icon))
    app.setStyleSheet(rc.css_rc) 

    mainw = pyFDA()
# http://stackoverflow.com/questions/18416201/core-dump-with-pyqt4
# http://stackoverflow.com/questions/11945183/what-are-good-practices-for-avoiding-crashes-hangs-in-pyqt
# http://stackoverflow.com/questions/5506781/pyqt4-application-on-windows-is-crashing-on-exit
# http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-widgets-in-pyqt
# http://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

        # Sets the active window to the active widget in response to a system event.
    app.setActiveWindow(mainw) #<---- That makes no difference!
    mainw.setWindowIcon(QtGui.QIcon(icon))

    desktop = QtGui.QDesktopWidget() # test the available desktop resolution
    desktop.setParent(mainw)
    screen_h = desktop.availableGeometry().height()
    screen_w = desktop.availableGeometry().width()
    logger.info("Available screen resolution: %d x %d", screen_w, screen_h)

    fontsize = 10
    if screen_h < 800:
        delta = 50
    else:
        delta = 100
    desktop.deleteLater()
    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # top L / top R, dx, dy
    mainw.setFocus()
    mainw.show()

    #start the application's exec loop, return the exit code to the OS
    app.exec_() # same behavior of sys.exit(app.exec_()) and app.exec_()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
