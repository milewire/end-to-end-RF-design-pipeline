# vertex_train.py
from google.cloud import aiplatform

def train_and_deploy(bucket: str, project_id: str, location: str):
    aiplatform.init(project=project_id, location=location, staging_bucket=bucket)

    job = aiplatform.AutoMLTabularTrainingJob(
        display_name="rf_nominal_training",
        optimization_prediction_type="classification",
        optimization_objective="minimize-log-loss",  # valid objective
    )

    # Point to the dataset already uploaded
    dataset = aiplatform.TabularDataset.create(
        display_name="rf_nominal_dataset",
        gcs_source=[f"gs://{bucket}/nominal_design.csv"]
    )

    model = job.run(
        dataset=dataset,
        target_column="coverage_ok",
        model_display_name="rf_nominal_model",
        training_fraction_split=0.7,
        validation_fraction_split=0.2,
        test_fraction_split=0.1,
        budget_milli_node_hours=1000,
        disable_early_stopping=False,
        sync=True,
    )

    endpoint = model.deploy(
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=1,
        sync=True,
    )

    return endpoint
