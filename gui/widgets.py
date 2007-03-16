#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.4.2 Release Mon Feb 26 08:57:40 2007
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Distributed under the GNU General Public License, see file COPYING
## Copyright (C) Benedict Verhegghe except where stated otherwise 
##
"""A collection of custom widgets used in the pyFormex GUI"""

import os,types
from PyQt4 import QtCore, QtGui
import globaldata as GD


class FileSelection(QtGui.QFileDialog):
    """A file selection dialog widget.

    You can specify a default path/filename that will be suggested initially.
    If a pattern is specified, only matching files will be shown.
    A pattern can be something like 'Images (*.png *.jpg)' or a list
    of such strings.
    Default mode is to accept any filename. You can specify exist=True
    to accept only existing files. Or set exist=True and multi=True to
    accept multiple files.
    If dir==True, a single existing directory is asked.
    """
    def __init__(self,path,pattern=None,exist=False,multi=False,dir=False):
        """The constructor shows the widget."""
        QtGui.QFileDialog.__init__(self)
        if os.path.isfile(path):
            self.setDirectory(os.path.dirname(path))
            self.selectFile(path)
        else:
            self.setDirectory(path)
        if type(pattern) == str:
            self.setFilter(pattern)
        else: # should be a list of patterns
            self.setFilters(pattern)
        if dir:
            mode = QtGui.QFileDialog.Directory
            caption = "Select a directory"
        elif exist:
            if multi:
                mode = QtGui.QFileDialog.ExistingFiles
                caption = "Select existing files"
            else:
                mode = QtGui.QFileDialog.ExistingFile
                caption = "Open existing file"
        else:
            mode = QtGui.QFileDialog.AnyFile
            caption = "Save file as"
        self.setFileMode(mode)
        self.setWindowTitle(caption)
        if exist:
            self.setLabelText(QtGui.QFileDialog.Accept,'Open')
        else:
            self.setLabelText(QtGui.QFileDialog.Accept,'Save')
        
    def getFilename(self):
        """Ask for a filename by user interaction.

        Return the filename selected by the user.
        If the user hits CANCEL or ESC, None is returned.
        """
        self.exec_()
        if self.result() == QtGui.QDialog.Accepted:
            files = map(str,self.selectedFiles())
            if self.fileMode() == QtGui.QFileDialog.ExistingFiles:
                return files
            else:
                return files[0]
        else:
            return None


class SaveImageDialog(FileSelection):
    """A file selection dialog with extra fields."""
    def __init__(self,path=None,pattern=None,exist=False,multi=False):
        """Create the dialog."""
        if path is None:
            path = GD.cfg['workdir']
        if pattern is None:
            pattern = "Images (*.png *.jpg)"
        FileSelection.__init__(self,path,pattern,exist)
        grid = self.layout()
        nr,nc = grid.rowCount(),grid.columnCount()
        self.win = QtGui.QCheckBox("Whole Window")
        self.mul = QtGui.QCheckBox("Multi mode")
        self.hot = QtGui.QCheckBox("Activate 'S' hotkey")
        self.aut = QtGui.QCheckBox('Autosave mode')
        self.mul.setChecked(multi)
        self.hot.setChecked(multi)
        self.win.setToolTip("If checked, the whole window is saved;\nelse, only the Canvas is saved.")
        self.mul.setToolTip("If checked, multiple images can be saved\nwith autogenerated names.")
        self.hot.setToolTip("If checked, a new image can be saved\nby hitting the 'S' key when focus is in the Canvas.")
        self.aut.setToolTip("If checked, a new image will saved\non each draw() operation")
        grid.addWidget(self.win,nr,0)
        grid.addWidget(self.mul,nr,1)
        grid.addWidget(self.hot,nr,2)
        grid.addWidget(self.aut,nr,3)

    def getResult(self):
        self.exec_()
        if self.result() == QtGui.QDialog.Accepted:
            fn = str(self.selectedFiles()[0])
            wi = self.win.isChecked()
            mu = self.mul.isChecked()
            hk = self.hot.isChecked()
            as = self.aut.isChecked()
            return fn,wi,mu,hk,as
        else:
            return None,False,False,False,False


        
