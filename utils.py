from typing import Tuple, Type
from SequentialSentenceClassifier import SequentialSentenceClassifier
from data import Data, MyDataset, get_KPN, get_SWDA, get_DYDA
from nets import Net, Params
from handlers import DialogueDataset
from query_strategies.strategy import Strategy
from torch.utils.data import Dataset
from query_strategies import (
    RandomSampling,
    TurnUncertainty,
    TotalTurnUncertainty,
    TurnEntropy,
    TotalTurnEntropy,
)


default_params: Params = {
    "SWDA": {
        "n_labels": 46,
        "model_name": "allenai/longformer-base-4096",
        "turn_length": 80,
        "train_args": {"batch_size": 1, "num_workers": 0},
        "test_args": {"batch_size": 1, "num_workers": 0},
        "optimizer_args": {"lr": 1e-5},
    },
    "DYDA": {
        "n_labels": 4,
        "model_name": "allenai/longformer-base-4096",
        "turn_length": 120,
        "train_args": {"batch_size": 1, "num_workers": 0},
        "test_args": {"batch_size": 1, "num_workers": 0},
        "optimizer_args": {"lr": 1e-5},
    },
    "KPN": {
        "n_labels": 19,
        "model_name": "allenai/longformer-base-4096",
        "turn_length": 224,
        "train_args": {"batch_size": 1, "num_workers": 0},
        "test_args": {"batch_size": 1, "num_workers": 0},
        "optimizer_args": {"lr": 1e-5},
    },
}


def get_handler(name: str) -> Type[Dataset]:
    return DialogueDataset


def get_dataset(
    name: str,
) -> Tuple[MyDataset, MyDataset]:
    if name == "SWDA":
        return get_SWDA()
    elif name == "DYDA":
        return get_DYDA()
    elif name == "KPN":
        return get_KPN()
    else:
        raise NotImplementedError


def get_net(name: str, device: str, n_epoch: int, params: Params = None) -> Net:
    if params == None:
        params = default_params

    return Net(SequentialSentenceClassifier, params[name], device, n_epoch)


def get_strategy(
    name: str,
    dataset: Data,
    net: Net,
    clipping: int,
) -> Type[Strategy]:
    if name == "RandomSampling":
        return RandomSampling(dataset, net)
    elif name == "TurnUncertainty":
        return TurnUncertainty(dataset, net, clipping)
    elif name == "TotalTurnUncertainty":
        return TotalTurnUncertainty(dataset, net, clipping)
    elif name == "TurnEntropy":
        return TurnEntropy(dataset, net, clipping)
    elif name == "TotalTurnEntropy":
        return TotalTurnEntropy(dataset, net, clipping)
    else:
        raise NotImplementedError
