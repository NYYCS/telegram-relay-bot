import multiprocessing
import gamebot

SENDER_TOKEN      =   "1622983332:AAHgC-aV9cJ8TgyGRtf9gFA_481HwxriHZ4"
RECIPIENT_TOKEN   =   "1564529243:AAGHN2j9ZoadbdbX_yzNbqfQmeFFETHyEq4"

if __name__ == "__main__":
    sconn, rconn = multiprocessing.Pipe()
    multiprocessing.Process(target=gamebot.Sender.run, args=(SENDER_TOKEN, sconn)).start()
    multiprocessing.Process(target=gamebot.Recipient.run, args=(RECIPIENT_TOKEN, rconn)).start()