"""Utility functions for OpenVoice."""

class HParams:
    """Hyperparameters container."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                v = HParams(**v)
            elif isinstance(v, list):
                # Keep lists as they are
                pass
            self[k] = v
        # Ensure critical fields exist with defaults
        if not hasattr(self, 'data'):
            self.data = HParams()
        if not hasattr(self, 'model'):
            self.model = HParams()
        if not hasattr(self, 'symbols'):
            self.symbols = []

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __contains__(self, key):
        return key in self.__dict__

    def __repr__(self):
        return self.__dict__.__repr__()


def get_hparams_from_file(config_path: str) -> HParams:
    """Load hyperparameters from a JSON file."""
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return HParams(**config)
