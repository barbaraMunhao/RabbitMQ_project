import pika
import uuid
from ConnectionConfig import ConectionConfig
from HandlerDB import HandlerDB

DURABLE = True
CREDENTIAL = ConectionConfig.CREDENTIAL
HOST = ConectionConfig.HOST


class Group(object):

    #Constructor
    def __init__(self, name, g_id, key=None, owner=None):
        self.name = name
        self.id = g_id
        if key is None:
            key = self.rand_key()
        self.exc_key = key
        self.owner = owner #if none = root (salas tem owner=root)

    @staticmethod
    def rand_key():
        ##return a valid nonused 4-caracteres-key
        # Convert UUID format to a Python string.
        random = str(uuid.uuid4())

        # Make all characters uppercase.
        random = random.upper()

        # Remove the UUID '-'.
        random = random.replace("-", "")

        # Return the random string.
        return random[0:4]

    @staticmethod
    #It receives the memo and the 4 characters that indicates it.
    def new_group(name, exc_key=None, owner=None):
        #It returns 0 when the data is not in the database.
        if exc_key is None:
            exc_key = Group.rand_key()
        if Group.exist(exc_key) == -2:
            if owner is not None:
                query = "INSERT INTO `group` (name, group_key, owner) VALUES('{0}','{1}', {2})".format(name, exc_key, owner)
            else:
                query = "INSERT INTO `group` (name, group_key) VALUES('{0}','{1}')".format(name, exc_key)
            #if it works, this is when the new_group is - in fact - registered in the database.
            error, group_id = HandlerDB.insert(query)
            if error == 0 and group_id is not None:
                return group_id, exc_key
            else:
                return -10, None
        else:
            return -10, None

    @staticmethod
    def group_key(name):
        connection = HandlerDB.connect()
        if connection != -1:
            try:
                cursor = connection.cursor(buffered=True)
                query = "SELECT `group_key` FROM `group` where `name`='{0}'".format(name)
                cursor.execute(query)
                records = cursor.fetchall()
            except Exception as e:
                print(e.message)
                connection.close()
                return -1
            connection.close()
            if len(records) < 1:
                return -1
            else:
                r = records.__getitem__(0)[0]
                return 0, r


    @staticmethod
    def exist(group_key):
        connection = HandlerDB.connect()
        if connection != -1:
            try:
                cursor = connection.cursor(buffered=True)
                query = "SELECT group_id FROM `group` where `group_key`='{0}'".format(group_key)
                cursor.execute(query)
                query_response = cursor.fetchall()
                if len(query_response) == 0:
                    return -2
                return query_response.__getitem__(0)[0]

            except Exception as e:
                print(e.message)
                return -1

            #It checks if there's any data.

            finally:
                connection.close()

    def create(self):
        query = "INSERT INTO `group` (name, group_key) VALUES('{0}','{1}')".format(self.name, self.exc_key)
        error, g_id = HandlerDB.insert(query)
        if error == 0:
            self.exc_key = g_id

    #It sets exchange to the group's specifications.
    def build_exchange(self, key=None):

        if key is None:
            key = self.exc_key
        exc = 'topic.' + key
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=CREDENTIAL))
        channel = connection.channel()
        channel.exchange_declare(exchange=exc, exchange_type='topic', durable=DURABLE)

    @staticmethod
    def add_user(group_id, user_id):
        connection = HandlerDB.connect()
        if connection == -1:
            return
        try:
            cursor = connection.cursor(buffered=True)
            query = "INSERT INTO user_key (user_id, key_id) VALUES({0},{1})".format(user_id, group_id)
            cursor.execute(query)
            connection.commit()
        except Exception as e:
            connection.close()
            print(e.msg)
            return -1
        return 0

    @staticmethod
    def id_by_name(name):
        connection = HandlerDB.connect()
        if connection != -1:
            try:
                cursor = connection.cursor(buffered=True)
                query = "SELECT `group_id` FROM `group` where `name`='{0}'".format(name)
                cursor.execute(query)
                records = cursor.fetchall()
            except Exception as e:
                print(e.message)
                connection.close()
                return -1, None
            connection.close()
            if len(records) < 1:
                return -1, None
            else:
                r = records.__getitem__(0)[0]
                return 0, r