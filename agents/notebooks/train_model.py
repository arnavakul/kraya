import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

os.makedirs("../models", exist_ok=True)
np.random.seed(42)
n_samples = 2000

# Generate realistic synthetic procurement training data
data = {
    'price_variance_pct': np.random.uniform(-0.20, 0.25, n_samples),
    'tco_markup_pct': np.random.uniform(0.0, 0.15, n_samples),
    'lead_time_days_delta': np.random.uniform(-5, 15, n_samples),
    'historical_delay_avg_days': np.random.choice([np.nan, 0.0, 1.2, 3.5, 7.0], size=n_samples, p=[0.2, 0.4, 0.2, 0.1, 0.1]),
    'historical_defect_rate': np.random.choice([np.nan, 0.0, 0.02, 0.05, 0.12], size=n_samples, p=[0.2, 0.5, 0.15, 0.1, 0.05]),
    'payment_terms_penalty': np.random.choice([0.0, 0.5, 1.0], size=n_samples),
    'warranty_months': np.random.choice([6, 12, 24, 36], size=n_samples),
    'category_experience_years': np.random.uniform(0.5, 10.0, n_samples),
    'extraction_completeness_pct': np.random.uniform(0.7, 1.0, n_samples),
    'anomaly_lowball_flag': np.random.choice([0.0, 1.0], size=n_samples, p=[0.95, 0.05])
}

df = pd.DataFrame(data)

# Impute missing values with neutral defaults for training
df_filled = df.fillna({
    'historical_delay_avg_days': 0.0,
    'historical_defect_rate': 0.0
})

# Formulate ground truth synthetic quality score (0-100)
scores = (
    75.0
    - (df_filled['price_variance_pct'] * 40)
    - (df_filled['tco_markup_pct'] * 30)
    - (df_filled['lead_time_days_delta'] * 1.5)
    - (df_filled['historical_delay_avg_days'] * 2.5)
    - (df_filled['historical_defect_rate'] * 100)
    - (df_filled['payment_terms_penalty'] * 5)
    + (df_filled['warranty_months'] * 0.3)
    + (df_filled['category_experience_years'] * 0.8)
    + (df_filled['extraction_completeness_pct'] * 10)
    - (df_filled['anomaly_lowball_flag'] * 15)
)
df_filled['target_score'] = np.clip(scores, 0, 100)

X = df_filled.drop(columns=['target_score'])
y = df_filled['target_score']

model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
model.fit(X, y)

model_path = "../models/evaluation_xgb_v1.bin"
joblib.dump(model, model_path)
print(f"Model successfully trained and saved to {model_path}")