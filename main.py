from multiprocessing import Process, Pipe

from bot import Angel, Host

import yaml

ANGEL_TOKEN = "1622983332:AAHgC-aV9cJ8TgyGRtf9gFA_481HwxriHZ4"
HOST_TOKEN = "1564529243:AAGHN2j9ZoadbdbX_yzNbqfQmeFFETHyEq4"

def load(filename):
    with open(filename, 'r') as f:
        return yaml.safe_load(f)

with open('what.txt', 'w') as f:
    f.write("STARTING")

ANGELS = load("angels.yaml")
HOSTS = load("hosts.yaml")

if __name__ == "__main__":
    angel_pipe, host_pipe = Pipe()
    _angel = Process(target=Angel.run, args=( ANGEL_TOKEN, angel_pipe, HOSTS, ))
    _host = Process(target=Host.run, args=(HOST_TOKEN, host_pipe, ANGELS, ))
    _angel.start()
    _host.start()