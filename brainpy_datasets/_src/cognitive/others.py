from typing import Union, Optional, Callable

import numpy as np

import brainpy as bp
from brainpy_datasets._src.cognitive.base import (CognitiveTask, TimeDuration, is_time_duration)
from brainpy_datasets._src.cognitive.utils import interval_of
from brainpy_datasets._src.utils.others import initialize

__all__ = [
  'AntiReach',
  'Reaching1D',
]


class AntiReach(CognitiveTask):
  """Anti-response task.

  During the fixation period, the agent fixates on a fixation point.
  During the following stimulus period, the agent is then shown a stimulus away
  from the fixation point. Finally, the agent needs to respond in the
  opposite direction of the stimulus during the decision period.

  Args:
    anti: bool, if True, requires an anti-response. If False, requires a
        pro-response, i.e. response towards the stimulus.
  """
  metadata = {
    'paper_link': 'https://www.nature.com/articles/nrn1345',
    'paper_name': 'Look away: the anti-saccade task and the voluntary control of eye movement',
  }

  def __init__(
      self,
      dt: Union[int, float] = 100.,
      anti: bool = True,
      t_fixation: TimeDuration = 500.,
      t_stimulus: TimeDuration = 500.,
      t_delay: TimeDuration = 0.,
      t_decision: TimeDuration = 500.,
      num_choice: int = 32,
      num_trial: int = 1024,
      seed: Optional[int] = None,
      input_transform: Optional[Callable] = None,
      target_transform: Optional[Callable] = None,
  ):
    super().__init__(input_transform=input_transform,
                     target_transform=target_transform,
                     dt=dt,
                     num_trial=num_trial,
                     seed=seed)
    # time
    self.t_fixation = is_time_duration(t_fixation)
    self.t_stimulus = is_time_duration(t_stimulus)
    self.t_delay = is_time_duration(t_delay)
    self.t_decision = is_time_duration(t_decision)

    # features
    self.num_choice = bp.check.is_integer(num_choice, )
    self._features = np.arange(0, 2 * np.pi, 2 * np.pi / num_choice)
    self._choices = np.arange(self.num_choice)
    self._feature_periods = {'fixation': 1, 'choice': num_choice}

    # others
    self.anti = anti

    # input / output information
    self.output_features = ['fixation'] + [f'choice {i}' for i in range(num_choice)]
    self.input_features = ['fixation'] + [f'stimulus {i}' for i in range(num_choice)]

  def sample_a_trial(self, item):
    n_fixation = int(initialize(self.t_fixation) / self.dt)
    n_stimulus = int(initialize(self.t_stimulus) / self.dt)
    n_delay = int(initialize(self.t_delay) / self.dt)
    n_decision = int(initialize(self.t_decision) / self.dt)
    _time_periods = {'fixation': n_fixation,
                          'stimulus': n_stimulus,
                          'delay': n_delay,
                          'decision': n_decision, }
    n_total = sum(_time_periods.values())
    X = np.zeros((n_total, self.num_choice + 1))
    Y = np.zeros(n_total, dtype=int)

    ground_truth = self.rng.choice(self._choices)
    if self.anti:
      stim_theta = np.mod(self._features[ground_truth] + np.pi, 2 * np.pi)
    else:
      stim_theta = self._features[ground_truth]

    ax0_fixation = interval_of('fixation', _time_periods)
    ax0_stimulus = interval_of('stimulus', _time_periods)
    ax0_delay = interval_of('delay', _time_periods)
    ax1_fixation = interval_of('fixation', self._feature_periods)
    ax1_choice = interval_of('choice', self._feature_periods)

    X[ax0_fixation, ax1_fixation] += 1.
    X[ax0_stimulus, ax1_fixation] += 1.
    X[ax0_delay, ax1_fixation] += 1.

    stim = np.cos(self._features - stim_theta)
    X[ax0_stimulus, ax1_choice] += stim

    Y[interval_of('decision', _time_periods)] = ground_truth + 1

    if self.input_transform is not None:
      X = self.input_transform(X)
    if self.target_transform is not None:
      Y = self.target_transform(Y)

    dim0 = tuple(_time_periods.items())
    dim1 = [('fixation', 1), ('stimulus', self.num_choice)]

    return [X, dict(ax0=dim0, ax1=dim1)], [Y, dict(ax0=dim0)]


class Reaching1D(CognitiveTask):
  r"""Reaching to the stimulus.

    The agent is shown a stimulus during the fixation period. The stimulus
    encodes a one-dimensional variable such as a movement direction. At the
    end of the fixation period, the agent needs to respond by reaching
    towards the stimulus direction.
    """
  metadata = {
    'paper_link': 'https://science.sciencemag.org/content/233/4771/1416',
    'paper_name': 'Neuronal population coding of movement direction',
  }

  def __init__(
      self,
      dt: Union[int, float] = 100.,
      t_fixation: TimeDuration = 500.,
      t_reach: TimeDuration = 500.,
      num_trial: int = 1024,
      num_choice: int = 2,
      seed: Optional[int] = None,
      input_transform: Optional[Callable] = None,
      target_transform: Optional[Callable] = None,
  ):
    super().__init__(input_transform=input_transform,
                     target_transform=target_transform,
                     dt=dt,
                     num_trial=num_trial,
                     seed=seed)

    # time
    self.t_fixation = is_time_duration(t_fixation)
    self.t_reach =is_time_duration(t_reach)


    # features
    self.num_choice = bp.check.is_integer(num_choice)
    self._features = np.linspace(0, 2 * np.pi, num_choice + 1)[:-1]
    self._feature_periods = {'target': num_choice, 'self': num_choice}

    # input / output information
    self.output_features = ['fixation', 'left', 'right']
    self.input_features = [f'target{i}' for i in range(num_choice)] + [f'self{i}' for i in range(num_choice)]

  def sample_a_trial(self, item):
    n_fixation = int(self.t_fixation / self.dt)
    n_reach = int(self.t_reach / self.dt)
    _time_periods = {'fixation': n_fixation, 'reach': n_reach, }
    n_total = sum(_time_periods.values())
    X = np.zeros((n_total, len(self.input_features)))
    Y = np.zeros(n_total, dtype=int)

    ground_truth = self.rng.uniform(0, np.pi * 2)

    ax0_fixation = interval_of('fixation', _time_periods)
    ax0_reach = interval_of('reach', _time_periods)
    ax1_target = interval_of('target', self._feature_periods)

    target = np.cos(self._features - ground_truth)
    X[ax0_reach, ax1_target] += target

    Y[ax0_fixation] = np.pi
    Y[ax0_reach] = ground_truth

    if self.input_transform is not None:
      X = self.input_transform(X)
    if self.target_transform is not None:
      Y = self.target_transform(Y)

    dim0 = tuple(_time_periods.items())
    dim1 = [('target', self.num_choice), ('self', self.num_choice)]

    return [X, dict(ax0=dim0, ax1=dim1)], [Y, dict(ax0=dim0)]

