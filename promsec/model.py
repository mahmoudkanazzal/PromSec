"""gGAN generator and discriminator."""

from __future__ import annotations

import torch.nn as nn
import torch_geometric.nn as pyg_nn

from utils import NODE_FEATURE_DIM


class Generator(nn.Module):
    """Two-layer GraphConv generator: maps a code graph g to an improved graph g_hat with the same nodes and edges."""

    def __init__(self, in_feats: int = NODE_FEATURE_DIM, hidden_feats: int = 128, out_feats: int = NODE_FEATURE_DIM):
        super().__init__()
        self.conv1 = pyg_nn.GraphConv(in_feats, hidden_feats)
        self.conv2 = pyg_nn.GraphConv(hidden_feats, out_feats)
        self.relu = nn.ReLU()

    def forward(self, x, edge_index):
        x = self.relu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return x, edge_index


class Discriminator(nn.Module):
    """Two-layer GraphConv discriminator: per-node probability that a graph is real."""

    def __init__(self, in_feats: int = NODE_FEATURE_DIM, hidden_feats: int = 64):
        super().__init__()
        self.conv1 = pyg_nn.GraphConv(in_feats, hidden_feats)
        self.conv2 = pyg_nn.GraphConv(hidden_feats, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index):
        x = self.relu(self.conv1(x, edge_index))
        return self.sigmoid(self.conv2(x, edge_index))
