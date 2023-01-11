from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pytorch_lightning as pl
from pytorch_lightning import Callback, LightningDataModule, LightningModule
from pytorch_lightning.accelerators import Accelerator
from pytorch_lightning.loggers import LightningLoggerBase
from pytorch_lightning.profiler import BaseProfiler
from torch.utils.data import DataLoader
from torchvision.transforms import Compose, ToTensor

from station.worker.loader import BaseLoader


class FederatedTrainer(pl.Trainer):
    def __init__(self, logger: Union[LightningLoggerBase, Iterable[LightningLoggerBase], bool] = True,
                 checkpoint_callback: bool = True, callbacks: Optional[List[Callback]] = None,
                 default_root_dir: Optional[str] = None, gradient_clip_val: float = 0, process_position: int = 0,
                 num_nodes: int = 1, num_processes: int = 1, gpus: Optional[Union[List[int], str, int]] = None,
                 auto_select_gpus: bool = False, tpu_cores: Optional[Union[List[int], str, int]] = None,
                 log_gpu_memory: Optional[str] = None, progress_bar_refresh_rate: int = 1,
                 overfit_batches: Union[int, float] = 0.0, track_grad_norm: Union[int, float, str] = -1,
                 check_val_every_n_epoch: int = 1, fast_dev_run: Union[int, bool] = False,
                 accumulate_grad_batches: Union[int, Dict[int, int], List[list]] = 1, max_epochs: int = 1000,
                 min_epochs: int = 1, max_steps: Optional[int] = None, min_steps: Optional[int] = None,
                 limit_train_batches: Union[int, float] = 1.0, limit_val_batches: Union[int, float] = 1.0,
                 limit_test_batches: Union[int, float] = 1.0, val_check_interval: Union[int, float] = 1.0,
                 flush_logs_every_n_steps: int = 100, log_every_n_steps: int = 50,
                 accelerator: Optional[Union[str, Accelerator]] = None, sync_batchnorm: bool = False,
                 precision: int = 32, weights_summary: Optional[str] = 'top', weights_save_path: Optional[str] = None,
                 num_sanity_val_steps: int = 2, truncated_bptt_steps: Optional[int] = None,
                 resume_from_checkpoint: Optional[Union[Path, str]] = None,
                 profiler: Optional[Union[BaseProfiler, bool, str]] = None, benchmark: bool = False,
                 deterministic: bool = False, reload_dataloaders_every_epoch: bool = False,
                 auto_lr_find: Union[bool, str] = False, replace_sampler_ddp: bool = True,
                 terminate_on_nan: bool = False, auto_scale_batch_size: Union[str, bool] = False,
                 prepare_data_per_node: bool = True, plugins: Optional[Union[str, list]] = None,
                 amp_backend: str = 'native', amp_level: str = 'O2', distributed_backend: Optional[str] = None,
                 automatic_optimization: Optional[bool] = None, move_metrics_to_cpu: bool = False,
                 enable_pl_optimizer: bool = None):
        super().__init__(logger, checkpoint_callback, callbacks, default_root_dir, gradient_clip_val, process_position,
                         num_nodes, num_processes, gpus, auto_select_gpus, tpu_cores, log_gpu_memory,
                         progress_bar_refresh_rate, overfit_batches, track_grad_norm, check_val_every_n_epoch,
                         fast_dev_run, accumulate_grad_batches, max_epochs, min_epochs, max_steps, min_steps,
                         limit_train_batches, limit_val_batches, limit_test_batches, val_check_interval,
                         flush_logs_every_n_steps, log_every_n_steps, accelerator, sync_batchnorm, precision,
                         weights_summary, weights_save_path, num_sanity_val_steps, truncated_bptt_steps,
                         resume_from_checkpoint, profiler, benchmark, deterministic, reload_dataloaders_every_epoch,
                         auto_lr_find, replace_sampler_ddp, terminate_on_nan, auto_scale_batch_size,
                         prepare_data_per_node, plugins, amp_backend, amp_level, distributed_backend,
                         automatic_optimization, move_metrics_to_cpu, enable_pl_optimizer)

    def setup_trainer(self, model: LightningModule):
        super().setup_trainer(model)

    def fit(self, model: LightningModule, train_dataloader: Optional[DataLoader] = None,
            val_dataloaders: Optional[Union[DataLoader, List[DataLoader]]] = None,
            datamodule: Optional[LightningDataModule] = None):
        return super().fit(model, train_dataloader, val_dataloaders, datamodule)

    def train(self):
        super().train()

    def run_evaluation(self, max_batches=None):
        return super().run_evaluation(max_batches)

    def track_output_for_epoch_end(self, outputs, output):
        return super().track_output_for_epoch_end(outputs, output)

    def run_test(self):
        return super().run_test()

    def run_sanity_check(self, ref_model):
        super().run_sanity_check(ref_model)

    def test(self, model: Optional[LightningModule] = None,
             test_dataloaders: Optional[Union[DataLoader, List[DataLoader]]] = None, ckpt_path: Optional[str] = 'best',
             verbose: bool = True, datamodule: Optional[LightningDataModule] = None):
        return super().test(model, test_dataloaders, ckpt_path, verbose, datamodule)

    def tune(self, model: LightningModule, train_dataloader: Optional[DataLoader] = None,
             val_dataloaders: Optional[Union[DataLoader, List[DataLoader]]] = None,
             datamodule: Optional[LightningDataModule] = None):
        super().tune(model, train_dataloader, val_dataloaders, datamodule)

    def call_setup_hook(self, model):
        super().call_setup_hook(model)

    def _reset_result_and_set_hook_fx_name(self, hook_name):
        return super()._reset_result_and_set_hook_fx_name(hook_name)

    def _cache_logged_metrics(self):
        super()._cache_logged_metrics()

    def call_hook(self, hook_name, *args, **kwargs):
        return super().call_hook(hook_name, *args, **kwargs)

    def on_batch_end(self):
        print("Batch Ended")
        super().on_batch_end()

    @staticmethod
    def available_plugins():
        return super().available_plugins()


if __name__ == '__main__':
    transform = Compose([ToTensor()])

    loader = BaseLoader(data_set="cifar/batch_1",
                        transform=transform,
                        config={"batch_size": 6, "num_workers": 0}
                        ).make_data_loader()

    trainer = FederatedTrainer()

    trainer.fit()
