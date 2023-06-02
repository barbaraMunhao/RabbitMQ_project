import threading
import pika
from HistoricHandler import HistoricHandler
from RPCClient import RpcClient
from Comands import Comands
from ConnectionConfig import ConectionConfig

CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class HistoricServer(threading.Thread):

    def __init__(self, id):
        threading.Thread.__init__(self)
        self.name = 't{0}'.format(id)
        self.queue_name = 'historic'

    def run(self):
        print("Running thread {0}".format(self.name))

        self.connect_rpc()
        while True:
            self.consume_rpc()

    def connect_rpc(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def consume_rpc(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.on_request)

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

    def resolve(self, body):

        sbody = body.split()

        if int(sbody[0]) == Comands.ACK_MSG.value:
            return self.confirm_message(sbody[1], sbody[2])
        else:
            if int(sbody[0]) == Comands.HIST.value:
                return self.get_historic(sbody[1])

            shift = len(sbody[0])+len(sbody[1])+2
            limit = len(body)
            msg = body[shift:limit]
            id_msg = HistoricHandler.insert_msg(sbody[0], sbody[1], msg)
            return str(id_msg)

    def confirm_message(self, user_id, msg_id):
         return HistoricHandler.confirm_msg(msg_id, user_id)

    def get_historic(self, user_id):
        s_msgs = HistoricHandler.sent_messages(user_id)
        rec_msgs = HistoricHandler.received_messages(user_id)
        payload = ""
        for m in rec_msgs:
            date = str(m[2])
            date = date[:-3]
            payload = payload + date + ' ' + m[1] + '.' + m[0] + '\n'
        payload = payload + '|'
        for m in s_msgs:
            date = str(m[2])
            date = date[:-3]
            payload = payload + date + ' ' + m[1] + '.' + m[0] + '\n'
        return payload


class HistoricAck(threading.Thread):

    def __init__(self, args):
        threading.Thread.__init__(self, target=self.confirm_msg, args=args)
        self.start()

    def confirm_msg(self, user_id, msg_id):
        rpc = RpcClient('historic')
        payload = '{0} {1} {2}'.format(Comands.ACK_MSG.value, user_id, msg_id)
        e = rpc.call(payload)
        if int(e) == -1:
            self.confirm_msg(user_id, msg_id)
        rpc.close_connection()





