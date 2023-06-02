"""The principal class and function."""
import re
import sys
import getpass
from RPCClient import RpcClient
from Comands import Comands
from User import User


class FACOMsg(object):

    #error message when the number of parameters (on shell) exceeds 4.
    def print_usage(self):
        print("\nFACOMsg login <USER> <PASSWORD>| join\n")

    def process_request(self, argv):
        argc = len(argv)
        #it checks the number of arguments.
        if argc > 4:
            self.print_usage()
            sys.exit(1)

        #Initialization screen
        elif argc == 1:
            print("---------------------- Welcome to FACOMSG ----------------------\n")

            print(" You can: ")
            print("   > LOGIN  : FACOMsg login or FACOMsg login <USER> <PASSWORD>")
            print("   > JOIN   : FACOMsg join\n")

            op = raw_input("what now?")
            if op == 'login':
                print("---------------------- FACOMSG | Login ----------------------\n")
                user = self.login()
                self.start_user_app(user)

            elif op == 'join':
                print("---------------------- FACOMSG | Join us ----------------------\n")
                # it will return an int that will indicate if the profile creation happened correctly or not.
                error, name = self.create_profile()
                if error == 0:
                    print("Your profile is ready for you, {0}.\n".format(name))
                else:
                    self.process_join_reponse(error)
                    self.create_profile()
        #Login scenario
        elif sys.argv[1] == 'login':

            #the user can pass login infos directly to the shell.
            if argc == 4:
                rga = argv[2]
                pwd = argv[3]
                user = self.request_authentication(rga, pwd)
            else:
                if sys.version_info < (3, 0):  # Python 2. #
                    input = raw_input


                print("---------------------- FACOMSG | Login ----------------------\n")
                user = self.login()


            #The FACOMsg app will effectively start.
            self.start_user_app(user)

        #Join scenario
        elif sys.argv[1] == 'join':
            print("---------------------- FACOMSG | Join us ----------------------\n")
            #it will return an int that will indicate if the profile creation happened correctly or not.
            error, name = self.create_profile()
            if error == 0:
                print("Your profile is ready for you, {0}.\n".format(name))
            else:
                self.process_join_reponse(error)
                self.create_profile()
#_________________________________________________________________________________

    #It receives the users infos to authenticate it so he/she can be logged in.
    def login(self):
        rga = raw_input("RGA>")
        pwd = getpass.getpass(prompt='Password>')
        user = self.request_authentication(rga, pwd)
        return user

    def create_profile(self):
        if sys.version_info < (3, 0): #Python 2. # ###review
            input = raw_input
        name = input("Full Name> ")
        rga = input("RGA> ")
        pwd1 = getpass.getpass(prompt='Password>')
        pwd2 = getpass.getpass(prompt='Confirm Password>')
        if pwd1 == pwd2:
            return self.request_profile(name, rga, pwd1), name
        else:

            while True:
                print('Password did not match. Please, try again.')
                pwd1 = getpass.getpass(prompt='Password>')
                pwd2 = getpass.getpass(prompt='Confirm Password>')
                if pwd1 == pwd2:
                    return self.request_profile(name, rga, pwd1), name
                else:
                    continue

    def request_profile(self, name, rga, pwd):
        print("Preparing everything...\n")
        rpcClient = RpcClient()
        payload ="{0} {3} {1} {2}".format(Comands.JOIN.value, rga, name, pwd)

        result = int(rpcClient.call(payload))
        return result

    def request_authentication(self, rga, pwd):
        rpcClient = RpcClient()
        payload = "{0} {1}{2}".format(Comands.LOGIN.value, rga, pwd)
        response = rpcClient.call(payload)
        user = self.process_authentication_response(response, rga)
        rpcClient.close_connection()
        return user

    def process_authentication_response(self, data, rga):
        if data == '-1':
            print("\n[!] Invalid User, please try again.\n")
            return self.login()
        else:

            print("\n---------------- FACOMSG | RGA:'{0}' --------------- \n".format(rga))
            return self.create_user(rga, data)

    def process_join_reponse(self, error):
        if error == Comands.USER_EXIST.value:
            print("RGA in use.")
        elif error == -1:
            print("Something bad accurred :/" \
            " Try again to be sure you're in.")

    def create_user(self, rga, data):
        sdata = data.split()
        user_id = sdata[1]
        keys = list(re.findall(r".\w\w\w\w", sdata[2]))
        gnames = list(sdata[3].split('.')[1:])
        user = User("", rga, user_id , keys, gnames)

        return user

    #App's initilization
    def start_user_app(self, user):
        user.connect()
        print(" Options: ")
        print("    send")
        print("    receive")
        print("    historic")
        print("    create_group")
        print("    add_participant")
        print("    subscribe")
        print("    help")
        print("    exit")
        user.app()

#MAIN
def main():

    try:
        facomsg = FACOMsg()
        facomsg.process_request(sys.argv)
    except KeyboardInterrupt:
        print("Closing all.\n")
        exit(0)


if __name__ == "__main__":
    main()
