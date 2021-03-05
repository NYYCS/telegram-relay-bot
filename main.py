from multiprocessing import Process, Pipe

from bot import Tianshi, Zhuren

import yaml

TIANSHI_TOKEN = "1622983332:AAHgC-aV9cJ8TgyGRtf9gFA_481HwxriHZ4"
ZHUREN_TOKEN = "1564529243:AAGHN2j9ZoadbdbX_yzNbqfQmeFFETHyEq4"


if __name__ == "__main__":
    p1, p2 = Pipe()
    p3, p4 = Pipe()
    t = Process(target=Tianshi.run, args=(TIANSHI_TOKEN, p1, p3, ))
    z = Process(target=Zhuren.run, args=(ZHUREN_TOKEN, p2, p4, ))
    t.start()
    z.start()