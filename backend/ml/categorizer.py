import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "category_model.pkl"

class TransactionCategorizer:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering"""
        df = df.copy()

        df["merchant_len"] = df["merchant"].str.len()
        df["amount_abs"] = df["amount"].abs()
        df["is_income"] = (df["amount"] > 0).astype(int)

        return df[["merchant_len", "amount_abs", "is_income"]]

    def train(self, transactions: list):
        """Train model from transactions"""
        if len(transactions) < 20:
            return False  # Not enough data

        df = pd.DataFrame([t.to_dict() for t in transactions])

        X = self.prepare_features(df)
        y = self.label_encoder.fit_transform(df["category"])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        self.model.fit(X_train, y_train)

        acc = accuracy_score(y_test, self.model.predict(X_test))
        print(f"✅ Category model trained | Accuracy: {acc:.2f}")

        joblib.dump((self.model, self.label_encoder), MODEL_PATH)
        return True

    def load(self):
        if MODEL_PATH.exists():
            self.model, self.label_encoder = joblib.load(MODEL_PATH)
            return True
        return False

    def predict(self, merchant: str, amount: float):
        if not self.model:
            if not self.load():
                return None

        data = pd.DataFrame([{
            "merchant": merchant,
            "amount": amount
        }])

        X = self.prepare_features(data)
        probs = self.model.predict_proba(X)[0]
        idx = np.argmax(probs)

        return {
            "category": self.label_encoder.inverse_transform([idx])[0],
            "confidence": probs[idx]
        }
