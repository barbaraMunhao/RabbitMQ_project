import pika
from mysql.connector import Error
from HandlerDB import HandlerDB
from Group import Group
from ProfileHandler import ProfileHandler
from SubscribeServer import SubscribeServer
from ConnectionConfig import ConectionConfig

CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class SubscribingProvider(object):

    def __init__(self):
        self.connect_rpc()
        self.consume_rpc()

    def connect_rpc(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='rpc_queue_subscribe')

    def consume_rpc(self):

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='rpc_queue_subscribe', on_message_callback=self.on_request)

        print("Running-  Awaiting RPC requests")
        self.channel.start_consuming()

    def on_request(self, ch, method, props, body):

        response = self.resolve(body)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def resolve(self, payload):
        splitted = payload.split()
        subs_type = splitted[0]
        user_id = splitted[1]
        target = splitted[2:]

        return self.save(subs_type, user_id, target)

    def prepare_conection(self, user_id, target):
        key = str(target)
        print("Preparing queue.\n")
        queue = "subscribe.{}".format(user_id)
        n_channel = self.connection.channel()
        try:
            n_channel.queue_declare(queue=queue, durable=True)
        except Error as e:
            print(e.message)
        n_channel.queue_bind(exchange=SubscribeServer.exc, queue=queue, routing_key=key)

    def save(self, type, user, pattern):

        if type == '2':#USER
            return self.subscribe_user(user, pattern[0])
        if(len(pattern)>1):
            f_pattern = ''
            for p in pattern:
                f_pattern = f_pattern + ' ' + p

        else:
            f_pattern = pattern[0]
        if type == '1':#GROUP
            return self.subscribe_group(user, f_pattern)

        #TYPE=0: PATTERN
        cnx = HandlerDB.connect()
        target = f_pattern
        id = self.pattern_exist(f_pattern, cnx)
        if id == -10: #Error
            return -1
        else:
            cursor = cnx.cursor(buffered=True)
            if id == -1: #DO not Exist
                try:

                    query = "INSERT INTO subscribe (pattern) VALUES('{0}')".format(f_pattern)
                    cursor.execute(query)
                    cnx.commit()
                    id = cursor.lastrowid
                except Error as e:
                    print(e.message)
                    return_value = -1
            try:
                query = "INSERT INTO subs_user (subs_pattern_id, subscriber) VALUES ({0},{1})".format(id, user)
                cursor.execute(query)
                cnx.commit()
                return_value = 0
            except Error as e:
                print(e.message)
                return_value = -1
        if return_value == 0:
            self.prepare_conection(user, target)
        return return_value

    def subscribe_group(self, user, group_name):

        e, id_group = Group.id_by_name(group_name)
        e, key = Group.group_key(group_name)
        if e != 0:
            return e
        cnx = HandlerDB.connect()
        if cnx == -1:
            return -1
        try:
            cursor = cnx.cursor()
            query = "INSERT INTO `subs_ug`(id_user, id_target, type)  VALUES({0},{1},{2})".format(user, id_group,0)
            cursor.execute(query)
            cnx.commit()
            target = "group.{}".format(key)
            self.prepare_conection(user, target)
        except Error as er:
            print(er.message)
            return -1

    def subscribe_user(self, user, rga):

        id_user = ProfileHandler.user_id(rga)

        if id_user < 0:
            return id_user

        cnx = HandlerDB.connect()
        if cnx == -1:
            return -1
        try:
            cursor = cnx.cursor()
            query = "INSERT INTO `subs_ug`(id_user, id_target, type)  VALUES({0},{1},{2})".format(user, id_user, 1)
            cursor.execute(query)
            cnx.commit()
            target = "user.{}".format(id_user)
            self.prepare_conection(user, target)
        except Error as er:
            print(er.message)
            return -1

    def pattern_exist(self, pattern, cnx):

        try:
            cursor = cnx.cursor(buffered=True)
            query = "SELECT id_sign FROM `subscribe` WHERE pattern='{0}'".format(pattern)
            cursor.execute(query)
            records = cursor.fetchall()
            if len(records) < 1:
                return -1
            else:
                r = records.__getitem__(0)[0]
                return r
        except Error as e:
            print(e.message)
            return -10


def main():

    try:
        provider = SubscribingProvider()
    except KeyboardInterrupt:
        print("Closing all.\n")
        exit(0)

if __name__ == "__main__":
    main()