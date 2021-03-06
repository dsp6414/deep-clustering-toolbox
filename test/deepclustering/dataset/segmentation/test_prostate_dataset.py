from unittest import TestCase
from deepclustering.dataset.segmentation.prostate_dataset import ProstateDataset
from pathlib import Path
import shutil, os


class TestDownloadDataset(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dataset_root = "./"
        self.dataset_subfolders = ["img", "gt"]
        if Path(self.dataset_root, ProstateDataset.folder_name).exists():
            shutil.rmtree(
                Path(self.dataset_root, ProstateDataset.folder_name), ignore_errors=True
            )
        if Path(self.dataset_root, ProstateDataset.zip_name).exists():
            os.remove(Path(self.dataset_root, ProstateDataset.zip_name))

    def test_download_dataset(self):
        dataset = ProstateDataset(
            root_dir=self.dataset_root,
            subfolders=self.dataset_subfolders,
            verbose=True,
            mode="train",
        )
        assert len(dataset) == 1129
        assert dataset.get_group_list().__len__() == 40

        dataset = ProstateDataset(
            root_dir=self.dataset_root,
            subfolders=self.dataset_subfolders,
            verbose=True,
            mode="val",
        )
        assert len(dataset) == 248
        assert dataset.get_group_list().__len__() == 10

    def tearDown(self) -> None:
        super().tearDown()
        if Path(self.dataset_root, ProstateDataset.folder_name).exists():
            shutil.rmtree(
                Path(self.dataset_root, ProstateDataset.folder_name), ignore_errors=True
            )
        if Path(self.dataset_root, ProstateDataset.zip_name).exists():
            os.remove(Path(self.dataset_root, ProstateDataset.zip_name))


class Test_ACDCDataset(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dataset_root = "./"
        self.dataset_subfolders = ["img", "gt"]

        if Path(self.dataset_root, ProstateDataset.folder_name).exists():
            shutil.rmtree(
                Path(self.dataset_root, ProstateDataset.folder_name), ignore_errors=True
            )
        if Path(self.dataset_root, ProstateDataset.zip_name).exists():
            os.remove(Path(self.dataset_root, ProstateDataset.zip_name))

    def test_dataset_iteration(self):
        dataset = ProstateDataset(
            root_dir=self.dataset_root,
            subfolders=self.dataset_subfolders,
            verbose=True,
            mode="train",
        )
        for i in range(len(dataset)):
            (img, gt), filename = dataset[i]

    def tearDown(self) -> None:
        super().tearDown()
        if Path(self.dataset_root, ProstateDataset.folder_name).exists():
            shutil.rmtree(
                Path(self.dataset_root, ProstateDataset.folder_name), ignore_errors=True
            )
        if Path(self.dataset_root, ProstateDataset.zip_name).exists():
            os.remove(Path(self.dataset_root, ProstateDataset.zip_name))
