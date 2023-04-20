from typing import Tuple, Type
from SequentialSentenceClassifier import SequentialSentenceClassifier
from data import MyDataset, get_SWDA, get_DYDA
from nets import (
    Net,
    Params,
    # HierarchicalDialogueActClassifier,
    # SequentialSentenceClassifier,
)
from handlers import DialogueDataset
from query_strategies.strategy import Strategy
from torch.utils.data import Dataset
from query_strategies import (
    RandomSampling,
    MaxTurnUncertainty,
    MinTurnUncertainty,
    AverageTurnUncertainty,
    MedianTurnUncertainty,
)


params: Params = {
    "SWDA": {
        "n_labels": 46,
        "model_name": "distilbert-base-cased",
        "max_turn_length": 80,
        "train_args": {"batch_size": 1, "num_workers": 0},
        "test_args": {"batch_size": 1, "num_workers": 0},
        "optimizer_args": {"lr": 1e-5},
    },
    "DYDA": {
        "n_labels": 4,
        "model_name": "distilbert-base-cased",
        "max_turn_length": 512,
        "train_args": {"batch_size": 1, "num_workers": 0},
        "test_args": {"batch_size": 1, "num_workers": 0},
        "optimizer_args": {"lr": 1e-5},
    },
}


def get_handler(name: str) -> Type[Dataset]:
    if name == "SWDA":
        return DialogueDataset
    if name == "DYDA":
        return DialogueDataset
    else:
        raise NotImplementedError


def get_dataset(
    name: str,
) -> Tuple[MyDataset, MyDataset]:
    if name == "SWDA":
        return get_SWDA()
    elif name == "DYDA":
        return get_DYDA()
    else:
        raise NotImplementedError


def get_net(name: str, device: str, n_epoch: int) -> Net:
    if name == "SWDA":
        return Net(SequentialSentenceClassifier, params[name], device, n_epoch)
    elif name == "DYDA":
        return Net(SequentialSentenceClassifier, params[name], device, n_epoch)
    else:
        raise NotImplementedError


def get_params(name: str) -> "dict[str, object]":
    return params[name]


def get_strategy(name: str) -> Type[Strategy]:
    if name == "RandomSampling":
        return RandomSampling
    elif name == "MaxTurnUncertainty":
        return MaxTurnUncertainty
    elif name == "MinTurnUncertainty":
        return MinTurnUncertainty
    elif name == "AverageTurnUncertainty":
        return AverageTurnUncertainty
    elif name == "MedianTurnUncertainty":
        return MedianTurnUncertainty
    # elif name == "MarginSampling":
    #     return MarginSampling
    # elif name == "EntropySampling":
    #     return EntropySampling
    # elif name == "LeastConfidenceDropout":
    #     return LeastConfidenceDropout
    # elif name == "MarginSamplingDropout":
    #     return MarginSamplingDropout
    # elif name == "EntropySamplingDropout":
    #     return EntropySamplingDropout
    # elif name == "KMeansSampling":
    #     return KMeansSampling
    # elif name == "KCenterGreedy":
    #     return KCenterGreedy
    # elif name == "BALDDropout":
    #     return BALDDropout
    # elif name == "AdversarialBIM":
    #     return AdversarialBIM
    # elif name == "AdversarialDeepFool":
    #     return AdversarialDeepFool
    else:
        raise NotImplementedError
