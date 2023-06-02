import re
import pika
from mysql.connector import errorcode
from Comands import Comands
from ProfileHandler import ProfileHandler
from User import User
from Group import Group
from ConnectionConfig import ConectionConfig
"""
Eh necessario que este server esteja rodando para que o cadastro e o login sejam feitos. Essas trocas
de mensagens estao sendo feitas via RPC e nao sao persistentes.
Para rodar basta : python Server.py
depois disso, com o servidor do rabbit tmbem funcionando, os outros modulos poderao ser utilizados.
"""
CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class Server(object):

    def __init__(self):

        self.direct_exchange()
        self.connect_rpc()
        self.consume_rpc()

    def connect_rpc(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        self.channel = connection.channel()
        self.channel.queue_declare(queue='rpc_queue')

    def consume_rpc(self):

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='rpc_queue', on_message_callback=self.on_request)

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

    """ Resolve a request switching the right method to process that. """
    def resolve(self, body):
        s = body.split(" ")
        comand = int(s[0])
        if comand == Comands.JOIN.value:

            try:
                name = re.split(r"\d\d\d\d\d\d\d\d\d\d\d\d ", body)[1]

                pwd = s[1]
                rga = s[2]

            except:
                return
            return self.create_profile(name, rga, pwd)

        elif comand == Comands.LOGIN.value:
            user = re.findall(r"\d\d\d\d\d\d\d\d\d\d\d\d", s[1])[0]

            pwd = re.split(r"\d\d\d\d\d\d\d\d\d\d\d\d", s[1])[1]

            return self.authentication(user, pwd)
        return 0

    #""""Uses the handler to create a profile"""

    def create_profile(self, name, rga, password):
        error, user_id = ProfileHandler.insert_user(name, rga, password)
        if error == 0:
            self.create_subscribe_queue(user_id)
            raw_keys = ProfileHandler.associated_keys(user_id)
            f_keys = []
            g_names = []
            for k in raw_keys:
                f_keys.append('.'+str(k[0]))
                g_names.append(str(k[1]))
            user = User(name, rga, user_id, f_keys, g_names)
            user.connect()
            user.bind()
            user.close_connection()
            return 0
        else:
            if error == errorcode. ER_DUP_ENTRY: #review
                print("Erro_server")
                return errorcode.ER_DUP_ENTRY
            else:
                return -1

    #"""Uses the handler to try login the user."""

    def authentication(self, user, password): ##user means rga, just numbers. TO DO

        user_id = ProfileHandler.exist(user, password)
        if user_id == -1:
            return -1
        else:
            return self.build_keys_msg(ProfileHandler.associated_keys(user_id), user_id)

    def build_keys_msg(self, keys, user_id):
        print(keys)
        payload = "{0} {1} ".format(Comands.USER_KEYS.value, user_id)
        for k in keys:
            payload = payload +"."+ str(k[0])
        payload = payload+" "
        for k in keys:
            payload = payload + "." + str(k[1])
        return payload

    def direct_exchange(self):
        exc = 'private'
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        channel = connection.channel()
        channel.exchange_declare(exchange=exc, exchange_type='direct', durable=True)
        connection.close()

    def create_subscribe_queue(self, id):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        channel = connection.channel()
        channel.queue_declare(queue='subscribe.{}'.format(id), durable=True)
        connection.close()


gid = Group.new_group('TRC', '1901')
trc = Group('TRC', gid, '1901')
trc.build_exchange()


gid2 = Group.new_group('TADS', '1902')

tads = Group('TADS', gid2, '1902')
tads.build_exchange()

gid4 = Group.new_group('CC', '1904')

cc = Group('CC', gid4, '1904')
cc.build_exchange()

gid5 = Group.new_group('EC', '1905')

ec = Group('EC', gid5, '1905')
ec.build_exchange()

gid6 = Group.new_group('ES', '1906')

es = Group('ES', gid6, '1906')
es.build_exchange()

gid7 = Group.new_group('SI', '1907')

si = Group('SI', gid7, '1907')
si.build_exchange()

server = Server()


