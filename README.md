## 操作指南

1. **服务器数据文件**: 将服务器数据放入 `server_info.xlsx` 文件中。
   
2. **安装 grpcurl**:
   - 如果服务器上没有安装 `grpcurl`，第一次运行时候，运行154行左右下列代码安装。安装后，之后运行可以注释掉这行代码：
     ```python
     install_grpcurl(ssh)
     ```

3. **钉钉 Webhook 配置**:
   - 请将你自己的钉钉 Webhook 填入以下位置。
     ```python
     # 填入你的钉钉 webhook
     webhook = ''
     ```
     如果没有钉钉，请注释掉 `send_to_dingtalk_webhook(message)` 代码。
      ```
      # 发送消息到钉钉
      # send_to_dingtalk_webhook(message)
      ```
