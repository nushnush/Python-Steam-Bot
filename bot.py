import socket
import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()
from steam import guard
from steam.client import SteamClient
from steam.enums import EResult

config = open("config.txt", "r+").read().splitlines()
SA = guard.SteamAuthenticator({ 'shared_secret': config[5], 'identity_secret': config[7] })
client = SteamClient()
server_socket = None

print("\nSteam Bot")
print("-" * 20)

# ======[ Events ]====== #

@client.on("error")
def handle_error(result):
    print("\nError", result)

@client.on("reconnect")
def handle_reconnect(delay):
    print("\nReconnect in {} seconds...".format(delay))

@client.on("disconnected")
def handle_disconnect():
    print("\nDisconnected.")

    if client.relogin_available:
        print("\nReconnecting...")
        client.reconnect(maxdelay=30)

@client.on("logged_on")
def handle_after_logon():
    print("Logged on as: {}".format(client.user.name))
    print("Community profile: {}".format(client.steam_id.community_url))
    print("Last logon: {}".format(client.user.last_logon))
    print("Last logoff: {}".format(client.user.last_logoff))
    print("Amount of friends: {}".format(len(client.friends)))

@client.on("chat_message")
def handle_chat_message(user, message):
    print("\n{} says \"{}\"".format(user.name, message))
    user.send_message('yo')

# ======[ Login Code ]====== #

try:
    result = client.login(username=config[1], password=config[3], two_factor_code=SA.get_code())

    if result != EResult.OK:
        raise SystemExit

    client.run_forever()

except KeyboardInterrupt:
    if client.connected:
        print("Logging out...")
        client.logout()
    raise SystemExit

# ======[ functions ]====== #

# TCP Command Recieve Structure: "ACCOUNT_PASSWORD|COMMAND_NAME|ADDITIONAL_TEXT"
# Example: "777777|Send_Message|Hey there buddy"

# TCP Response Structure: "SUCCESS/ERROR|ADDITIONAL_TEXT"
# Example: "ERROR|Password is incorrect"

def initiate_tcp():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((config[9], config[11]))
    server_socket.listen(5)

    while True:
        client_socket, address = server_socket.accept()
        print("[TCP] Connection from {} established.".format(address))
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            
            parts = data.split("|")
            if parts[0] == data:        # could not split the data for some reason
                client_socket.send(bytes('ERROR|Missing seperator', 'utf-8'))
                break

            if parts[0] != config[3]:   # wrong password
                client_socket.send(bytes('ERROR|Password is incorrect', 'utf-8'))
                break

            print("[TCP] Data from {}: {}".format(address, data))
            execute_tcp_command(clientsocket=client_socket, data=parts)
        
        client_socket.close()
        
    server_socket.close()

def create_client_socket(message):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((config[9], config[11]))

    try:
        client_socket.send(message.encode('utf-8'))
        data = client_socket.recv(1024)
        print(str(data))
    
    except KeyboardInterrupt:
        print("Exited by user")
    
    client_socket.close()

def execute_tcp_command(clientsocket, data):
    clientsocket.send(bytes('SUCCESS|Command has been executed', 'utf-8'))