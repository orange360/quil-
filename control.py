import requests
import paramiko
import json
import pandas as pd
import logging


# Configure logging for the script
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('output.log', 'a', 'utf-8'),
                              logging.StreamHandler()])

# Set paramiko logging level to WARNING to suppress INFO messages
paramiko.util.log_to_file('paramiko.log', level='WARNING')

logger = logging.getLogger(__name__)

def send_to_dingtalk_webhook(message):
    webhook = ''
    if not webhook:  # 如果webhook为空，则不执行后续代码
        return
    webhook_url = webhook
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }

    try:
        response = requests.post(webhook_url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info("消息已成功发送到钉钉机器人！")
        else:
            logger.error(f"发送消息到钉钉机器人失败，错误代码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"发生异常：{e}")
    except Exception as e:
        logger.error(f"发生异常：{e}")

def ssh_connect(hostname, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password)
        return ssh
    except Exception as e:
        logger.error(f"An error occurred while connecting: {str(e)}")
        return None

def execute_command(ssh, command):
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output, error
    except Exception as e:
        logger.error(f"An error occurred while executing command: {str(e)}")
        return None, None

def install_quil(ssh):
    command = 'sudo -i wget albert.vip/auto_install_quil_and_initia_reboot.sh && chmod +x auto_install_quil_and_initia_reboot.sh && ./auto_install_quil_and_initia_reboot.sh'
    output, error = execute_command(ssh, command)
    logger.info(output)
    if error:
        logger.error(f"Error: {error}")

def clone_store_repo(ssh):
    command = 'sudo -i rm -rf /www/ceremonyclient/node/.config/store/ && cd /www/ceremonyclient/node/.config/ && git clone https://github.com/a154225859/store.git'
    output, error = execute_command(ssh, command)
    logger.info(output)
    if error:
        logger.error(f"Error: {error}")

def run_check_script(ssh, name):
    command = 'sudo grpcurl -plaintext localhost:8337 quilibrium.node.node.pb.NodeService.GetNodeInfo'
    output, error = execute_command(ssh, command)

    if output:
        # Parse and extract maxFrame if output is a JSON
        try:
            output_json = json.loads(output)
            peerId = output_json.get("peerId")
            max_frame = output_json.get("maxFrame")
            if max_frame:
                logger.info(f"name: {name}")
                logger.info(f"peerId: {peerId}")
                logger.info(f"maxFrame: {max_frame}\n")
        except json.JSONDecodeError:
            reboot(ssh, name)
            logger.info(f"{name}挂了: {output}", end='')

    if error:
        logger.error(f"{name}挂了: \n{error}", end='')
        reboot(ssh, name)

def run_start_script(ssh):
    command = 'sudo cd /root/ && ./start.sh'
    output, error = execute_command(ssh, command)
    logger.info(output)
    if error:
        logger.error(f"Error: {error}")

def read_server_info(file_path):
    df = pd.read_excel(file_path)
    servers = df.to_dict(orient='records')
    return servers

def reboot(ssh, name):
    message = f"{name}挂了，进行重启"
    send_to_dingtalk_webhook(message)
    logger.info(f"{name}已经重启\n")
    command = 'sudo reboot'
    output, error = execute_command(ssh, command)
    if error:
        logger.error(f"Error: {error}")

def check_grpcurl_installed(ssh):
    check_command = 'which grpcurl'
    output, error = execute_command(ssh, check_command)
    return output.strip() != ""

def install_grpcurl(ssh):
    if not check_grpcurl_installed(ssh):
        install_command = (
            'wget https://github.com/fullstorydev/grpcurl/releases/download/v1.8.7/grpcurl_1.8.7_linux_x86_64.tar.gz && '
            'tar -xvf grpcurl_1.8.7_linux_x86_64.tar.gz && '
            'sudo mv grpcurl /usr/local/bin/ && '
            'rm grpcurl_1.8.7_linux_x86_64.tar.gz'
        )
        output, error = execute_command(ssh, install_command)
        logger.info("Installing grpcurl Output:", output)
        logger.error("Installing grpcurl Error:", error)
    else:
        logger.info("grpcurl is already installed.")

file_path = 'server_info.xlsx'
servers = read_server_info(file_path)

for server in servers:
    name = server['name']
    hostname = server['hostname']
    port = server['port']
    username = server['username']
    password = server['password']

    ssh = ssh_connect(hostname, port, username, password)

    if ssh:
        # Uncomment the line below to install grpcurl if not already installed
        # install_grpcurl(ssh)
        run_check_script(ssh, name)
        ssh.close()
