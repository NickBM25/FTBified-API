import os
import socket
from paramiko import AutoAddPolicy, AuthenticationException, SSHClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Fetch variables
USERNAME = os.getenv("SFTP_USERNAME")
PASSWORD = os.getenv("SFTP_PASSWORD")
HOSTNAME = os.getenv("SFTP_HOSTNAME")
PORT = os.getenv("SFTP_PORT")
NAME = os.getenv("SFTP_NAME")


def getfile(path):
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())

    try:
        ssh_client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD, port=PORT)
    except socket.gaierror:
        raise ConnectionError("Server not found.")
    except TimeoutError:
        raise ConnectionError("Connection timed out. Server is offline or unreachable.")
    except AuthenticationException:
        raise ConnectionError("Authentication failed. Please check your username and password.")

    try:
        with ssh_client.open_sftp() as sftp:
            with sftp.open(path) as file:
                content = file.read().decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError("File not found.")
    finally:
        ssh_client.close()

    return content