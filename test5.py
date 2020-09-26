# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created: Thu Sep 10 20:52:52 2020
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

import sys
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QRubberBand
from PyQt5.QtCore import QRect, QSize

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

def resize_image(image):
    baseheight = 640
    img = Image.open(image)
    hpercent = (baseheight / float(img.size[1]))
    wsize = int((float(img.size[0]) * float(hpercent)))
    img = img.resize((wsize, baseheight), Image.ANTIALIAS)
    img.save(image)


class Ui_test:
    def setupUi(self, test):
        test.setObjectName(_fromUtf8("test"))
        test.resize(1092, 589)
        self.horizontalLayout = QtWidgets.QHBoxLayout(test)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        # self.label = QtWidgets.QLabel(test)
        self.label = ImageLabel()
        self.label.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label)

        self.textBrowser = QtWidgets.QTextBrowser(test)
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.horizontalLayout.addWidget(self.textBrowser)
        self.textLayout = QtWidgets.QHBoxLayout(self.textBrowser)
        #self.child_label = QtWidgets.QLabel(self.textBrowser)
        #self.child_label_2 = QtWidgets.QLabel(self.textBrowser)
        #self.textLayout.addWidget(self.child_label)
        #self.textLayout.addWidget(self.child_label_2)

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.child_label= QtWidgets.QLabel(self.textBrowser)

        self.pushButton_2 = QtWidgets.QPushButton(test)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.pushButton_2.clicked.connect(self.get_file)
        self.verticalLayout.addWidget(self.pushButton_2)

        self.pushButton_3 = QtWidgets.QPushButton(test)
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.pushButton_3.clicked.connect(self.show_text)
        self.verticalLayout.addWidget(self.pushButton_3)

        self.pushButton = QtWidgets.QPushButton(test)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(test)
        QtCore.QMetaObject.connectSlotsByName(test)

    def retranslateUi(self, test):
        test.setWindowTitle(_translate("test", "test", None))
        self.label.setText(_translate("test", "                                               PDF Viewer                                                   ", None))
        #self.child_label.setText(_translate("test","y",None))
        #self.child_label_2.setText(_translate("test","uh",None))
        self.pushButton_2.setText(_translate("test", "Import PDF", None))
        self.pushButton_3.setText(_translate("test", "Export PDF", None))
        self.pushButton.setText(_translate("test", "Editing Mode", None))

    def get_file(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(test, 'Open file','c:\\',"Image files (*.jpeg *.pdf)")
        #dir = QtWidgets.QFileDialog.getExistingDirectory()
        #print(dir)
        if not fname[0]:
            return
        images = convert_from_path(fname[0])
        images[0].save('out.jpg','JPEG')
        resized = resize_image('out.jpg')
        self.label.setPixmap(QtGui.QPixmap('out.jpg'))

    def select(self,label):
        label.setFlat(False)
        #label.setText(_translate("test","NOPE",None))

    def show_text(self):
        string = "This is example text! asdfasdfasdf"
        #characters = []
        #self.labels = []
        for i in range(0,len(string)):
            new_label = QtWidgets.QPushButton(test)
            self.labels.append(new_label)
            #characters.append(new_label)
            new_label.setFlat(True)
            new_label.setText(_translate("test",string[i],None))
            self.textLayout.addWidget(new_label)
            new_label.clicked.connect(lambda: self.select(new_label))

class ImageLabel(QtWidgets.QLabel):
    def __init__(self):
        """ Provides event support for the image label """
        super(ImageLabel, self).__init__()
        self.rubberBand = 0
        self.selectPolygon = False
        self.polygonPoints = []
        # self.setMouseTracking(True)

    def mousePressEvent(self, event):
        """ Collects points for the polygon and creates selection boxes """
        if self.selectPolygon:
            self.polygonPoints.append((event.x(),event.y()))

        self.origin = event.pos()
        if not self.rubberBand:
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        """ Displays the selection box """
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """ Hides the selection box """
        self.rubberBand.hide()
        print(self.origin, event.pos())


# https://doc.qt.io/qtforpython/PySide2/QtWidgets/QRubberBand.html
class MainWidget(QtWidgets.QWidget):
    def __init__(self):
        """ Calls the UI immediately and provides event support """
        super(MainWidget, self).__init__()
        self.ui = Ui_test()
        self.ui.setupUi(self)

    def keyPressEvent(self, event):
        """ Called when a key is pressed """
        if event.key() == QtCore.Qt.Key_Return:
            self.ui.label.selectPolygon = not self.ui.label.selectPolygon
            print(self.ui.label.polygonPoints)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    test = MainWidget()
    test.show()
    sys.exit(app.exec_())
