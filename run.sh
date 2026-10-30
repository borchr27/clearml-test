#!/usr/bin/env bash
# ==============================================================================
# ClearML Orchestrator & Experiment Manager
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="config.yaml"

# Locate pixi executable
if command -v pixi &> /dev/null; then
    PIXI_CMD="pixi"
elif [[ -x "${HOME}/.pixi/bin/pixi" ]]; then
    PIXI_CMD="${HOME}/.pixi/bin/pixi"
else
    echo "Error: 'pixi' executable not found in PATH or ~/.pixi/bin/pixi"
    exit 1
fi

# Load REMOTE_HOST and DEFAULT_QUEUE dynamically from config.yaml
if [[ -f "$CONFIG_FILE" ]]; then
    eval "$("$PIXI_CMD" run python -c "
import yaml
try:
    with open('$CONFIG_FILE', 'r') as f:
        cfg = yaml.safe_load(f) or {}
    cml = cfg.get('clearml', {})
    host = cml.get('remote_host', 'mitchell@revel-pc-02')
    queue = cml.get('queue_name', 'gpu_queue')
    print(f'REMOTE_HOST=\"{host}\"')
    print(f'DEFAULT_QUEUE=\"{queue}\"')
except Exception:
    print('REMOTE_HOST=\"mitchell@revel-pc-02\"')
    print('DEFAULT_QUEUE=\"gpu_queue\"')
")"
else
    REMOTE_HOST="mitchell@revel-pc-02"
    DEFAULT_QUEUE="gpu_queue"
fi

print_header() {
    echo -e "\033[1;34m>>> ClearML Manager: $1\033[0m"
}

print_success() {
    echo -e "\033[1;32m✔ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m✖ $1\033[0m"
}

usage() {
    cat <<EOF
ClearML Remote Execution & Training Manager

Usage:
  ./run.sh <command> [options]

Commands:
  train             Run a single training experiment
    --remote        Dispatch to remote GPU daemon (default)
    --local         Run locally on your PC
    --file <path>   Specify local .pt file (default: mnist_dataset.pt)
    --usage <type>  File usage: 'data_file' (dataset) or 'checkpoint' (weights)
    --epochs <N>    Override number of epochs

  hpo               Run Hyperparameter Optimization sweep
    --jobs <N>        Total experiments to run (default: 10)
    --concurrency <N> Max concurrent tasks on GPUs (default: 2)
    --queue <name>    Target worker queue (default: gpu_queue)

  agent             Manage ClearML worker daemon on revel-pc-02
    status          Check if clearml-agent daemon is active
    logs            Tail live logs from ~/.clearml/agent.log or dump tmux buffer
    logs --attach   Attach directly to the live interactive tmux session
    attach          Attach directly to the live interactive tmux session
    start           Start daemon in tmux on revel-pc-02 (tees to agent.log)
    stop            Stop daemon processes on revel-pc-02

  upload-dataset    Register and upload a local dataset folder
    --path <dir>    Path to local dataset directory (required)
    --name <name>   Dataset name in ClearML (default: mnist-dataset)
    --project <p>   Project name (default: datasets)

  ui                Print / open ClearML Web Dashboard URL
  help              Show this help message

Examples:
  ./run.sh train --remote --epochs 5
  ./run.sh train --local
  ./run.sh hpo --jobs 5 --concurrency 2
  ./run.sh agent status
  ./run.sh agent logs
EOF
}

