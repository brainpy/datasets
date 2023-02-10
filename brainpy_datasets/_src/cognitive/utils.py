from typing import Sequence, Union, Optional, Tuple, Any

import numpy as np

import brainpy as bp

__all__ = [
  'interval_of',
]


def _slice(target):
  if target is None:
    loc = slice(None, None, None)
  elif isinstance(target, int):
    loc = target
  elif isinstance(target, tuple):
    assert len(target) == 2
    loc = slice(target[0], target[1], None)
  else:
    raise ValueError
  return loc


def add(target: np.ndarray,
        value: Any,
        *slices):
  slices = [slice(None, None, None) if s is None else s for s in slices]
  target[slices] += value


def set(target: np.ndarray,
        value: Any,
        *slices):
  slices = [slice(None, None, None) if s is None else s for s in slices]
  target[slices] = value


def interval_of(elem: str, total: Union[dict[str, int], Sequence[Tuple[str, int]]]) -> slice:
  if isinstance(total, dict):
    total = tuple(total.items())
  bp.check.is_sequence(total, elem_type=tuple)
  s = 0
  for k, v in total:
    if k == elem:
      return slice(s, s + v, None)
    else:
      s += v
  else:
    raise ValueError('Not found')
