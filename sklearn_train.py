import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import os


def train_local_model(input_csv="outputs/nominal_design.csv",
                      model_path="outputs/rf_model.pkl"):
    # Load your simulated dataset
    df = pd.read_csv(input_csv)

    # Encode target
    y = df["coverage_ok"].map({"yes": 1, "no": 0})

    # Features: drop target and any non-numeric columns (e.g., site_id)
    X = df.drop(columns=["coverage_ok"], errors="ignore")
    X = X.select_dtypes(include=["number"])  # keep numeric only
    feature_names = list(X.columns)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train RandomForest
    clf = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )
    clf.fit(X_train, y_train)

    # Evaluate
    preds = clf.predict(X_test)
    print("Classification Report:\n", classification_report(y_test, preds))

    # Save model and feature names
    os.makedirs("outputs", exist_ok=True)
    artifact = {"model": clf, "feature_names": feature_names}
    joblib.dump(artifact, model_path)
    print(f"✅ Model saved → {model_path} (features: {feature_names})")

    return model_path


