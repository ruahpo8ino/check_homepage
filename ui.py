import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtTest
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
import asyncio
import aiohttp
import datetime


form_class = uic.loadUiType("mainwindow.ui")[0] # 해당 UI로 formclas 생성

async def get_status_from_url(home_info, window, i):
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(home_info[0], timeout=2) as res:
                try:
                    status = res.status
                    window.home_list.iloc[i, 2] = str(status)

                except Exception as ex:
                    whindow.home_list.iloc[i, 2] = 'Connect X'

    except Exception as exc:
        window.home_list.iloc[i, 2] = 'Timeout'


def make_item(new):
    item = QTableWidgetItem(new)
    item.setTextAlignment(Qt.AlignCenter)
    return item

def make_color_item(new, r, g, b):
    item = QTableWidgetItem(new)
    item.setTextAlignment(Qt.AlignCenter)
    item.setForeground(QBrush(QColor(r,g,b)))
    return item



class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cnt = 0
        self.home_list = pd.read_csv('home_list.csv', index_col='name', encoding='UTF8',
                                dtype={'url': str,
                                       'latest': str,
                                       'result': str,
                                       'af': bool, }
                                )
        self.stop.setEnabled(False)
        self.sitetable.setColumnWidth(0, 100)
        self.sitetable.setColumnWidth(1, 400)
        self.sitetable.setColumnWidth(2, 150)
        self.sitetable.setColumnWidth(3, 100)
        self.sitetable.cellClicked.connect(self.connect_info)
        self.home_apply.clicked.connect(self.apply)
        self.home_delete.clicked.connect(self.delete)
        self.start.clicked.connect(self.check_start)
        self.stop.clicked.connect(self.check_stop)
        self.make_list()


    def make_list(self):
        if len(self.home_list) != 0:
            for i in range(0, len(self.home_list)):
                self.sitetable.setItem(self.cnt, 0, make_item(self.home_list.index[i]))
                for j in range(0, 3):
                    self.sitetable.setItem(self.cnt, j+1, make_item(str(self.home_list.iloc[i, j])))
                if self.home_list.iloc[i, 2] == '200':
                    self.sitetable.setItem(self.cnt, 4, make_color_item('●', 0, 255, 0))
                else:
                    self.sitetable.setItem(self.cnt, 4, make_color_item('▲', 255, 0, 0))

                self.cnt += 1

    def new_line(self):
        self.home_name.setText("")
        self.home_url.setText("")
        self.check_af.setChecked(False)

    def new_list(self):
        self.sitetable.clearContents()
        self.cnt = 0

    def connect_info(self):
        try:
            self.home_name.setText(self.home_list.index[self.sitetable.currentRow()])
            self.home_url.setText(self.home_list.iloc[self.sitetable.currentRow()][0])
            self.check_af.setChecked(self.home_list.iloc[self.sitetable.currentRow()][3])

        except:
            self.new_line()

    def showMessageBox(self, text):
        self.msgbox = QMessageBox()
        self.msgbox.setIcon(QMessageBox.Information)
        self.msgbox.setText(text)
        self.msgbox.setWindowTitle("Error")
        self.msgbox.setStandardButtons(QMessageBox.Ok)
        self.msgbox.exec()
        self.new_line()

    def apply(self):
        if (self.home_name.text() in self.home_list.index) or (self.home_list['url']==self.home_url.text()).any():
            self.showMessageBox('이미 등록된 홈페이지입니다.')
        elif self.home_url.text().startswith('http') == False:
            self.showMessageBox('유효하지 않는 주소입니다.\nhttp://, https://를 확인하세요.')
        else:
            self.home_list.loc[self.home_name.text()] = [self.home_url.text(), '-', '-', self.check_af.isChecked()]
            self.new_list()
            self.make_list()
            self.new_line()
            self.cnt += 1

    def delete(self):
        try:
            self.home_list = self.home_list.drop(self.home_name.text())
            self.sitetable.removeRow(self.sitetable.currentRow())
            self.new_line()
            self.cnt -= 1
        except:
            pass

    def check_start(self):
        if len(self.home_list) == 0:
            self.showMessageBox('홈페이지를 등록하여 주십시오.')
        else:
            self.start.setEnabled(False)
            self.spin_cycle.setEnabled(False)
            self.stop.setEnabled(True)
            self.home_info.setEnabled(False)
            self.checking = True
            self.cycle = self.spin_cycle.value()*60000
            while self.checking == True:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                        asyncio.gather(*(get_status_from_url(self.home_list.iloc[i], self, i) for i in range(len(self.home_list))))
                )
                now = datetime.datetime.now().strftime('%Y-%m-%d/%H:%M')
                self.home_list['latest'] = now
                self.new_list()
                self.make_list()
                QtTest.QTest.qWait(self.cycle)


    def check_stop(self):
        self.stop.setEnabled(False)
        self.start.setEnabled(True)
        self.spin_cycle.setEnabled(True)
        self.checking = False
        self.home_info.setEnabled(True)

    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                     "종료",
                                     "종료하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            self.checking = False
            self.home_list.to_csv('home_list.csv', na_rep='-')
            event.accept()
        else:
            event.ignore()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec()