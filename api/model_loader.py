"""
BlockML-Gov Model Loader v1.0
Automatic library detection and installation
Supports any ML algorithm
"""
import subprocess
import sys
import pickle
import importlib
import os
import hashlib
from typing import Optional

# ── Library mapping ──────────────────────────────────
# model_class_name → (pip_package, import_module)
LIBRARY_MAP = {
    # Scikit-learn (usually pre-installed)
    "RandomForestClassifier":     ("scikit-learn", "sklearn"),
    "GradientBoostingClassifier": ("scikit-learn", "sklearn"),
    "LogisticRegression":         ("scikit-learn", "sklearn"),
    "SVC":                        ("scikit-learn", "sklearn"),
    "LinearSVC":                  ("scikit-learn", "sklearn"),
    "DecisionTreeClassifier":     ("scikit-learn", "sklearn"),
    "ExtraTreesClassifier":       ("scikit-learn", "sklearn"),
    "AdaBoostClassifier":         ("scikit-learn", "sklearn"),
    "BaggingClassifier":          ("scikit-learn", "sklearn"),
    "MLPClassifier":              ("scikit-learn", "sklearn"),
    "KNeighborsClassifier":       ("scikit-learn", "sklearn"),

    # XGBoost
    "XGBClassifier":              ("xgboost", "xgboost"),
    "XGBRegressor":               ("xgboost", "xgboost"),

    # LightGBM
    "LGBMClassifier":             ("lightgbm", "lightgbm"),
    "LGBMRegressor":              ("lightgbm", "lightgbm"),

    # CatBoost
    "CatBoostClassifier":         ("catboost", "catboost"),
    "CatBoostRegressor":          ("catboost", "catboost"),

    # Imbalanced-learn
    "BalancedRandomForestClassifier": (
        "imbalanced-learn", "imblearn"),
    "EasyEnsembleClassifier":     ("imbalanced-learn", "imblearn"),

    # PyTorch (basic wrapper)
    "Sequential":                 ("torch", "torch"),

    # TensorFlow/Keras
    "Functional":                 ("tensorflow", "tensorflow"),
}

# ── SHAP explainer mapping ───────────────────────────
SHAP_MAP = {
    "tree": [
        "RandomForestClassifier",
        "GradientBoostingClassifier",
        "XGBClassifier","XGBRegressor",
        "LGBMClassifier","LGBMRegressor",
        "CatBoostClassifier","CatBoostRegressor",
        "DecisionTreeClassifier",
        "ExtraTreesClassifier",
        "AdaBoostClassifier",
        "BalancedRandomForestClassifier"
    ],
    "linear": [
        "LogisticRegression",
        "LinearSVC", "Ridge",
        "Lasso", "ElasticNet"
    ],
    "deep": [
        "Sequential", "Functional"
    ],
    "kernel": [
        "SVC", "KNeighborsClassifier",
        "MLPClassifier"
    ]
}

def get_shap_explainer_type(model_type: str) -> str:
    """Get the appropriate SHAP explainer type"""
    for explainer, models in SHAP_MAP.items():
        if model_type in models:
            return explainer
    return "kernel"  # Universal fallback

def check_library_installed(import_module: str) -> bool:
    """Check if a library is installed"""
    try:
        importlib.import_module(import_module)
        return True
    except ImportError:
        return False

def install_library(pip_package: str) -> dict:
    """
    Automatically install a missing library
    Returns installation result
    """
    print(f"📦 Installing {pip_package}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install",
             pip_package, "--quiet",
             "--break-system-packages"],
            capture_output=True, text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"✅ {pip_package} installed successfully")
            return {
                "success": True,
                "package": pip_package,
                "message": f"{pip_package} installed"
            }
        else:
            print(f"❌ Failed to install {pip_package}: "
                  f"{result.stderr}")
            return {
                "success": False,
                "package": pip_package,
                "message": result.stderr[:200]
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "package": pip_package,
            "message": "Installation timeout (>120s)"
        }
    except Exception as e:
        return {
            "success": False,
            "package": pip_package,
            "message": str(e)
        }

def load_model_safe(model_path: str) -> dict:
    """
    Load model with automatic library installation
    Returns model info and status
    """
    if not os.path.exists(model_path):
        return {
            "success": False,
            "error": f"File not found: {model_path}"
        }

    # Compute hash
    with open(model_path, "rb") as f:
        content = f.read()
    model_hash = "sha256:" + hashlib.sha256(
        content).hexdigest()

    # Try loading directly first
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        model_type = type(model).__name__
        return _build_result(model, model_type,
                             model_hash, model_path,
                             installed=False)
    except ModuleNotFoundError as e:
        # Extract missing module name
        missing = str(e).split("'")[1] \
            if "'" in str(e) else str(e)
        print(f"⚠️ Missing module: {missing}")

        # Find the pip package to install
        pip_pkg = _find_pip_package(missing)
        if not pip_pkg:
            return {
                "success": False,
                "error": f"Unknown library: {missing}",
                "missing_module": missing
            }

        # Install it
        install_result = install_library(pip_pkg)
        if not install_result["success"]:
            return {
                "success": False,
                "error": f"Failed to install {pip_pkg}",
                "install_error": install_result["message"]
            }

        # Retry loading after installation
        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            model_type = type(model).__name__
            return _build_result(
                model, model_type, model_hash,
                model_path, installed=True,
                installed_package=pip_pkg)
        except Exception as e2:
            return {
                "success": False,
                "error": f"Still failed after install: {e2}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Load error: {str(e)}"
        }

