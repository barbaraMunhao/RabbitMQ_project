""""The objetcs of this class are responsible for load profiles from the right file,
for bind a profile with its respective file where are stored informations about subscriptions,etc..."""

import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import re
from HandlerDB import HandlerDB


class ProfileHandler(HandlerDB):


    @staticmethod
    def insert_user(name, rga, password):
        cnx = HandlerDB.connect()
        if cnx != -1:
            try:
                cursor = cnx.cursor()
                query = "INSERT INTO user (rga,name,pwd) VALUES('{0}','{1}','{2}')".format(rga, name, password)
                cursor.execute(query)
                cnx.commit()
                user_id = cursor.lastrowid

                g_id = ProfileHandler.bind_rga_course(rga, cnx)
                if g_id != -1:
                    try:
                        query = "INSERT INTO user_key (user_id, key_id) VALUES({0},{1})".format(user_id, g_id)
                        cursor.execute(query)
                        cnx.commit()
                    except Error as e:
                        cnx.close()
                        print(e.msg)
                        return -1, None

            except Error as e:
                cnx.close()
                print(e.msg)
                if e.errno == errorcode. ER_DUP_ENTRY: # Rga exists
                    return errorcode. ER_DUP_ENTRY, None
                else:
                    return -1, None
            cnx.close()
            return 0, user_id
        else:
            return -1, None

    @staticmethod
    def exist(rga, password):
        cnx = HandlerDB.connect()
        if cnx != -1:
            try:
                cursor = cnx.cursor(buffered=True)
                query = "SELECT user_id FROM `user` WHERE rga='{0}' and pwd='{1}'".format(rga, password)
                cursor.execute(query)
                records = cursor.fetchall()

            except Error as e:
                print(e.msg)
                cnx.close()
                return -1
            cnx.close()
            if len(records) < 1:
                return -1
            else:
                r = records.__getitem__(0)[0]
                return r

    @staticmethod
    def bind_rga_course(rga, cnx):
        code = re.findall(r"\d\d\d\d", rga)[1]
        try:
            cursor = cnx.cursor(buffered=True)
            query = "SELECT group_id FROM `group` WHERE group_key = '{0}'".format(code)
            cursor.execute(query)
            records = cursor.fetchall()
        except Error as e:
            print(e.msg)
            return -1
        if len(records) < 1:
            return -1
        else:
            r = records.__getitem__(0)[0]
            return r

    @staticmethod
    def associated_keys(user_id):
        cnx = HandlerDB.connect()
        try:
            cursor = cnx.cursor(buffered=True)
            query = "SELECT group_key, name FROM `group`, `user_key` WHERE user_key.user_id = {0}" \
                    " and user_key.key_id = group.group_id".format(user_id)
            cursor.execute(query)
            records = cursor.fetchall()

            cnx.close()
            return records
        except Error as e:
            print(e.msg)
            cnx.close()
            return -1
    @staticmethod
    def user_id(rga):
        cnx = HandlerDB.connect()
        if cnx != -1:
            try:
                cursor = cnx.cursor(buffered=True)
                query = "SELECT user_id FROM `user` WHERE rga='{0}'".format(rga)
                cursor.execute(query)
                records = cursor.fetchall()

            except Error as e:
                print(e.msg)
                cnx.close()
                return -1
            cnx.close()
            if len(records) < 1:
                return -1
            else:
                r = records.__getitem__(0)[0]
                return r

