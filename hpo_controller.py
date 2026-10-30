from clearml.automation import (
    DiscreteParameterRange,
    UniformParameterRange,
    HyperParameterOptimizer,
    RandomSearch,
)
from clearml.automation.optuna import OptimizerOptuna  # optional: or RandomSearch
from clearml import Task


import argparse
from clearml.automation import (
    DiscreteParameterRange,
    UniformParameterRange,
    HyperParameterOptimizer,
    RandomSearch,
)
from clearml.automation.optuna import OptimizerOptuna  # optional: or RandomSearch
from clearml import Task


def main():
    parser = argparse.ArgumentParser(description="ClearML Hyperparameter Optimizer Sweep")
    parser.add_argument("--jobs", type=int, default=10, help="Total number of experiments to run")
    parser.add_argument("--concurrency", type=int, default=2, help="Max concurrent tasks on workers")
    parser.add_argument("--queue", type=str, default="gpu_queue", help="Queue where daemon workers listen")
    parser.add_argument("--project", type=str, default="clearml-test", help="ClearML project name")
    parser.add_argument("--base-task", type=str, default="mnist-training", help="Base task name template")
    args = parser.parse_args()

    # 1. Initialize controller task in ClearML
    Task.init(
        project_name=args.project,
        task_name="mnist-hpo-controller",
        task_type=Task.TaskTypes.optimizer,
        reuse_last_task_id=False,
    )

    # 2. Find base task template (or specify task_id directly)
    base_task = Task.get_task(
        project_name=args.project,
        task_name=args.base_task,
    )

    if not base_task:
        raise ValueError(
            f"Base task '{args.base_task}' in project '{args.project}' not found. "
            "Please run 'pixi run python train_mnist_remote.py' once first to create the base task."
        )

    # 3. Define hyperparameter search spaces
    parameters = [
        UniformParameterRange("General/learning_rate", min_value=0.0001, max_value=0.01, step_size=0.0005),
        DiscreteParameterRange("General/batch_size", values=[64, 128, 256]),
        DiscreteParameterRange("General/hidden_dim", values=[32, 64, 128]),
    ]

    # 4. Configure optimizer
    optimizer = HyperParameterOptimizer(
        base_task_id=base_task.id,
        hyper_parameters=parameters,
        objective_metric_title="Loss",
        objective_metric_series="Validation",
        objective_metric_sign="min",  # minimize validation loss
        optimizer_class=RandomSearch,  # or OptimizerOptuna for Bayesian search
        execution_queue=args.queue,
        max_number_of_concurrent_tasks=args.concurrency,
        total_max_jobs=args.jobs,
    )

    # 5. Start HPO sweep
    print(f"Starting ClearML HPO sweep: {args.jobs} jobs ({args.concurrency} concurrent) on queue '{args.queue}'...")
    optimizer.start()
    optimizer.wait()
    optimizer.stop()
    print("HPO sweep complete! Check ClearML UI for comparison.")


if __name__ == "__main__":
    main()