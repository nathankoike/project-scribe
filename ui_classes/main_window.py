# -*- coding: utf-8 -*-
import sys
from ui_classes.page import Page
import json
from PyQt5 import QtCore, QtGui, QtWidgets
from file_manipulation.pdf import pdf_processing as pp
from ui_classes.interface import UserInterface


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        """ Calls the UI immediately and provides event support """
        super(MainWindow, self).__init__()
        self.ui = UserInterface()
        self.ui.setupUi(self)

    def keyPressEvent(self, event):
        """ Called when a key is pressed """
        # cancel polygon selection when ESC is pressed
        if event.key() == QtCore.Qt.Key_Escape and len(self.ui.label._page._polygon_points) > 0:
            # Delete polygon user is currently making
            self.ui.label._page._selected_polygon = None
            self.ui.label._page._polygon_start = None
            self.ui.label._lines = []
            self.ui.label._start_of_line = []
            self.ui.label._page._polygon = QtGui.QPolygon()
            self.ui.label._page._polygon_points = []
            self.ui.label.update()

    # create a dictionary containing all the information needed to reconstruct
    # a single line on a page
    def _save_line(self, line):
        # create a dictionary for the information in the line
        current_line = {}

        current_line['og_wh'] = line._original_pixmap_w_h
        current_line['og_pts'] = line._original_vertices
        current_line['points'] = line._vertices
        current_line['transcribed'] = line._is_transcribed
        current_line['training'] = line._ready_for_training
        current_line['block'] = line._block_number
        current_line['transcription'] = line._transcription

        return current_line

    # create a dictionary containing all the information needed to reconstruct
    # a single page of a document
    def _save_page(self, page):
        # create a dictionary for the information in each page
        current_page = {}

        # create a list to hold all the lines
        lines = []

        # for every line on the page
        for i in range(len(page._page_lines)):
            # add the line to the dictionary of lines
            lines.append(self._save_line(page._page_lines[i]))

        # write the pixmap to a file
        page.writePixmaptoFile()

        # save the pixmap image data of the page into the dictionary
        current_page['pixmap'] = pp.read_binary("jpg.jpg")

        # save the lines of the document
        current_page['lines'] = lines

        return current_page

    # save the project
    def save(self):
        # get a nice filename
        fname = self.ui.fname

        # format the filename nicely
        if fname == None:
            fname = ""
        else:
            fname = ".".join(fname.split('.')[:-1])

        # get the file to save to
        fname = QtWidgets.QFileDialog.getSaveFileName(test, 'Save file',f'c:\\\\{fname}.json',"Project files (*.json *.prj)")

        # Return if no file name is given
        if not fname[0]:
            return

        try:
            self.fname = fname[0]

            # open a file to save
            save_file = open(fname[0], "w")

            # create a dictionary to hold all of the binaries
            project = {}

            # get the window size for the project to load polygons properly
            project['window'] = [self.size().width(), self.size().height()]

            # save the model that the user was using
            project['model'] = self.ui.model

            # save the current page number
            project["index"] = self.ui.page

            # store all the pages in a list
            pages = []

            # for every page in the document
            for i in range(len(self.ui.pages)):
                # add the page to the dictionary of pages
                pages.append(self._save_page(self.ui.pages[i]))

            # save the pages to the project
            project['pages'] = pages

            # save the project
            save_file.write(json.dumps(project))

        except Exception as err:
            print("there was an error\n")
            print(err)

    def closeEvent(self, event):
        # try to stop training
        try:
            self.ui.stop_train()
        except:
            pass

        # close gracefully
        event.accept()