class AppearenceDialog(QtGui.QDialog):
    """A dialog for setting the GUI appearance."""
    def __init__(self):
        """Create the Appearance dialog."""
        self.font = None
        QtGui.QDialog.__init__(self)
        self.setWindowTitle('Appearance Settings')
        # Style
        styleLabel = QtGui.QLabel('Style')
        self.styleCombo = QtGui.QComboBox()
        styles = map(str,QtGui.QStyleFactory().keys())
        GD.debug("Available styles : %s" % styles)
        style = GD.app.style().objectName()
        GD.debug("Current style : %s" % style)
        self.styleCombo.addItems(styles)
        self.styleCombo.setCurrentIndex([i.lower() for i in styles].index(style))
        # Font
        fontLabel = QtGui.QLabel('Font')
        font = GD.app.font().toString()
        GD.debug("Current font : %s" % font)
        self.fontButton = QtGui.QPushButton(font)
        self.connect(self.fontButton,QtCore.SIGNAL("clicked()"),self.setFont)
        # Accept/Cancel Buttons
        acceptButton = QtGui.QPushButton('OK')
        self.connect(acceptButton,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("accept()"))
        cancelButton = QtGui.QPushButton('Cancel')
        self.connect(cancelButton,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("reject()"))
        # Putting it all together
        grid = QtGui.QGridLayout()
        grid.setColumnStretch(1,1)
        grid.setColumnMinimumWidth(1,250)
        grid.addWidget(styleLabel,0,0)
        grid.addWidget(self.styleCombo,0,1,1,2)
        grid.addWidget(fontLabel,1,0)
        grid.addWidget(self.fontButton,1,1,1,-1)
        grid.addWidget(acceptButton,2,3)
        grid.addWidget(cancelButton,2,4)
        self.setLayout(grid)
        


    def setFont(self):
        font,ok = selectFont()
        if ok:
            self.fontButton.setText(font.toString())
            self.font = font

            
    def getResult(self):
        self.exec_()
        if self.result() == QtGui.QDialog.Accepted:
            style = QtGui.QStyleFactory().create(self.styleCombo.currentText())
            return style,self.font 
        else:
            return None,None

        
class Selection(QtGui.QDialog):
    """A dialog for selecting one or more items from a list."""
    
    selection_mode = {
        None: QtGui.QAbstractItemView.NoSelection,
        'single': QtGui.QAbstractItemView.SingleSelection,
        'multi': QtGui.QAbstractItemView.MultiSelection,
        'contiguous': QtGui.QAbstractItemView.ContiguousSelection,
        'extended': QtGui.QAbstractItemView.ExtendedSelection,
        }
    
    def __init__(self,slist=[],title='Selection Dialog',mode=None,sort=False,\
                 selected=[]):
        """Create the SelectionList dialog.

        selected is a list of items that are initially selected.
        """
        QtGui.QDialog.__init__(self)
        self.setWindowTitle(title)
        # Selection List
        self.listw = QtGui.QListWidget()
        self.listw.addItems(slist)
        if sort:
            self.listw.sortItems()
        if selected:
            self.setSelected(selected)
        self.listw.setSelectionMode(self.selection_mode[mode])
        # Accept/Cancel Buttons
        acceptButton = QtGui.QPushButton('OK')
        self.connect(acceptButton,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("accept()"))
        cancelButton = QtGui.QPushButton('Cancel')
        self.connect(cancelButton,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("reject()"))
        # Putting it all together
        grid = QtGui.QGridLayout()
        grid.setColumnStretch(1,1)
        grid.setColumnMinimumWidth(1,250)
        grid.addWidget(self.listw,0,0,1,-1)
        grid.addWidget(acceptButton,1,0)
        grid.addWidget(cancelButton,1,1)
        self.setLayout(grid)

    def setSelected(self,selected):
        """Mark the specified items as selected."""
        for s in selected:
            for i in self.listw.findItems(s,QtCore.Qt.MatchExactly):
                # OBSOLETE: should be changed with Qt version 4.2 or later
                self.listw.setItemSelected(i,True)
                # SHOULD BECOME:
                # i.setSelected(True) # requires Qt 4.2
                # i.setCheckState(QtCore.Qt.Checked)

                
    def getResult(self):
        self.exec_()
        if self.result() == QtGui.QDialog.Accepted:
            res = [ i.text() for i in self.listw.selectedItems() ]
            return map(str,res)
        else:
            return []
        

# !! The QtGui.QColorDialog can not be instantiated or subclassed.
# !! The color selection dialog is created by the static getColor
# !! function.

def getColor(col=None):
    """Create a color selection dialog and return the selected color.

    col is the initial selection.
    If a valid color is selected, its string name is returned, usually as
    a hex #RRGGBB string. If the dialog is canceled, None is returned.
    """
    if type(col) == tuple:
        col = QtGui.QColor.fromRgb(*col)
    else:
        col = QtGui.QColor(col)
    col = QtGui.QColorDialog.getColor(col)
    if col.isValid():
        return str(col.name())
    else:
        return None


