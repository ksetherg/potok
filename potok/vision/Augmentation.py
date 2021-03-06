from ..core import Operator, Node
from ..core import Data, DataDict
from ..core import ApplyToDataDict

import copy
from typing import List, Iterator, Tuple
import numpy as np
from tqdm import tqdm
import gc


class AlbAugment(Node):
    def __init__(self, 
                 augmentations,
                 apply_y=False,
                 **kwargs):
        super().__init__(**kwargs)
        self.augmentations = augmentations
        self.apply_y = apply_y
    
    def fit(self, x: DataDict, y: DataDict) -> Tuple[DataDict, DataDict]:
        x_aug = copy.copy(x.X)
        y_aug = copy.copy(y.Y)
        x_aug, y_aug = self.augment(x_aug, y_aug, augs=self.augmentations)
        return x_aug, y_aug
    
    @ApplyToDataDict()
    def augment(self, *args, **kwargs):
        assert len(args) != 0, 'Not enough arguments.'
        if kwargs:
            augmentations = kwargs['augs']

            if self.apply_y:
                assert len(args) == 2, 'Not enough arguments.'
                X, y = args
                imgs, msks = [], []
                for img, msk in tqdm(zip(X.data, y.data), total=len(X), desc='Augmenting'):
                    augmented = augmentations(image=img, mask=msk)
                    imgs.append(augmented['image'])
                    msks.append(augmented['mask'])
                return X.copy(data=np.asarray(imgs)), y.copy(data=np.asarray(msks))
            else:
                X = args[0]
                imgs = []
                for img in tqdm(X.data, desc='Augmenting'):
                    augmented = augmentations(image=img)
                    imgs.append(augmented['image'])

                if len(args) == 1:
                    return X.copy(data=np.asarray(imgs))
                elif len(args) == 2:
                    return X.copy(data=np.asarray(imgs)), args[1]
        else:
            return args
            
    def predict_forward(self, x: DataDict) -> DataDict:
        """Central crop and resize on test and validation"""
        x_aug = copy.copy(x.X)
        x_aug = self.augment(x_aug, augs=self.augmentations)
        return x_aug