import httpx
import time
import os  # 引入 os 模块以读取环境变量

# 假设 randomize 是一个自定义模块
from utils.randomize import generate
from utils.location import encrypted_latitude, encrypted_longitude
# from utils.wechatPush import send_push_notification # 不再使用旧推送
from utils.data import account, password, school_id, province, city, address, address_name

def send_server_chan(title, content):
    """
    使用 Server酱 发送推送消息
    从环境变量获取 SERVER_CHAN_SENDKEY
    """
    # 获取 GitHub Secrets 中设置的环境变量
    send_key = os.environ.get("SERVER_CHAN_SENDKEY")
    
    if not send_key:
        print("⚠️ 未检测到 SERVER_CHAN_SENDKEY 环境变量，跳过 Server酱 推送")
        return

    url = f"https://sctapi.ftqq.com/{send_key}.send"
    data = {
        'title': title,
        'desp': content
    }
    
    try:
        # 使用 httpx 发送 POST 请求
        response = httpx.post(url, data=data)
        resp_json = response.json()
        if resp_json.get('code') == 0:
            print("✅ Server酱推送成功")
        else:
            print(f"❌ Server酱推送失败: {resp_json}")
    except Exception as e:
        print(f"❌ Server酱发送请求异常: {e}")


def login_and_get_token():
    token, uuid = generate()
    print(f"初始随机token为：{token}")

    url = f"https://api.xixunyun.com/login/api?token={token}&from=app&version=4.9.7&school_id={school_id}"
    payload = {
        'app_version': '4.9.7',
        'uuid': uuid,
        'request_source': 3,
        'platform': 2,
        'password': password,
        'system': '14',
        'school_id': school_id,
        'account': account,
        'app_id': 'cn.vanber.xixunyun.saas'
    }
    headers = {
        'User-Agent': 'okhttp/3.8.1',
        'content-type': 'application/x-www-form-urlencoded',
        'Host': 'api.xixunyun.com',
        'user-agent': 'okhttp/3.8.1'
    }

    try:
        with httpx.Client() as client:
            login_response = client.post(url, headers=headers, data=payload)
            login_response_data = login_response.json()
            if login_response_data.get('code') == 20000:
                cookies = login_response.cookies
                token = login_response.json()['data']['token']
                print("登录成功")
                return token, cookies
            else:
                msg = login_response_data.get('message')
                print(f"登录失败，信息：{msg}")
                # 登录失败也尝试推送
                send_server_chan("习讯云登录失败", f"账号：{account}\n原因：{msg}")
                return None, None
    except httpx.RequestError as e:
        print(f"登录时发生请求错误：{e}")
        return None, None


def signin_with_token(token, cookies):
    time.sleep(5)  # 等待5秒
    url = f"https://api.xixunyun.com/signin_rsa?token={token}&from=app&version=4.9.7&school_id={school_id}"

    payload = {
        'address': address,
        'province': province,
        'city': city,
        'latitude': encrypted_latitude,
        'longitude': encrypted_longitude,
        'address_name': address_name
    }
    headers = {
        'User-Agent': 'okhttp/3.8.1',
        'Cookie': str(cookies),
        'content-type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Host': 'api.xixunyun.com',
        'Connection': 'keep-alive'
    }

    try:
        with httpx.Client() as client:
            sign_response_data = client.post(url, headers=headers, data=payload).json()
            sign_message = sign_response_data.get('message')

            if sign_response_data.get('code') == 20000:
                signin_result = "习讯云签到成功"
                print(f"{signin_result}，信息：{sign_message}")
                # 发送成功推送
                send_server_chan(signin_result, f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n信息：{sign_message}")

            else:
                signin_result = "习讯云签到失败"
                print(f"{signin_result}，信息：{sign_message}")
                # 发送失败推送
                send_server_chan(signin_result, f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n错误信息：{sign_message}")
                
    except httpx.RequestError as e:
        err_msg = f"签到请求发生异常：{e}"
        print(err_msg)
        send_server_chan("习讯云脚本错误", err_msg)


if __name__ == "__main__":
    token, cookies = login_and_get_token()
    if token and cookies:
        signin_with_token(token, cookies)
