import random
import numpy as np
import cv2 as cv
import time
import psutil
import threading
import json

from helpers.utils import image_reshape


def cgne(matrix_type, signal_type, user, algorithm):
    global max_cpu_usage
    global v
    start_time = time.time()

    model_path = "model_2"
    if matrix_type == "1":
        model_path = "model_1"
    # r0=g−Hf0
    file = open(f'./input/{model_path}/{signal_type}.csv', 'rb')
    entry_sign = np.loadtxt(file, delimiter=',')
    matrix = open(f'./input/{model_path}/H.csv', 'rb')
    matrix = np.loadtxt(matrix, delimiter=',')

    # p0=HTr0
    p = np.matmul(matrix.T, entry_sign)

    # f0=0
    image = np.zeros_like(len(p))

    count = 1
    error = 0
    while error < float(1e10 ** (-4)):
        # αi=rTiripTipi
        alpha = np.dot(entry_sign.T, entry_sign) / np.dot(p.T, p)

        # fi+1=fi+αipi
        image = image + alpha * p.T

        # ri+1=ri−αiHpi
        ri = entry_sign - alpha * np.dot(matrix, p)

        # ϵ=||ri+1||2−||ri||2
        error += np.linalg.norm(entry_sign, ord=2) - np.linalg.norm(ri, ord=2)
        if error < 1e10 - 4:
            break

        # βi=rTi+1ri+1rTiri
        beta = np.dot(entry_sign.T, ri) / np.dot(ri.T, entry_sign)

        # pi+1=HTri+1+βipi
        p = np.dot(matrix.T, ri) + beta * p

        count += 1

    v = False
    time.sleep(0.25)

    image = image_reshape(image, matrix_type)
    process = psutil.Process()
    memory = process.memory_info().rss / 1000000
    run_time = time.time() - start_time

    data = {
        "userName": user,
        "iterations": count,
        "runTime": run_time,
        "error": error,
        "memory": memory,
        "signType": signal_type,
        "algorithm": algorithm,
        "cpu": max_cpu_usage,
    }
    print(data)

    filename = './results/report_cgne.json'
    listObj = []

    # Read JSON file
    with open(filename) as fp:
        listObj = json.load(fp)

    listObj.append(data)

    with open(filename, 'w') as json_file:
        json.dump(listObj, json_file,
                  indent=4,
                  separators=(',', ': '))

    memory = process.memory_info().rss / 1000000

    # # Salvar imagem localmente
    final = cv.resize(image, None, fx=10, fy=10, interpolation=cv.INTER_AREA)
    cv.imwrite('./results/cgne_result.png', final)


def cgnr(matrix_type, signal_type, user, algorithm):
    global max_cpu_usage
    global v
    start_time = time.time()
    model_path = "model_2"
    if matrix_type == "1":
        model_path = "model_1"
    file = open(f'./input/{model_path}/{signal_type}.csv', 'rb')
    entry_sign = np.loadtxt(file, delimiter=',')
    matrix = open(f'./input/{model_path}/H.csv', 'rb')
    matrix = np.loadtxt(matrix, delimiter=',')

    # z0=HTr0
    p = np.matmul(matrix.T, entry_sign)
    z = p

    # f0=0
    image = np.zeros_like(len(p))

    count = 1
    erro = 0
    while erro < 1e10 ** (-4):
        print("foi no cgnr linha 177")

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
        erro = np.linalg.norm(ri, ord=2) - np.linalg.norm(entry_sign, ord=2)
        if erro < 1e10 ** (-4):
            break

        count += 1

    image = image_reshape(image, matrix_type)
    process = psutil.Process()
    memory = process.memory_info().rss / 1000000
    run_time = time.time() - start_time

    v = False

    time.sleep(0.2)

    data = {
        "userName": user,
        "iterations": count,
        "runTime": run_time,
        "error": erro,
        "memory": memory,
        "signType": signal_type,
        "algorithm": algorithm,
        "cpu": max_cpu_usage,
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
                  separators=(',', ': '))

    process.memory_info().rss / 1000000
    final = cv.resize(image, None, fx=10, fy=10, interpolation=cv.INTER_AREA)
    cv.imwrite('./results/cgnr_result.png', final)


def main():
    t = threading.Thread(target=monitor_cpu_usage)
    t.start()

    algorithms = ['cgne', 'cgnr']
    algorithm = random.choice(algorithms)
    matrixes = ['1', '2']
    matrix_type = random.choice(matrixes)
    signals = ['G-1', 'G-2', 'G-3']
    signal_type = random.choice(signals)
    users = ['user a', 'user b', 'user c']
    user = random.choice(users)
    if algorithm == 'cgne':
        t2 = threading.Thread(target=cgne, args=(matrix_type, signal_type, user, algorithm))
        t2.start()
    else:
        t2 = threading.Thread(target=cgnr, args=(matrix_type, signal_type, user, algorithm))
        t2.start()
    t2.join()
    t.join()


def monitor_cpu_usage():
    global v
    global max_cpu_usage

    v = True
    max_cpu_usage = 0

    cpu_usage_list_by_second = []
    while v:
        cpu_usage_list_by_second.append(psutil.cpu_percent(interval=0.25))
    max_cpu_usage = max(cpu_usage_list_by_second)


if __name__ == '__main__':
    main()
