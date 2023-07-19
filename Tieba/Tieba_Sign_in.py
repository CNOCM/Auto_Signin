import os
import requests
import logging
import hashlib


# 从环境变量中获取参数
bduss = os.environ['BDUSS']
bark_url = os.environ['BARK_URL']


headers = {
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366"
}

cookies = {
    'BDUSS': bduss,
}


# 设置日志记录的基本配置
def log(msg, level='info'):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    if level == 'info':
        logging.info(msg)
    elif level == 'error':
        logging.error(msg)

# 获取tbs


def get_tbs():
    url = "https://tieba.baidu.com/dc/common/tbs"
    log("开始获取tbs", level='info')
    try:
        response = requests.get(url, headers=headers,
                                cookies=cookies, timeout=10)
        tbs = response.json().get("tbs")
        log("获取tbs结束", level='info')
        return tbs
    except Exception as e:
        log(f"获取tbs出错: {e}", level='error')
        return None


# 获取关注的贴吧列表
def get_tieba_list():
    url = "https://tieba.baidu.com/mo/q/newmoindex"
    log("开始获取贴吧列表", level='info')
    try:
        response = requests.get(url, headers=headers,
                                cookies=cookies, timeout=10)
        if response.status_code == 200 and response.json().get('no') == 0:
            forum_list = response.json()['data'].get('like_forum', [])
            num_tieba = len(forum_list)
            log(f"获取贴吧列表成功，共关注{num_tieba}个吧", level='info')
            return [forum['forum_name'] for forum in forum_list], num_tieba
        else:
            log(f"请求失败，状态码：{response.status_code}", level='error')
            return None
    except Exception as e:
        log(f"获取贴吧列表失败: {str(e)}", level='error')
        return None


# 进行贴吧签到
def tieba_sign_in():
    tbs = get_tbs()
    forum_list, num_tieba = get_tieba_list()
    success_count = 0
    failure_count = 0
    for forum_name in forum_list:
        data = {
            'kw': forum_name,
            'tbs': tbs,
            'sign': hashlib.md5(f'kw={forum_name}tbs={tbs}tiebaclient!!!'.encode('utf8')).hexdigest()
        }
        try:
            response = requests.post(
                'http://c.tieba.baidu.com/c/c/forum/sign',
                headers=headers,
                cookies=cookies,
                data=data,
                timeout=10
            )
            error_code = response.json().get('error_code')
            # 如果已经签到过了，跳过
            if error_code == '160002':
                log(f'"{forum_name}吧" 已签到！', level='info')
                success_count += 1
            elif error_code == '0':
                user_sign_rank = response.json()["user_info"]["user_sign_rank"]
                cont_sign_num = response.json()["user_info"]["cont_sign_num"]
                log(f'"{forum_name}" 签到成功，您是第 {user_sign_rank} 个签到的用户！连续签到{cont_sign_num}天', level='info')
                success_count += 1
            else:
                log(
                    f'"{forum_name}" 签到失败！以下为返回数据：{str(response.json())}', level='error')
                failure_count += 1
        except Exception as e:
            log(f'"{forum_name}" 签到失败！{str(e)}', level='error')
            failure_count += 1
    if success_count == num_tieba:
        message = f"签到{num_tieba}个，成功{success_count}个，失败{failure_count}个！\n🎉恭喜，所有贴吧签到成功！！"
        log(message, level='info')
    else:
        message = f"签到{num_tieba}个，成功{success_count}个，失败{failure_count}个！"
        log(message, level='error')
    # 调用Bark_notification函数推送信息到手机
    bark_notification(message)


# Bark推送信息到手机
def bark_notification(message):
    title = '贴吧签到结果'
    params = {
        'title': title,
        'body': message,
        'group': 'Daily Signin'
    }
    requests.get(bark_url, params=params)


# 运行脚本
tieba_sign_in()
