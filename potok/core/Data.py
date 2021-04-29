from dataclasses import dataclass
from typing import List, Collection, Iterator
import copy


class Data:
    def X(self) -> 'Data':
        raise Exception('Not implemented.')

    def Y(self) -> 'Data':
        raise Exception('Not implemented.')

    @property
    def index(self) -> Collection:
        raise Exception('Not implemented.')

    def get_by_index(self, index) -> 'Data':
        raise Exception('Not implemented')

    def reindex(self, index) -> 'Data':
        raise Exception('Not implemented')

    @classmethod
    def combine(cls, datas: List['Data']) -> 'Data':
        raise Exception('Not implemented')
    
    def copy(self, **kwargs) -> 'Data':
        new_data = copy.copy(self)
        new_data.__dict__.update(kwargs)
        return new_data


@dataclass #(frozen=True) not pickable
class DataUnit:    
    train: Data = None
    valid: Data = None
    test: Data = None
    
    def __post_init__(self):
        types = [type(v) for k, v in self]
        assert len(types) >= 1, 'Currently empty DataUnits are not allowed.'
        assert types.count(types[0]) == len(types), 'All types must be the same.'
        
    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state: dict):
        self.__dict__.update(state)
        return 
    
    def __reduce__(self):
        return self.__class__, copy.copy(tuple(self.__dict__.values()))
        
    def __iter__(self) -> Iterator:
        new_dict = {k: v for k, v in self.__dict__.items() if v is not None}
        return iter(new_dict.items())
    
    def __getitem__(self, key: str) -> Data:
        return self.__dict__[key]
    
    def __setitem__(self, key: str, value: Data):
        assert key in ['train', 'valid', 'test'], f'Key Error: {key}.'
        self.update({key: value})
        return

    def to_dict(self) -> dict:
        return self.__dict__.copy()
    
    def update(self, state: dict):
        self.__dict__.update(state)
        return 
        
    @property
    def units(self) -> list:
        units = [k for k, v in self]
        return units
    
    @property
    def X(self) -> 'DataUnit':
        '''can be parallelized'''
        X = {k: v.X for k, v in self}
        return DataUnit(**X)
    
    @property
    def Y(self) -> 'DataUnit':
        '''can be parallelized'''
        Y = {k: v.Y for k, v in self}
        return DataUnit(**Y)
    
    @property
    def index(self) -> 'DataUnit':
        '''can be parallelized'''
        indx = {k: v.index for k, v in self}
        return DataUnit(**indx)

    def get_by_index(self, index: 'DataUnit') -> 'DataUnit':
        '''can be parallelized'''
        assert self.units == index.units, 'Units must match.'
        res = {k1: v1.get_by_index(v2) for k1, v1, k2, v2 in zip(self, index)}
        return DataUnit(**res)

    def reindex(self, index: 'DataUnit') -> 'DataUnit':
        '''can be parallelized'''
        assert self.units == index.units, 'Units must match.'
        res = {k1: v1.reindex(v2) for k1, v1, k2, v2 in zip(self, index)}
        return DataUnit(**res)

    @classmethod
    def combine(cls, datas: List['DataUnit']) -> 'DataUnit':
        '''can be parallelized'''
        layer = DataLayer(*datas)
        args = {}
        for unit in layer.units:
            unit_data = layer[unit].to_list()
            args[unit] = unit_data[0].combine(unit_data)
        raise DataUnit(*args)
    
    def copy(self, **kwargs) -> 'DataUnit':
        new_data = copy.copy(self)
        new_data.__dict__.update(kwargs)
        return new_data


@dataclass(init=False)
class DataLayer:
    args: List[DataUnit]

    def __init__(self, *args):
        self.args = args
        self.validate_types(args)
    
    def validate_types(self, args: List[DataUnit]):
        notna = [arg is not None for arg in args]
        assert all(notna), 'DataLayer contains None.'
        types = [type(arg) for arg in args]
        assert types.count(types[0]) == len(types), 'All types must be the same.'
        
    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        return
    
    def __reduce__(self):
        return self.__class__, copy.copy(tuple(*self.__dict__.values()))
        
    def __iter__(self) -> Iterator:
        return iter(self.to_list())
    
    def __len__(self) -> int:
        return len(self.to_list())
    
    def __getitem__(self, key: str) -> 'DataLayer':
        res = [DataUnit(**{key: arg[key]}) for arg in self]
        return DataLayer(*res)
            
    def to_list(self) -> list:
        return list(*self.__dict__.copy().values())

    def update(self, data: list):
        new = self.__dict__.update({'args': tuple(data)})
        return

    @property
    def units(self) -> list:
        units = [arg.units for arg in self]
        intersection = list(set.intersection(*map(set, units)))
        assert len(intersection) >= 1, 'Units intersection is empty.'
        return intersection

    @property
    def X(self) -> 'DataLayer':
        '''can be parallelized'''
        X = [arg.X for arg in self]
        return DataLayer(*X)
    
    @property
    def Y(self) -> 'DataLayer':
        '''can be parallelized'''
        Y = [arg.Y for arg in self]
        return DataLayer(*Y)
    
    @property
    def index(self) -> 'DataLayer':
        '''can be parallelized'''
        indx = [v.index for v in self]
        return DataLayer(*indx)

    def get_by_index(self, index: 'DataLayer') -> 'DataLayer':
        '''can be parallelized'''
        assert len(self) == len(index), 'DataLayers must be same shape.'
        res = [v1.get_by_index(v2) for v1, v2 in zip(self, index)]
        return DataLayer(*res)

    def reindex(self, index: 'DataLayer') -> 'DataLayer':
        '''can be parallelized'''
        assert len(self) == len(index), 'DataLayers must be same shape.'
        res = [v1.reindex(v2) for v1, v2 in zip(self, index)]
        return DataLayer(*res)

    @classmethod
    def combine(cls, datas: List['DataLayer']):
        raise Exception('Not implemented.')
    
    def copy(self, **kwargs) -> 'DataLayer':
        new_data = copy.copy(self)
        new_data.__dict__.update(kwargs)
        return new_data