"""
依赖：
ADB_full_screen_rich.ui
"""
from aip import AipOcr
import os
import yaml
import time
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QPlainTextEdit
from PySide2.QtCore import QObject, Signal
from threading import Thread


class MySignal(QObject):
    text_show = Signal(QPlainTextEdit, str)


my_signal = MySignal()


class UI:
    def __init__(self):
        self.app = QApplication([])
        self.window = QUiLoader().load('ADB_full_screen_rich.ui')
        self.window.connectADB.clicked.connect(self.connectADB)
        self.window.disconnectADB.clicked.connect(self.disconnectADB)
        self.window.shoot_now.clicked.connect(self.shoot_now)
        self.window.test_btn.clicked.connect(self.test_btn)
        my_signal.text_show.connect(self.update_text)

    def test_btn(self):
        """用于测试"""
        my_signal.text_show.emit(None, '一般看见这种图我都是直接点赞的')

    def __append_info(self, info):
        """ 像命令行内插入文本 """
        self.window.cmd_out.appendPlainText(info)
        self.window.cmd_out.ensureCursorVisible()

    def exec_cmd(self, cmd) -> None:
        """ 执行一个cmd命令，并将输出插入到文本框中 """
        r = os.popen(cmd)
        t = r.read()
        self.__append_info(t)

    def connectADB(self):
        """ Callback button of connectADB """
        self.exec_cmd('adb start-server')
        self.exec_cmd('adb devices')

    def disconnectADB(self):
        """ Callback button of disconnectADB """
        self.exec_cmd('adb kill-server')

    def update_text(self, obj, text):
        """ 用于多线程展示最终结果，开头加个当前时间 """
        # 获取需要换行的字符
        new_line_in = self.window.new_line.text()

        # 高亮关键字
        keyword = self.window.highlight.text()
        # 关键字长度
        key_lenth = len(keyword)
        # 这一步处理 html，找高亮
        indexx = text.find(keyword)
        if indexx != -1 and indexx != 0:
            print('检测到关键字：', indexx)
            html_before = f"<font size=4>{text[:indexx]}</font>"
            html_high = f"<font size=4 color=\"red\">{text[indexx:indexx + key_lenth]}</font>"
            html_end = f"<font size=4>{text[indexx + key_lenth:]}</font>"
            html = html_before + html_high + html_end
        else:
            print('纯文本')
            html = f"<font size=4>{text}</font>"
        # html是没有换行的文本
        # 换行
        # 先检测界面输入的长度
        if len(new_line_in) != 0:
            print('换行！')
            # 然后空格分隔
            new_lines = new_line_in.split(' ')
            # 添加换行
            for i in new_lines:
                print('换行文本：', i)
                # t 是最终文本
                html = html.replace(i, i + '<br>' + '\n')
            print(html)

        self.window.rich_out.setHtml(html)

    def __ocr(self):
        """ OCR本地图片，用 多线程调用此方法 """
        # OCR it
        t = recognize('test.png')
        # set the text
        my_signal.text_show.emit(self.window.text_out, t)

    def shoot_now(self):
        """ 截图 """
        # get screen shot
        self.exec_cmd('adb shell screencap /sdcard/test.png')
        self.exec_cmd('adb pull /sdcard/test.png ./')
        self.__append_info('开启多线程...')
        t = Thread(target=self.__ocr)
        t.setDaemon(True)
        t.start()

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


def get_time() -> str:
    """ 返回时间 """
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return f'[{now}]'


if __name__ == '__main__':
    ui = UI()
    ui.run()
