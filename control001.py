import requests

import paramiko
import json
import pandas as pd

def send_to_dingtalk_webhook(message):
    # 填入你的钉钉webhook
    webhook= ''
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
        # print(message)
        # print(webhook_url)
        if response.status_code == 200:
            print("消息已成功发送到钉钉机器人！")
            # print(response)
        else:
            print(f"发送消息到钉钉机器人失败，错误代码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"发生异常：{e}")
    except Exception as e:
        print(f"发生异常：{e}")

def ssh_connect(hostname, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password)
        return ssh
    except Exception as e:
        print(f"An error occurred while connecting: {str(e)}")
        return None

def execute_command(ssh, command):
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output, error
    except Exception as e:
        print(f"An error occurred while executing command: {str(e)}")
        return None, None

def install_quil(ssh):
    command = 'sudo -i wget albert.vip/auto_install_quil_and_initia_reboot.sh && chmod +x auto_install_quil_and_initia_reboot.sh && ./auto_install_quil_and_initia_reboot.sh'
    output, error = execute_command(ssh, command)
    print(output)
    if error:
        print(f"Error: {error}")

def clone_store_repo(ssh):
    command = 'sudo -i rm -rf /www/ceremonyclient/node/.config/store/ && cd /www/ceremonyclient/node/.config/ && git clone https://github.com/a154225859/store.git'
    output, error = execute_command(ssh, command)
    print(output)
    if error:
        print(f"Error: {error}")

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
                print(f"name: {name}")
                print(f"peerId: {peerId}")
                print(f"maxFrame: {max_frame}\n")
        except json.JSONDecodeError:
            reboot(ssh, name)
            print(f"{name}挂了: {output}", end='')

    if error:
        print(f"{name}挂了: \n{error}", end='')
        reboot(ssh, name)


def run_start_script(ssh):
    command = 'sudo cd /root/ && ./start.sh'
    output, error = execute_command(ssh, command)
    print(output)
    if error:
        print(f"Error: {error}")

# 从xlsx文件读取服务器信息
def read_server_info(file_path):
    df = pd.read_excel(file_path)
    servers = df.to_dict(orient='records')
    return servers

# 重启服务器
def reboot(ssh, name):
    message = f"{name}挂了，进行重启"
    send_to_dingtalk_webhook(message)
    print(f"{name}已经重启\n")
    command = 'sudo reboot'
    output, error = execute_command(ssh, command)
    if error:
        print(f"Error: {error}")


def check_grpcurl_installed(ssh):
    check_command = 'which grpcurl'
    output, error = execute_command(ssh, check_command)
    return output.strip() != ""

def install_grpcurl(ssh):
    # 检查 grpcurl 是否已安装
    if not check_grpcurl_installed(ssh):
        # 安装 grpcurl
        install_command = (
            'wget https://github.com/fullstorydev/grpcurl/releases/download/v1.8.7/grpcurl_1.8.7_linux_x86_64.tar.gz && '
            'tar -xvf grpcurl_1.8.7_linux_x86_64.tar.gz && '
            'sudo mv grpcurl /usr/local/bin/ && '
            'rm grpcurl_1.8.7_linux_x86_64.tar.gz'
        )
        output, error = execute_command(ssh, install_command)
        print("Installing grpcurl Output:", output)
        print("Installing grpcurl Error:", error)
    else:
        print("grpcurl is already installed.")


# 配置服务器信息文件路径
file_path = 'server_info.xlsx'
servers = read_server_info(file_path)

for server in servers:
    name = server['name']
    hostname = server['hostname']
    port = server['port']
    username = server['username']
    password = server['password']

    # 连接服务器
    ssh = ssh_connect(hostname, port, username, password)

    if ssh:
        # 根据需要调用不同的函数
        # install_grpcurl(ssh)# 第一次运行没有grp时候，运行一次，后面关掉
        run_check_script(ssh, name)

        # 关闭连接
        ssh.close()
