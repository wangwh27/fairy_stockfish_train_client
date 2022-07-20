import sys
import torch
import pickle
import requests
import time
import json
import hashlib
import traceback
import gzip
import client
debug = False
HOST = "http://mc.vcccz.com:15001"
if debug:
    HOST = "http://127.0.0.1:5001"


data_total = 0
start_time = time.time()


def upload_data(data, version, user):
    print("正在压缩棋谱，原始大小为", round(len(data) / 1024), "KB")
    data = gzip.compress(data)
    tryCount = 2
    rep = None
    print("正在发送棋谱, 大小为", round(len(data) / 1024), "KB")
    try:
        try:
            upload_start_time = time.time()
            rep = requests.post(HOST + f"/upload_batch?m_ver={version}&p_ver={client.program_version}&user={user}" , files={"file": data}, timeout=90)
            print("上传棋谱耗时", round(time.time() - upload_start_time, 2), "秒")
        except TimeoutError:
            rep = None
            print("传输超时")
        while (rep is None or rep.status_code != 200) and tryCount > 0:
            tryCount -= 1
            print("传输失败，重试中")
            try:
                upload_start_time = time.time()
                rep = requests.post(HOST + f"/upload_batch?m_ver={version}&p_ver={client.program_version}&user={user}" , files={"file": data}, timeout=90)
                print("上传棋谱耗时", round(time.time() - upload_start_time, 2), "秒")
            except TimeoutError:
                rep = None
                print("传输超时")
        if rep is not None and rep.status_code == 200:
            try:
                ret = rep.json()
                print(ret)
                if "server_speed" in ret:
                    print("上传成功，服务器当前速度: %.1f fps" % ret["server_speed"])
                    if "msg" in ret:
                        print(ret["msg"])
                if "model_info" in ret:
                    return ret["model_info"]["weight_version"], ret["model_info"]["urls"]
                else:
                    return -1, []
            except json.JSONDecodeError:
                print("Json Decode Error")
    except Exception as e:
        print("棋谱传送失败:", repr(e))

    return version, ""


def get_model_info():
    try:
        rep = requests.get(HOST + "/model_info")
        info = rep.json()
        return info
    except Exception as e:
        print("获取模型版本失败:", repr(e))
        return None


def download_obj(url):
    req = requests.get(url)
    return req.content


def download_pkl(url):
    try:
        return pickle.loads(download_obj(url))
    except Exception as e:
        print("下载pkl文件失败:", repr(e))
        return None


def download_file(url, save_path):
    data = download_obj(url)
    with open(save_path, "wb") as f:
        f.write(data)