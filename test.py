import os


def ocr(file) -> str:
    r = os.popen('Windows.Media.Ocr.Cli.exe "%s"' % file)
    return r.read()


if __name__ == '__main__':
    print(ocr('test.png'))
