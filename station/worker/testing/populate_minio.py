import torchvision
import os
import pickle
import numpy as np
from PIL import Image as pimg
from tqdm import tqdm

MINIO_PATH = "../../../data"
CIFAR_PATH = "../../data/cifar10/cifar-10-batches-py"


def load_cifar_10(download=True):
    cifar_path = os.path.join(MINIO_PATH, "cifar10")
    batch_path = os.path.join(cifar_path, "cifar-10-batches-py")

    # Download the torchvision cifar 10 dataset
    if download:
        torchvision.datasets.CIFAR10(cifar_path, download=True)

    # Extract image data and labels from the batches
    extract_cifar_10_batches(batch_path, cifar_path)


def extract_cifar_10_batches(batch_path: str, out_path: str):
    # load metadata
    categories = pickle.load(open(os.path.join(batch_path, "batches.meta"), "rb"))[
        "label_names"
    ]
    # Extract the 5 data batches
    for i in range(5):

        # create directory for batch if it doesn't exist
        if not os.path.isdir(os.path.join(out_path, f"batch_{i + 1}")):
            os.mkdir(os.path.join(out_path, f"batch_{i + 1}"))
        # load batch file
        file = f"data_batch_{i + 1}"
        images, labels, filenames = load_cifar_pickle(batch_path, file)
        # save images as png files
        print(f"Extracting images for batch {i}")
        for j, image in enumerate(tqdm(images)):

            string_label = str(categories[labels[j]])
            # Create class directory if it does not exist
            class_dir = os.path.join(out_path, f"batch_{i + 1}", string_label)
            if not os.path.isdir(class_dir):
                os.mkdir(class_dir)
            outfile = (
                out_path + f"/batch_{i + 1}/" + string_label + "/" + str(filenames[j])
            )
            # Transpose image to fit regular image dimensions
            img_array = image.transpose(1, 2, 0)
            img = pimg.fromarray(img_array, mode="RGB")
            img.save(outfile)


def load_cifar_pickle(path, file):
    f = open(os.path.join(path, file), "rb")
    dict = pickle.load(f, encoding="bytes")
    images = dict[b"data"]
    images = np.reshape(images, (10000, 3, 32, 32))
    labels = np.array(dict[b"labels"])
    filenames = np.array((dict[b"filenames"])).astype("str")
    return images, labels, filenames


if __name__ == "__main__":
    load_cifar_10(download=False)
