import json
import pandas as pd
import numpy as np
import joblib
import re

from sklearn.base import clone
from sklearn.model_selection import train_test_split, KFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.utils.class_weight import compute_sample_weight

from extract_features import extract_conditions, extract_skills
from data_loader import data_load
from build_skill_list import build_skill_list

from xgboost import XGBClassifier
import lightgbm as lgb

def clean_name(c):
    c = (str(c).replace("◎", "_dbl")
               .replace("○", "_circ")
               .replace("×", "_x"))
    return re.sub(r'[^0-9a-zA-Z_]+', '_', c)

def simplify(r):
    if r == 1:
        return 1
    elif 2 <= r <= 3:
        return 2
    elif 4 <= r <= 6:
        return 3
    else:
        return 4
    
def data_preprocessing_1():

    with open("data/raw/rule.json", "r") as n:
        rules = json.load(n)

    with open("data/raw/skills.json", "r", encoding="utf-8") as q:
        skills_data = json.load(q)

    skill_rarity = {s["name"]: s["rarity"] for s in skills_data}

    all_data = data_load(["cm14_input", "cm17_input", "cm16_input", "cm18_input", "cm19_input", "cm20_input", "cm21_input"])

    threshold = {
            "unique skill": 15,
            "rare skill": 15,
            "normal skill": 50
        }
    
    frequent_skill = build_skill_list(all_data, skill_rarity, threshold)

    rows = []
    for uma in all_data:
        row = extract_skills(uma, rules, frequent_skill)
        rows.append(row)

    df = pd.DataFrame(rows)
    print("--- 5 Data Pertama ---")
    print(df.head())
    print("\n--- Ukuran Tabel (Baris, Kolom) ---")
    print(df.shape)

    X = df.drop(["rank"], axis=1)
    y = df["rank"]
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

    orig_cols = list(X.columns)
    clean_cols = [f"f{i}_" + clean_name(c) for i, c in enumerate(orig_cols)]
    col_map = dict(zip(clean_cols, orig_cols))
    X.columns = clean_cols

    return X, y, col_map

def data_preprocessing_2():

    with open("data/raw/rule.json", "r") as n:
        rules = json.load(n)

    all_data = data_load(["cm14_input", "cm17_input", "cm16_input", "cm18_input", "cm19_input", "cm20_input", "cm21_input"])

    rows = []
    for uma in all_data:
        row = extract_conditions(uma, rules)
        rows.append(row)

    df = pd.DataFrame(rows)

    print("--- 5 Data Pertama ---")
    print(df.head())
    print("\n--- Ukuran Tabel (Baris, Kolom) ---")
    print(df.shape)

    X = df.drop(["rank"], axis=1)             
    y = df["rank"]                                       
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

    return X, y

