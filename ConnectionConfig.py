import pika

class ConectionConfig(object):

    CREDENTIAL = pika.PlainCredentials('admin', 'admin')
    HOST = '192.168.1.19'  # 'localhost'