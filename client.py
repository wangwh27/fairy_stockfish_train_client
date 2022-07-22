import os
import shutil
import sys
import threading
import random
import traceback

import client_helper
import time
import fairy
import argparse

FILE_NAME = "xiangqi.bin"
FILE_NAME_UPLOAD = "xiangqi-upload.bin"
program_version = "1.1"
model_version = -1
Debug = False
generate_amount = 10000
parser = argparse.ArgumentParser(description="分布式生成棋谱")
parser.add_argument("--user", default="VinXiangQi", type=str, help="用于统计训练量的用户名")
parser.add_argument("--threads", default=-1, type=int, help="用于跑谱的核心数")
Args = parser.parse_args()
generation_params = {}

param_keys_map = {
    "d": "depth",
    "el": "eval_limit",
    "edl": "eval_diff_limit",
    "rmi": "random_move_min_ply",
    "rma": "random_move_max_ply",
    "rc": "random_move_count",
    "rmp": "random_multi_pv",
    "pdi": "random_multi_pv_diff",
    "pde": "random_multi_pv_depth",
    "wmi": "write_min_ply",
    "wma": "write_max_ply",
}


def params_decompress(params_compressed):
    new_params = {}
    for k, v in params_compressed.items():
        if k in param_keys_map:
            new_params[param_keys_map[k]] = v
        else:
            new_params[k] = v
    return new_params


def check_update():
    global generation_params
    info = client_helper.get_model_info()
    while info is None:
        print("获取模型版本失败")
        time.sleep(1)
        info = client_helper.get_model_info()
    print(info)
    generation_params = params_decompress(info["params"])
    update_book(info["book_urls"])
    update_model(info["weight_version"], info["urls"])


def update_model(ver, urls):
    global model_version
    if Debug:
        return
    if ver != model_version:
        print(f"发现新模型: {ver}")
        if urls is None or len(urls) == 0:
            print("未找到下载地址，更新失败！")
            return
        st = time.time()
        client_helper.download_file_multiurl_retry(urls, "xiangqi-weights.nnue")
        time.sleep(0.2)
        file_size = os.path.getsize("xiangqi-weights.nnue")
        if file_size < 1024 * 1024:
            with open("xiangqi-weights.nnue", "r") as f:
                print(f.read())
            print("文件下载错误！")
        model_version = ver
        print(f"更新模型成功！耗时: {round(time.time() - st, 1)}s")


def update_book(urls):
    if urls is not None and len(urls) > 0:
        print("正在下载开局库")
        st = time.time()
        client_helper.download_file_multiurl_retry(urls, "xiangqi-book.epd")
        print(f"下载成功！耗时: {round(time.time()-st, 1)}s")


def upload_data():
    global generation_params
    with open(FILE_NAME_UPLOAD, "rb") as f:
        result = client_helper.upload_data(f.read(), model_version, Args.user)
        if "params" in result:
            generation_params = params_decompress(result["params"])
    shutil.rmtree(FILE_NAME_UPLOAD, ignore_errors=True)
    update_model(result[0], result[1])


if __name__ == "__main__":
    print("-----------------------------------")
    print(f"----- 以 {Args.user} 身份进行训练 -----")
    print("-----------------------------------")
    check_update()
    while True:
        try:
            print("开始生成棋谱，该过程耗时较长，请耐心等待……")
            start_time = time.time()
            fairy.generate_data(generation_params, threads=Args.threads, amount=generate_amount)
            time_cost = time.time() - start_time
            speed = generate_amount / time_cost
            generate_amount = int(120 * speed)
            generate_amount = (generate_amount // 10000) * 10000
            generate_amount = max(generate_amount, 10000)
            print("生成完成！耗时: {0}s, 下次生成预计生成 {1} 棋谱".format(round(time_cost, 1), generate_amount))
            if not os.path.exists(FILE_NAME):
                print("棋谱文件不存在，上传失败！")
                time.sleep(1)
                continue
            shutil.move(FILE_NAME, FILE_NAME_UPLOAD)
            thread_upload = threading.Thread(target=upload_data)
            thread_upload.setDaemon(True)
            thread_upload.start()
        except Exception as ex:
            print(repr(ex))
            traceback.print_exc()
        time.sleep(0.1)