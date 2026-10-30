import os
import shutil
import yaml
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
from torchvision import datasets, transforms
from clearml import Task, Dataset
import matplotlib.pyplot as plt


class SimpleCNN(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 7 * 7, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 10)
        self.dropout = nn.Dropout(0.25)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(-1, 64 * 7 * 7)
        self.dropout(x)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


def get_freest_device() -> torch.device:
    """Finds and returns the CUDA device with the most free VRAM, or CPU if CUDA is unavailable."""
    if not torch.cuda.is_available():
        print("CUDA not available. Falling back to CPU.")
        return torch.device("cpu")

    num_devices = torch.cuda.device_count()
    if num_devices == 0:
        print("No CUDA devices detected. Falling back to CPU.")
        return torch.device("cpu")

    best_idx = 0
    max_free = 0

    print(f"Detected {num_devices} CUDA device(s):")
    for idx in range(num_devices):
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info(idx)
            free_gb = free_bytes / (1024**3)
            total_gb = total_bytes / (1024**3)
            print(f"  [GPU {idx}] {torch.cuda.get_device_name(idx)}: {free_gb:.2f} GB free / {total_gb:.2f} GB total")
            if free_bytes > max_free:
                max_free = free_bytes
                best_idx = idx
        except Exception as e:
            print(f"  [GPU {idx}] Error querying memory: {e}")

    device = torch.device(f"cuda:{best_idx}")
    print(f"Selected device: {device} ({torch.cuda.get_device_name(best_idx)}) with {max_free / (1024**3):.2f} GB free VRAM.")
    return device


def load_dataset_from_pt(file_path: str, transform=None):
    """
    Loads a dataset from a .pt file.
    Supports tuple/list: (images, labels) or dict: {'data': ..., 'targets': ...}
    """
    print(f"Loading data from tensor file: {file_path}")
    raw_obj = torch.load(file_path, map_location="cpu")

    if isinstance(raw_obj, (tuple, list)) and len(raw_obj) >= 2:
        x, y = raw_obj[0], raw_obj[1]
    elif isinstance(raw_obj, dict):
        if "data" in raw_obj and "targets" in raw_obj:
            x, y = raw_obj["data"], raw_obj["targets"]
        elif "x" in raw_obj and "y" in raw_obj:
            x, y = raw_obj["x"], raw_obj["y"]
        elif "images" in raw_obj and "labels" in raw_obj:
            x, y = raw_obj["images"], raw_obj["labels"]
        else:
            raise ValueError(f"Dictionary in {file_path} does not have recognized keys: {list(raw_obj.keys())}")
    elif isinstance(raw_obj, torch.Tensor):
        raise ValueError(f"File {file_path} only contains a single Tensor, targets/labels missing.")
    else:
        raise ValueError(f"Unsupported object type in {file_path}: {type(raw_obj)}")

    if not isinstance(x, torch.Tensor):
        x = torch.tensor(x)
    if not isinstance(y, torch.Tensor):
        y = torch.tensor(y)

    # Ensure shape is (N, 1, 28, 28) for 2D images if flat
    if x.ndim == 3:
        x = x.unsqueeze(1)
    if x.dtype != torch.float32:
        x = x.float()
    # Normalize if values in 0-255
    if x.max() > 1.0:
        x = x / 255.0

    full_dataset = TensorDataset(x, y.long())
    val_size = int(len(full_dataset) * 0.2)
    train_size = len(full_dataset) - val_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])
    return train_ds, val_ds


