from typing import List, Tuple
import torch
import torch.nn.functional as F
import numpy as np
import gc
from pathlib import Path

from ..core import Regressor, DataDict, Data


class NNModel(Regressor):
    def __init__(self, model,
                 optimizer,
                 loss_func,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.model = model
        self.optimizer = optimizer
        self.loss_func = loss_func

        self.train_loss_error = None

    def _restate_(self) -> None:
        self.__dict__['model'] = None
        self.__dict__['optimizer'] = None

    def _save_(self, prefix: Path = None) -> None:
        path = prefix / 'model_weights.pth'
        if self.model is not None and self.optimizer is not None:
            torch.save({
                        'model_state_dict': self.model.state_dict(),
                        'optimizer_state_dict': self.optimizer.state_dict(),
                        }, path)

    def _load_(self, prefix: Path = None) -> None:
        path = prefix / 'model_weights.pth'
        try:
            checkpoint = torch.load(path)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        except OSError:
            raise Exception('Cant find Model weights.')
            
    def transform_x(self, x: Data) -> Data:
        x_new = np.swapaxes(x.data, -1, 1)
        x_new = torch.from_numpy(x_new)
        x_new = x_new.to(torch.device("cuda"), dtype=torch.float32)
        return x_new

    def transform_y(self, y: Data) -> Data:
        y_new = torch.from_numpy(y.data)
        y_new = y_new.to(torch.device("cuda"), dtype=torch.long)
        return y_new

    # def _transform_forward_(self):
    #     pass
    #
    # def _transform_backward_(self):
    #     pass

    def _fit_(self, x: Data, y: Data) -> None:
        self.model.train()

        x_frwd = self.transform_x(x)
        y_frwd = self.transform_y(y)
        
        self.optimizer.zero_grad()
        y_pred = self.model(x_frwd)
        loss = self.loss_func(y_pred, y_frwd)
        loss.backward()
        self.optimizer.step()
        return None
        # with torch.no_grad():
        #     logits = F.log_softmax(y_pred, dim=1)
        #     y_frwd = y.copy(data=logits.cpu().numpy())
        # gc.collect()
        # return x, y_frwd

    def _predict_(self, x: Data) -> Data:
        self.model.eval()
        x_frwd = self.transform_x(x)
        with torch.no_grad():
            y_pred = self.model(x_frwd)
            logits = F.log_softmax(y_pred, dim=1)
            pred = x.copy(data=logits.cpu().numpy())
        return pred
