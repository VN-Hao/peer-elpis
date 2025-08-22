import math
import torch
from torch import nn
from torch.nn import functional as F

from torch.nn import Conv1d, ConvTranspose1d
from .weight_norm_compat import weight_norm, remove_weight_norm

from voice.internal_openvoice import commons
from voice.internal_openvoice.commons import init_weights, get_padding
from voice.internal_openvoice.transforms import piecewise_rational_quadratic_transform
from voice.internal_openvoice.attentions import Encoder as AttnEncoder

LRELU_SLOPE = 0.1

class LayerNorm(nn.Module):
    def __init__(self, channels, eps=1e-5):
        super().__init__()
        self.channels = channels
        self.eps = eps
        self.gamma = nn.Parameter(torch.ones(channels))
        self.beta = nn.Parameter(torch.zeros(channels))
    def forward(self, x):
        x = x.transpose(1, -1)
        x = F.layer_norm(x, (self.channels,), self.gamma, self.beta, self.eps)
        return x.transpose(1, -1)

class ConvReluNorm(nn.Module):
    def __init__(self,in_channels,hidden_channels,out_channels,kernel_size,n_layers,p_dropout):
        super().__init__()
        assert n_layers > 1
        self.conv_layers = nn.ModuleList()
        self.norm_layers = nn.ModuleList()
        self.conv_layers.append(nn.Conv1d(in_channels,hidden_channels,kernel_size,padding=kernel_size//2))
        self.norm_layers.append(LayerNorm(hidden_channels))
        self.relu_drop = nn.Sequential(nn.ReLU(), nn.Dropout(p_dropout))
        for _ in range(n_layers-1):
            self.conv_layers.append(nn.Conv1d(hidden_channels,hidden_channels,kernel_size,padding=kernel_size//2))
            self.norm_layers.append(LayerNorm(hidden_channels))
        self.proj = nn.Conv1d(hidden_channels,out_channels,1)
        self.proj.weight.data.zero_(); self.proj.bias.data.zero_()
    def forward(self,x,x_mask):
        x_org = x
        for c,n in zip(self.conv_layers,self.norm_layers):
            x = c(x * x_mask)
            x = n(x)
            x = self.relu_drop(x)
        x = x_org + self.proj(x)
        return x * x_mask

class DDSConv(nn.Module):
    def __init__(self, channels,kernel_size,n_layers,p_dropout=0.):
        super().__init__()
        self.convs_sep = nn.ModuleList(); self.convs_1x1=nn.ModuleList(); self.norms_1=nn.ModuleList(); self.norms_2=nn.ModuleList()
        for i in range(n_layers):
            dilation = kernel_size**i
            padding = (kernel_size * dilation - dilation)//2
            self.convs_sep.append(nn.Conv1d(channels,channels,kernel_size,groups=channels,dilation=dilation,padding=padding))
            self.convs_1x1.append(nn.Conv1d(channels,channels,1))
            self.norms_1.append(LayerNorm(channels)); self.norms_2.append(LayerNorm(channels))
        self.drop = nn.Dropout(p_dropout)
    def forward(self,x,x_mask,g=None):
        if g is not None: x = x + g
        for c_sep,c_1,n1,n2 in zip(self.convs_sep,self.convs_1x1,self.norms_1,self.norms_2):
            y = c_sep(x * x_mask); y = n1(y); y = F.gelu(y); y = c_1(y); y = n2(y); y = F.gelu(y); y = self.drop(y); x = x + y
        return x * x_mask

class WN(nn.Module):
    def __init__(self, hidden_channels,kernel_size,dilation_rate,n_layers,gin_channels=0,p_dropout=0.):
        super().__init__()
        assert kernel_size % 2 == 1
        self.hidden_channels=hidden_channels; self.n_layers=n_layers; self.gin_channels=gin_channels
        self.in_layers=nn.ModuleList(); self.res_skip_layers=nn.ModuleList(); self.drop=nn.Dropout(p_dropout)
        if gin_channels != 0:
            self.cond_layer = weight_norm(nn.Conv1d(gin_channels,2*hidden_channels*n_layers,1), name='weight')
        for i in range(n_layers):
            dilation = dilation_rate**i
            padding = int((kernel_size * dilation - dilation)/2)
            in_layer = weight_norm(nn.Conv1d(hidden_channels,2*hidden_channels,kernel_size,dilation=dilation,padding=padding), name='weight')
            self.in_layers.append(in_layer)
            res_skip_channels = 2*hidden_channels if i < n_layers-1 else hidden_channels
            res_skip_layer = weight_norm(nn.Conv1d(hidden_channels,res_skip_channels,1), name='weight')
            self.res_skip_layers.append(res_skip_layer)
    def forward(self,x,x_mask,g=None):
        output = torch.zeros_like(x)
        n_channels_tensor = torch.IntTensor([self.hidden_channels])
        if g is not None:
            g = self.cond_layer(g)
        for i in range(self.n_layers):
            x_in = self.in_layers[i](x)
            g_l = g[:, i*2*self.hidden_channels:(i+1)*2*self.hidden_channels,:] if g is not None else torch.zeros_like(x_in)
            acts = commons.fused_add_tanh_sigmoid_multiply(x_in, g_l, n_channels_tensor)
            acts = self.drop(acts)
            res_skip = self.res_skip_layers[i](acts)
            if i < self.n_layers -1:
                res = res_skip[:, :self.hidden_channels, :]
                x = (x + res) * x_mask
                output = output + res_skip[:, self.hidden_channels:, :]
            else:
                output = output + res_skip
        return output * x_mask

class ResBlock1(nn.Module):
    def __init__(self, channels,kernel_size=3,dilation=(1,3,5)):
        super().__init__()
        self.convs1 = nn.ModuleList([
            weight_norm(Conv1d(channels,channels,kernel_size,1,dilation=d,padding=get_padding(kernel_size,d))) for d in dilation
        ])
        self.convs2 = nn.ModuleList([
            weight_norm(Conv1d(channels,channels,kernel_size,1,dilation=1,padding=get_padding(kernel_size,1))) for _ in dilation
        ])
        self.convs1.apply(init_weights); self.convs2.apply(init_weights)
    def forward(self,x,x_mask=None):
        for c1,c2 in zip(self.convs1,self.convs2):
            xt = F.leaky_relu(x, LRELU_SLOPE); xt = xt * x_mask if x_mask is not None else xt; xt = c1(xt)
            xt = F.leaky_relu(xt, LRELU_SLOPE); xt = xt * x_mask if x_mask is not None else xt; xt = c2(xt); x = xt + x
        if x_mask is not None: x = x * x_mask
        return x
    def remove_weight_norm(self):
        for l in self.convs1: remove_weight_norm(l)
        for l in self.convs2: remove_weight_norm(l)

class ResBlock2(nn.Module):
    def __init__(self, channels,kernel_size=3,dilation=(1,3)):
        super().__init__()
        self.convs = nn.ModuleList([
            weight_norm(Conv1d(channels,channels,kernel_size,1,dilation=d,padding=get_padding(kernel_size,d))) for d in dilation
        ])
        self.convs.apply(init_weights)
    def forward(self,x,x_mask=None):
        for c in self.convs:
            xt = F.leaky_relu(x, LRELU_SLOPE); xt = xt * x_mask if x_mask is not None else xt; xt = c(xt); x = xt + x
        if x_mask is not None: x = x * x_mask
        return x
    def remove_weight_norm(self):
        for l in self.convs: remove_weight_norm(l)

class Log(nn.Module):
    def forward(self,x,x_mask,reverse=False,**kwargs):
        if not reverse:
            y = torch.log(torch.clamp_min(x,1e-5)) * x_mask
            logdet = torch.sum(-y,[1,2])
            return y, logdet
        else:
            return torch.exp(x) * x_mask

class Flip(nn.Module):
    def forward(self,x,*args,reverse=False,**kwargs):
        x = torch.flip(x,[1])
        if not reverse:
            logdet = torch.zeros(x.size(0), device=x.device, dtype=x.dtype)
            return x, logdet
        else:
            return x

class ElementwiseAffine(nn.Module):
    def __init__(self, channels):
        super().__init__(); self.m=nn.Parameter(torch.zeros(channels,1)); self.logs=nn.Parameter(torch.zeros(channels,1))
    def forward(self,x,x_mask,reverse=False,**kwargs):
        if not reverse:
            y = self.m + torch.exp(self.logs) * x; y = y * x_mask; logdet = torch.sum(self.logs * x_mask,[1,2]); return y, logdet
        else:
            return (x - self.m) * torch.exp(-self.logs) * x_mask

class ResidualCouplingLayer(nn.Module):
    def __init__(self, channels, hidden_channels,kernel_size,dilation_rate,n_layers,p_dropout=0,gin_channels=0,mean_only=False):
        assert channels % 2 == 0
        super().__init__(); self.half=channels//2; self.mean_only=mean_only
        self.pre = nn.Conv1d(self.half, hidden_channels,1)
        self.enc = WN(hidden_channels,kernel_size,dilation_rate,n_layers,gin_channels=gin_channels,p_dropout=p_dropout)
        self.post = nn.Conv1d(hidden_channels, self.half*(2-mean_only),1)
        self.post.weight.data.zero_(); self.post.bias.data.zero_()
    def forward(self,x,x_mask,g=None,reverse=False):
        x0,x1 = torch.split(x,[self.half]*2,1)
        h = self.pre(x0) * x_mask; h = self.enc(h,x_mask,g=g); stats = self.post(h) * x_mask
        if not self.mean_only: m, logs = torch.split(stats,[self.half]*2,1)
        else: m=stats; logs=torch.zeros_like(m)
        if not reverse:
            x1 = m + x1 * torch.exp(logs) * x_mask; x = torch.cat([x0,x1],1); logdet = torch.sum(logs,[1,2]); return x, logdet
        else:
            x1 = (x1 - m) * torch.exp(-logs) * x_mask; return torch.cat([x0,x1],1)

class ConvFlow(nn.Module):
    def __init__(self,in_channels,filter_channels,kernel_size,n_layers,num_bins=10,tail_bound=5.0):
        super().__init__(); self.half=in_channels//2; self.num_bins=num_bins; self.tail_bound=tail_bound; self.filter_channels=filter_channels
        self.pre = nn.Conv1d(self.half, filter_channels,1)
        self.convs = DDSConv(filter_channels,kernel_size,n_layers)
        self.proj = nn.Conv1d(filter_channels, self.half*(num_bins*3-1),1)
        self.proj.weight.data.zero_(); self.proj.bias.data.zero_()
    def forward(self,x,x_mask,g=None,reverse=False):
        x0,x1 = torch.split(x,[self.half]*2,1)
        h = self.pre(x0); h = self.convs(h,x_mask,g=g); h = self.proj(h) * x_mask
        b,c,t = x0.shape; h = h.reshape(b,c,-1,t).permute(0,1,3,2)
        uw = h[...,:self.num_bins] / math.sqrt(self.filter_channels)
        uh = h[...,self.num_bins:2*self.num_bins] / math.sqrt(self.filter_channels)
        ud = h[...,2*self.num_bins:]
        x1, logabsdet = piecewise_rational_quadratic_transform(x1, uw, uh, ud, inverse=reverse, tails='linear', tail_bound=self.tail_bound)
        x = torch.cat([x0,x1],1) * x_mask; logdet = torch.sum(logabsdet * x_mask,[1,2])
        if not reverse: return x, logdet
        else: return x

class TransformerCouplingLayer(nn.Module):
    def __init__(self, channels, hidden_channels,kernel_size,n_layers,n_heads,p_dropout=0,filter_channels=0,mean_only=False,wn_sharing_parameter=None,gin_channels=0):
        assert n_layers == 3 and channels % 2 == 0
        super().__init__(); self.half=channels//2; self.mean_only=mean_only
        self.pre = nn.Conv1d(self.half, hidden_channels,1)
        self.enc = AttnEncoder(hidden_channels, filter_channels, n_heads, n_layers, kernel_size, p_dropout, gin_channels=gin_channels) if wn_sharing_parameter is None else wn_sharing_parameter
        self.post = nn.Conv1d(hidden_channels, self.half*(2-mean_only),1); self.post.weight.data.zero_(); self.post.bias.data.zero_()
    def forward(self,x,x_mask,g=None,reverse=False):
        x0,x1 = torch.split(x,[self.half]*2,1); h = self.pre(x0) * x_mask; h = self.enc(h,x_mask,g=g); stats = self.post(h) * x_mask
        if not self.mean_only: m, logs = torch.split(stats,[self.half]*2,1)
        else: m=stats; logs=torch.zeros_like(m)
        if not reverse:
            x1 = m + x1 * torch.exp(logs) * x_mask; x = torch.cat([x0,x1],1); logdet = torch.sum(logs,[1,2]); return x, logdet
        else:
            x1 = (x1 - m) * torch.exp(-logs) * x_mask; return torch.cat([x0,x1],1)

class Generator(nn.Module):
    def __init__(self,initial_channel,resblock,resblock_kernel_sizes,resblock_dilation_sizes,upsample_rates,upsample_initial_channel,upsample_kernel_sizes,gin_channels=0):
        super().__init__(); self.num_kernels=len(resblock_kernel_sizes); self.num_upsamples=len(upsample_rates)
        self.conv_pre = Conv1d(initial_channel, upsample_initial_channel,7,1,padding=3)
        resblock_cls = ResBlock1 if resblock == '1' or resblock is True else ResBlock2
        self.ups = nn.ModuleList()
        for i,(u,k) in enumerate(zip(upsample_rates, upsample_kernel_sizes)):
            self.ups.append(weight_norm(ConvTranspose1d(upsample_initial_channel//(2**i), upsample_initial_channel//(2**(i+1)), k,u,padding=(k-u)//2)))
        self.resblocks = nn.ModuleList()
        for i in range(len(self.ups)):
            ch = upsample_initial_channel//(2**(i+1))
            for k,d in enumerate(resblock_kernel_sizes):
                dil = resblock_dilation_sizes[k]
                self.resblocks.append(resblock_cls(ch, resblock_kernel_sizes[k], dil))
        self.conv_post = Conv1d(ch,1,7,1,padding=3,bias=False)
        self.ups.apply(init_weights)
        if gin_channels != 0: self.cond = nn.Conv1d(gin_channels, upsample_initial_channel,1)
    def forward(self,x,g=None):
        x = self.conv_pre(x)
        if g is not None: x = x + self.cond(g)
        for i in range(self.num_upsamples):
            x = F.leaky_relu(x, LRELU_SLOPE); x = self.ups[i](x); xs=None
            for j in range(self.num_kernels):
                rb = self.resblocks[i*self.num_kernels+j](x)
                xs = rb if xs is None else xs + rb
            x = xs / self.num_kernels
        x = F.leaky_relu(x); x = self.conv_post(x); return torch.tanh(x)
    def remove_weight_norm(self):
        for l in self.ups: remove_weight_norm(l)
        for l in self.resblocks: l.remove_weight_norm()

class ReferenceEncoder(nn.Module):
    def __init__(self,spec_channels,gin_channels=0,layernorm=True):
        super().__init__(); ref_enc_filters=[32,32,64,64,128,128]; K=len(ref_enc_filters)
        filters=[1]+ref_enc_filters
        self.convs = nn.ModuleList([
            weight_norm(nn.Conv2d(filters[i], filters[i+1], (3,3), stride=(2,2), padding=(1,1))) for i in range(K)
        ])
        self.spec_channels=spec_channels
        self.layernorm = nn.LayerNorm(spec_channels) if layernorm else None
        out_ch = spec_channels
        self.gru = nn.GRU(input_size=ref_enc_filters[-1]*self._calc_out_channels(spec_channels,3,2,1,K), hidden_size=128, batch_first=True)
        self.proj = nn.Linear(128, gin_channels)
    def _calc_out_channels(self,L,kernel_size,stride,pad,n_convs):
        for _ in range(n_convs): L = (L - kernel_size + 2*pad)//stride + 1
        return L
    def forward(self,inputs,mask=None):
        N = inputs.size(0); out = inputs.view(N,1,-1,self.spec_channels)
        if self.layernorm is not None: out = self.layernorm(out)
        for c in self.convs: out = F.relu(c(out))
        out = out.transpose(1,2); T=out.size(1); out = out.contiguous().view(N,T,-1); self.gru.flatten_parameters(); _, h = self.gru(out)
        return self.proj(h.squeeze(0))

class ResidualCouplingBlock(nn.Module):
    def __init__(self, channels, hidden_channels,kernel_size,dilation_rate,n_layers,n_flows=4,gin_channels=0):
        super().__init__(); self.flows=nn.ModuleList()
        for _ in range(n_flows):
            self.flows.append(ResidualCouplingLayer(channels, hidden_channels, kernel_size,dilation_rate,n_layers, gin_channels=gin_channels, mean_only=True))
            self.flows.append(Flip())
    def forward(self,x,x_mask,g=None,reverse=False):
        if not reverse:
            for f in self.flows: x,_ = f(x,x_mask,g=g,reverse=reverse) if isinstance(f, ResidualCouplingLayer) else f(x, reverse=reverse)
        else:
            for f in reversed(self.flows): x = f(x,x_mask,g=g,reverse=reverse) if isinstance(f, ResidualCouplingLayer) else f(x, reverse=reverse)
        return x
