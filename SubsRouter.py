
import threading
import pika
from HandlerDB import HandlerDB
from mysql.connector import Error
from ConnectionConfig import ConectionConfig

CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class SubsRouter(object):
    exc = 'direct.subscribe'

    def __init__(self, tuple):
        self.db_connection = HandlerDB.connect()
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        self.channel = self.connection.channel()
        self.p_list = list()
        self.ug_list = list()
        self.p_finished = False
        self.ug_finished = False
        self.start(tuple)
        self.connection.close()


    #Threads creation and start
    def start(self, tuple):
        self.p_handler =  PatternSubscribeHandler(self.db_connection, tuple, self.p_list, self.p_finished)
        self.ug_handler = GroupUserSubscribeHandler(self.db_connection, tuple, self.ug_list, self.ug_finished)
        self.p_handler.start()
        self.ug_handler.start()
        self.route(tuple)

    def route(self, tuple):

        while self.p_handler.flag == False and self.ug_handler == False:
            continue
        if self.p_handler.flag:
            self.send(0, tuple)
            while not self.ug_handler.flag:
                continue
            self.send(1, tuple)

        else: # Group/User finished
            self.send(1, tuple)
            while not self.p_handler.flag:
                continue
            self.send(0, tuple)

    def send(self, code, tuple):
        msg = str(tuple[1])

        if code == 0: #Pattern subscribe
            for p in self.p_list:
                self.channel.basic_publish(
                    exchange=SubsRouter.exc, routing_key=p, body=msg,
                    properties=pika.BasicProperties(delivery_mode=2))
        else: #GROUP/USER subscribe

            for p in self.ug_list:
                self.channel.basic_publish(
                    exchange=SubsRouter.exc, routing_key=p, body=msg,
                    properties=pika.BasicProperties(delivery_mode=2))










class PatternSubscribeHandler(threading.Thread):

    def __init__(self, db_cnx, msg, list, flag):
        threading.Thread.__init__(self)
        self.list = list
        self.flag = flag
        self.cnx = db_cnx
        self.msg = msg

    def run(self):
        patterns = self.get_patterns()
        if patterns == 0:
            print("No subs..\n")
        if patterns == -1:
            print("ERROR\n")
        else:
            payload = str(self.msg[1])
            d = payload.find('::')
            if d != -1:
                payload = payload[d+2:]
            for p in patterns:
                p = str(p[0])
                f = payload.find(str(p))
                if f == -1:
                    print("not appending {}\n".format(str(p)))
                    continue
                print("appending {}\n".format(str(p)))
                self.list.append(str(p))
            self.flag = True

    def get_patterns(self):
        if self.cnx == -1:
            return -1
        try:
            cursor = self.cnx.cursor(buffered=True)
            query = "SELECT `pattern` FROM subscribe"
            cursor.execute(query)
            patterns = cursor.fetchall()
            if len(patterns) == 0:
                return 0
            return patterns
        except Error as e:
            print(e.message)
            return -1


class GroupUserSubscribeHandler(threading.Thread):

    def __init__(self, db_cnx, msg, list, flag):
        threading.Thread.__init__(self)
        self.list = list
        self.flag = flag
        self.cnx = db_cnx
        self.msg = msg

    def run(self):
        user_key = 'user.{}'.format(str(self.msg[2]))
        self.list.append(user_key)
        if self.msg[3] == 1:
            group_key = 'group.{}'.format(str(self.msg[4]))
            self.list.append(group_key)
        self.flag = True