from ConnectionConfig import ConectionConfig
import pika
import uuid

"""Just a RPC client that could be used to connect with the Server."""

CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class RpcClient(object):

    def __init__(self, rk='rpc_queue'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))

        self.response = None
        self.corr_id = None
        self.channel = self.connection.channel()
        self.rk = rk
        result = self.channel.queue_declare('', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, payload):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.rk,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(payload))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def close_connection(self):
        try:
            self.connection.close(0)
        except:
            return 0


