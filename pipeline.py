import os
import logging
import argparse
from simulate import simulate_nominal_design
from gcs_utils import upload_to_gcs
from sklearn_train import train_local_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def main(args):
    try:
        # 1. Ensure folders
        os.makedirs(args.outputs_dir, exist_ok=True)
        logger.info(f"Ensured output directory: {args.outputs_dir}")

        # 2. Run simulation
        logger.info("Starting simulation...")
        simulate_nominal_design(args.input_csv, os.path.join(args.outputs_dir, args.output_csv))
        logger.info("Simulation complete.")

        # 3. Upload to GCS
        logger.info("Uploading results to GCS...")
        upload_to_gcs(args.bucket, os.path.join(args.outputs_dir, args.output_csv), args.gcs_blob)
        logger.info("Upload complete.")

        # 4. Train local model instead of Vertex AI
        logger.info("Training local RandomForest model...")
        model_path = train_local_model(os.path.join(args.outputs_dir, args.output_csv))
        logger.info(f"Local model ready at: {model_path}")

        logger.info("🎯 End-to-end pipeline complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrate the end-to-end RF design pipeline.")
    parser.add_argument('--input_csv', type=str, default='data/candidates.csv', help='Path to input candidates CSV')
    parser.add_argument('--outputs_dir', type=str, default='outputs', help='Directory for output files')
    parser.add_argument('--output_csv', type=str, default='nominal_design.csv', help='Output CSV filename')
    parser.add_argument('--bucket', type=str, default='rf-demo-bucket', help='GCS bucket name')
    parser.add_argument('--gcs_blob', type=str, default='nominal_design.csv', help='GCS blob name for upload')
    parser.add_argument('--project_id', type=str, default='rf-demo-vertex', help='Google Cloud project ID')
    parser.add_argument('--location', type=str, default='us-central1', help='Vertex AI location')
    args = parser.parse_args()
    main(args)
