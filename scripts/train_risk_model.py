"""
Train ML model for rainfall-based risk assessment
Random Forest classifier for high rainfall event prediction
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import json
from datetime import datetime

def engineer_features(df):
    """Create features for ML model"""
    
    print("\nEngineering features...")
    
    # Parse timestamp
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    
    # Time-based features
    df['hour'] = df['timestamp_dt'].dt.hour
    df['day_of_week'] = df['timestamp_dt'].dt.dayofweek
    df['month'] = df['timestamp_dt'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Sort by station and time for rolling calculations
    df = df.sort_values(['station_id', 'timestamp_dt'])
    
    # Calculate rolling rainfall windows
    print("  Calculating rolling windows...")
    df['rainfall_15min'] = df.groupby('station_id')['reading_value'].transform(
        lambda x: x.rolling(window=3, min_periods=1).sum()
    )
    df['rainfall_1hr'] = df.groupby('station_id')['reading_value'].transform(
        lambda x: x.rolling(window=12, min_periods=1).sum()
    )
    df['rainfall_3hr'] = df.groupby('station_id')['reading_value'].transform(
        lambda x: x.rolling(window=36, min_periods=1).sum()
    )
    
    # Lag features
    df['rainfall_lag1'] = df.groupby('station_id')['reading_value'].shift(1).fillna(0)
    df['rainfall_lag2'] = df.groupby('station_id')['reading_value'].shift(2).fillna(0)
    
    # Station location features (already in data)
    # longitude, latitude
    
    return df

def create_labels(df, threshold_mm_per_hr=30):
    """Create binary labels for high rainfall events"""
    
    # Convert 5-minute reading to hourly rate
    df['rainfall_rate_mm_per_hr'] = df['reading_value'] * 12
    
    # Label high rainfall events (>30 mm/hr is considered high risk)
    df['high_rainfall_event'] = (df['rainfall_rate_mm_per_hr'] > threshold_mm_per_hr).astype(int)
    
    print(f"\nLabel distribution:")
    print(f"  High rainfall events: {df['high_rainfall_event'].sum():,} ({df['high_rainfall_event'].mean()*100:.2f}%)")
    print(f"  Normal conditions: {(df['high_rainfall_event']==0).sum():,} ({(df['high_rainfall_event']==0).mean()*100:.2f}%)")
    
    return df

def train_model():
    """Train Random Forest classifier"""
    
    print("="*80)
    print("Training Rainfall Risk Assessment Model")
    print("="*80)
    
    # Load sample data from database
    import sqlite3
    db_path = Path("data/drainguard.db")
    
    print(f"\nLoading data from: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # Load rainfall readings
    df = pd.read_sql_query("""
        SELECT timestamp, station_id, station_name, 
               longitude, latitude, reading_value
        FROM rainfall_readings
        ORDER BY timestamp, station_id
    """, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} records")
    
    # Engineer features
    df = engineer_features(df)
    
    # Create labels
    df = create_labels(df, threshold_mm_per_hr=30)
    
    # Remove rows with NaN values
    df = df.dropna()
    
    # Select features for training
    feature_columns = [
        'reading_value',
        'rainfall_15min',
        'rainfall_1hr',
        'rainfall_3hr',
        'rainfall_lag1',
        'rainfall_lag2',
        'hour',
        'day_of_week',
        'month',
        'is_weekend',
        'longitude',
        'latitude'
    ]
    
    X = df[feature_columns]
    y = df['high_rainfall_event']
    
    print(f"\nFeatures: {len(feature_columns)}")
    print(f"Samples: {len(X):,}")
    
    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train):,} samples")
    print(f"Test set: {len(X_test):,} samples")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("\nTraining Random Forest classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    print("✓ Model training complete")
    
    # Evaluate on test set
    print("\n" + "="*80)
    print("Model Evaluation")
    print("="*80)
    
    y_pred = rf_model.predict(X_test_scaled)
    y_pred_proba = rf_model.predict_proba(X_test_scaled)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'High Rainfall']))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"True Negatives: {cm[0][0]:,}  | False Positives: {cm[0][1]:,}")
    print(f"False Negatives: {cm[1][0]:,} | True Positives: {cm[1][1]:,}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    for _, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:<20}: {row['importance']:.4f}")
    
    # Save model and artifacts
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print(f"\nSaving model artifacts to: {models_dir}")
    
    # Save model
    model_path = models_dir / "risk_assessment_rf.pkl"
    joblib.dump(rf_model, model_path)
    print(f"✓ Saved model: {model_path}")
    
    # Save scaler
    scaler_path = models_dir / "feature_scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"✓ Saved scaler: {scaler_path}")
    
    # Save feature names
    features_path = models_dir / "feature_names.json"
    with open(features_path, 'w') as f:
        json.dump(feature_columns, f, indent=2)
    print(f"✓ Saved feature names: {features_path}")
    
    # Save metadata
    metadata = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "training_date": datetime.now().isoformat(),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features": feature_columns,
        "threshold_mm_per_hr": 30,
        "test_accuracy": float((y_pred == y_test).mean()),
        "feature_importance": feature_importance.to_dict('records')
    }
    
    metadata_path = models_dir / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata: {metadata_path}")
    
    return rf_model, scaler, feature_columns

if __name__ == "__main__":
    model, scaler, features = train_model()
    print("\n" + "="*80)
    print("Model Training Complete!")
    print("="*80)
    print("\nModel files saved in models/ directory")
    print("Ready for integration into backend API")
