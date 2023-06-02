import pika
from RPCClient import RpcClient
from HistoricServer import HistoricAck
from Comands import Comands
from HistoricHandler import HistoricHandler
from Group import Group
from ProfileHandler import ProfileHandler
from ConnectionConfig import ConectionConfig

CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST

class User(object):

    def __init__(self, name, rga, user_id, keys=None, group_name=None):
        self.BROKER = HOST
        self.DURABLE = True
        self.name = name
        self.rga = rga
        self.id = user_id
        self.my_groups = dict()
        self.keys = keys
        self.group_name = group_name
        self.subscribe_queue = "subscribe.{0}".format(self.id)
        self.subscribe_historic = list()
        self.hist_connector = None

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        self.channel = self.connection.channel()

    def close_connection(self):
        try:
            self.connection.close(0)
        except:
            return 0

    def bind(self, group_key=None):
        if group_key is None:
            group_key = self.keys
        # queue created for each created user - so a private/direct message can be send.
        self.declare_queue(self.rga)
        self.channel.queue_bind(exchange='private', queue=self.rga, routing_key=self.rga)
        for g in group_key:
            q = self.rga + g
            self.declare_queue(q)
            self.join_group(g, q)

    def declare_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name, durable=self.DURABLE)

    def join_group(self, group, queue=None):
        binding_key = '*' + group
        exc = 'topic' + group

        if queue is None:
            queue = self.rga + group
            self.declare_queue(queue)
        self.channel.queue_bind(exchange=exc, queue=queue, routing_key=binding_key)
        #self.close_connection()

    def callback(self, ch, method, properties, body):
        sbody = body.split()
        id_msg = sbody[0]
        body = body[len(id_msg)+1:]
        t = HistoricAck([self.id, id_msg])
        print(body)

    def subscribe_callback(self, ch, method, properties, body):
        print("From Subscribe::{}".format(body))
        self.subscribe_historic.append(body)

    def start(self):
        try:
            print("____________________________________________________________\n")
            print("____________________Messages Arriving_______________________\n")

            for k in self.keys:
                queue = self.rga + k
                self.channel.basic_consume(queue=queue, on_message_callback=self.callback, auto_ack=True)

            self.channel.basic_consume(queue=self.rga, on_message_callback=self.callback, auto_ack=True)
            if self.subscribe_queue is not None:

                self.channel.basic_consume(queue=self.subscribe_queue, on_message_callback=self.subscribe_callback, auto_ack=True)

            self.channel.start_consuming()

        except KeyboardInterrupt:
            self.stop()
            print("____________________________________________________________\n")
            print("____________________________________________________________\n")

    def stop(self):
        self.channel.stop_consuming()

    def group_key(self, name):

        try:
            return '.'+self.my_groups[name]
        except KeyError:
            for n in range(len(self.group_name)):

                if name == self.group_name[n]:
                    return self.keys[n]
                error, key = Group.group_key(name)
                if error == 0:
                    return '.'+key
        return -1

    def help(self):
        try:

            print("> Try: send | historic | receive | help |  create_group | add_participant | subscribe")
            print("____________________________________________________________")
        except KeyboardInterrupt:
            self.app()

    def historic(self):
        try:
            print("Collecting your historic, just a few seconds.")
            payload = "{0} {1}".format(Comands.HIST.value, self.id)
            if self.hist_connector is None:
                self.hist_connector = RpcClient('historic')
            msgs = self.hist_connector.call(payload)
            f_msgs = HistoricHandler.format_historic(msgs)
            print("____________________________________________________________\n")
            print("_________________________HISTORIC___________________________\n")
            print(f_msgs)
            self.print_subscribe_historic()
        except KeyboardInterrupt:
            self.app()

    def print_subscribe_historic(self):
        print("From Subscribe[{}]".format(len(self.subscribe_historic)))
        for m in self.subscribe_historic:
            print(m)

    def send(self):
        try:
            n_dst = raw_input("To :")# rga | group name
            msg_body = raw_input("Message>> ")

            if n_dst[1].isalpha(): #Group

                dst = self.group_key(n_dst)
                if dst == -1:
                    print("Absented Group, try again.\n")
                    return
                exc = 'topic' + dst
                key = self.rga + dst
                payload = n_dst + ' :: ' + msg_body
                dst = dst[1:]

            else:

                exc = 'private'
                key = n_dst
                dst = n_dst
                payload = msg_body
            id_msg = self.prepare_message(dst, payload)
            payload = "{0} {1}".format(id_msg, payload)
            self.send_message(exc, key, payload)
        except KeyboardInterrupt:

            self.app()

    def prepare_message(self, dst, payload):
        try:
            if self.hist_connector is None:
                self.hist_connector = RpcClient('historic')
            req ="{0} {1} {2}".format(self.id, dst, payload)
            id_msg = self.hist_connector.call(req)

            return id_msg
        except KeyboardInterrupt:
            exit(0)

    def send_message(self, dst, key, body):

        if self.connection.is_closed:
            self.connect()
        self.channel.basic_publish(
            exchange=dst, routing_key=key, body=body,
            properties=pika.BasicProperties(delivery_mode=2))

    def create_group(self):

        try:
            name = raw_input("Group name:")# rga | group name
            ngid, exc = Group.new_group(name, owner=self.id)
            if ngid == Comands.GROUP_EXIST.value:
                print("Existent group, try to create one with another name ;)\n")
                return
            print("Creating a new group..\n")
            group = Group(name, ngid, exc, self.id)
            group.build_exchange()
            Group.add_user(group.id, self.id)
            self.my_groups[name] = exc
            if(self.connection.is_closed):
                self.connect()
            self.join_group('.'+exc)
            self.keys.append("."+exc)
            self.group_name.append(name)
        except KeyboardInterrupt:
            exit(0)

    def add_participant(self):

        group_name = raw_input("Group Name:")
        rga = raw_input("RGA:")
        group_key = self.group_key(group_name)
        if group_key == -1:
            print("Absented Group, try again.\n")
            return
        group_id = Group.exist(group_key[1:])
        if group_id == -1:
            print("Try again, please.\n")
            return
        user_id = ProfileHandler.user_id(rga)
        Group.add_user(group_id, user_id)
        q_name = rga + group_key
        self.declare_queue(q_name)
        self.join_group(group_key, q_name)
        print("Adding into the group..\n")

    def subscribe(self):
        c = raw_input("What kind?")
        if c == 'pattern':
            code = 0
        elif c == 'group':
            code = 1
        elif c == 'user':
            code = 2
        else:
            return
        target = raw_input("Target:")
        rpc = RpcClient('rpc_queue_subscribe')
        body ='{2} {0} {1}'.format(self.id, target, code)
        result = rpc.call(body)
        if result > -1:
            if self.subscribe_queue is None:
                self.subscribe_queue = "subscribe.{0}".format(self.id)
            print("Subscribing done!\n")
        else:
            print("Something bad happend, try again, please.\n")

    def app(self):
        """print(" Options: ")
        print("   > send")
        print("   > historic")
        print("   > help")"""

        command = raw_input('\n What now? ')
        #print("____________________________________________________________")

        try:
            # send() | help() | historic()
            if command == "send":
                self.send()
            elif command == 'historic':
                self.historic()
            elif command == 'receive':
                print("Press Ctrl+C to stop receiving.")
                self.start()
            elif command == 'exit':
                exit(0)
            elif command == 'create_group':
                self.create_group()
            elif command == 'add_participant':
                self.add_participant()
            elif command == 'subscribe':
                self.subscribe()
            else:
                self.help()
            self.app()

        except Exception as e:
            print(e.message)
            exit(0)

        finally:
            exit(0)