# Helper to modify config.yaml keys safely using python
set_config_value() {
    local key_path="$1"
    local value="$2"
    "$PIXI_CMD" run python -c "
import yaml

with open('$CONFIG_FILE', 'r') as f:
    cfg = yaml.safe_load(f) or {}

keys = '$key_path'.split('.')
d = cfg
for k in keys[:-1]:
    if k not in d or not isinstance(d[k], dict):
        d[k] = {}
    d = d[k]

# Handle types
val = '$value'
if val.lower() == 'true':
    val = True
elif val.lower() == 'false':
    val = False
elif val.isdigit():
    val = int(val)
elif val.replace('.', '', 1).isdigit() and '.' in val:
    val = float(val)

d[keys[-1]] = val

with open('$CONFIG_FILE', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
"
}

# Ensure git status is clean or warned before remote dispatch
check_git_remote() {
    if git rev-parse --is-inside-work-tree &>/dev/null; then
        local uncommitted
        uncommitted=$(git status --porcelain)
        if [[ -n "$uncommitted" ]]; then
            print_warning "Uncommitted git changes detected."
            echo "Auto-committing and pushing so the remote daemon has the latest code..."
            git add -A
            git commit -m "Auto-update before ClearML run: $(date '+%Y-%m-%d %H:%M:%S')" || true
            git push origin HEAD || print_warning "Could not push to remote. Ensure git remote is reachable."
        fi
    fi
}

cmd_train() {
    local execute_remotely=true
    local file_path=""
    local file_usage=""
    local epochs=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --remote)
                execute_remotely=true
                shift
                ;;
            --local)
                execute_remotely=false
                shift
                ;;
            --file)
                file_path="$2"
                shift 2
                ;;
            --usage)
                file_usage="$2"
                shift 2
                ;;
            --epochs)
                epochs="$2"
                shift 2
                ;;
            *)
                print_error "Unknown train option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Update config.yaml values
    set_config_value "clearml.execute_remotely" "$execute_remotely"
    if [[ -n "$file_path" ]]; then
        set_config_value "data.file_path" "$file_path"
    fi
    if [[ -n "$file_usage" ]]; then
        set_config_value "data.file_usage" "$file_usage"
    fi
    if [[ -n "$epochs" ]]; then
        set_config_value "training.epochs" "$epochs"
    fi

    if [[ "$execute_remotely" == true ]]; then
        print_header "Dispatching single training run to remote queue ($DEFAULT_QUEUE)..."
        check_git_remote
    else
        print_header "Running training locally..."
    fi

    "$PIXI_CMD" run python train_mnist_remote.py
}

cmd_hpo() {
    local jobs=10
    local concurrency=2
    local queue="$DEFAULT_QUEUE"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --jobs)
                jobs="$2"
                shift 2
                ;;
            --concurrency)
                concurrency="$2"
                shift 2
                ;;
            --queue)
                queue="$2"
                shift 2
                ;;
            *)
                print_error "Unknown hpo option: $1"
                usage
                exit 1
                ;;
        esac
    done

    print_header "Launching HPO Controller: $jobs total experiments ($concurrency concurrent) on queue '$queue'..."
    check_git_remote
    "$PIXI_CMD" run python hpo_controller.py --jobs "$jobs" --concurrency "$concurrency" --queue "$queue"
}

