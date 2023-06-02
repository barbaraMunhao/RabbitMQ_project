import pika
from mysql.connector import Error
from HandlerDB import HandlerDB

from ConnectionConfig import ConectionConfig
from SubsRouter import *
CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST



class SubscribeServer(object):
    exc = 'direct.subscribe'
    def __init__(self):
        self.db_connection = HandlerDB.connect()
        self.last_processed_message = None
        self.init()
        self.observe()

    #Make initial configuration.
    def init(self):
        print("Configuring...\n")
        self.exchange = self.create_subscribe_exchange()
        self.last_processed_message = 0

    def create_subscribe_exchange(self):

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        channel = connection.channel()
        channel.exchange_declare(exchange=SubscribeServer.exc, exchange_type='direct', durable=True)
        connection.close()
        return SubscribeServer.exc

    # Keep observing arrived messages at DB.
    def observe(self):
        if self.db_connection == -1:
            return -1

        while True:
            try:
                cnx = HandlerDB.connect()
                cursor = cnx.cursor()
                query = "SELECT * FROM `emergent_message` WHERE message_id > {0}".format(self.last_processed_message)
                cursor.execute(query)
                records = cursor.fetchall()
                cursor.close()
                cnx.close()
                if len(records) > 0:
                    self.last_processed_message = self.last_processed_message + len(records)
                    self.process_messages(records)
                else:
                    continue

            except Error as e:
                print(e.message)

    def process_messages(self, messages_tuple):

        for m in messages_tuple:
            SubsRouter(m)
        return

def main():

    try:
        server = SubscribeServer()
    except KeyboardInterrupt:
        print("Closing all.\n")
        exit(0)

if __name__ == "__main__":
    main()


