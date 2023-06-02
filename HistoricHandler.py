""""This class is responsible for  process historic requests"""
from HandlerDB import HandlerDB
from mysql.connector import Error
from datetime import datetime

class HistoricHandler(HandlerDB):

    def __init__(self):
        print("init")

    @staticmethod
    def insert_msg(src, dst, body):

        try:
            dtime = datetime.now()
            if len(dst) == 4: # GROUP
                dtype = 1
            else:              # DIRECT
                dtype = 0

            query = "INSERT INTO emergent_message (body, src, dst_type, dst, date) " \
                    "VALUES('{0}',{1},{2},'{3}','{4}')".format(body, src, dtype, dst, dtime)
            err, msg_id = HandlerDB.insert(query)
            if err == -1:
                print("Error.\n")
                return err
            else:
                return msg_id

        except Error as e:
            print("Error.\n")
            return -1

    @staticmethod
    def confirm_msg(msg_id, user_id):
        cnx = HandlerDB.connect()
        if cnx == -1:
            return -1
        try:
            cursor = cnx.cursor(buffered=True)
            query = 'SELECT * FROM `emergent_message` WHERE message_id = {0}'.format(msg_id)
            cursor.execute(query)
            records = cursor.fetchall()

            if len(records) < 0:
                return -1

            records = records[0]
            dst_type = records[3]
            dtime = records[5]
            if dst_type == 0: #direct
                table = 'user'
                t_field = 'user_id'
                field = 'rga'
            else: # Group
                table = 'group'
                t_field = 'group_id'
                field = 'group_key'
            query = "SELECT {1} FROM `{0}` WHERE {2}='{3}'".format(table, t_field, field, records[4])
            cursor.execute(query)
            dst_id = cursor.fetchall()
            if dst_id < 0:
                return -1
            dst_id = dst_id[0][0]

            query = "INSERT INTO `persistent_messages`(src_id, body,dst_id, dst_type,date)" \
                    " VALUES({0},'{1}',{2},{3},'{4}')".format(records[2], records[1], dst_id, dst_type, dtime)
            cursor.execute(query)
            cnx.commit()
            persistent_msg_id = cursor.lastrowid
            query = 'INSERT INTO `read_messages`(msg_id, user_id) VALUES({0},{1})'.format(persistent_msg_id, user_id)
            cursor.execute(query)
            cnx.commit()
            persistent_msg_id = cursor.lastrowid
            cnx.close()
            return persistent_msg_id
        except Error as e:
            print(e.msg)
            cnx.close()
            return -1

    @staticmethod
    def received_messages(user_id):
        try:
            cnx = HandlerDB.connect()
            if cnx == -1:
                return -1
            cursor = cnx.cursor(buffered=True)
            query = "SELECT body,rga, date FROM `persistent_messages`,`read_messages`,`user` WHERE read_messages.user_id={0} " \
                    "AND read_messages.msg_id= persistent_messages.msg_id" \
                    " AND persistent_messages.src_id = user.user_id".format(user_id)
            cursor.execute(query)
            msgs = cursor.fetchall()
            return msgs
        except Error as e:
            print(e.msg)

    @staticmethod
    def sent_messages(user_id):
        try:
            cnx = HandlerDB.connect()
            if cnx == -1:
                return -1
            cursor = cnx.cursor(buffered=True)
            query = "SELECT body, dst, date FROM `emergent_message` WHERE src={0}".format(user_id)
            cursor.execute(query)
            msgs = cursor.fetchall()
            return msgs
        except Error as e:
            print(e.msg)

    @staticmethod
    def format_historic(msgs):
        block = msgs.split('|')

        r_msgs = block[0].split('\n')[:-1]
        s_msgs = block[1].split('\n')[:-1]
        rec = "Received Messages[{0}]\n".format(len(r_msgs))
        for m in r_msgs:
            n = m[:12+17]
            b = m[13+17:]
            f = n + " :: " + b + "\n"
            rec = rec + f
        rec = rec + "\nSent Messages[{0}]\n".format(len(s_msgs))
        for m in s_msgs:
            if m[4+17] == '.':
                n = m[:4+17]
                b = m[5+17:]
            else:
                n = m[:12+17]
                b = m[13+17:]
            f = n + " :: " + b + "\n"
            rec = rec + f
        return rec


