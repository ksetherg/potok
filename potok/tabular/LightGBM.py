import lightgbm as lgb
import pandas as pd
from typing import List, Iterator, Tuple

from ..core import Node, ApplyToDataUnit, DataUnit, Data
from .TabularData import TabularData


class LightGBM(Node):
    def __init__(self,
                 target=None,
                 features=None,
                 cat_features=None,
                 mode='Regressor',
                 objective='mse',
                 eval_metric='mse',
                 num_class=None,
                 weight=None,
                 **kwargs,
                 ):

        super().__init__(**kwargs)
        self.target = target
        self.features = features
        self.cat_features = cat_features
        self.mode = mode
        self.weight = weight

        self.model_params = dict(
            n_estimators=2000,
            learning_rate=0.1,
            num_class = num_class,
            objective=objective,
            # class_weight='balanced',
            importance_type='split',
            n_jobs=-1,
        )

        self.training_params = dict(
            eval_metric=eval_metric,
            early_stopping_rounds=50,
            verbose=100,
        )

        self.model = None
        self.cat_features_idx = None
        self.feature_importance_df = None


    def _fit_(self, x: DataUnit, y: DataUnit) -> Tuple[DataUnit, DataUnit]:
        self._set_model_()

        if self.target is None:
            self.target = x['train'].target

        if self.features is None:
            self.features = x['train'].data.columns

        x_train, x_valid = x['train'].data[self.features], x['valid'].data[self.features]
        y_train, y_valid = y['train'].data.dropna()[self.target], y['valid'].data[self.target]
        x_train = x_train.reindex(y_train.index)

        if self.weight is not None:
            w_train, w_valid = y['train'].data.dropna()[self.weight], y['valid'].data[self.weight]
        else:
            w_train, w_valid = None, None

        if self.cat_features is not None:
            self._set_cat_features_(list(self.features))
        else:
            self.cat_features_idx = 'auto'

        if len(self.target) > 1 and self.mode == "Classifier":
            y_train = self._ohe_decode_(y_train)
            y_valid = self._ohe_decode_(y_valid)

        print('Training LightGBM')
        print(f'X_train = {x_train.shape} y_train = {y_train.shape}')
        print(f'X_valid = {x_valid.shape} y_valid = {y_valid.shape}')

        self.model = self.model.fit(X=x_train, y=y_train, sample_weight=w_train,
                                    eval_set=[(x_valid, y_valid)], eval_sample_weight=[w_valid],
                                    categorical_feature=self.cat_features_idx,
                                    **self.training_params)

        self._make_feature_importance_df_()
        return None

    def fit(self, x: DataUnit, y: DataUnit) -> Tuple[DataUnit, DataUnit]:
        self._fit_(x, y)
        y_frwd = self.predict_forward(x)
        return x, y_frwd

    @ApplyToDataUnit(mode='efficient')
    def predict_forward(self, x : DataUnit) -> DataUnit:
        assert self.model is not None, 'Fit model before or load from file.'
        x_new = x.data[self.features]
        if self.mode == 'Classifier':
            prediction = self.model.predict_proba(x_new)
            prediction = pd.DataFrame(prediction, index=x.index)
        elif self.mode == 'Regressor':
            prediction = self.model.predict(x_new)
            prediction = pd.DataFrame(prediction, index=x.index, columns=[self.target])
        y = TabularData(data=prediction, target=self.target)
        return y
    
    def _set_cat_features_(self, features):
        cat_features_idx = []
        for cat_feature in self.cat_features:
            idx = features.index(cat_feature)
            cat_features_idx.append(idx)
        self.cat_features_idx = cat_features_idx

    def _set_model_(self):
        if self.mode == 'Regressor':
            self.model = lgb.LGBMRegressor()
        elif self.mode == 'Classifier':
            self.model = lgb.LGBMClassifier()
        else:
            raise Exception('Unknown mode %s' % self.mode)

        self.model.set_params(**self.model_params)

    def _ohe_decode_(self, data):
        df = data[self.target]
        df = df.idxmax(axis=1).to_frame('Target')
        df['Target'] = df['Target'].astype(int)
        return df

    def _make_feature_importance_df_(self):
        feature_importance = self.model.feature_importances_
        feature_names = self.model.feature_name_

        importance = {}
        for pair in sorted(zip(feature_importance, feature_names)):
            importance[pair[1]] = pair[0]

        self.feature_importance_df = pd.DataFrame.from_dict(importance, orient='index', columns=['weight'])
        self.feature_importance_df.index.name = 'features'

    def get_feature_importance(self, child=None):
        if not hasattr(self, 'feature_importance_df'):
            return None
        return self.feature_importance_df