import torch

from ..modules.text_grounding_net import UniFusion


def get_positionnet_default_params():
    return {
        "in_dim": 768,
        "mid_dim": 3072,
        "out_dim": 768,
        "test_drop_boxes": False,
        "test_drop_masks": True,
        "test_drop_points": False,
        "test_drop_scribbles": True,
        "train_add_boxes": True,
        "train_add_masks": True,
        "train_add_points": True,
        "train_add_scribbles": True,
        "use_seperate_tokenizer": True,
    }


def prepare_positionnet(checkpoint, params) -> torch.nn.Module:
    model = UniFusion(**params)
    model.load_state_dict(checkpoint, strict=False)
    return model
