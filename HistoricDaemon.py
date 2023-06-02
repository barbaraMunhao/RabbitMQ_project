"""keep waiting requests """
from HistoricServer import HistoricServer


class HistoricDaemon(object):

    def __init__(self, thread_pool=5):
        print("Starting Historic Server\n")

        self.pool = []

        for i in range(thread_pool):
            t = HistoricServer(i)
            self.pool.append(t)

    def start(self): ## Listening
        for t in self.pool:
            t.start()



def main():
    try:
        hist_daemon = HistoricDaemon()
        hist_daemon.start()
    except KeyboardInterrupt:
        print("Closing all!\n")
        exit(0)

if __name__ == "__main__":
    main()

