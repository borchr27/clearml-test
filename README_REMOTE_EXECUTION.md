# ClearML Remote Execution & Training Guide

This setup allows you to dispatch training jobs from your local PC to a remote GPU machine (`revel-pc-02`) running a `clearml-agent` daemon.

- **No manual SSH execution scripts needed per run**: ClearML handles code packaging and execution.
- **Local File Shipping**: Easily ship local `.pt` files (such as `mnist_cnn.pt`) to the remote GPU machine without needing Git commits.
- **Config-driven**: All settings are defined in `config.yaml`.
- **Dynamic GPU allocation**: Automatically selects the GPU with the most free VRAM (falls back to CPU if needed).
- **Data clean-up**: Temporary dataset copies and downloaded artifacts are automatically wiped from the GPU machine when training finishes.

---

## 1. Files Overview

- **`config.yaml`**: Main configuration file containing ClearML settings, dataset/file options, and hyperparameters.
- **`train_mnist_remote.py`**: Training script supporting local or remote dispatch, local file artifact shipping, freest-GPU selection, metric reporting, and automatic cleanup.
- **`upload_dataset.py`**: Helper script to register and upload a local dataset directory to ClearML once (if using large multi-file datasets).

---

## 2. Using Datasets and Local Files

You can provide data to the remote training job in three ways:

### Option A: ClearML Dataset Registry (Multi-file / Large Datasets)
Upload a local dataset folder once to ClearML, and all remote workers will pull and cache it automatically:

1. Upload the directory using `upload_dataset.py`:
   ```bash
   pixi run python upload_dataset.py --path ./data/mnist_raw --name "mnist-dataset" --project "datasets"
   ```
2. In `config.yaml`:
   ```yaml
   data:
     source_type: "clearml_dataset"
     dataset_project: "datasets"
     dataset_name: "mnist-dataset"
     file_path: ""                 # No local file needed
     file_usage: "none"
     cleanup_after_run: false      # Let ClearML manage local caching on the GPU machine
   ```

### Option B: Local Tensor Dataset File (`.pt` Artifact)
Ship a local `.pt` file containing PyTorch tensors (e.g. `mnist_dataset.pt` with `{"data": ..., "targets": ...}` or `(images, labels)`):

1. In `config.yaml`:
   ```yaml
   data:
     file_path: "mnist_dataset.pt"     # Local file path on your PC
     file_usage: "data_file"          # 'data_file' parses as TensorDataset
     cleanup_after_run: true          # Deletes the temp file on remote runner after run
     source_type: "file_artifact"
   ```
2. When you run `train_mnist_remote.py`:
   - Your local PC uploads `mnist_dataset.pt` as an artifact to the ClearML Task.
   - The remote agent downloads the artifact into `/tmp`, loads it into a `TensorDataset`, and trains on the GPU.

### Option C: Pre-trained Model Checkpoint Weights (`.pt` Artifact)
If your `.pt` file contains a model `state_dict` (e.g. `mnist_cnn.pt` with `conv1.weight`, `conv1.bias`, etc.) rather than dataset images:

1. In `config.yaml`:
   ```yaml
   data:
     file_path: "mnist_cnn.pt"
     file_usage: "checkpoint"         # 'checkpoint' loads initial model weights
     cleanup_after_run: true
     source_type: "builtin"           # Or 'clearml_dataset' for training data
   ```
2. The remote agent loads the weights into the neural network before training starts, fine-tuning your existing model.

---

## 3. One-Time Setup: ClearML Daemon on the GPU Machine (`revel-pc-02`)

Log into the GPU machine once to initialize ClearML and start the background agent:

```bash
ssh mitchell@revel-pc-02
```

### Step 3.1: Initialize ClearML Credentials (if not done already)
```bash
pixi run clearml-init
```
Follow the prompts and paste your API keys from the ClearML Web UI (Settings -> Workspace -> Create new credentials).

### Step 3.2: Start the Agent Daemon
Run the agent in a persistent `tmux` session so it stays alive after disconnecting:

```bash
# Start a tmux session
tmux new -s clearml_daemon

# Launch the daemon listening on the queue specified in config.yaml (e.g. gpu_queue)
# Use --create-queue to automatically create the queue if it does not exist yet:
pixi run clearml-agent daemon --queue gpu_queue --create-queue
```

*Detach from the tmux session by pressing `Ctrl + B`, then release and press `D`.*
The agent is now waiting to receive and execute jobs.

---

## 4. Configuration (`config.yaml`)

```yaml
clearml:
  project_name: "clearml-test"
  task_name: "mnist-training"
  execute_remotely: false        # Set to true to dispatch to revel-pc-02; false for local run
  queue_name: "gpu_queue"         # Queue listened to by the agent daemon
  remote_host: "mitchell@revel-pc-02" # SSH host for remote daemon management
  upload_artifacts: true         # Uploads final trained weights to ClearML

data:
  file_path: "mnist_dataset.pt"  # Local file to ship to remote runner
  file_usage: "data_file"        # 'data_file' or 'checkpoint'
  temp_local_dir: "/tmp/mnist_data"
  cleanup_after_run: true        # Deletes temp data after training finishes
  source_type: "file_artifact"   # 'file_artifact', 'builtin', 'clearml_dataset', or 'local_path'

training:
  epochs: 3
  batch_size: 128
  test_batch_size: 1000
  learning_rate: 0.001
  hidden_dim: 64
  seed: 42
```

---

## 5. Master Management Script (`run.sh`)

You can manage all operations (training, HPO sweeps, remote daemons, and datasets) using the all-in-one `./run.sh` script:

```bash
# 1. Dispatch a training run to the remote GPU (default: remote)
./run.sh train

# Override options on the fly:
./run.sh train --remote --epochs 5 --file mnist_dataset.pt --usage data_file
./run.sh train --local

# 2. Run Hyperparameter Optimization (HPO) Sweep
./run.sh hpo --jobs 10 --concurrency 2

# 3. Manage the remote agent on revel-pc-02 over SSH
./run.sh agent status          # Check if daemon is active
./run.sh agent logs            # Tail live logs from ~/.clearml/agent.log
./run.sh agent attach          # Attach directly to the live interactive tmux screen
./run.sh agent start           # Launch daemon in persistent tmux session (tees to log)
./run.sh agent stop            # Stop remote daemon

# 4. Upload a local dataset directory to ClearML Dataset registry
./run.sh upload-dataset --path ./data/mnist_raw --name "mnist-dataset"

# 5. Open ClearML Web Dashboard
./run.sh ui
```

---

## 6. Manual Execution (Pixi Commands)

If you prefer calling python scripts directly without the wrapper script:

### Mode A: Test Run Locally (on your PC)
Ensure `execute_remotely: false` in `config.yaml`, then run:
```bash
pixi run python train_mnist_remote.py
```

### Mode B: Dispatch to Remote GPU Machine (`revel-pc-02`)
1. Set `execute_remotely: true` in `config.yaml`.
2. Run from your local PC:
   ```bash
   pixi run python train_mnist_remote.py
   ```

### Mode C: Run HPO Optimization Sweep
```bash
pixi run python hpo_controller.py --jobs 10 --concurrency 2
```
