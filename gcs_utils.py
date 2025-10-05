from google.cloud import storage
import os

def upload_to_gcs(bucket_name, source_file, destination_blob):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"Uploaded {source_file} to gs://{bucket_name}/{destination_blob}")

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)
    upload_to_gcs("rf-demo-bucket", "outputs/nominal_design.csv", "nominal_design.csv")
