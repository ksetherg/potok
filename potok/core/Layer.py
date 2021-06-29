# import ray
from pathlib import Path
from typing import List, Tuple

from .Node import Node
from .Data import Data, DataUnit, DataLayer


class Layer(Node):
    def __init__(self, *nodes, **kwargs):
        super().__init__(**kwargs)
        layer = []
        for node in nodes:
            if isinstance(node, Node):
                layer.append(node)
            else:
                raise Exception(f'Unknown node type={node.__class__.__name__}')
                
        self.layer = layer

    def __len__(self) -> int:
        return len(self.layer)

    def __getitem__(self, idx: int) -> Node:
        res = self.layer[idx]
        return res

    def save(self, prefix: Path):
        for i, node in enumerate(self.layer):
            suffix_nd = node.name + '_' + str(i)
            prefix_nd = prefix / suffix_nd
            node.save(prefix_nd)
    
    def load(self, prefix: Path):
        for i, node in enumerate(self.layer):
            suffix_nd = node.name + '_' + str(i)
            prefix_nd = prefix / suffix_nd
            node.load(prefix_nd)

    def fit(self, x, y):
        assert len(self.layer) == len(x) == len(y), 'Layer and data shapes must be same.'
        res = [node.fit(xx, yy) for node, xx, yy in zip(self.layer, x, y)]
        x2 = self._flatten_forward_(list(map(lambda v: v[0], res)))
        y2 = self._flatten_forward_(list(map(lambda v: v[1], res)))
        return x2, y2
    
    def predict_forward(self, x):
        assert len(self.layer) == len(x), 'Layer and data shapes must be same.'        
        res = [node.predict_forward(xx) for node, xx in zip(self.layer, x)]
        x2 = self._flatten_forward_(res)
        return x2
    
    def predict_backward(self, y):
        y2 = self._flatten_backward_(y)
        assert len(self.layer) == len(y2), 'Layer and data shapes must be same.'
        res = [node.predict_backward(yy) for node, yy in zip(self.layer, y2)]
        result = DataLayer(*res)
        return result

    def _flatten_forward_(self, data: List) -> DataLayer:
        if isinstance(data[0], (DataLayer, list)):
            data = data[0]
        return DataLayer(*data)

    def _flatten_backward_(self, data: DataLayer) -> DataLayer:
        if len(data) > len(self.layer):
            data = DataLayer(*[data])
        elif len(data) < len(self.layer):
            raise Exception('Layer and data shapes must be same.')
        return data


# class Layer(Node):
#     def __init__(self, *nodes, **kwargs):
#         super().__init__(**kwargs)
#         layer = []
#         for node in nodes:
#             if isinstance(node, Node):
#                 layer.append(node.copy)
#             else:
#                 raise Exception(f'Unknown node type={node.__class__.__name__}')
                
#         self.layer = layer
#         self.shapes = None

#     def fit(self, x, y):
#         assert len(self.layer) == len(x) == len(y), 'Layer and data shapes must be same.'

#         actors = [ray.remote(node.__class__).remote(**node.__dict__) for node in self.layer]
#         res = [node.fit.remote(xx, yy) for node, xx, yy in zip(actors, x, y)]

#         states = ray.get([node.__getstate__.remote() for node in actors])
#         [node.__setstate__(state) for node, state in zip(self.layer, states)]
        
#         res = ray.get(res)

#         x2 = DataLayer(*self._flatten_forward_(list(map(lambda x: x[0], res))))
#         y2 = DataLayer(*self._flatten_forward_(list(map(lambda x: x[1], res))))
#         return x2, y2
    
#     def predict_forward(self, x):
#         assert len(self.layer) == len(x), 'Layer and data shapes must be same.'        
#         res = [ray.remote(node.predict_forward.__func__).remote(node, xx) for node, xx in zip(self.layer, x)]
#         result = ray.get(res)
#         result1d = DataLayer(*self._flatten_forward_(result))
#         return result1d
    
#     def predict_backward(self, y):
#         y2 = self._flatten_backward_(y)
#         assert len(self.layer) == len(y2), 'Layer and data shapes must be same.'
#         res = [ray.remote(node.predict_backward.__func__).remote(node, yy) for node, yy in zip(self.layer, y2)]
#         result = DataLayer(*ray.get(res))
#         return result
    
#     def _flatten_forward_(self, irr_list):
#         flat = []
#         shapes = []
#         for i in irr_list:
#             if isinstance(i, (DataLayer, list)):
#                 flat.extend(i)
#                 shapes.append(len(i))
#             elif isinstance(i, (DataUnit, Data)):
#                 flat.append(i)
#                 shapes.append(0)
#             else:
#                 raise Exception(f'Unknown type of data={i.__class__.__name__}')
#         self.shapes = shapes
#         return flat
    
#     def _flatten_backward_(self, list1d):
#         if isinstance(list1d, DataLayer):
#             list1d = list1d.to_list()
#         start = 0
#         end = 0
#         irr_list = []
#         for d in self.shapes:
#             if d == 0:
#                 sl = list1d[start]
#                 start += 1
#                 irr_list.append(sl)
#             else:
#                 end = start + d
#                 sl = DataLayer(*list1d[start:end])
#                 start = end
#                 irr_list.append(sl)
#         return irr_list