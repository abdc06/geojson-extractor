import sys
import os
import json
import geopandas as gpd
from simplify import simplify_geojson
from collections import OrderedDict
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QProgressDialog, QPushButton
from PyQt6.QtCore import QThread, Qt, pyqtSignal, QObject
from PyQt6 import uic
import qtmodern.styles
import qtmodern.windows
import time


def replaceName(text):
    if text.find("서울") >= 0:
        return "서울"
    elif text.find("부산") >= 0:
        return "부산"
    elif text.find("대구") >= 0:
        return "대구"
    elif text.find("인천") >= 0:
        return "인천"
    elif text.find("광주") >= 0:
        return "광주"
    elif text.find("대전") >= 0:
        return "대전"
    elif text.find("울산") >= 0:
        return "울산"
    elif text.find("세종") >= 0:
        return "세종"
    elif text.find("경기") >= 0:
        return "경기"
    elif text.find("강원") >= 0:
        return "강원"
    elif text.find("충청북") >= 0 or text.find("충북") >= 0:
        return "충북"
    elif text.find("충청남") >= 0 or text.find("충남") >= 0:
        return "충남"
    elif text.find("전라북") >= 0 or text.find("전북") >= 0:
        return "전북"
    elif text.find("전라남") >= 0 or text.find("전남") >= 0:
        return "전남"
    elif text.find("경상북") >= 0 or text.find("경북") >= 0:
        return "경북"
    elif text.find("경상남") >= 0 or text.find("경남") >= 0:
        return "경남"
    elif text.find("제주") >= 0:
        return "제주"
    else:
        return text


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


form = resource_path('app.ui')
form_class = uic.loadUiType(form)[0]


