"""Compatibility wrapper to eliminate deprecation warning for weight_norm.

Torch >=2.4 deprecates torch.nn.utils.weight_norm in favor of
torch.nn.utils.parametrizations.weight_norm. We centralize the logic
here so the rest of the code keeps a stable API without warnings.
"""
from __future__ import annotations

import warnings

try:  # Preferred new API
    from torch.nn.utils.parametrizations import weight_norm as _new_weight_norm
    from torch.nn.utils.parametrize import remove_parametrizations as _remove_parametrizations
    _USE_NEW = True
except Exception:  # Fallback to legacy
    from torch.nn.utils import weight_norm as _old_weight_norm  # type: ignore
    from torch.nn.utils import remove_weight_norm as _old_remove_weight_norm  # type: ignore
    _USE_NEW = False

__all__ = ["weight_norm", "remove_weight_norm"]


def weight_norm(module, name: str = "weight", dim: int = 0):  # noqa: D401
    """Apply weight norm without emitting future deprecation warnings."""
    if _USE_NEW:
        return _new_weight_norm(module, name=name, dim=dim)
    # Suppress single deprecation warning if still on legacy path
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        return _old_weight_norm(module, name=name, dim=dim)  # type: ignore


def remove_weight_norm(module, name: str = "weight"):
    """Remove weight norm regardless of API generation."""
    if _USE_NEW:
        # If parametrization exists, remove it; ignore if already removed
        try:
            _remove_parametrizations(module, name, leave_parametrized=False)
        except Exception:
            pass
    else:
        try:  # type: ignore
            _old_remove_weight_norm(module, name)
        except Exception:
            pass
    return module
