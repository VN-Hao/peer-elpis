"""
Text encoding module for OpenVoice.
"""

import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from .commons import init_weights

class TextEncoder(nn.Module):
    def __init__(self,
                n_vocab,
                out_channels,
                hidden_channels,
                filter_channels,
                n_heads,
                n_layers,
                kernel_size,
                p_dropout):
        super().__init__()
        self.n_vocab = n_vocab
        self.out_channels = out_channels
        self.hidden_channels = hidden_channels
        self.filter_channels = filter_channels
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.kernel_size = kernel_size
        self.p_dropout = p_dropout

        # Initialize embedding with proper dimensions
        self.emb = nn.Embedding(n_vocab, hidden_channels)
        init_weights(self.emb, mean=0.0, std=hidden_channels**-0.5)  # Use our init_weights

        self.encoder = Encoder(
            hidden_channels,
            filter_channels,
            n_heads,
            n_layers,
            kernel_size,
            p_dropout)
        self.proj = nn.Conv1d(hidden_channels, out_channels * 2, 1)

    def forward(self, x, x_lengths=None):
        if x_lengths is None:
            x_lengths = torch.LongTensor([x.size(1)]).to(x.device)
            
        x = self.emb(x) * math.sqrt(self.hidden_channels)  # [b, t, h]
        x = torch.transpose(x, 1, -1)  # [b, h, t]
        x_mask = torch.unsqueeze(sequence_mask(x_lengths, x.size(2)), 1).to(x.dtype)
        
        x = self.encoder(x * x_mask, x_mask)
        stats = self.proj(x) * x_mask
        
        m, logs = torch.split(stats, self.out_channels, dim=1)
        return x, m, logs, x_mask


def sequence_mask(lengths, maxlen):
    """Create sequence mask tensor."""
    batch_size = lengths.shape[0]
    seq_range = torch.arange(0, maxlen).to(lengths.device)
    seq_range_expand = seq_range.unsqueeze(0).expand(batch_size, maxlen)
    seq_length_expand = lengths.unsqueeze(-1)
    return (seq_range_expand < seq_length_expand).to(lengths.dtype)