cmd_agent() {
    local action="${1:-status}"
    case "$action" in
        status)
            print_header "Checking ClearML Agent on $REMOTE_HOST..."
            ssh "$REMOTE_HOST" '
                if tmux has-session -t clearml_daemon 2>/dev/null; then
                    echo "✔ clearml_daemon tmux session is RUNNING."
                else
                    RUNNING_PIDS=$(ps -eo pid,cmd | grep -E "[c]learml-agent daemon|[c]learml_agent" | awk "{print \$1}")
                    if [[ -n "$RUNNING_PIDS" ]]; then
                        echo "✔ clearml-agent process is RUNNING outside tmux (PIDs: $RUNNING_PIDS)."
                    else
                        echo "✖ clearml-agent is NOT running on revel-pc-02."
                    fi
                fi
            '
            ;;
        logs)
            local mode="${2:-}"
            if [[ "$mode" == "--attach" || "$mode" == "-a" ]]; then
                print_header "Attaching to clearml_daemon tmux on $REMOTE_HOST (Detach with Ctrl+B then D)..."
                ssh -t "$REMOTE_HOST" "tmux attach-session -t clearml_daemon"
            else
                print_header "Streaming ClearML Agent logs from $REMOTE_HOST (Ctrl+C to exit)..."
                ssh -t "$REMOTE_HOST" '
                    LOG_FILE="$HOME/.clearml/agent.log"
                    if [[ -f "$LOG_FILE" ]]; then
                        echo "Tailing log file: $LOG_FILE"
                        tail -n 50 -f "$LOG_FILE"
                    elif tmux has-session -t clearml_daemon 2>/dev/null; then
                        echo "Note: ~/.clearml/agent.log not found yet. Dumping live tmux screen..."
                        tmux capture-pane -pt clearml_daemon -S -50
                        echo ""
                        echo "(Tip: Run \"./run.sh agent logs --attach\" to attach directly to the live tmux session)"
                    else
                        LATEST_LOG=$(ls -t /tmp/.clearml_agent_daemon_out*.txt 2>/dev/null | head -n 1)
                        if [[ -n "$LATEST_LOG" ]]; then
                            echo "Following daemon log: $LATEST_LOG"
                            tail -n 50 -f "$LATEST_LOG"
                        else
                            echo "No active agent logs found on revel-pc-02."
                        fi
                    fi
                '
            fi
            ;;
        attach)
            print_header "Attaching to clearml_daemon tmux on $REMOTE_HOST (Detach with Ctrl+B then D)..."
            ssh -t "$REMOTE_HOST" "tmux attach-session -t clearml_daemon"
            ;;
        start)
            print_header "Starting ClearML Agent on $REMOTE_HOST in tmux..."
            ssh "$REMOTE_HOST" "
                mkdir -p ~/.clearml
                if tmux has-session -t clearml_daemon 2>/dev/null; then
                    echo 'Session clearml_daemon already exists. Restarting...'
                    tmux kill-session -t clearml_daemon
                fi
                tmux new-session -d -s clearml_daemon 'cd ~/projects/clearml-test && pixi run clearml-agent daemon --queue $DEFAULT_QUEUE --create-queue 2>&1 | tee -a ~/.clearml/agent.log'
                echo '✔ Daemon started in tmux session \"clearml_daemon\" listening on $DEFAULT_QUEUE'
                echo '✔ Output tee-ed to ~/.clearml/agent.log'
            "
            ;;
        stop)
            print_header "Stopping ClearML Agent on $REMOTE_HOST..."
            ssh "$REMOTE_HOST" '
                tmux kill-session -t clearml_daemon 2>/dev/null || true
                pkill -f "clearml-agent daemon" 2>/dev/null || true
                pkill -f "clearml_agent" 2>/dev/null || true
                echo "✔ clearml-agent stopped."
            '
            ;;
        *)
            print_error "Unknown agent action: $action. Use: status | logs [--attach] | attach | start | stop"
            exit 1
            ;;
    esac
}

cmd_upload_dataset() {
    local data_path=""
    local dataset_name="mnist-dataset"
    local project_name="datasets"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --path)
                data_path="$2"
                shift 2
                ;;
            --name)
                dataset_name="$2"
                shift 2
                ;;
            --project)
                project_name="$2"
                shift 2
                ;;
            *)
                print_error "Unknown upload-dataset option: $1"
                usage
                exit 1
                ;;
        esac
    done

    if [[ -z "$data_path" ]]; then
        print_error "Missing required argument: --path <directory>"
        exit 1
    fi

    print_header "Uploading dataset at '$data_path' as '$dataset_name' in project '$project_name'..."
    "$PIXI_CMD" run python upload_dataset.py --path "$data_path" --name "$dataset_name" --project "$project_name"
}

cmd_ui() {
    local url="https://app.clear.ml"
    print_header "ClearML Web Dashboard: $url"
    if command -v xdg-open &>/dev/null; then
        xdg-open "$url" &>/dev/null &
    elif command -v open &>/dev/null; then
        open "$url" &
    fi
}

# Main routing
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 0
    fi

    local command="$1"
    shift

    case "$command" in
        train)
            cmd_train "$@"
            ;;
        hpo)
            cmd_hpo "$@"
            ;;
        agent)
            cmd_agent "$@"
            ;;
        upload-dataset)
            cmd_upload_dataset "$@"
            ;;
        ui)
            cmd_ui
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            print_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
