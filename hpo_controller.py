from clearml.automation import (
    DiscreteParameterRange,
    UniformParameterRange,
    HyperParameterOptimizer,
    RandomSearch,
)
from clearml.automation.optuna import OptimizerOptuna  # optional: or RandomSearch
from clearml import Task


def main():
    # 1. Initialize controller task in ClearML
    Task.init(
        project_name="clearml-test",
        task_name="mnist-hpo-controller",
        task_type=Task.TaskTypes.optimizer,
        reuse_last_task_id=False,
    )

    # 2. Find base task template (or specify task_id directly)
    base_task = Task.get_task(
        project_name="clearml-test",
        task_name="mnist-training",
    )

    if not base_task:
        raise ValueError(
            "Base task 'mnist-training' in project 'clearml-test' not found. "
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
        execution_queue="gpu_queue",   # queue where daemon workers listen
        max_number_of_concurrent_tasks=2,  # concurrent tasks (e.g. 1 per GPU)
        total_max_jobs=10,                 # total experiments
    )

    # 5. Start HPO sweep
    print("Starting ClearML Hyperparameter Optimization sweep...")
    optimizer.start()
    optimizer.wait()
    optimizer.stop()
    print("HPO sweep complete! Check ClearML UI for comparison.")


if __name__ == "__main__":
    main()