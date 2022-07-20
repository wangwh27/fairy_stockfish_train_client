import sys
import os
import time
import subprocess
import multiprocessing as mp

FILE_NAME = "xiangqi.bin"
params = f"""
setoption name UCI_Variant value xiangqi
setoption name Use NNUE value pure
setoption name EvalFile value ./xiangqi-weights.nnue
setoption name Threads value [Threads]
setoption name Hash value 1024
generate_training_data depth 9 count 10000 random_multi_pv 4 random_multi_pv_diff 100 random_move_count 8 random_move_max_ply 20 write_min_ply 5 eval_limit 10000 set_recommended_uci_options data_format bin output_file_name {FILE_NAME}
"""


def generate_data(threads=-1):
    if threads < 1:
        threads = mp.cpu_count()
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
    while os.path.exists(FILE_NAME):
        time.sleep(0.1)
    exe_file = "fairy.exe" if os.name == "nt" else "./fairy"
    if os.name != "nt":
        os.system("chmod +x " + exe_file)
    fairy = subprocess.Popen([exe_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tmp_params = params.replace("[Threads]", str(threads))
    fairy.stdin.write(tmp_params.encode())
    fairy.stdin.flush()
    output = fairy.stdout.readline()
    while output:
        output = output.decode("utf-8").replace("\r\n", "")
        if "sfen" in output or "evaluation" in output:
            print(output)
        if "finished" in output:
            print(output)
            time.sleep(1)
            fairy.terminate()
            break
        output = fairy.stdout.readline()
    while not os.path.exists(FILE_NAME):
        time.sleep(0.1)


if __name__ == "__main__":
    generate_data()