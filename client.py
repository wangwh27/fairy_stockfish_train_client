import os
import sys
import threading
import random
import traceback

import client_helper
import time
import fairy
import argparse

FILE_NAME = "xiangqi.bin"
program_version = "1.0"
model_version = -1
Debug = False
parser = argparse.ArgumentParser(description="分布式生成棋谱")
parser.add_argument("--user", default="VinXiangQi", type=str, help="用于统计训练量的用户名")
parser.add_argument("--threads", default=-1, type=int, help="用于跑谱的核心数")
Args = parser.parse_args()


def check_update():
    info = client_helper.get_model_info()
    while info is None:
        print("获取模型版本失败")
        time.sleep(1)
        info = client_helper.get_model_info()
    print(info)
    update_model(info["weight_version"], info["urls"])


def update_model(ver, urls):
    global model_version
    if Debug:
        return
    if ver != model_version:
        print(f"发现新模型: {ver}")
        url = random.choice(urls)
        st = time.time()
        client_helper.download_file(url, "xiangqi-weights.nnue")
        model_version = ver
        print(f"更新模型成功！耗时: {round(time.time() - st, 1)}s")


if __name__ == "__main__":
    print("-----------------------------------")
    print(f"----- 以 {Args.user} 身份进行训练 -----")
    print("-----------------------------------")
    check_update()
    while True:
        try:
            print("开始生成棋谱，该过程耗时较长，请耐心等待……")
            fairy.generate_data(Args.threads)
            if not os.path.exists(FILE_NAME):
                print("棋谱文件不存在，上传失败！")
                time.sleep(1)
                continue
            with open(FILE_NAME, "rb") as f:
                result = client_helper.upload_data(f.read(), model_version, Args.user)
            update_model(result[0], result[1])
        except Exception as ex:
            print(repr(ex))
            traceback.print_exc()
        time.sleep(0.1)