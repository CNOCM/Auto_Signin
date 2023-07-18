import os
import requests
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# 获取贴吧列表
def get_tieba_list():
    url = "https://tieba.baidu.com/mo/q/newmoindex"
    # 设置自定义的User-Agent头
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366",
    }
    cookies = {
        "BDUSS": bduss
    }
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        data = response.json().get("data")
        # 获取 tbs（每次签到都需要）
        tbs = data.get("tbs")
        # 获取关注的贴吧列表
        like_forum = data.get("like_forum")
        logging.info(f"获取贴吧列表成功，共关注{len(like_forum)}个贴吧")
        return tbs, like_forum
    else:
        error_msg = f"请求失败，状态码：{response.status_code}"
        raise ValueError(error_msg)


# 进行贴吧签到
def tieba_sign_in():
    tbs, like_forum = get_tieba_list()
    total_forum = len(like_forum)
    success = []
    failure = []
    url = "https://tieba.baidu.com/sign/add"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip,deflate,br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Connection": "keep-alive",
        "Host": "tieba.baidu.com",
        "Referer": "https://tieba.baidu.com/",
        "x-requested-with": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366"
    }
    for forum in like_forum:
        # 如果已经签到过了，跳过
        if forum.get("is_sign") == 1:
            success.append(f"[{forum['forum_name']}吧] 已签到")
        else:
            data = {
                "tbs": tbs,
                "kw": forum["forum_name"],
                "ie": "utf-8"
            }
            try:
                resp = requests.post(url, headers=headers, data=data)
                obj = resp.json()
                if obj["data"]["errmsg"] == "success" and obj["data"]["errno"] == 0 and obj["data"]["uinfo"][
                        "is_sign_in"] == 1:
                    msg = f"[{forum['forum_name']}] 签到成功 排名 {obj['data']['uinfo']['user_sign_rank']} 积分 {obj['data']['uinfo']['cont_sign_num']}"
                    success.append(msg)
                else:
                    error_codes = {
                        2150040: "需要验证码",
                        1011: "未加入此吧或等级不够",
                        1102: "签到过快",
                        1101: "重复签到",
                        1010: "目录出错"
                    }
                    error_msg = error_codes.get(obj.get("no"), "签到失败")
                    msg = f"[{forum['forum_name']}] {error_msg}"
                    failure.append(msg)
            except requests.RequestException as err:
                msg = f"[{forum['forum_name']}] 签到异常\n{err}"
                failure.append(msg)
    success_count = len(success)
    failure_count = len(failure)
    logging.info("签到成功列表:")
    for msg in success:
        logging.info(msg)
    logging.info("签到失败列表:")
    for msg in failure:
        logging.info(msg)
    # 调用Bark_notification函数推送信息到手机
    bark_notification(total_forum, success_count, failure_count)


# Bark推送信息到手机
def bark_notification(total_forum, success_count, failure_count):
    title = '贴吧签到结果'
    message = f"签到{total_forum}个，成功{success_count}个，失败{failure_count}个！\n🎉恭喜，所有贴吧签到成功！！"
    params = {
        'title': title,
        'body': message
    }
    requests.get(bark_url, params=params)


# 从环境变量中获取参数
bduss = os.environ['BDUSS']
bark_url = os.environ['BARK_URL']


# 运行脚本
tieba_sign_in()
