from threading import Thread
import webbrowser

import keyboard
import pyautogui as ag
import pyperclip as clip
import yaml
from aip import AipOcr
from PIL import Image, ImageGrab
from PySide2.QtCore import QObject, Signal
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QLabel


class MySignal(QObject):
    coords_info = Signal(QLabel, str)
    main_info = Signal(QLabel, str)


my_signal = MySignal()


class UI:
    def __init__(self):
        # GUI
        self.app = QApplication([])
        self.window = QUiLoader().load('ui.ui')
        self.window.btn_ocr.clicked.connect(self.btn_ocr)
        self.window.btn_search.clicked.connect(self.btn_search)
        self.window.btn_set_pos.clicked.connect(self.btn_set_pos)
        # Signal
        my_signal.coords_info.connect(self.update_coords)
        my_signal.main_info.connect(self.update_main)
        # 截图的左上、右下坐标
        self.lt = (0, 0)
        self.rb = (0, 0)
        # 截图名称
        self.shot_name = 'screenshot.png'
        # 识别内容
        self.recognized_text = ''

    def update_main(self, obj, msg):
        """ 多线程修改主要提示的回调 """
        self.window.status_text.setText(msg)

    def update_coords(self, obj, msg):
        """ 多线程修改坐标位置的回调 """
        self.window.coords.setText(msg)

    def sample_position(self) -> tuple:
        """ 采集鼠标位置，自动采集两个坐标，用多线程开启这个函数 """
        # LT
        my_signal.main_info.emit(
            self.window.status_text, '移动鼠标到左上角并按下 Shift 键')
        keyboard.wait('shift')
        left_top_x, left_top_y = ag.position()
        # RB
        my_signal.main_info.emit(
            self.window.status_text, '移动鼠标到右下角并按下 Shift 键')
        keyboard.wait('shift')
        right_bottom_x, right_bottom_y = ag.position()
        # Update
        my_signal.coords_info.emit(
            self.window.coords, f'({left_top_x}, {left_top_y}, {right_bottom_x}, {right_bottom_y})')
        self.lt = (left_top_x , left_top_y)
        self.rb = (right_bottom_x, right_bottom_y)
        # finish
        my_signal.main_info.emit(
            self.window.status_text, '采集完成')

    def get_screen_shot(self) -> None:
        """ 截取指定区域的屏幕图像 """
        if self.lt == (0, 0) or self.rb == (0, 0):
            print('未采集坐标！')
            return
        pos = (self.lt[0], self.lt[1], self.rb[0], self.rb[1])
        image = ImageGrab.grab((pos))
        image.save(self.shot_name)
        print('截图已保存')

    def btn_set_pos(self):
        """ Callback button of btn_set_pos """
        t = Thread(target=self.sample_position)
        t.setDaemon(True)
        t.start()
        print('多线程启动')

    def btn_ocr(self):
        """ Callback button of 截图+识别 """
        image = ImageGrab.grab((self.lt[0], self.lt[1], self.rb[0], self.rb[1]))
        image.save(self.shot_name)
        text = recognize(self.shot_name)
        print(text)
        self.window.plainTextEdit.setPlainText(text)
        self.recognized_text = text
        clip.copy(text)

    def btn_search(self):
        """ Callback button of 截图+搜索 """
        # 直接调用一次识别方法，然后打开浏览器就好了
        self.btn_ocr()
        # 检测长度防止无法搜索
        if len(self.recognized_text) > 40:
            text = self.recognized_text[:40]
        else:
            text = self.recognized_text
        url = f'https://www.baidu.com/s?ie=utf-8&wd={text}'
        print(url)
        webbrowser.open(url)
        
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
