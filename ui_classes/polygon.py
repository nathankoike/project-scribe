import copy
from PyQt5 import QtCore, QtGui


class Polygon():
    def __init__(self, polygon, points, og_pixmap_w, og_pixmap_h, og_pts=None):
        self._original_pixmap_w_h = (og_pixmap_w, og_pixmap_h)
        self._polygon = polygon
        self._image_name = None
        self._vertices = points

        if og_pts != None:
            self._original_vertices = copy.deepcopy(og_pts)
        else:
            self._original_vertices = copy.deepcopy(points)

        self._vertex_handles = None
        self._block_number = None
        self._transcription = ""
        self._is_transcribed = False
        self._ready_for_training = False

    def set_transcription(self, transcription):
        self._transcription = transcription

    def updatePolygon(self):
        self._polygon = QtGui.QPolygon()
        for vertex in self._vertices:
            point = QtCore.QPoint(vertex[0],vertex[1])
            self._polygon << point

    def set_block_number(self, number):
        """ Sets the index of the polygon/text """
        self._block_number = number
