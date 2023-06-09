import os
from typing import List, Tuple, Type, TypedDict
import numpy as np
from torch.utils.data import Dataset
from datasets import load_dataset, load_from_disk, DatasetDict, Dataset as HF_Dataset
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


class Metrics(TypedDict):
    accuracy: float
    f1: float
    precision: float
    recall: float


MyDataset = Tuple[List[List[str]], List[List[int]]]


class Data:
    def __init__(
        self,
        train: MyDataset,
        test: MyDataset,
        handler: Type[Dataset],
    ):
        self.train = train
        self.test = test
        self.handler = handler
        self.n_pool = len(train[1])
        self.n_test = len(test[1])

        self.labeled_idxs: np.ndarray = np.zeros(self.n_pool, dtype=bool)

    def initialize_labels(self, num: int) -> None:
        # generate initial labeled pool
        tmp_idxs: np.ndarray = np.arange(self.n_pool)
        np.random.shuffle(tmp_idxs)
        self.labeled_idxs[tmp_idxs[:num]] = True

    def get_labeled_data(self) -> Tuple[np.ndarray, Dataset]:
        labeled_idxs: np.ndarray = np.arange(self.n_pool)[self.labeled_idxs]
        indexed: MyDataset = (
            [self.train[0][i] for i in labeled_idxs],
            [self.train[1][i] for i in labeled_idxs],
        )
        return labeled_idxs, self.handler(indexed)

    def get_unlabeled_data(self) -> Tuple[np.ndarray, Dataset]:
        unlabeled_idxs = np.arange(self.n_pool)[~self.labeled_idxs]
        indexed: MyDataset = (
            [self.train[0][i] for i in unlabeled_idxs],
            [self.train[1][i] for i in unlabeled_idxs],
        )
        return unlabeled_idxs, self.handler(indexed)

    def get_train_data(self) -> Tuple[np.ndarray, Dataset]:
        return self.labeled_idxs.copy(), self.handler(self.train)

    def get_test_data(self) -> Dataset:
        return self.handler(self.test)

    def cal_test_metrics(self, preds: np.ndarray) -> Metrics:
        y_true = np.concatenate(self.test[1])
        y_pred = preds

        metrics = classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        )
        # also print the metrics
        print(classification_report(y_true, y_pred, zero_division=0))

        return {
            "accuracy": metrics["accuracy"],
            "f1": metrics["macro avg"]["f1-score"],
            "recall": metrics["macro avg"]["recall"],
            "precision": metrics["macro avg"]["precision"],
        }


def convert(
    dataset: HF_Dataset, x="Utterance", y="Label", group="Dialogue_ID"
) -> MyDataset:
    def process_group(group):
        group_df = pd.DataFrame(group[1])
        total_length = group_df[x].str.len().sum() / 4
        if total_length > 4000:
            print(f"skipped dialogue: {group[0]}")
            return None
        turns = group_df[x].tolist()
        labels = group_df[y].tolist()

        # Add [ACTOR1] and [ACTOR2] tags to the turns
        tagged_turns = []
        for i, turn in enumerate(turns):
            if i % 2 == 0:  # Even turn indices correspond to the first speaker
                tagged_turns.append("[ACTOR1] " + turn)
            else:  # Odd turn indices correspond to the second speaker
                tagged_turns.append("[ACTOR2] " + turn)

        return tagged_turns, labels

    if not isinstance(dataset, pd.DataFrame):
        df = dataset.to_pandas()
    else:
        df = dataset
    grouped = df.groupby(group)
    results = list(map(process_group, grouped))
    all_turns, all_labels = zip(*[r for r in results if r is not None])
    all_turns = list(all_turns)
    all_labels = list(all_labels)
    return all_turns, all_labels


def get_silicone_dataset(dataset_name: str):
    main_dataset_name = "silicone"
    dataset_dir = f"data/{dataset_name}"

    # Load the dataset
    if os.path.exists(dataset_dir):
        # load the dataset from disk
        dataset = load_from_disk(dataset_dir)
        print("Dataset loaded from disk")
    else:
        # load the dataset from Hugging Face and save it to disk
        dataset = load_dataset(main_dataset_name, dataset_name)
        dataset.save_to_disk(dataset_dir)
        print("Dataset loaded from Hugging Face and saved to disk")

    train = convert(dataset["train"])
    test = convert(dataset["test"])
    return train, test


def get_KPN() -> Tuple[MyDataset, MyDataset]:
    def convert(dataset: HF_Dataset) -> MyDataset:
        return dataset["text"], dataset["label"]

    dataset_name = "kpn"
    dataset_dir = f"data/{dataset_name}"

    # Load the dataset
    if os.path.exists(dataset_dir):
        # load the dataset from disk
        dataset = load_from_disk(dataset_dir)
        print("Dataset loaded from disk")
    else:
        print("Need the kpn dataset to exist")
        return None

    train = convert(dataset["train"])
    test = convert(dataset["test"])
    return train, test


def get_SWDA() -> Tuple[MyDataset, MyDataset]:
    return get_silicone_dataset("swda")


def get_DYDA() -> Tuple[MyDataset, MyDataset]:
    return get_silicone_dataset("dyda_da")


def convert_kpn_data():
    # read the csv
    df = pd.read_csv("kpn.csv", index_col=0)

    # remove the index
    df = df.reset_index(drop=True)

    # drop the unnecessary columns
    df = df.drop(columns=["segments"])

    # remove the brackets from the dialogue acts
    df["dialogue_acts"] = df["dialogue_acts"].apply(lambda x: x.strip("[]"))

    # encode the labels
    le = LabelEncoder()
    df["label"] = le.fit_transform(df["dialogue_acts"])

    print(le.classes_)

    # sort the turns by turn order
    df = (
        df.groupby("conversation_id", group_keys=True)
        .apply(lambda x: x.sort_values(by=["order"]))
        .reset_index(drop=True)
    )

    # create the nested structure
    df = df.groupby("conversation_id").agg(list)

    # remove the conversations with more than 4000 tokens
    total_length = lambda text_list: sum([len(text) for text in text_list])
    df = df[df["text"].apply(total_length) / 4 < 4000]

    # split the data into train and test
    train_data, test_data = train_test_split(df, test_size=0.1, random_state=42)
    print(train_data.shape, test_data.shape)

    # create the dataset dict
    train_dataset = HF_Dataset.from_pandas(train_data)
    test_dataset = HF_Dataset.from_pandas(test_data)
    dataset_dict = DatasetDict({"train": train_dataset, "test": test_dataset})

    os.makedirs("data/kpn", exist_ok=True)
    dataset_dict.save_to_disk("data/kpn")
