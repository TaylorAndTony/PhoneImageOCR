"""
依赖：
ADB_full_screen_rich.ui
"""
import os
import cv2 as cv
import time
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QPlainTextEdit
from PySide2.QtCore import QObject, Signal
from threading import Thread


class MySignal(QObject):
    text_show = Signal(QPlainTextEdit, str)
    update_lines = Signal()


my_signal = MySignal()


class UI:
    def __init__(self):
        # scale ratio, if the image needed to be resized
        self.ratio = 1
        # lines, store the up and bottom lines
        self.lines = []
        # gui
        self.app = QApplication([])
        self.window = QUiLoader().load('ADB_full_screen_rich.ui')
        self.window.connectADB.clicked.connect(self.connectADB)
        self.window.disconnectADB.clicked.connect(self.disconnectADB)
        self.window.shoot_now.clicked.connect(self.shoot_now)
        self.window.test_btn.clicked.connect(self.test_btn)
        self.window.setCrop.clicked.connect(self.setCrop)
        self.window.resetCrop.clicked.connect(self.resetCrop)
        # signals
        my_signal.update_lines.connect(self.update_lines)
        my_signal.text_show.connect(self.update_text)

    def update_lines(self):
        """ signal callback, to update the coord text on the gui """
        self.window.cropArea.setText(str(self.lines))

    def resetCrop(self):
        self.lines = []
        my_signal.update_lines.emit()

    def setCrop(self):
        """ Callback button of setCoord """

        def __onMouse(event, x, y, flags, param) -> None:
            """callback function to handle mouse"""
            if event == cv.EVENT_LBUTTONDOWN:
                # this is a scaled image
                cv.imshow('imageShow', scaled)
                self.lines.append(int(y / self.ratio))
                if len(self.lines) > 2:
                    self.lines = self.lines[-2:]
                print(self.lines)
                my_signal.update_lines.emit()

        # read the first image in the folder
        first = cv.imread('test.png', 0)

        # calc whether the image is needed to resize
        width, height = first.shape[1], first.shape[0]
        if width > 1200:
            # scale the image
            targetWidth = 900
            self.ratio = targetWidth / width
            targetHeight = int(height * self.ratio)
            scaled = cv.resize(first, (targetWidth, targetHeight))

        elif height > 800:
            targetHeight = 700
            self.ratio = targetHeight / height
            targetWidth = int(width * self.ratio)
            scaled = cv.resize(first, (targetWidth, targetHeight))
        else:
            scaled = first

        cv.namedWindow('imageShow')
        cv.imshow('imageShow', scaled)
        cv.setMouseCallback('imageShow', __onMouse)


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
                html = html.replace(i, '<br>' + i + '<br>' + '\n')
            print(html)

        self.window.rich_out.setHtml(html)

    def __ocr(self, name):
        """ OCR本地图片，用 多线程调用此方法 """
        # OCR it
        r = os.popen(f'Windows.Media.Ocr.Cli.exe "{name}"')
        t = r.read()
        # set the text
        my_signal.text_show.emit(None, t)

    def shoot_now(self):
        """ 截图 """
        # get screen shot
        self.exec_cmd('adb shell screencap /sdcard/test.png')
        self.exec_cmd('adb pull /sdcard/test.png ./')
        # 每次接图都需要检测有没有裁剪坐标
        if len(self.lines) == 2:
            img = cv.imread('test.png')
            up = self.lines[0]
            down = self.lines[1]
            img = img[up:down, :]
            cv.imwrite('crop.png', img)
            name = 'crop.png'
            print('猜见了才剪了裁剪了图片')
        else:
            name = 'test.png'
        self.__append_info(f'开启多线程...文件目标：{name}')
        t = Thread(target=self.__ocr, args=(name,))
        t.setDaemon(True)
        t.start()

    def run(self):
        self.window.show()
        self.app.exec_()


def get_time() -> str:
    """ 返回时间 """
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return f'[{now}]'


if __name__ == '__main__':
    ui = UI()
    ui.run()
