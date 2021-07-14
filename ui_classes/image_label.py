# -*- coding: utf-8 -*-
import time
from multiprocessing import Process
import json
import glob
from ui_classes.page import Page
from fpdf import FPDF
from PyQt5 import QtCore, QtGui, QtWidgets
from file_manipulation.pdf import pdf_processing as pp
from HandwritingRecognitionSystem_v2 import train, config
from shutil import copyfile, rmtree
import ui_classes.interface


class ImageLabel(QtWidgets.QLabel):
    def __init__(self, ui):
        """ Provides event support for the image label """
        super(ImageLabel, self).__init__()
        self._ui = ui
        self._page = None
        self._lines = []
        self._start_of_line = []
        self._end_of_line = []
        self._polygon_layer = True
        self.setMouseTracking(True)

    def toggle_polygon_layer(self):
        if self._polygon_layer:
            self._polygon_layer = False
            self._ui.polygon_layer.setText('Turn Polygon Layer On')
        else:
            self._polygon_layer = True
            self._ui.polygon_layer.setText('Turn Polygon Layer Off')
        self.update()

    def contextMenuEvent(self, event):
        """ Right click menu """
        if not self._page:
            return

        contextMenu = QtWidgets.QMenu()
        delete = contextMenu.addAction("Delete")
        transcribe = contextMenu.addAction("Transcribe")
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

        point = QtCore.QPoint(event.x(), event.y())
        if self._page.pointInPolygon(point):
            self._page.selectClickedPolygon(point)
            if action == delete:
                self._page.deleteSelectedPolygon()
            elif action == transcribe:
                self._ui.transcribe_selected_polygon()

    def paintEvent(self, event):
        """ Paints a polygon on the pixmap after selection
            during selection of a polygon points the current line """
        painter = QtGui.QPainter(self)

        if self._page:
            scaledPixmap = self._page._pixmap.scaled(self.rect().size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self._page._pixmap_rect = QtCore.QRect(self.rect().topLeft(), scaledPixmap.size())
            painter.drawPixmap(self._page._pixmap_rect, scaledPixmap)

            painter.setPen(QtCore.Qt.red)

            if self._polygon_layer:
                if self._page._polygon_start:
                    # draw ellipse for first point in polygon
                    painter.drawEllipse(self._page._polygon_start[0]-5,self._page._polygon_start[1]-5,10,10)

                if  self._start_of_line and self._end_of_line:
                    painter.drawLine(self._start_of_line, self._end_of_line)

                for start, end in self._lines:
                    painter.drawLine(start, end)

                for page_line in self._page._page_lines:
                    if page_line._is_transcribed:
                        painter.setPen(QtCore.Qt.green)
                    elif page_line._ready_for_training:
                        painter.setPen(QtCore.Qt.yellow)
                    else:
                        painter.setPen(QtCore.Qt.red)
                    painter.drawConvexPolygon(page_line._polygon)

            painter.setPen(QtCore.Qt.red)

            if self._page._selected_polygon:
                if self._polygon_layer:
                    # Show vertices
                    for vertex in self._page._selected_polygon._vertices:
                        painter.drawEllipse(int(vertex[0]-5),int(vertex[1]-5),10,10)

            # highlight polygon
            if self._ui.highlighter_on and self._page._highlighted_polygon:
                path = QtGui.QPainterPath()
                polyf = QtGui.QPolygonF()
                for point in self._page._highlighted_polygon._polygon:
                    x = float(point.x())
                    y = float(point.y())
                    pointf = QtCore.QPointF(x, y)
                    polyf << pointf

                painter.setPen(QtCore.Qt.NoPen)
                color = QtGui.QColor(255, 255, 0, 80)
                path.addPolygon(polyf)
                painter.fillPath(path, color)

    def resizeEvent(self, event):
        """ scale polygons based on the image size during window resizing """
        if not self._page:
            return

        self.resizePolygonsToPixmap()

    def resizePolygonsToPixmap(self):
        scaledPixmap = self._page._pixmap.scaled(self.rect().size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        new_pixmap_rect = QtCore.QRect(self.rect().topLeft(), scaledPixmap.size())

        # scale from the pixmap size when the polygon was created and the
        # pixmap from when it was originally created
        for page_line in self._page._page_lines:
            for i, point in enumerate(page_line._original_vertices):
                scale_x = new_pixmap_rect.size().width() / page_line._original_pixmap_w_h[0]
                scale_y = new_pixmap_rect.size().height() / page_line._original_pixmap_w_h[1]
                page_line._vertices[i] = (point[0] * scale_x, point[1] * scale_y)
            page_line.updatePolygon()

        self.update()

    def mousePressEvent(self, event):
        """ Collects points for the polygon and creates selection boxes """
        if not self._page:
            return

        point = QtCore.QPoint(event.x(), event.y())

        if self._page._pixmap_rect.contains(event.x(), event.y()):
            # make sure not already in polygons
            if self._polygon_layer and (self._start_of_line or self._page.pointSelectsItem(point) == False):
                # removes bug where user can select a polygon draw a new one
                # and then delete the previous selection in one click
                if (self._page._polygon_start and
                    self._page._polygon_start[0]-5 < point.x() < self._page._polygon_start[0]+5 and
                    self._page._polygon_start[1]-5 < point.y() < self._page._polygon_start[1]+5):
                    # close the polygon
                    self._page.selectPolygon()
                    self._page._selected_polygon = None
                    self._page._polygon_start = None

                else:
                    self._page._selected_polygon = None

                    if self._start_of_line:
                        self._lines.append((self._start_of_line, event.pos()))
                    else:
                        # first point in polygon
                        self._page._polygon_start = event.x(),event.y()
                    self._start_of_line = event.pos()
                    self._page._polygon_points.append((event.x(),event.y()))
                    self._page._polygon << event.pos()

            elif self._polygon_layer and self._page.pointInVertexHandle(point):
                self._page._dragging_vertex = True
                self._page.selectClickedVertexHandle(point)

            else:
                # select clicked polygon
                self._page.selectClickedPolygon(point)

                # highlight
                if self._ui.highlighter_on and self._page._selected_polygon:
                    self._page._highlighted_polygon = self._page._selected_polygon

                    # move cursor to corresponding line
                    self._ui.move_cursor(self._page._selected_polygon._block_number)

                    # highlight line
                    self._ui.highlight_line()

            self.update()

    def mouseMoveEvent(self, event):
        """ updates the painter and lets it draw the line from
            the last clicked point to end """
        if not self._page:
            return
        point = event.pos()
        if self._page and self._page._dragging_vertex == True:
            self._page._selected_polygon._vertices[self._page._selected_vertex_index] = (point.x(),point.y())
            self._page._selected_polygon.updatePolygon()
        else:
            self._end_of_line = event.pos()

        self.update()

    def mouseReleaseEvent(self, event):
        if not self._page:
            return

        if self._page._dragging_vertex:
            self._page._dragging_vertex = False
