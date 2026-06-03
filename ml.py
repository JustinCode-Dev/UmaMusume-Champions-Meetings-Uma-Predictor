import json
import os
import numpy as np
import pandas as pd
import sklearn 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report
from extract_features import extract


all_data = []
folder = "data/raw/input/cm_12_input"
for filename in os.listdir(folder):
    if filename.endswith(".json"):
        with open(os.path.join(folder, filename), "r") as b:
            input_data = json.load(b)
            all_data.append(input_data)

with open("data/raw/cm_data/cm_12.json", "r") as f:
    cm_data = json.load(f)     

rows = []
for uma in all_data:
    row = extract(uma, cm_data, training=True)
    rows.append(row)

df = pd.DataFrame(rows)
print(df.head())
print(df.shape)

df["top3"] = df["rank"].apply(lambda x: 1 if x <= 3 else 0)
X = df.drop(["rank", "top3"], axis=1)
y = df["top3"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print("accuracy:", accuracy_score(y_test, y_pred))
print("MAE:", mean_absolute_error(y_test, y_pred))
print(classification_report(y_test, y_pred))