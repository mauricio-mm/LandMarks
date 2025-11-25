import sys
import cv2
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

def funcao_abrecam():
    global capture
    capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    dimensions = (640,480)
    timer.setInterval(50)
    timer.timeout.connect(get_frame)
    timer.start()

def get_frame():
    ok, frame = capture.read()
    image = QImage(frame,640,480, QImage.Format_RGB888).rgbSwapped()
    pixmap = QPixmap(image)
    # janela.AreaCamera.setPixmap(pixmap)

def funcao_abreimagem():
    nome_arquivo = QFileDialog.getOpenFileName(filter="Image (*.*)")[0]
    imagem_color = cv2.imread(nome_arquivo)
    cv2.imwrite('imagem_original.png', imagem_color)
    pixmap = QPixmap('imagem_original.png')
    # janela.AreaImagem.setPixmap(pixmap)
