from aip import AipOcr
import os
import yaml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication


class UI:
    def __init__(self):
        self.app = QApplication([])
        self.window = QUiLoader().load('ADB_full_screen.ui')
        self.window.connectADB.clicked.connect(self.connectADB)
        self.window.disconnectADB.clicked.connect(self.disconnectADB)
        self.window.shoot_now.clicked.connect(self.shoot_now)

    def exec_cmd(self, cmd) -> None:
        """ 执行一个cmd命令，并将输出插入到文本框中 """
        r = os.popen(cmd)
        t = r.read()
        self.window.cmd_out.appendPlainText(t)
        self.window.cmd_out.ensureCursorVisible()

    def connectADB(self):
        """ Callback button of connectADB """
        self.exec_cmd('adb start-server')
        self.exec_cmd('adb devices')

    def disconnectADB(self):
        """ Callback button of disconnectADB """
        self.exec_cmd('adb kill-server')

    def shoot_now(self):
        """ Callback button of shoot_now """
        # get screen shot
        self.exec_cmd('adb shell screencap /sdcard/test.png')
        self.exec_cmd('adb pull /sdcard/test.png ./')
        # OCR it
        t = recognize('test.png')
        # set the text
        self.window.text_out.setPlainText(t)

    def run(self):
        self.window.show()
        self.app.exec_()


def recognize(image) -> str:
    """ OCR识别给定的图片文字内容 """
    with open('settings.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    with open(image, 'rb') as f:
        img = f.read()

    APP_ID = config['APP_ID']
    API_KEY = config['API_KEY']
    SECRET_KEY = config['SECRET_KEY']

    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    res = client.basicGeneral(img)
    words = res['words_result']
    res = ''
    for line in words:
        res += line['words']
    return res


if __name__ == '__main__':
    ui = UI()
    ui.run()