if __name__ == "__main__":

    custom_weight = {
        0: 5.53305,
        1: 3.231,
        2: 2.18,
        3: 1.612
    }

    X_1, y_1, col_map = data_preprocessing_1()
    y_simplified_1 = y_1.apply(simplify)
    y_simplified_1 = y_simplified_1 - 1

    X_2, y_2 = data_preprocessing_2()
    y_simplified_2 = y_2.apply(simplify)
    y_simplified_2 = y_simplified_2 - 1
    sample_weights = y_simplified_2.map(custom_weight)
    
    X_train_1, X_test_1, y_train_1, y_test_1= train_test_split(X_1, y_simplified_1, test_size=0.2, stratify=y_simplified_1, random_state=42)
    X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(X_2, y_simplified_2, test_size=0.2, stratify=y_simplified_2, random_state=42)
    
    assert (y_train_1.reset_index(drop=True) == y_train_2.reset_index(drop=True)).all(), "y is not aligned!"

    kf = KFold(n_splits=3, shuffle=True, random_state=42)

    def k_fold (model_blueprint, X_data, y_data, kf, X_test=None, use_eval_set=False, use_sample_weight=False, custom_weight='balanced', **fit_kwargs):
        n_classes = y_data.nunique()
        oof_proba = np.zeros((len(y_data), n_classes))
        test_proba_folds = np.zeros((kf.n_splits, len(X_test), n_classes)) if X_test is not None else None

        for fold, (train_idx, val_idx) in enumerate(kf.split(X_data, y_data)):
            model = clone(model_blueprint)
            X_train, X_val = X_data.iloc[train_idx], X_data.iloc[val_idx]
            y_train, y_val = y_data.iloc[train_idx], y_data.iloc[val_idx]

            sample_weight = compute_sample_weight(class_weight=custom_weight, y=y_train) if use_sample_weight else None

            if use_eval_set:
                model.fit(X_train, y_train, eval_set=[(X_val, y_val)], sample_weight=sample_weight, **fit_kwargs)
            else:
                model.fit(X_train, y_train, sample_weight=sample_weight) 

            oof_proba[val_idx] = model.predict_proba(X_val)

            if X_test is not None: 
                test_proba_folds[fold] = model.predict_proba(X_test)

        return oof_proba, test_proba_folds

    def evaluate(y_data, oof_proba, y_test=None, test_proba_fold=None, name=""):
        oof_class = np.argmax(oof_proba, axis=1)
        print(f"\n=========== {name} ===========")
        print(f"OOF accuracy: {accuracy_score(y_data, oof_class):.2%}")
        print(f"OOF MAE: {mean_absolute_error(y_data, oof_class):.3f}")
        print(confusion_matrix(y_data, oof_class))

        if test_proba_fold is not None:
            for fold in range(test_proba_fold.shape[0]):
                test_class = np.argmax(test_proba_fold[fold], axis=1)
                print(f"\nFold {fold} Test accuracy: {accuracy_score(y_test, test_class):.2%}")
                print(confusion_matrix(y_test, test_class))

            test_proba_avg = test_proba_fold.mean(axis=0)
            test_class_avg = np.argmax(test_proba_avg, axis=1)
            print(f"\nAvg Test accuracy: {accuracy_score(y_test, test_class_avg):.2%}")
            print(confusion_matrix(y_test, test_class_avg))
            print("\nTest Classification Report:")
            print(classification_report(y_test, test_class_avg, zero_division=0))
            
            return test_proba_avg

        return None

    def calculate_weird_event_rate_per_class(predictions_proba, actual_classes, n_classes=4, threshold=0.15):
        prediction_classes = np.argmax(predictions_proba, axis=1)

        rates = {}
        for cls in range(n_classes):
            mask = prediction_classes == cls
            if mask.sum() == 0:
                rates[cls] = 0.0
                continue

            subset_proba = predictions_proba[mask]
            subset_actual = actual_classes[mask]

            weird_count = 0
            for i in range(len(subset_actual)):
                proba_to_actual = subset_proba[i][subset_actual[i]]
                if proba_to_actual < threshold:
                    weird_count += 1

            rates[cls] = weird_count / mask.sum()

        return rates

    model_blueprint_rf = RandomForestClassifier(
        n_estimators=1000,
        max_depth=14,
        min_samples_leaf=5,
        min_samples_split=10,
        max_features='sqrt',
        n_jobs=-1,
        class_weight=custom_weight,
        random_state=42
    )
    
    model_blueprint_lgb = lgb.LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.4,
        num_leaves=15,           
        min_child_samples=25,    
        colsample_bytree=0.5,    
        subsample=0.7,
        subsample_freq=1,
        reg_lambda=15,
        random_state=42,
        verbose=-1,
        class_weight=custom_weight,
        max_depth=6
    )

    model_blueprint_xgb = XGBClassifier(
        n_estimators=2000,
        learning_rate=0.05,
        grow_policy='lossguide',   
        max_leaves=18,             
        min_child_weight=30,       
        colsample_bytree=0.5,
        subsample=0.7,
        reg_lambda=15,
        random_state=42,
        eval_metric='mlogloss',
    )

    lgb_model = model_blueprint_lgb.fit(X_1, y_simplified_1)
    xgb_model = model_blueprint_xgb.fit(X_2, y_simplified_2, sample_weight=sample_weights)

    joblib.dump(lgb_model, "model/ml/lgb_model.pkl")
    joblib.dump(xgb_model, "model/ml/xgb_model.pkl")

    oof_proba_lgb, test_proba_folds_lgb = k_fold(
        model_blueprint_lgb,
        X_train_1, y_train_1,
        kf,
        X_test=X_test_1,
        use_eval_set=True,
        eval_metric='multi_logloss',
        callbacks=[lgb.early_stopping(70), lgb.log_evaluation(0)],
    )

    oof_proba_xgb, test_proba_folds_xgb = k_fold(
        model_blueprint_xgb,
        X_train_2, y_train_2,
        kf,
        X_test=X_test_2,
        use_eval_set=True,
        use_sample_weight=True,
        custom_weight=custom_weight,
        verbose = False
    )
    
    cols_1 = [f"skill_class{i}" for i in range(oof_proba_lgb.shape[1])]
    cols_2 = [f"stats_class{i}" for i in range(oof_proba_xgb.shape[1])]

    meta_df_train = pd.DataFrame(oof_proba_lgb, columns=cols_1)
    meta_df_train[cols_2] = oof_proba_xgb
    print(meta_df_train.head())
    print(meta_df_train.shape)

    test_avg_1 = test_proba_folds_lgb.mean(axis=0)
    test_avg_2 = test_proba_folds_xgb.mean(axis=0)
 
    meta_df_test = pd.DataFrame(test_avg_1, columns=cols_1)
    meta_df_test[cols_2] = test_avg_2

    print(meta_df_test.shape)

    meta_model = LogisticRegression(
        max_iter=1000, 
        random_state=42,
        class_weight=custom_weight,
        solver='lbfgs',
        C=1.5
    )

    lr_model = meta_model.fit(meta_df_train, y_train_1)

    joblib.dump(lr_model, "model/ml/meta_model.pkl")

    meta_pred = meta_model.predict_proba(meta_df_test)

    prediction_classes = np.argmax(meta_pred, axis=1)

    test_avg_lgb = evaluate(y_train_1, oof_proba_lgb, y_test_1, test_proba_folds_lgb, name="LightGBM")
    
    test_avg_xgb = evaluate(y_train_2, oof_proba_xgb, y_test_2, test_proba_folds_xgb, name="XGBoost")
    print("\n====== LogisticRegression ======")
    print(f"Stacked accuracy: {accuracy_score(y_test_1, prediction_classes):.2%}")
    print(f"OOF MAE: {mean_absolute_error(y_test_1, prediction_classes):.3f}")
    print(confusion_matrix(y_test_1, prediction_classes))

    results_df = X_test_2.copy()

    results_df['actual_rank'] = y_test_2.values
    results_df['predicted_class'] = prediction_classes
    results_df['diff'] = (results_df['predicted_class'] - results_df['actual_rank']).abs()
    results_df = results_df.sort_values('diff', ascending=False)
    confident_wrong = results_df[results_df['predicted_class'] != results_df["actual_rank"]]
    confident_wrong.to_csv('prediction_review.csv', index=False)


    weird_rates = calculate_weird_event_rate_per_class(meta_pred, y_test_2.values, n_classes=4, threshold=0.25)
    for cls, rate in weird_rates.items():
        print(f"Class {cls}: {rate}")