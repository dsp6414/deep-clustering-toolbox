"""
In this file, we adopt the original IMSAT loss here.
"""
import torch
from torch import Tensor
from torch import nn
from torch.nn import functional as F

from .loss import Entropy, KL_div
from ..utils import simplex


class MultualInformaton_IMSAT(nn.Module):
    """
    This module takes the entropy and conditional entropy form of the MI.
     Input should be predictions of images in a large batch. The entropy should be
     The entropy of the average prediction and the conditional entropy should be that of the prediction.
     MI(X,Y) = H(Y) - H(Y|X) = entropy(average(p_y)) - average(entropy(p_y))
    """

    def __init__(self, mu=4.0, eps=1e-8):
        """
        :param mu: balance term between entropy(average(p_y)) and average(entropy(p_y))
        :param eps: small value for calculation stability
        """
        super().__init__()
        assert mu > 0, f'mu should be positive, given {mu}.'
        self.mu = mu
        self.eps = eps

    def forward(self, pred_logit: Tensor):
        assert not simplex(pred_logit), f'pred_log should not be simplex.'
        probs: Tensor = F.softmax(pred_logit, 1)
        p_average: Tensor = torch.mean(probs, dim=0).unsqueeze(0)
        assert probs.shape.__len__() == p_average.shape.__len__()
        return self.mu * Entropy(self.eps)(p_average) - Entropy(self.eps)(probs).mean()


class Perturbation_Loss(nn.Module):
    """
    calculate the loss between original images and transformed images
    """

    def __init__(self, distance_func: nn.Module = KL_div(reduce=True)):
        super().__init__()
        self.distance_func = distance_func

    def forward(self, pred_logit: Tensor, pre_logit_t: Tensor):
        """
        :param pred_logit: pred_logit for original image
        :param pre_logit_t: pred_logit for transfomred image
        :return:
        """
        assert not simplex(pred_logit, 1)
        assert not simplex(pre_logit_t, 1)
        pred: Tensor = F.softmax(pred_logit, 1)
        pred_t: Tensor = F.softmax(pre_logit_t, 1)
        loss: Tensor = self.distance_func(pred_t, pred)
        return loss