"""
Sequence classifier over hand-landmark feature vectors.

Design rationale (why this architecture, for a laptop CPU/Arc iGPU with
no CUDA):
  - Input is tiny per frame (126 floats) vs. raw video (huge), so even a
    plain BiLSTM trains fast on CPU with a few thousand short sequences.
  - A single architecture handles BOTH static signs (alphabet/digits —
    trained on short, mostly-repeated-frame windows) and dynamic signs
    (words — trained on real motion windows). We don't need two separate
    models; the windowing/data just differs.
  - Bidirectional because a sign's motion can be clearer read "backwards"
    at inference-buffer boundaries; keeps the model robust to where in
    the gesture the window was cut.

This file is imported by both ml/training/train.py (to build + train it)
and apps/ml-service/app/core/inference.py (to load + run it), so the
architecture used to train a checkpoint always exactly matches the one
used to serve it.
"""

import torch
import torch.nn as nn


class SignSequenceClassifier(nn.Module):
    def __init__(
        self,
        input_size: int = 126,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 66,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.norm = nn.LayerNorm(hidden_size * 2)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, seq_len, input_size)
        returns: (batch, num_classes) logits
        """
        lstm_out, _ = self.lstm(x)  # (batch, seq_len, hidden*2)
        # Mean-pool over time — robust to slightly different sequence
        # lengths / where the gesture sits inside the window.
        pooled = lstm_out.mean(dim=1)
        pooled = self.norm(pooled)
        pooled = self.dropout(pooled)
        return self.classifier(pooled)
