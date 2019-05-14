from abc import ABC, abstractmethod
from copy import deepcopy as dcopy

import torch
import yaml
from pathlib2 import Path
from torch.utils.data import DataLoader

from ..meters import MeterInterface
from ..model import Model
from ..writer import SummaryWriter, DrawCSV


class _Trainer(ABC):
    """
    Abstract class for a general trainer, which has _train_loop, _eval_loop,load_state, state_dict, and save_checkpoint
    functions. All other trainers are the subclasses of this class.
    """
    METER_CONFIG = {}
    METERINTERFACE = MeterInterface(METER_CONFIG)

    def __init__(self, model: Model, train_loader: DataLoader, val_loader: DataLoader, max_epoch: int = 100,
                 save_dir: str = './runs/test', checkpoint_path: str = None, device='cpu', config: dict = None) -> None:
        super().__init__()
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.save_dir: Path = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True, parents=True)
        (self.save_dir / 'meters').mkdir(exist_ok=True, parents=True)
        self.checkpoint = checkpoint_path
        self.max_epoch = int(max_epoch)
        self.best_score: float = -1
        self._start_epoch = 0  # whether 0 or loaded from the checkpoint.
        self.device = torch.device(device)
        if checkpoint_path:
            assert Path(checkpoint_path).exists() and Path(checkpoint_path).is_dir()
            state_dict = torch.load(str(Path(checkpoint_path) / 'last.pth'), map_location=torch.device('cpu'))
            self.load_checkpoint(state_dict)

        if config:
            # save config file to save_dir
            self.config = dcopy(config)
            try:
                self.config.pop('Config')
            except KeyError:
                pass
            with open(self.save_dir / 'config.yaml', 'w') as outfile:
                yaml.dump(self.config, outfile, default_flow_style=False)
        self.model.to(self.device)
        self.writer = SummaryWriter(str(self.save_dir))
        # todo: try to override the DrawCSV
        self.drawer = DrawCSV(columns_to_draw=['', ''], save_dir=str(self.save_dir), save_name='plot.png')

    def start_training(self):
        for epoch in range(self._start_epoch, self.max_epoch):
            self._train_loop(
                train_loader=self.train_loader,
                epoch=epoch,
            )
            with torch.no_grad():
                current_score = self._eval_loop(self.val_loader, epoch)
            self.METERINTERFACE.step()
            self.model.schedulerStep()
            # save meters and checkpoints
            for k, v in self.METERINTERFACE.aggregated_meter_dict.items():
                v.summary().to_csv(self.save_dir / f'meters/{k}.csv')
            self.METERINTERFACE.summary().to_csv(self.save_dir / f'wholeMeter.csv')
            self.writer.add_scalars('Scalars', self.METERINTERFACE.summary().iloc[-1].to_dict(), global_step=epoch)
            self.drawer.draw(self.METERINTERFACE.summary(), together=False)
            self.save_checkpoint(self.state_dict, epoch, current_score)

    def to(self, device):
        self.model.to(device=device)

    @abstractmethod
    def _train_loop(self, train_loader, epoch, mode, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def _eval_loop(self, val_loader, epoch, mode, **kwargs) -> float:
        """
        return the
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    @property
    def state_dict(self):
        state_dictionary = {}
        state_dictionary['model_state_dict'] = self.model.state_dict
        state_dictionary['meter_state_dict'] = self.METERINTERFACE.state_dict
        return state_dictionary

    def save_checkpoint(self, state_dict, current_epoch, best_score):
        save_best: bool = True if best_score > self.best_score else False
        if save_best:
            self.best_score = best_score
        state_dict['epoch'] = current_epoch
        state_dict['best_score'] = self.best_score

        torch.save(state_dict, str(self.save_dir / 'last.pth'))
        if save_best:
            torch.save(state_dict, str(self.save_dir / 'best.pth'))

    def load_checkpoint(self, state_dict):
        self.model.load_state_dict(state_dict['model_state_dict'])
        self.METERINTERFACE.load_state_dict(state_dict['meter_state_dict'])
        self.best_score = state_dict['best_score']
        self._start_epoch = state_dict['epoch'] + 1
