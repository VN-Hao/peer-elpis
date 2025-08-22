"""
Attentions module for OpenVoice implementation.
"""

import math
import torch
from torch import nn
from torch.nn import functional as F


class Encoder(nn.Module):
    """Encoder module with multi-head self-attention."""
    
    def __init__(self, hidden_channels, filter_channels, n_heads, n_layers,
                 kernel_size=1, p_dropout=0.0, window_size=None, **kwargs):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.filter_channels = filter_channels
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.kernel_size = kernel_size
        self.p_dropout = p_dropout
        self.window_size = window_size

        self.drop = nn.Dropout(p_dropout)
        self.attn_layers = nn.ModuleList()
        self.norm_layers_1 = nn.ModuleList()
        self.ffn_layers = nn.ModuleList()
        self.norm_layers_2 = nn.ModuleList()
        
        for _ in range(self.n_layers):
            self.attn_layers.append(
                MultiHeadAttention(
                    hidden_channels,
                    hidden_channels,
                    n_heads,
                    window_size=window_size,
                    p_dropout=p_dropout,
                    **kwargs
                )
            )
            self.norm_layers_1.append(LayerNorm(hidden_channels))
            self.ffn_layers.append(
                FFN(
                    hidden_channels,
                    hidden_channels,
                    filter_channels,
                    kernel_size,
                    p_dropout=p_dropout,
                    **kwargs
                )
            )
            self.norm_layers_2.append(LayerNorm(hidden_channels))

    def forward(self, x, x_mask=None):
        """Forward pass of encoder."""
        attn_mask = x_mask
        for i in range(self.n_layers):
            y = self.attn_layers[i](x, x, attn_mask)
            y = self.drop(y)
            x = self.norm_layers_1[i](x + y)

            y = self.ffn_layers[i](x, x_mask)
            y = self.drop(y)
            x = self.norm_layers_2[i](x + y)
        return x


class FFN(nn.Module):
    """Feed-forward network with Conv1d layers."""
    
    def __init__(self, in_channels, out_channels, filter_channels, kernel_size,
                 p_dropout=0.0, activation=None, **kwargs):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.filter_channels = filter_channels
        self.kernel_size = kernel_size
        self.p_dropout = p_dropout
        self.activation = activation

        self.conv_1 = nn.Conv1d(
            in_channels, filter_channels, kernel_size, padding=kernel_size//2
        )
        self.conv_2 = nn.Conv1d(
            filter_channels, out_channels, kernel_size, padding=kernel_size//2
        )
        self.drop = nn.Dropout(p_dropout)

    def forward(self, x, x_mask=None):
        """Forward pass of FFN."""
        x = self.conv_1(x)
        x = torch.relu(x)
        x = self.drop(x)
        x = self.conv_2(x)
        if x_mask is not None:
            x = x * x_mask
        return x


