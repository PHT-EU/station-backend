# This is only a test file to test with a simple endpoint later files will be storde and load from minIO

import os
import random
import string


def generate_random_text_file(filename, size):
    """
    generate a random letters and write them to file
    :param filename: the filename
    :param size: the size in bytes
    :return: void
    """
    print("Generating file...")
    chars = ''.join([random.choice(string.ascii_letters) for i in range(size)])
    with open("/opt/pht_results/test_result.txt", 'w') as file:
        file.write(chars)


if __name__ == '__main__':
    # 20 mb
    FILE_SIZE = 1024 * 1024 * 20
    RESULTS_DIR = "/opt/pht_results"
    FILE_NAME = "test_result.txt"
    print(f"Generating a new random file: Size={FILE_SIZE}b")

    generate_random_text_file(os.path.abspath(os.path.join(RESULTS_DIR, FILE_NAME)), FILE_SIZE)
    with open(os.path.join(RESULTS_DIR, FILE_NAME), "r") as f:
        print(f.read(200))
    print("File Generated Successfully")