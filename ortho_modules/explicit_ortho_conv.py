import torch.nn.functional as F
import torch.nn as nn
import torch
import einops


class ECO(nn.Module):
    def __init__(
        self,
        in_channels:int,
        out_channels:int,
        kernel_size:int=3,
        stride:int=1,
        bias:bool=False,
    ):
        super(ECO, self).__init__()
        assert (stride == 1) or (stride == 2) or (stride == 3)

        self.out_channels = out_channels
        self.in_channels = in_channels * stride * stride
        self.max_channels = max(self.out_channels, self.in_channels)
        self.stride = stride
        self.kernel_size = kernel_size
        self.bias = bias
        self.conv = nn.Conv2d(self.max_channels, self.max_channels, self.kernel_size, stride=1, bias=self.bias)

    def forward(self, x):
        if self.stride > 1:
            x = einops.rearrange(
                x,
                "b c (w k1) (h k2) -> b (c k1 k2) w h",
                k1=self.stride,
                k2=self.stride,
            )
             
        if self.out_channels > self.in_channels:
            diff_channels = self.out_channels - self.in_channels
            p4d = (0, 0, 0, 0, 0, diff_channels, 0, 0)
            curr_z = F.pad(x, p4d)
        else:
            curr_z = x

        self.conv.dilation = (max(1, x.shape[-1] // self.kernel_size),)

        if self.kernel_size > 1:
            self.conv.padding = (max(1, x.shape[-1] // self.kernel_size),)

        curr_z = self.conv(curr_z)
        z = curr_z

        z = z[:, : self.out_channels, :, :]

        return z
    
    
class ECOBlock(nn.Module):
    def __init__(
        self, in_planes, planes, conv_layer, stride=1, kernel_size=3
    ):
        super(ECOBlock, self).__init__()
        self.conv = conv_layer(
                        in_channels=in_planes,
                        out_channels=planes,
                        kernel_size=kernel_size,
                        stride = stride,
        
        )
        self.activation = nn.ReLU()

    def forward(self, x):
        x = self.activation(self.conv(x))
        return x