def acquire_dataset(cfg_data, transform, local_artifact_file=None):
    """
    Acquires the dataset based on config.
    Supports:
      1. file_artifact (mnist_cnn.pt passed as artifact)
      2. clearml_dataset
      3. builtin (torchvision download)
      4. local_path
    """
    temp_dir = Path(cfg_data.get("temp_local_dir", "/tmp/mnist_data")).expanduser().resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    source_type = cfg_data.get("source_type", "file_artifact")
    file_usage = cfg_data.get("file_usage", "data_file")

    if local_artifact_file and file_usage == "data_file":
        try:
            return load_dataset_from_pt(local_artifact_file, transform), temp_dir
        except Exception as e:
            print(f"Note: Could not parse {local_artifact_file} as TensorDataset ({e}).")
            print("Falling back to standard dataset acquisition...")

    print(f"Setting up dataset at: {temp_dir} using mode '{source_type}'...")

    if source_type == "clearml_dataset":
        dataset_proj = cfg_data.get("dataset_project", "datasets")
        dataset_name = cfg_data.get("dataset_name", "mnist")
        print(f"Retrieving ClearML Dataset: {dataset_proj}/{dataset_name}...")
        cml_dataset = Dataset.get(dataset_project=dataset_proj, dataset_name=dataset_name)
        data_path = cml_dataset.get_local_copy(str(temp_dir))
        train_dataset = datasets.MNIST(data_path, train=True, download=False, transform=transform)
        test_dataset = datasets.MNIST(data_path, train=False, download=False, transform=transform)
    elif source_type == "local_path":
        local_path = cfg_data.get("local_path", str(temp_dir))
        train_dataset = datasets.MNIST(local_path, train=True, download=False, transform=transform)
        test_dataset = datasets.MNIST(local_path, train=False, download=False, transform=transform)
    else:  # builtin
        train_dataset = datasets.MNIST(str(temp_dir), train=True, download=True, transform=transform)
        test_dataset = datasets.MNIST(str(temp_dir), train=False, download=True, transform=transform)

    return (train_dataset, test_dataset), temp_dir


