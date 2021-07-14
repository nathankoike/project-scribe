# -*- coding: utf-8 -*-
import os
import json
import glob
from fpdf import FPDF
from PyQt5 import QtCore, QtGui, QtWidgets
from shutil import copyfile, rmtree
from multiprocessing import Process

from file_manipulation.pdf import pdf_processing as pp
from HandwritingRecognitionSystem_v2 import train, config

import ui_classes.page as page
from ui_classes.polygon import Polygon
from ui_classes.image_label import ImageLabel


class UserInterface:
    def setupUi(self, MainWindow):
        """ Creates layout of UI """
        # Main Widget
        self.mainWindow = QtWidgets.QWidget(MainWindow)
        MainWindow.setWindowTitle("project::SCRIBE")
        MainWindow.setCentralWidget(self.mainWindow)
        self.mainWindow.setObjectName("mainWindow")
        MainWindow.resize(1092, 589)

        self.model = "HandwritingRecognitionSystem_v2/UImodel"

        self.process = QtCore.QProcess(self.mainWindow)
        self._pid = -1

        self.pathToHandwritingSystem = os.getcwd()

        # Horizontal layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.mainWindow)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Image label
        self.image = ImageLabel(self)
        self.image.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.image, stretch=5)

        # Text box
        self.textBrowser = QtWidgets.QTextEdit()
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.cursorPositionChanged.connect(self.saveText)
        self.highlighted_cursor = None
        self.highlighter_on = True
        self.horizontalLayout.addWidget(self.textBrowser, stretch=5)

        # Menu bar
        self.menuBar = QtWidgets.QMenuBar(self.mainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1000, 21))

        ### file menu
        self.fileMenu = self.menuBar.addMenu('&File')

        # import file
        self.import_f = self.fileMenu.addAction('Import File')
        self.import_f.setShortcut("Ctrl+I")
        self.import_f.triggered.connect(self.get_file)

        # export pdf
        self.export_f = self.fileMenu.addAction('Export PDF')
        self.export_f.setShortcut("Ctrl+E")
        self.export_f.triggered.connect(self.export_pdf)

        # export txt
        self.export_f = self.fileMenu.addAction('Export txt')
        self.export_f.setShortcut("Ctrl+Shift+E")
        self.export_f.triggered.connect(self.export_file)

        # load project
        self.load_save = self.fileMenu.addAction('Open Project')
        self.load_save.setShortcut("Ctrl+O")
        self.load_save.triggered.connect(self.load_from_json)

        # save project
        self.save_proj = self.fileMenu.addAction('Save Project')
        self.save_proj.setShortcut("Ctrl+S")
        self.save_proj.triggered.connect(MainWindow.save)

        # load model
        self.load_model = self.fileMenu.addAction('Load Model')
        self.load_model.setShortcut("Ctrl+L")
        self.load_model.triggered.connect(self.selectModel)

        ### view menu
        self.viewMenu = self.menuBar.addMenu('&View')

        # toggle polygons
        self.polygon_layer = self.viewMenu.addAction('Turn Polygon Layer Off')
        self.polygon_layer.setShortcut("Ctrl+Shift+P")
        self.polygon_layer.triggered.connect(self.image.toggle_polygon_layer)

        # toggle highlighting
        self.highlighting = self.viewMenu.addAction('Turn Highlighting Off')
        self.highlighting.setShortcut("Ctrl+Shift+H")
        self.highlighting.triggered.connect(self.toggle_highlighting)

        ### polygon menu
        self.polygonMenu = self.menuBar.addMenu('&Polygons')

        # transcribe polygons
        self.transcribe = self.polygonMenu.addAction('Transcribe All Polygons')
        self.transcribe.setShortcut("Ctrl+T")
        self.transcribe.triggered.connect(self.transcribe_all_polygons)

        # continue training
        self.continue_train = self.polygonMenu.addAction('Continue Training Existing Model')
        self.continue_train.triggered.connect(self.continueTraining)

        # train new model
        self.train = self.polygonMenu.addAction('Train Lines from Scratch')
        self.train.triggered.connect(self.trainLines)

        # stop training
        self.stop_train = self.polygonMenu.addAction('Stop Training')
        self.stop_train.triggered.connect(self.stopTraining)
        self.stop_train.setDisabled(True)

        ### advanced menu
        self.polygonMenu = self.menuBar.addMenu('&Advanced')

        # add files to training directory
        self.add_data = self.polygonMenu.addAction('Send Data for Large Batch Training')
        self.add_data.triggered.connect(self.add_training_files)

        # train new model (do not add new files to training directory)
        self.train = self.polygonMenu.addAction('Train Lines from Scratch with Current Data Batch (Does Not Send New Data)')
        self.train.triggered.connect(self.train_current_lines)

        # continue training existing model (do not add new files to training directory)
        self.train = self.polygonMenu.addAction('Continue Training with Current Data Batch (Does Not Send New Data)')
        self.train.triggered.connect(self.continue_current_lines)

        # stop training
        self.stop_train_a = self.polygonMenu.addAction('Stop Training')
        self.stop_train_a.triggered.connect(self.stopTraining)
        self.stop_train_a.setDisabled(True)

        MainWindow.setMenuBar(self.menuBar)

        # save the filename
        self.fname = None

        # initialize attributes for later use
        self.page = 0
        self.pages = []
        self.textCursor = None

        # Page change stuff
        self.page_layout = QtWidgets.QVBoxLayout()
        self._h_layout = QtWidgets.QHBoxLayout()
        self.pageNumberLabel = QtWidgets.QLabel("Page ")
        self.inputPageNumber = QtWidgets.QLineEdit()
        self.inputPageNumber.setAlignment(QtCore.Qt.AlignCenter)
        self.inputPageNumber.setValidator(QtGui.QIntValidator())
        self.inputPageNumber.editingFinished.connect(self.jumpToPage)
        self.inputPageNumber.setReadOnly(True)
        self._h_layout.addWidget(self.pageNumberLabel)
        self._h_layout.addWidget(self.inputPageNumber)
        self.page_layout.addLayout(self._h_layout)

        self.prev_next_page_layout = QtWidgets.QHBoxLayout()
        self.previous_page_button = QtWidgets.QPushButton()
        self.previous_page_button.setObjectName(("previous_page_button"))
        self.previous_page_button.clicked.connect(self.previous_page)
        self.prev_next_page_layout.addWidget(self.previous_page_button)
        self.next_page_button = QtWidgets.QPushButton()
        self.next_page_button.setObjectName(("next_page_button"))
        self.next_page_button.clicked.connect(self.next_page)
        self.prev_next_page_layout.addWidget(self.next_page_button)
        self.page_layout.addLayout(self.prev_next_page_layout)
        self.horizontalLayout.addLayout(self.page_layout)

        # Put text on widgets
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self.mainWindow)

    def retranslateUi(self):
        """ Puts text on QWidgets """
        self.previous_page_button.setText("←")
        self.next_page_button.setText("→")

    # export the current transcription as a pdf
    def export_pdf(self, fname):
        # get a nice filename
        fname = self.fname

        # format the filename nicely
        if fname == None:
            fname = ""
        else:
            fname = ".".join(fname.split('.')[:-1])

        # get the file to save to
        fname = QtWidgets.QFileDialog.getSaveFileName(self.mainWindow, 'Save file',f'c:\\\\{fname}.pdf',"Document type (*.pdf)")

        # Return if no file name is given
        if not fname[0]:
            return

        # create a new pdf
        pdf = FPDF()
        pdf.set_font("Arial", size=11)

        # for every page of the document
        for i in range(len(self.pages)):
            # add a new page to the pdf
            pdf.add_page()

            # for every line on the page
            for line in self.pages[i]._page_lines:
                pdf.cell(0, 10, txt=line._transcription, ln=1, align="L")

        # write to the pdf
        pdf.output(fname[0])

    # get the text data from every page and create one text document with all
    # the current transcriptions
    def export_file(self):
        # get a nice filename
        fname = self.fname

        # format the filename nicely
        if fname == None:
            fname = ""
        else:
            fname = ".".join(fname.split('.')[:-1])

        # get the file to save to
        fname = QtWidgets.QFileDialog.getSaveFileName(self.mainWindow, 'Save file',f'c:\\\\{fname}.txt',"Document type (*.txt)")

        # Return if no file name is given
        if not fname[0]:
            return

        try:
            file = open(fname[0], "w")

            # write out some branding
            file.write("DOCUMENT TRANSCRIPTION MADE WITH project::SCRIBE\n")

            # for every page of the document
            for i in range(len(self.pages)):
                # write a page header
                file.write(f"\n>>> PAGE {i + 1} <<<\n")

                # for every line on the page
                for line in self.pages[i]._page_lines:
                    # write the contents of the page
                    file.write(line._transcription + '\n')

            file.close()

        except Exception as err:
            pass

    def get_file(self):
        """ Gets the embedded jpgs from a pdf """
        self.fname = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, 'Open file','c:\\\\',"Image files (*.jpg *.pdf)")[0]

        # Return if no file name is given
        if not self.fname:
            return

        # clear the list of pages and the current page
        self.page = 0
        self.pages = []

        # Returns a list of all of the pixmaps of the pdf
        imgs = pp.get_pdf_contents(self.fname)

        # Make the appropriate number of pages and assign them pixmaps
        for pixmap in imgs:
            self.pages.append(page.Page(self.image))
            self.pages[-1]._pixmap = pixmap

        self.image._page = self.pages[self.page]
        self.image.update()

        # Initialize page number layout
        self.initializePageNum()

    def initializePageNum(self):
        self.updatePageNum()
        self.inputPageNumber.setReadOnly(False)
        self.pageNumberLabel.setText(f"Page out of {len(self.pages)}:")

    def updatePage(self):
        self.image._page = self.pages[self.page]

        self.image.resizePolygonsToPixmap()
        self.updatePageNum()
        self.updateTextBox()

    def updatePageNum(self):
        self.inputPageNumber.setText(str(self.page + 1))

    def updatePolygonFiles(self):
        """ updates the polygon crop files in the HandwritingRecognitionSystem to the current page's page lines"""
        for line in self.image._page._page_lines:
            file_path = "HandwritingRecognitionSystem_v2/formalsamples/Images/"+line._image_name
            self.image._page._polygon_points = line._vertices.copy()
            self.image._page.polygonCrop(file_path)
            self.image._page._polygon_points = []

    def next_page(self):
        """ Next page button """
        if hasattr(self, "page") and self.page < len(self.pages) - 1:
            # change the page index and update the page
            self.page += 1
            self.updatePage()
        else:
            print('\a', end="")

    def previous_page(self):
        """ Previous page button """
        if hasattr(self, "page") and self.page > 0:
            self.page -= 1
            self.updatePage()
        else:
            print('\a', end="")

    def find_ckpt_number(self):
        with open(f"{self.model}/checkpoint", "r", encoding="utf-8") as f:
            firstline = f.readline()
        return int(firstline[firstline.find("-") + 1:-2])

    # add files to the training directory without training
    def add_training_files(self):
        # only train if the page is loaded
        if self.image._page:
            self.model = QtWidgets.QFileDialog.getExistingDirectory()

            # Return if no file name is given
            if not self.model:
                return

            if not os.path.isdir(f"{self.model}/Text/"):
                os.mkdir(f"{self.model}/Text/")
            if not os.path.isdir(f"{self.model}/Images/"):
                os.mkdir(f"{self.model}/Images/")
            if not os.path.isdir(f"{self.model}/Labels/"):
                os.mkdir(f"{self.model}/Labels/")
            if not os.path.isfile(f"{self.model}/CHAR_LIST"):
                copyfile('HandwritingRecognitionSystem_v2/UImodel/CHAR_LIST', f"{self.model}/CHAR_LIST")

            self.image._page.trainLines()

    # train only the lines that have already been sent
    def train_current_lines(self, resume_training=False):
        # only train if the page is loaded
        if self.image._page:
            self.model = QtWidgets.QFileDialog.getExistingDirectory()

            # Return if no file name is given
            if not self.model:
                return

            # change button text and disconnect from trainLines
            self.train.setDisabled(True)
            self.continue_train.setDisabled(True)
            self.stop_train.setDisabled(False)
            self.stop_train_a.setDisabled(False)

            # change to the text directory of the model
            os.chdir(self.model + "/Labels")

            # get the number of files in the directory
            file_number = len(glob.glob('*')) + 1

            os.chdir("..")


            # configure the charlist earlier
            config.cfg.CHAR_LIST = self.model + "/CHAR_LIST"

            # the checkpoint to resume training
            ckpt = 0

            # check if were resuming or restarting
            if resume_training:
                ckpt = self.find_ckpt_number()
                print(ckpt)

            # start training process
            self.process = Process(
                target=train.run,
                args=(
                    file_number,
                    self.model,
                    ckpt,
                    )
                )
            self.process.start()

    # continue training without sending new data
    def continue_current_lines(self):
        self.train_current_lines(True)

    def trainLines(self, continue_training=False):
        """ train on selected polygons """
        # only train if the page is loaded
        if self.image._page:
            self.model = QtWidgets.QFileDialog.getExistingDirectory()

            # Return if no file name is given
            if not self.model:
                return

            continue_training_at_epoch = 0
            if not continue_training:
                if os.path.isdir(f"{self.model}/Text/"):
                    rmtree(f"{self.model}/Text")
                else:
                    os.mkdir(f"{self.model}/Text/")

                if os.path.isdir(f"{self.model}/Images/"):
                    rmtree(f"{self.model}/Images")
                else:
                    os.mkdir(f"{self.model}/Images/")

                if os.path.isdir(f"{self.model}/Labels/"):
                    rmtree(f"{self.model}/Labels")
                else:
                    os.mkdir(f"{self.model}/Labels/")

                if not os.path.isfile(f"{self.model}/CHAR_LIST"):
                    copyfile('HandwritingRecognitionSystem_v2/UImodel/CHAR_LIST', f"{self.model}/CHAR_LIST")
            else:
                continue_training_at_epoch = self.find_ckpt_number()


            # change button text and disconnect from trainLines
            self.train.setDisabled(True)
            self.continue_train.setDisabled(True)
            self.stop_train.setDisabled(False)
            self.stop_train_a.setDisabled(False)

            # change to the text directory of the model
            os.chdir(self.model + "/Labels")

            # get the number of files in the directory
            file_number = len(glob.glob('*')) + 1
            os.chdir("..")


            # configure the charlist earlier
            config.cfg.CHAR_LIST = self.model + "/CHAR_LIST"

            # start training process
            file_number = self.image._page.trainLines()
            self.process = Process(
                target=train.run,
                args=(
                    file_number,
                    self.model,
                    continue_training_at_epoch,
                    )
                )
            self.process.start()

    def continueTraining(self):
        """ pick a model to continue training from for selected polygons """
        self.trainLines(True)

    def stopTraining(self):
        # change button text and disconnect from stopTraining function
        self.train.setDisabled(False)
        self.continue_train.setDisabled(False)
        self.stop_train.setDisabled(True)
        self.stop_train_a.setDisabled(True)

        # kill the training process
        self.process.terminate()
        self.process.join()

        self.remove_old_ckpts()

    def remove_old_ckpts(self):
        with open(f"{self.model}/checkpoint", "r") as f:
            firstline = f.readline()

        inside_ckpt_name = False
        checkpoint_name = ""
        for letter in reversed(firstline):
            if letter == "/" or letter == "\\":
                break
            if inside_ckpt_name and letter != '"':
                checkpoint_name = letter + checkpoint_name
            if letter == '"':
                inside_ckpt_name = not inside_ckpt_name

        for filename in os.listdir(self.model):
            if "ckpt" in filename and checkpoint_name not in filename:
                filename_relPath = os.path.join(self.model, filename)
                os.remove(filename_relPath)

    def jumpToPage(self):
        pageNumber = int(self.inputPageNumber.text()) - 1
        if pageNumber < 0:
            pageNumber  = 0
        elif pageNumber >= len(self.pages):
            pageNumber = len(self.pages) - 1

        # change the page index and object
        self.page = pageNumber
        self.updatePage()

    def transcribe_selected_polygon(self):
        """ Transcribes one polygon """
        p = self.image._page._selected_polygon
        self.image._page._polygon_points = p._vertices.copy()
        image_name = self.image._page.polygonCrop()
        self.image._page._polygon_points = []
        transcript = self.image._page.transcribePolygon(image_name)

        p.set_transcription(transcript)
        p._is_transcribed = True
        self.updateTextBox()

    def transcribe_all_polygons(self):
        """ Transcribes all polygons """
        if not self.image._page:
            return

        for p in self.image._page._page_lines:
            if not p._is_transcribed and not p._ready_for_training:
                self.image._page._polygon_points = p._vertices.copy()
                image_name = self.image._page.polygonCrop()
                self.image._page._polygon_points = []
                transcript = self.image._page.transcribePolygon(image_name)
                p.set_transcription(transcript)
                p._is_transcribed = True
        self.updateTextBox()

    def toggle_highlighting(self):
        """ Turn highlighting on if off and off if on """
        if self.highlighter_on:
            self.highlighter_on = False
            self.highlighting.setText('Turn Highlighting On')
            # clear highlighted text
            if self.highlighted_cursor:
                old_cursor = self.textBrowser.textCursor()
                fmt = QtGui.QTextBlockFormat()
                fmt.setBackground(QtGui.QColor("white"))
                self.highlighted_cursor.setBlockFormat(fmt)
                self.textBrowser.setTextCursor(old_cursor)
                self.highlighted_cursor = None
                self.image._page._highlighted_polygon = None
        else:
            self.highlighter_on = True
            self.highlighting.setText('Turn Highlighting Off')

        self.image.update()

    def move_cursor(self, line):
        """ Moves cursor to given line """
        textCursor = self.textBrowser.textCursor()
        textCursor.movePosition(1)
        for _ in range(line):
            textCursor.movePosition(12)
        self.textBrowser.setTextCursor(textCursor)

    def highlight_line(self):
        """ Highlights line where cursor currently is """
        if self.highlighter_on and self.image._page._highlighted_polygon:
            fmt = QtGui.QTextBlockFormat()

            # clear prevosly highlighted block, if any
            if self.highlighted_cursor:
                fmt.setBackground(QtGui.QColor("white"))
                self.highlighted_cursor.setBlockFormat(fmt)

            # highlight block cursor is currently on
            self.highlighted_cursor = self.textBrowser.textCursor()
            fmt.setBackground(QtGui.QColor("yellow"))
            self.highlighted_cursor.setBlockFormat(fmt)

    def highlight(self):
        """ Highlights line where cursor is and the corresponding polygon.
        Called when cursor position changes. """

        if self.image._page and self.highlighter_on:
            index = self.textBrowser.textCursor().blockNumber()

            # select and highlight corresponding polygon
            for item in self.image._page._page_lines:
                if item._block_number == index:
                    self.image._page._highlighted_polygon = item
                    self.image._page._selected_polygon = item
                    self.image.update()

            # highlight line
            self.highlight_line()

    def updateTextBox(self):
        if self.image._page:
            old_highlighter_on = self.highlighter_on
            self.highlighter_on = False

            text = ""
            for line in self.image._page._page_lines:
                text = text + line._transcription + "\n"
            # chops off final newline
            text = text[:-1]
            self.textBrowser.setText(text)

            self.highlighter_on = old_highlighter_on

            if self.image._page._highlighted_polygon:
                index = self.image._page._highlighted_polygon._block_number
                self.move_cursor(index)
                self.highlight_line()

    def saveText(self):
        if self.image._page:
            self.image._page.saveLines()
            self.highlight()
        else:
            self.textBrowser.undo()
            print('\a', end="")

    def selectModel(self):
        """allows user to select the model they want to use"""
        self.model = QtWidgets.QFileDialog.getExistingDirectory()

    # load all the lines from the json file
    def _load_lines(self, new_page, lines):
        # loop through all the lines in the page
        for i in range(len(lines)):
            # try to get the original pixmap size
            try:
                og_wh = lines[i]['og_wh']
            except:
                og_wh = (self.mainWindow.size().width(), self.mainWindow.size().height())

            # try to get the original points
            try:
                og_pts = lines[i]['og_pts']
            except:
                og_pts = lines[i]["points"]

            # make a new line object
            new_line = Polygon(None, lines[i]["points"], og_wh[0], og_wh[1], og_pts)

            # backwards compatibility
            try:
                # set the _is_transcribed and _ready_for_training attributes
                new_line._is_transcribed = lines[i]['transcribed']
                new_line._ready_for_training = lines[i]['training']
            except:
                pass

            # make the polygon for the line
            new_line.updatePolygon()

            # set the block number for proper rendering order
            new_line._block_number = lines[i]["block"]

            # set the transcription
            new_line._transcription = lines[i]["transcription"]

            # append the line object
            new_page._page_lines.append(new_line)

    # load all the pages from the json file
    def _load_pages(self, pages):
        # loop through all the pages
        for i in range(len(pages)):
            # make a new page
            new_page = page.Page(self.image)

            # save the pixmap to the disk
            with open("jpg.jpg", "wb") as file:
                file.write(pages[i]["pixmap"].encode("Latin-1"))

            # restore the old pixmap
            new_page._pixmap = QtGui.QPixmap("jpg.jpg")

            # restore the lines from of the page
            self._load_lines(new_page, pages[i]["lines"])

            # add the page to the current project
            self.pages.append(new_page)

    # load the project from a json file
    def load_from_json(self):
        # get the file to load from
        fname = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, 'Open file','c:\\\\',"Project files (*.json *.prj)")

        # Return if no file name is given
        if not fname[0]:
            return

        # set the filename
        self.fname = fname[0]

        # clear the list of pages and the current page
        self.page = 0
        self.pages = []

        # create a convenient way to access the saved information
        saved = None

        # load the json file as dictionary
        with open(fname[0], "r") as file:
            saved = json.loads(file.read())

        # restore the window size
        self.mainWindow.resize(saved["window"][0], saved["window"][1])

        # maintain backwards compatibility
        try:
            # reload the same model from before
            self.model = saved['model']
        except:
            pass

        # load all the pages
        self._load_pages(saved["pages"])

        # set the page number to the saved page number
        self.page = saved['index']

        self.image._page = self.pages[self.page]
        self.image.update()

        # Initialize page number layout
        self.initializePageNum()

        # add the transcriptions
        self.updateTextBox()