def load_model_from_bytes(content: bytes,
                          tmp_path: str) -> dict:
    """
    Load model from bytes with auto-install
    Used during upload
    """
    # Write to temp file
    with open(tmp_path, "wb") as f:
        f.write(content)

    result = load_model_safe(tmp_path)
    return result

def _build_result(model, model_type: str,
                  model_hash: str, model_path: str,
                  installed: bool = False,
                  installed_package: str = None) -> dict:
    """Build standardized result dict"""
    shap_type = get_shap_explainer_type(model_type)

    # Get library info
    lib_info = LIBRARY_MAP.get(model_type,
                               ("unknown", "unknown"))

    return {
        "success":           True,
        "model":             model,
        "model_type":        model_type,
        "model_hash":        model_hash,
        "model_path":        model_path,
        "n_features":        getattr(model,
                                "n_features_in_", "N/A"),
        "shap_explainer":    shap_type,
        "library":           lib_info[0],
        "auto_installed":    installed,
        "installed_package": installed_package,
        "supports_shap":     shap_type != "kernel",
        "classes":           getattr(model,
                                "classes_", [0, 1]).tolist()
                             if hasattr(model, "classes_")
                             else [0, 1]
    }

def _find_pip_package(missing_module: str) -> Optional[str]:
    """Find pip package name from missing module"""
    # Direct module → package mapping
    module_to_pip = {
        "xgboost":    "xgboost",
        "lightgbm":   "lightgbm",
        "catboost":   "catboost",
        "imblearn":   "imbalanced-learn",
        "sklearn":    "scikit-learn",
        "torch":      "torch",
        "tensorflow": "tensorflow",
        "keras":      "tensorflow",
        "cv2":        "opencv-python",
        "PIL":        "Pillow",
    }

    # Check direct match
    if missing_module in module_to_pip:
        return module_to_pip[missing_module]

    # Check partial match
    for mod, pkg in module_to_pip.items():
        if mod in missing_module:
            return pkg

    # Try using module name as package name
    return missing_module

def create_shap_explainer(model,
                          model_type: str,
                          X_background=None):
    """
    Create appropriate SHAP explainer
    for any model type
    """
    import shap
    explainer_type = get_shap_explainer_type(model_type)

    try:
        if explainer_type == "tree":
            return shap.TreeExplainer(model)

        elif explainer_type == "linear":
            if X_background is not None:
                return shap.LinearExplainer(
                    model, X_background)
            return shap.LinearExplainer(
                model,
                shap.maskers.Independent(X_background)
                if X_background is not None
                else None)

        elif explainer_type == "deep":
            if X_background is not None:
                return shap.DeepExplainer(
                    model, X_background[:100])
            return None

        else:  # kernel — universal fallback
            if X_background is not None:
                background = shap.sample(
                    X_background, 100)
                return shap.KernelExplainer(
                    model.predict_proba, background)
            return None

    except Exception as e:
        print(f"⚠️ SHAP explainer error: {e}")
        return None

def compute_global_shap(model,
                        model_type: str,
                        X_sample,
                        feature_names: list) -> dict:
    """
    Compute GLOBAL SHAP values for a model
    (not per transaction — on full sample)
    Used after model upload for ML Engineer review
    """
    try:
        import shap
        import numpy as np

        explainer = create_shap_explainer(
            model, model_type, X_sample)

        if explainer is None:
            return {"error": "Explainer not available"}

        # Compute SHAP values
        shap_values = explainer.shap_values(X_sample)

        # Handle different output formats
        if isinstance(shap_values, list):
            # Binary classification → use fraud class
            vals = shap_values[1]
        else:
            vals = shap_values

        # Global feature importance
        mean_abs = np.abs(vals).mean(axis=0)

        features = []
        for i, fname in enumerate(feature_names):
            features.append({
                "feature":    fname,
                "importance": round(float(mean_abs[i]), 4),
                "rank":       0
            })

        features.sort(
            key=lambda x: x["importance"], reverse=True)
        for i, f in enumerate(features):
            f["rank"] = i + 1

        return {
            "model_type":        model_type,
            "explainer_type":    get_shap_explainer_type(
                model_type),
            "n_samples":         len(X_sample),
            "n_features":        len(feature_names),
            "global_importance": features,
            "top_5_features":    features[:5],
            "computed_at":       __import__(
                "datetime").datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"⚠️ Global SHAP error: {e}")
        return {"error": str(e)}