class App(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.SidoFilePathButton.clicked.connect(self.openSidoFile)
        self.SigFilePathButton.clicked.connect(self.openSigFile)
        self.EmdFilePathButton.clicked.connect(self.openEmdFile)
        self.ResultFilePathButton.clicked.connect(self.openResultFile)

        self.HelpButton.clicked.connect(self.help)
        self.StartButton.clicked.connect(self.action)
        self.CloseButton.clicked.connect(QApplication.instance().quit)

        # show the login window
        self.show()

    def action(self):
        if self.validation():
            self.setProgressBar()
            self.runner = ExecuteRunner(self)
            self.runner.signals.progress.connect(self.updateProgress)
            self.setButtonEnabled(False)
            self.runner.start()

    def openSidoFile(self):
        fname = QFileDialog.getOpenFileName(self, "", "", "shp(*.shp)")
        self.SidoFilePathEdit.setText(fname[0])

    def openSigFile(self):
        fname = QFileDialog.getOpenFileName(self, "", "", "shp(*.shp)")
        self.SigFilePathEdit.setText(fname[0])

    def openEmdFile(self):
        fname = QFileDialog.getOpenFileName(self, "", "", "shp(*.shp)")
        self.EmdFilePathEdit.setText(fname[0])

    def openResultFile(self):
        folder = QFileDialog.getExistingDirectory(self)
        self.ResultFilePathEdit.setText(folder)

    def updateProgress(self, n):
        self.progress.setValue(n)

    def showMessageBox(self, message):
        box = QMessageBox()
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("알림")
        box.setText(message)
        box.setStandardButtons(QMessageBox.Yes)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText('확인')
        box.exec_()

    def help(self):
        box = QMessageBox()
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("도움말")
        box.setText("Email: reinf92@stcreative.kr")
        box.setStandardButtons(QMessageBox.Yes)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText('확인')
        box.exec_()

    def setProgressBar(self):
        self.progress = QProgressDialog('작업중입니다.', '', 0, 100, self)
        self.progress.setWindowTitle("작업상태")

        progressCancelButton = QPushButton("Cancel")
        self.progress.setCancelButton(progressCancelButton)
        progressCancelButton.hide()

        self.progress.setWindowFlags(Qt.WindowType.Window |
                                     Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)
        self.progress.setValue(0)
        self.progress.show()

    def setButtonEnabled(self, enabled):
        self.SidoFilePathButton.setEnabled(enabled)
        self.SigFilePathButton.setEnabled(enabled)
        self.EmdFilePathButton.setEnabled(enabled)
        self.ResultFilePathButton.setEnabled(enabled)
        self.StartButton.setEnabled(enabled)
        self.CloseButton.setEnabled(enabled)

    def validation(self):
        sidoFilePathText = self.SidoFilePathEdit.text()
        sigFilePathText = self.SigFilePathEdit.text()
        emdFilePathText = self.EmdFilePathEdit.text()
        resultFilePathText = self.ResultFilePathEdit.text()

        if sidoFilePathText == "":
            self.showMessageBox("시도 쉐이프 파일은 필수입니다.")
            return False

        if sigFilePathText != "" and sidoFilePathText == "":
            self.showMessageBox("상위 행정구역 쉐이프 파일은 필수입니다.")
            return False

        if emdFilePathText != "" and (sigFilePathText == "" or sidoFilePathText == ""):
            self.showMessageBox("상위 행정구역 쉐이프 파일은 필수입니다.")
            return False

        if resultFilePathText == "":
            self.showMessageBox("결과물 저장 경로는 필수입니다.")
            return False

        return True


class ExecuteRunner(QThread):

    def __init__(self, widget):
        self.widget = widget
        self.signals = WorkerSignals()

        self.SidoFilePathText = self.widget.SidoFilePathEdit.text()
        self.SigFilePathText = self.widget.SigFilePathEdit.text()
        self.EmdFilePathText = self.widget.EmdFilePathEdit.text()
        self.ResultFilePathText = self.widget.ResultFilePathEdit.text()

        super().__init__()

    def removeTempFile(self, file):
        if os.path.isfile(file):
            os.remove(file)

    def run(self):
        print(">>>>> ==================== running.... ====================")

        per = 1
        if self.SidoFilePathText != "" and self.SigFilePathText != "" and self.EmdFilePathText != "":
            per = 5
        elif self.SidoFilePathText != "" and self.SigFilePathText != "" and self.EmdFilePathText == "":
            per = 2
        elif self.SidoFilePathText != "" and self.SigFilePathText == "" and self.EmdFilePathText == "":
            per = 1

        if self.SidoFilePathText != "":
            self.sidoWorker(per)
        if self.SigFilePathText != "":
            self.sigWorker(per)
        if self.EmdFilePathText != "":
            self.emdWorker(per)

        self.widget.setButtonEnabled(True)

        self.removeTempFile(self.ResultFilePathText + "/A1.geojson")
        self.removeTempFile(self.ResultFilePathText + "/A2.geojson")
        self.removeTempFile(self.ResultFilePathText + "/B1.geojson")
        self.removeTempFile(self.ResultFilePathText + "/B2.geojson")
        self.removeTempFile(self.ResultFilePathText + "/C1.geojson")
        self.removeTempFile(self.ResultFilePathText + "/C2.geojson")

        print(">>>>> ==================== complete.... ====================")

    def sidoWorker(self, per):
        df = gpd.read_file(self.SidoFilePathText, encoding="euc-kr")
        df2 = df.to_crs(epsg=4326)
        df2.rename(columns={
                   "CTPRVN_CD": "id", "CTP_ENG_NM": "name_eng", "CTP_KOR_NM": "name"}, inplace=True)
        df2["name"] = df2.apply(lambda x: replaceName(x["name"]), axis=1)
        self.signals.progress.emit(int(30/per))

        # speed

        df2.to_file(
            filename=self.ResultFilePathText + "/A1.geojson", driver="GeoJSON")
        self.signals.progress.emit(int(70/per))

        simplify_geojson(self.ResultFilePathText + "/A1.geojson",
                         self.ResultFilePathText + "/A2.geojson", 0.004)
        self.signals.progress.emit(int(90/per))

        # 스킵
        sidoFile = open(file=self.ResultFilePathText +
                        "/A2.geojson", mode="r", encoding="utf8")
        sidoGeoJsonData = json.load(sidoFile)
        sidoFeatures = sidoGeoJsonData["features"]

        fileData = OrderedDict()
        fileData["type"] = "FeatureCollection"
        fileData["features"] = sidoFeatures

        with open(self.ResultFilePathText + "/00.json", 'w', encoding="utf8") as makeFile:
            json.dump(fileData, makeFile, ensure_ascii=False, indent=4)
            self.signals.progress.emit(int(100/per))

    def sigWorker(self, per):
        t1 = time.time()
        df = gpd.read_file(self.SigFilePathText, encoding="euc-kr")
        df2 = df.to_crs(epsg=4326)
        df2.rename(columns={
                   "SIG_CD": "id", "SIG_ENG_NM": "name_eng", "SIG_KOR_NM": "name"}, inplace=True)
        df2["name"] = df2.apply(lambda x: replaceName(x["name"]), axis=1)
        self.signals.progress.emit(int(116.5/per))

        df2.to_file(
            filename=self.ResultFilePathText + "/B1.geojson", driver="GeoJSON")
        self.signals.progress.emit(int(152.5/per))

        simplify_geojson(self.ResultFilePathText + "/B1.geojson",
                         self.ResultFilePathText + "/B2.geojson", 0.0005)
        self.signals.progress.emit(int(192/per))

        sigFile = open(file=self.ResultFilePathText +
                       "/B2.geojson", mode="r", encoding="utf8")
        sigGeoJsonData = json.load(sigFile)
        sigFeatures = sigGeoJsonData["features"]

        sidoFile = open(file=self.ResultFilePathText +
                        "/A2.geojson", mode="r", encoding="utf8")
        sidoGeoJsonData = json.load(sidoFile)
        sidoFeatures = sidoGeoJsonData["features"]

        for feature in sidoFeatures:
            filterFeatures = list(filter(lambda n: n["properties"]["id"].find(
                feature["properties"]["id"]) == 0, sigFeatures))

            fileData = OrderedDict()
            fileData["type"] = "FeatureCollection"
            fileData["features"] = filterFeatures

            with open(self.ResultFilePathText + "/" + feature["properties"]["id"] + ".json", 'w', encoding="utf8") as makeFile:
                json.dump(fileData, makeFile, ensure_ascii=False, indent=4)
        self.signals.progress.emit(int(200/per))

    def emdWorker(self, per):
        df = gpd.read_file(self.EmdFilePathText, encoding="euc-kr")
        df2 = df.to_crs(epsg=4326)
        df2.rename(columns={
                   "EMD_CD": "id", "EMD_ENG_NM": "name_eng", "EMD_KOR_NM": "name"}, inplace=True)
        df2["name"] = df2.apply(lambda x: replaceName(x["name"]), axis=1)
        self.signals.progress.emit(int(410/per))

        df2.to_file(
            filename=self.ResultFilePathText + "/C1.geojson", driver="GeoJSON")
        self.signals.progress.emit(int(443.5/per))

        simplify_geojson(self.ResultFilePathText + "/C1.geojson",
                         self.ResultFilePathText + "/C2.geojson", 0.00015)
        self.signals.progress.emit(int(483.5/per))

        emdFile = open(file=self.ResultFilePathText +
                       "/C2.geojson", mode="r", encoding="utf8")
        emdGeoJsonData = json.load(emdFile)
        emdFeatures = emdGeoJsonData["features"]

        sigFile = open(file=self.ResultFilePathText +
                       "/B2.geojson", mode="r", encoding="utf8")
        sigGeoJsonData = json.load(sigFile)
        sigFeatures = sigGeoJsonData["features"]

        for feature in sigFeatures:
            filterFeatures = list(filter(lambda n: n["properties"]["id"].find(
                feature["properties"]["id"]) == 0, emdFeatures))

            fileData = OrderedDict()
            fileData["type"] = "FeatureCollection"
            fileData["features"] = filterFeatures

            with open(self.ResultFilePathText + "/" + feature["properties"]["id"] + ".json", 'w', encoding="utf8") as makeFile:
                json.dump(fileData, makeFile, ensure_ascii=False, indent=4)

        self.signals.progress.emit(int(500/per))


class WorkerSignals(QObject):
    progress = pyqtSignal(int)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    qtmodern.styles.dark(app)

    wd = App()
    sys.exit(app.exec())