class MultiHeadAttention(nn.Module):
    """Multi-head attention module."""
    
    def __init__(self, channels, out_channels, n_heads, window_size=None,
                 heads_share=True, p_dropout=0.0, proximal_bias=False,
                 proximal_init=False, **kwargs):
        super().__init__()
        self.channels = channels
        self.out_channels = out_channels
        self.n_heads = n_heads
        self.window_size = window_size
        self.heads_share = heads_share
        self.proximal_bias = proximal_bias
        self.p_dropout = p_dropout
        self.attn = None

        self.k_channels = channels // n_heads
        self.conv_q = nn.Conv1d(channels, channels, 1)
        self.conv_k = nn.Conv1d(channels, channels, 1)
        self.conv_v = nn.Conv1d(channels, channels, 1)
        if window_size is not None:
            n_heads_rel = 1 if heads_share else n_heads
            rel_stddev = self.k_channels**-0.5
            self.emb_rel_k = nn.Parameter(torch.randn(n_heads_rel, window_size * 2 + 1, self.k_channels) * rel_stddev)
            self.emb_rel_v = nn.Parameter(torch.randn(n_heads_rel, window_size * 2 + 1, self.k_channels) * rel_stddev)
        self.conv_o = nn.Conv1d(channels, out_channels, 1)
        self.drop = nn.Dropout(p_dropout)

        nn.init.xavier_uniform_(self.conv_q.weight)
        nn.init.xavier_uniform_(self.conv_k.weight)
        if proximal_init:
            self.conv_k.weight.data.copy_(self.conv_q.weight.data)
        nn.init.xavier_uniform_(self.conv_v.weight)

    def forward(self, x, c, attn_mask=None):
        """Forward pass of multi-head attention."""
        q = self.conv_q(x)
        k = self.conv_k(c)
        v = self.conv_v(c)
        
        x = self.attention(q, k, v, mask=attn_mask)
        
        x = self.conv_o(x)
        return x

    def attention(self, query, key, value, mask=None):
        """Compute scaled dot-product attention."""
        b, d, t_s = key.size()
        t_t = query.size(2)
        
        # Reshape for multi-head attention
        q = query.view(b, self.n_heads, self.k_channels, t_t)
        k = key.view(b, self.n_heads, self.k_channels, t_s)
        v = value.view(b, self.n_heads, self.k_channels, t_s)
        
        # Compute attention scores
        scores = torch.matmul(q.transpose(2,3), k) / math.sqrt(self.k_channels)
        
        if self.window_size is not None:
            assert t_s == t_t, "Relative attention requires same length for key and query"
            # Add relative position embeddings
            scores = self._attention_bias_forward(scores)
            
        if mask is not None:
            scores = scores.masked_fill(mask, -1e4)
            
        p_attn = F.softmax(scores, dim=-1)
        p_attn = self.drop(p_attn)
        output = torch.matmul(p_attn, v.transpose(2,3))
        output = output.transpose(2,3).contiguous().view(b, d, t_t)
        
        self.attn = p_attn.detach()
        return output

    def _attention_bias_forward(self, scores):
        """Add relative position embeddings to attention scores."""
        slen = scores.size(3)
        n_heads = scores.size(1)
        
        # Get relative position embeddings
        pos_emb_k = self._get_relative_embeddings(self.emb_rel_k, slen)
        pos_emb_v = self._get_relative_embeddings(self.emb_rel_v, slen)
        
        if self.heads_share:
            pos_emb_k = pos_emb_k.expand(n_heads, -1, -1)
            pos_emb_v = pos_emb_v.expand(n_heads, -1, -1)
            
        # Add relative position embeddings to scores
        scores = scores + self._matmul_with_relative_keys(pos_emb_k)
        
        return scores

    def _get_relative_embeddings(self, relative_embeddings, length):
        """Get relative position embeddings."""
        pad_length = max(length - (self.window_size + 1), 0)
        slice_start_position = max((self.window_size + 1) - length, 0)
        slice_end_position = slice_start_position + 2 * length - 1
        
        if pad_length > 0:
            padded_embeddings = F.pad(
                relative_embeddings,
                (0, 0, pad_length, pad_length),
                mode='replicate'
            )
        else:
            padded_embeddings = relative_embeddings
            
        used_embeddings = padded_embeddings[:, slice_start_position:slice_end_position]
        return used_embeddings

    def _matmul_with_relative_keys(self, relative_embeddings):
        """Compute attention scores with relative keys."""
        rel_logits = torch.matmul(
            query.permute(0,1,3,2),
            relative_embeddings.transpose(-2,-1)
        )
        rel_logits = rel_logits.permute(0,1,3,2)
        scores = torch.cat(
            [rel_logits[:,:,:,-1:], rel_logits[:,:,:,:-1]], dim=-1
        )
        return scores
        

class LayerNorm(nn.Module):
    """Layer normalization module."""
    
    def __init__(self, channels, eps=1e-4):
        super().__init__()
        self.channels = channels
        self.eps = eps

        self.gamma = nn.Parameter(torch.ones(channels))
        self.beta = nn.Parameter(torch.zeros(channels))

    def forward(self, x):
        n_dims = len(x.shape)
        mean = torch.mean(x, 1, keepdim=True)
        variance = torch.mean((x - mean) ** 2, 1, keepdim=True)

        x = (x - mean) * torch.rsqrt(variance + self.eps)

        shape = [1, -1] + [1] * (n_dims - 2)
        x = x * self.gamma.view(*shape) + self.beta.view(*shape)
        return x