## !! THIS IS NOT FULLY FUNCTIONAL YET
## It can already be used for string items  
class inputDialog(QtGui.QDialog):
    """A dialog widget to set the value of one or more items.

    This feature is still experimental (though already used in a few places.
    """
    
    def __init__(self,items,caption='Input Dialog',*args):
        """Creates a dialog which asks the user for the value of items.

        Each item in the 'items' list is a tuple holding at least the name
        of the item, and optionally some more elements that limit the type
        of data that can be entered. The general format of an item is:
          name,value,type,range,default
        It should fit one of the following schemes:
        ('name') or ('name',str) : type string, any string input allowed
        ('name',int) : type int, any integer value allowed
        ('name',int,'min','max') : type int, only min <= value <= max allowed
        For each item a label with the name and a LineEdit widget are created,
        with a validator function where appropriate.
        """
        QtGui.QDialog.__init__(self,*args)
        self.resize(400,200)
        self.setWindowTitle(caption)
        self.fields = []
        self.result = []
        form = QtGui.QVBoxLayout()
        for item in items:
            # Create the text label
            label = QtGui.QLabel(item[0])
            # Create the input field
            input = QtGui.QLineEdit(str(item[1]))
            if len(item) == 2 or item[2] == 'str':
                pass
                #print "%s is a string"%item[0]
            elif item[2] == 'int':
                #print "%s is an integer"%item[0]
                if len(item) ==3 :
                    input.setValidator(QtGui.QIntValidator(input))
                else:
                    input.setValidator(QtGui.QIntValidator(item[3][0],item[3][1],input))
            elif item[2] == 'float':
                pass
                #print "%s is a float"%item[0]
            input.selectAll()
            self.fields.append([label,input])
            # Add label and input field to a horizontal layout in the form
            line = QtGui.QHBoxLayout()
            line.addWidget(label)
            line.addWidget(input)
            form.addLayout(line)
        # add OK and Cancel buttons
        but = QtGui.QHBoxLayout()
        spacer = QtGui.QSpacerItem(0,0,QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum )
        but.addItem(spacer)
        ok = QtGui.QPushButton("OK",self)
        ok.setDefault(True)
        cancel = QtGui.QPushButton("CANCEL",self)
        #cancel.setAccel(QtGui.QKeyEvent.Key_Escape)
        #cancel.setDefault(True)
        but.addWidget(cancel)
        but.addWidget(ok)
        form.addLayout(but)
        self.connect(cancel,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("reject()"))
        self.connect(ok,QtCore.SIGNAL("clicked()"),self.acceptdata)
        self.setLayout(form)
        # Set the keyboard focus to the first input field
        self.setFocusProxy(self.fields[0][1])
        self.fields[0][0].setFocus()
        self.show()
        
    def acceptdata(self):
        for label,data in self.fields:
            self.result.append([str(label.text()),str(data.text())])
        self.accept()
        
    def getResult(self):
        accept = self.exec_() == QtGui.QDialog.Accepted
        GD.app.processEvents()
        return (self.result, accept)


def selectFont():
    """Ask the user to select a font.

    A font selection dialog widget is displayed and the user is requested
    to select a font.
    Returns a tuple (font,ok), where ok will be true if the user exited
    the dialog with the OK or ENTER button.
    """
    return QtGui.QFontDialog.getFont()


class Menu(QtGui.QMenu):
    """A popup menu for user actions."""

    def __init__(self,title='UserMenu',insert=True):
        """Create the user menu."""
        QtGui.QMenu.__init__(self,title)
        self.insert = insert
        if self.insert:
            GD.gui.insertMenu(self)
        else:
            self.setWindowFlags(QtCore.Qt.Dialog)
            self.setWindowTitle(title)
        self.done = False

    def addItem(self,item,val=None):
        if item == '---':
            self.addSeparator()
        elif isinstance(val, list):
            pop = Menu(item,insert=False)
            pop.addItems(val)
            self.addMenu(pop)
        else:
            if type(val) == str:
                val = eval(val)
            self.addAction(item,val)

    def addItems(self,itemlist):
        for txt,val in itemlist:
            self.addItem(txt,val)

    def process(self):
        if not self.done:
            if not self.insert:
                self.show()
            GD.app.processEvents()

    def close(self):
        """Close the menu."""
        self.done=True
        #print self.done
        #print self.insert
        if self.insert:
            GD.gui.removeMenu(self)
# End
