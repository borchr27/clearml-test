"""
Helper utility to register and upload a local dataset directory to ClearML.
Once uploaded, any remote worker daemon can automatically pull it via Dataset.get().
"""

import argparse
from clearml import Dataset


def upload_dataset(data_path: str, dataset_name: str, dataset_project: str):
    print(f"Creating ClearML Dataset '{dataset_name}' in project '{dataset_project}'...")
    dataset = Dataset.create(
        dataset_name=dataset_name,
        dataset_project=dataset_project,
    )

    print(f"Adding files from local directory: {data_path}...")
    dataset.add_files(path=data_path)

    print("Uploading dataset to ClearML storage...")
    dataset.upload()

    print("Finalizing dataset version...")
    dataset.finalize()
    print(f"Dataset successfully created and uploaded! ID: {dataset.id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a local dataset to ClearML")
    parser.add_argument("--path", type=str, required=True, help="Local directory path containing data files")
    parser.add_argument("--name", type=str, default="mnist", help="Dataset name in ClearML")
    parser.add_argument("--project", type=str, default="datasets", help="Project name in ClearML")

    args = parser.parse_args()
    upload_dataset(args.path, args.name, args.project)
