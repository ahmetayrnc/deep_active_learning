import argparse
import numpy as np
import torch
from data import Data
from utils import get_dataset, get_handler, get_net
from pprint import pprint
import os
import pandas as pd
from transformers import logging as transformers_logging


def main(args: dict) -> pd.DataFrame:
    # set environment variable to disable parallelism in tokenizers
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # disable transformers warnings
    transformers_logging.set_verbosity_error()

    # fix random seed
    np.random.seed(args["seed"])
    torch.manual_seed(args["seed"])
    torch.backends.cudnn.enabled = False

    # device
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    print(f"Running experiments on: {device}")

    # load dataset
    print("Loading dataset...")
    train, test = get_dataset(args["dataset_name"])
    number_of_samples = int(len(train[0]) * args["fraction"])
    print(f"Number of samples to train on: {number_of_samples}")
    train = train[0][:number_of_samples], train[1][:number_of_samples]
    handler = get_handler(args["dataset_name"])
    dataset = Data(train, test, handler)
    print(f"Dataset loaded.")

    # load network
    print("Loading network...")
    net = get_net(args["dataset_name"], device, args["n_epoch"])  # load network
    print(f"Network loaded.")

    def epoch_metrics():
        y_pred = net.predict(dataset.get_test_data())
        _ = dataset.cal_test_metrics(y_pred)

    # train network
    _, train_data = dataset.get_train_data()
    net.train(train_data, epoch_callback=epoch_metrics)


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1, help="random seed")
    parser.add_argument(
        "--n_epoch", type=int, default=1, help="number of epochs to train"
    )
    parser.add_argument(
        "--fraction", type=float, default=1.0, help="fraction of samples to train on"
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="SWDA",
        choices=["SWDA"],
        help="dataset to use",
    )

    args = parser.parse_args()
    args_dict = vars(args)
    pprint(args_dict)

    main(args_dict)