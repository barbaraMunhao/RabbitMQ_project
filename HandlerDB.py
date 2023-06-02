
import mysql.connector
from mysql.connector import Error



class HandlerDB(object):

    @staticmethod
    #It stablishes connection with the database.
    #Attention is needed so the password is correctly passed.
    def connect():
        try:
            return mysql.connector.connect(user='root', password='',
                                           host='localhost', database='facomsg')
        except mysql.connector.Error as err:
            print("Connection Error")
            return -1

    @staticmethod
    #It runs the query inside the database.
    def insert(query):
        cnx = HandlerDB.connect()
        error = 0
        target_id = None
        if cnx == -1:
            return -1, None
        try:
            #it allows Python to execute sql commands in a database session.
            cursor = cnx.cursor()
            cursor.execute(query)
            cnx.commit()
            target_id = cursor.lastrowid
        except Error as e:
            print("Cursor " + cursor)
            print(e.msg)
            error = -1

        finally:
            cnx.close()
            return error, target_id
