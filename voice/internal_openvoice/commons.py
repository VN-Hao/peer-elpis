# Vendored from OpenVoice (MIT License) with minimal adjustments.
from __future__ import annotations
import math
import torch
from torch.nn import functional as F

__all__ = [
    'init_weights','get_padding','convert_pad_shape','intersperse','sequence_mask',
    'generate_path','fused_add_tanh_sigmoid_multiply'
]

def init_weights(m, mean=0.0, std=0.01):
    if m.__class__.__name__.find('Conv') != -1:
        m.weight.data.normal_(mean, std)

def get_padding(kernel_size, dilation=1):
    return int((kernel_size * dilation - dilation) / 2)

def convert_pad_shape(pad_shape):
    layer = pad_shape[::-1]
    return [item for sub in layer for item in sub]

def intersperse(lst, item):
    result = [item] * (len(lst) * 2 + 1)
    result[1::2] = lst
    return result

def sequence_mask(length, max_length=None):
    if max_length is None:
        max_length = length.max()
    x = torch.arange(max_length, dtype=length.dtype, device=length.device)
    return x.unsqueeze(0) < length.unsqueeze(1)

def generate_path(duration, mask):
    """Upstream OpenVoice duration path construction.

    Args:
        duration: Tensor (B, 1, Tx)
        mask: Tensor (B, 1, Ty, Tx)
    Returns:
        path: (B, 1, Ty, Tx)
    """
    b, _, t_y, t_x = mask.shape
    cum_duration = torch.cumsum(duration, -1)
    cum_duration_flat = cum_duration.view(b * t_x)
    path = sequence_mask(cum_duration_flat, t_y).to(mask.dtype)
    path = path.view(b, t_x, t_y)
    path = path - F.pad(path, convert_pad_shape([[0,0],[1,0],[0,0]]))[:, :-1]
    path = path.unsqueeze(1).transpose(2, 3) * mask
    return path

@torch.jit.script
def fused_add_tanh_sigmoid_multiply(input_a, input_b, n_channels):
    n_channels_int = n_channels[0]
    in_act = input_a + input_b
    t_act = torch.tanh(in_act[:, :n_channels_int, :])
    s_act = torch.sigmoid(in_act[:, n_channels_int:, :])
    return t_act * s_act
