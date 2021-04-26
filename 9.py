import os
import sys

import requests
from PyQt5 import QtCore, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow

import math

SCREEN_SIZE = [900, 700]


class MapParams():
    def __init__(self):
        self.latitude, self.longitude, self.st = 55.703118, 37.530887, 0.01
        self.zoom = 16
        self.layer = "map"
        self.pt = ""

    def update(self, event):
        if event.key() == QtCore.Qt.Key_PageUp and self.zoom > 2:
            self.zoom -= 1
        elif event.key() == QtCore.Qt.Key_PageDown and self.zoom < 19:
            self.zoom += 1
        elif event.key() == QtCore.Qt.Key_Left:
            self.longitude -= self.st * math.pow(2, 15 - self.zoom)
            if self.longitude < -180:
                self.longitude += 360
        elif event.key() == QtCore.Qt.Key_Right:
            self.longitude += self.st * math.pow(2, 15 - self.zoom)
            if self.longitude > 180:
                self.longitude -= 360
        elif event.key() == QtCore.Qt.Key_Up and -85 <= self.latitude + self.st * math.pow(2, 15 - self.zoom) <= 85:
            self.latitude += self.st * math.pow(2, 15 - self.zoom)
        elif event.key() == QtCore.Qt.Key_Down and -85 <= self.latitude - self.st * math.pow(2, 15 - self.zoom) <= 85:
            self.latitude -= self.st * math.pow(2, 15 - self.zoom)


class WorkMap(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('9.ui', self)
        self.initUI()
        self.showIm()

    def showIm(self):
        params = {
            "ll": ",".join([str(self.mp.longitude), str(self.mp.latitude)]),
            "z": str(self.mp.zoom),
            "l": str(self.mp.layer)
        }
        if self.mp.pt != "":
            params["pt"] = self.mp.pt
        api_server = "http://static-maps.yandex.ru/1.x/"
        response = requests.get(api_server, params=params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(response.url)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

        self.pixmap = QPixmap(self.map_file)
        self.image.setPixmap(self.pixmap)

    def initUI(self):
        self.setGeometry(100, 100, *SCREEN_SIZE)
        self.setWindowTitle('Отображение карты')
        self.search_btn.clicked.connect(self.search)
        self.hide_search_btn.clicked.connect(self.hide_search)
        self.search_edit.setFocusPolicy(Qt.ClickFocus)
        self.mp = MapParams()
        self.map_layer.addItem("схема")
        self.map_layer.addItem("спутник")
        self.map_layer.addItem("гибрид")
        self.map_layer.currentTextChanged.connect(self.change)

    def hide_search(self):
        self.mp.pt = ""
        self.address.setText("")
        self.search_edit.clear()
        self.showIm()

    def search(self):
        if self.search_edit.text() == "":
            return
        geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode=" \
                           f"{self.search_edit.text()}&format=json"
        response = requests.get(geocoder_request)
        if response:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_coodrinates = toponym["Point"]["pos"].split()
            toponym_as = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
            self.address.setText(toponym_as)
            self.mp.latitude = float(toponym_coodrinates[1])
            self.mp.longitude = float(toponym_coodrinates[0])
            self.mp.pt = ",".join([str(self.mp.longitude), str(self.mp.latitude), "pm2rdm"])
        else:
            print("Ошибка выполнения запроса:")
            print(geocoder_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
        self.showIm()

    def change(self, layer):
        if layer == "схема":
            self.mp.layer = "map"
        elif layer == "спутник":
            self.mp.layer = "sat"
        elif layer == "гибрид":
            self.mp.layer = "sat,skl"
        self.showIm()

    def closeEvent(self, event):
        os.remove(self.map_file)

    def keyPressEvent(self, event):
        self.mp.update(event)
        event.accept()
        self.showIm()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WorkMap()
    ex.show()
    sys.exit(app.exec())