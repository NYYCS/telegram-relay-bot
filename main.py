import multiprocessing
import gamebot

SENDER_TOKEN      =   ""
RECIPIENT_TOKEN   =   ""

if __name__ == "__main__":
    sconn, rconn = multiprocessing.Pipe()
    multiprocessing.Process(target=gamebot.Sender.run, args=(SENDER_TOKEN, sconn)).start()
    multiprocessing.Process(target=gamebot.Recipient.run, args=(RECIPIENT_TOKEN, rconn)).start()