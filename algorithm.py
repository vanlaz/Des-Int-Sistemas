import json
import random
import time

import numpy as np
import psutil
import threading
import cv2 as cv

from helpers.utils import image_reshape, processing_requirements


def export_results(image, matrix_type, start_time, user, count, abs_error, signal_type, algorithm, req_count):
    image = image_reshape(image, matrix_type)
    process = psutil.Process()
    run_time = time.time() - start_time

    v = False

    time.sleep(0.2)

    data = {
        "userName": user,
        "iterations": count,
        "runTime": run_time,
        "error": abs_error,
        "matrix": matrix_type,
        "signType": signal_type,
        "algorithm": algorithm,
        "cpu (%)": avr_cpu_usage,
        "ram_usage (GB)": avr_ram_usage,
        "ram_available (GB)": avr_ram_available
    }
    print(f'Result: `{data}')
    print(algorithm)
    filename = f'./results/report_{algorithm}.json'
    listObj = []

    #read json file
    with open(filename) as fp:
        listObj = json.load(fp)

    #add data to json file
    listObj.append(data)

    with open(filename, 'w') as json_file:
        json.dump(listObj, json_file,
                  indent=4,
                  separators=(',', ': '))

    final = cv.resize(image, None, fx=10, fy=10, interpolation=cv.INTER_AREA)
    cv.imwrite(f'./results/{algorithm}_result_{req_count}.png', final)

def cgne(matrix_type, signal_type, user, algorithm, req_count):
    global avr_cpu_usage
    global avr_ram_available
    global avr_ram_used
    global v
    start_time = time.time()

    entry_sign, matrix = processing_requirements(matrix_type, signal_type)

    # p0=HTr0
    p = np.matmul(matrix.T, entry_sign)

    # f0=0
    image = np.zeros_like(len(p))

    count = 1   

    while True:
        print(f"[Iteração {count}]")
        print("executando CGNE")
        # αi=rTiripTipi
        alpha = np.dot(entry_sign.T, entry_sign) / np.dot(p.T, p)

        # fi+1=fi+αipi
        image = image + alpha * p.T

        # ri+1=ri−αiHpi
        ri = entry_sign - alpha * np.dot(matrix, p)

        # ϵ=||ri+1||2−||ri||2
        error = np.linalg.norm(entry_sign, ord=2) - np.linalg.norm(ri, ord=2)
        
        abs_error = abs(error)
        
        if abs_error < 1e-4 or count > 100:
            break

        # βi=rTi+1ri+1rTiri
        beta = np.dot(entry_sign.T, ri) / np.dot(ri.T, entry_sign)

        # pi+1=HTri+1+βipi
        p = np.dot(matrix.T, ri) + beta * p

        count += 1

    v = False
    time.sleep(0.25)

    export_results(image, matrix_type, start_time, user, count, abs_error, signal_type, algorithm, req_count)

def cgnr(matrix_type, signal_type, user, algorithm, req_count):
    global avr_cpu_usage
    global avr_ram_usage
    global avr_ram_available
    global v
    start_time = time.time()

    entry_sign, matrix = processing_requirements(matrix_type, signal_type)

    # z0=HTr0
    p = np.matmul(matrix.T, entry_sign)
    z = p

    # f0=0
    image = np.zeros_like(len(p))

    count = 1
    
    while True:
        
        print(f"[Iteração {count}]")
        print("executando CGNR")

        # wi=Hpi
        w = np.matmul(matrix, p)

        # αi=||zi||22/||wi||22
        alpha = np.linalg.norm(z, ord=2) ** 2 / np.linalg.norm(w, ord=2) ** 2

        # fi+1=fi+αipi
        image = image + alpha * p.T

        # ri+1=ri−αiwi
        ri = entry_sign - alpha * w

        # zi+1=HTri+1
        z = np.matmul(matrix.T, ri)

        # βi=||zi+1||22/||zi||22
        beta = np.linalg.norm(z, ord=2) ** 2 / np.linalg.norm(z, ord=2) ** 2

        # pi+1=zi+1+βipi
        p = z + beta * p

        # ϵ=||ri+1||2−||ri||2
        error = np.linalg.norm(ri, ord=2) - np.linalg.norm(entry_sign, ord=2)
       
        abs_error = abs(error)
        if abs_error < 1e-4 or count > 100 :
            break

        count += 1

    image = image_reshape(image, matrix_type)
    process = psutil.Process()
    run_time = round(time.time() - start_time, 2)

    v = False

    time.sleep(0.2)

    data = {
        "userName": user,
        "iterations": count,
        "runTime": run_time,
        "error": abs_error,
        "matrix": matrix_type,
        "signType": signal_type,
        "algorithm": algorithm,
        "cpu (%)": avr_cpu_usage,
        "ram_usage (GB)": avr_ram_usage,
        "ram_available (GB)": avr_ram_available
    }
    print(data)
    filename = './results/report_cgnr.json'
    listObj = []

    # Read JSON file
    with open(filename) as fp:
        listObj = json.load(fp)


    listObj.append(data)

    with open(filename, 'w') as json_file:
        json.dump(listObj, json_file, 
                            indent=4,  
                            separators=(',',': '))

    final = cv.resize(image, None, fx=10, fy=10, interpolation=cv.INTER_AREA)
    cv.imwrite(f'./results/cgnr_result_{req_count}.png', final)


def monitor_cpu_usage():
    global v
    global avr_cpu_usage

    v = True
    avr_cpu_usage = 0


    cpu_usage_list_by_second = []
    while v:
        cpu_usage_list_by_second.append(psutil.cpu_percent(interval=0.25))
    avr_cpu_usage = np.round(np.average(cpu_usage_list_by_second), 2)

def ram_usage():
    global v
    global avr_ram_available
    global avr_ram_usage

    v = True
    avr_ram_usage = 0
    avr_ram_available = 0

    ram_available_list_by_second = []
    ram_usage_list_by_second = []

    while v:
        ram_available_list_by_second.append(psutil.virtual_memory().available)
        ram_usage_list_by_second.append(psutil.virtual_memory().used)

    avr_ram_available = np.round(np.average(ram_available_list_by_second) / (1024.0 ** 3), 2)
    avr_ram_usage = np.round(np.average(ram_usage_list_by_second) / (1024.0 ** 3), 2)

def execute_algorithm(random_params):
    thread_cpu = threading.Thread(target=monitor_cpu_usage)
    thread_cpu.start()

    thread_ram = threading.Thread(target=ram_usage)
    thread_ram.start()

    args = (
                random_params["matrix_type"], 
                random_params["signal_type"], 
                random_params["user"], 
                random_params["algorithm"], 
                random_params["req_count"]
            )

    if random_params["algorithm"] == 'cgne':
        thread_alg = threading.Thread(
            target=cgne, 
            args=(args))
        thread_alg.start()
    else:
        thread_alg = threading.Thread(
            target=cgnr, 
            args=(args))

        thread_alg.start()

    thread_alg.join()
    thread_cpu.join()
    thread_ram.join()


if __name__ == '__main__':
    execute_algorithm()