def cleanup_dataset(temp_dir, cfg_data, artifact_path=None):
    """Removes temporary dataset directory and temporary artifact file if cleanup_after_run is True."""
    if cfg_data.get("cleanup_after_run", False):
        if temp_dir and os.path.exists(temp_dir):
            print(f"Cleaning up temporary data directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)
        if artifact_path and os.path.exists(artifact_path) and "/tmp" in str(artifact_path):
            print(f"Cleaning up downloaded artifact: {artifact_path}")
            try:
                os.remove(artifact_path)
            except OSError:
                pass


def train_one_epoch(model, device, train_loader, optimizer, criterion, epoch, logger):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * data.size(0)
        pred = output.argmax(dim=1, keepdim=True)
        correct += pred.eq(target.view_as(pred)).sum().item()
        total += data.size(0)

        if (batch_idx + 1) % 50 == 0 and logger:
            step = epoch * len(train_loader) + batch_idx
            logger.report_scalar(title="Batch Loss", series="train", value=loss.item(), iteration=step)

    epoch_loss = running_loss / total
    epoch_acc = 100.0 * correct / total
    return epoch_loss, epoch_acc


def evaluate(model, device, test_loader, criterion):
    model.eval()
    test_loss, correct, total = 0.0, 0, 0

    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += criterion(output, target).item() * data.size(0)
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += data.size(0)

    test_loss /= total
    test_acc = 100.0 * correct / total
    return test_loss, test_acc


def log_sample_predictions(model, device, test_loader, logger, num_samples=10):
    model.eval()
    try:
        images, labels = next(iter(test_loader))
        with torch.no_grad():
            outputs = model(images.to(device))
            preds = outputs.argmax(dim=1).cpu()

        fig, axes = plt.subplots(2, 5, figsize=(10, 5))
        axes = axes.flatten()

        for idx in range(min(num_samples, len(images))):
            img = images[idx].squeeze().numpy()
            true_lbl = labels[idx].item()
            pred_lbl = preds[idx].item()
            axes[idx].imshow(img, cmap="gray")
            color = "green" if pred_lbl == true_lbl else "red"
            axes[idx].set_title(f"P: {pred_lbl} | T: {true_lbl}", color=color)
            axes[idx].axis("off")

        plt.tight_layout()
        if logger:
            logger.report_matplotlib_figure(
                title="Sample Predictions",
                series="Epoch Final",
                figure=fig,
                iteration=0,
            )
        plt.close(fig)
    except Exception as e:
        print(f"Could not generate sample prediction plot: {e}")


def main():
    # 1. Load config.yaml if present locally (on remote agent without git repo, ClearML restores it)
    config_path = Path("config.yaml")
    cfg = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}

    cml_cfg = cfg.get("clearml", {})
    data_cfg = cfg.get("data", {})
    train_cfg = cfg.get("training", {})

    # 2. ClearML initialization
    task = Task.init(
        project_name=cml_cfg.get("project_name", "clearml-test"),
        task_name=cml_cfg.get("task_name", "mnist-training"),
        task_type=Task.TaskTypes.training,
        output_uri=True,
    )

    # Restore/sync configuration dictionary from ClearML
    cfg = task.connect_configuration(configuration=cfg)
    cml_cfg = cfg.get("clearml", {})
    data_cfg = cfg.get("data", {})
    train_cfg = cfg.get("training", {})

    # Explicitly connect training hyperparameters under 'General' section for HPO & UI editing
    train_cfg = task.connect(train_cfg, name="General")

    # 3. Handle data file artifact (e.g. mnist_cnn.pt)
    file_path = data_cfg.get("file_path", "mnist_cnn.pt")
    local_artifact_path = None

    if task.running_locally():
        # Running on your PC: upload the local file as an artifact to ClearML
        if file_path and os.path.exists(file_path):
            print(f"[Local PC] Uploading file '{file_path}' as artifact to ClearML...")
            task.upload_artifact(name="input_pt_file", artifact_object=file_path)
            local_artifact_path = file_path
        else:
            print(f"[Local PC] Warning: File '{file_path}' not found locally.")

        # If remote execution is enabled, enqueue and exit locally
        if cml_cfg.get("execute_remotely", False):
            queue = cml_cfg.get("queue_name", "gpu_queue")
            print(f"[Local PC] Enqueuing task to queue '{queue}' for remote execution...")
            task.execute_remotely(queue_name=queue)
    else:
        # Running on the remote machine (revel-pc-02): pull down the artifact
        print("[Remote Agent] Detected remote execution. Fetching artifact from ClearML...")
        if "input_pt_file" in task.artifacts:
            local_artifact_path = task.artifacts["input_pt_file"].get_local_copy()
            print(f"[Remote Agent] Downloaded input file to: {local_artifact_path}")
        elif file_path and os.path.exists(file_path):
            local_artifact_path = file_path

    logger = task.get_logger()

    # 4. Device selection (dynamic freest GPU with CPU fallback)
    device = get_freest_device()
    task.set_parameter("device", str(device))
    torch.manual_seed(train_cfg.get("seed", 42))

    # 5. Data transforms & loading
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])

    temp_data_dir = None
    try:
        (train_dataset, test_dataset), temp_data_dir = acquire_dataset(
            data_cfg, transform, local_artifact_file=local_artifact_path
        )

        is_cuda = device.type == "cuda"
        train_loader = DataLoader(
            train_dataset,
            batch_size=train_cfg.get("batch_size", 128),
            shuffle=True,
            num_workers=2 if is_cuda else 0,
            pin_memory=is_cuda,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=train_cfg.get("test_batch_size", 1000),
            shuffle=False,
        )

        # 6. Model setup: check if the .pt file is weights/checkpoint
        model = SimpleCNN(hidden_dim=train_cfg.get("hidden_dim", 64)).to(device)

        if local_artifact_path and data_cfg.get("file_usage") == "checkpoint":
            try:
                state_dict = torch.load(local_artifact_path, map_location=device)
                if isinstance(state_dict, dict):
                    model.load_state_dict(state_dict)
                    print(f"Successfully loaded initial model weights from {local_artifact_path}")
            except Exception as e:
                print(f"Could not load {local_artifact_path} as state_dict: {e}")

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=train_cfg.get("learning_rate", 0.001))

        epochs = train_cfg.get("epochs", 3)
        print(f"Starting training on {device} for {epochs} epochs...")

        for epoch in range(1, epochs + 1):
            train_loss, train_acc = train_one_epoch(
                model, device, train_loader, optimizer, criterion, epoch - 1, logger
            )
            val_loss, val_acc = evaluate(model, device, test_loader, criterion)

            print(
                f"Epoch {epoch:02d}/{epochs:02d} | "
                f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%"
            )

            if logger:
                logger.report_scalar(title="Loss", series="Train", value=train_loss, iteration=epoch)
                logger.report_scalar(title="Loss", series="Validation", value=val_loss, iteration=epoch)
                logger.report_scalar(title="Accuracy", series="Train", value=train_acc, iteration=epoch)
                logger.report_scalar(title="Accuracy", series="Validation", value=val_acc, iteration=epoch)

        # 7. Post-training artifacts and sample figures
        print("Logging sample predictions plot...")
        log_sample_predictions(model, device, test_loader, logger)

        if cml_cfg.get("upload_artifacts", True):
            model_path = "mnist_model_trained.pt"
            torch.save(model.state_dict(), model_path)
            task.upload_artifact(name="mnist_weights", artifact_object=model_path)
            print(f"Model saved and uploaded as artifact: {model_path}")

        task.close()
        print("Training run completed successfully!")

    finally:
        # Guarantee cleanup of temporary data directory and downloaded artifact on remote machine
        cleanup_dataset(temp_data_dir, data_cfg, artifact_path=local_artifact_path)


if __name__ == "__main__":
    main()
