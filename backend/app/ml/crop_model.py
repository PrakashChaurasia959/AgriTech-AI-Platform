"""
Crop recommendation — ML classifier.

Loading priority:
  1. If CROP_MODEL_PATH points to a valid .pkl / .joblib file (e.g. a model
     trained on the Kaggle Crop Recommendation Dataset), load it directly.
     The external model must expose `predict_proba(X)` and `classes_`
     (i.e. a scikit-learn Pipeline or classifier).

  2. Otherwise, auto-train a Random Forest on 3,000 synthetic samples
     that encode real agronomic optima for 20 major crops.
     The trained model is cached to  app/ml/crop_model.joblib  so subsequent
     restarts skip re-training.

Either way the public `recommender.recommend(...)` interface is identical.
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings

logger = logging.getLogger(__name__)

# Internal auto-trained model cache (inside the package directory)
_INTERNAL_CACHE = Path(__file__).parent / "crop_model.joblib"

# ──────────────────────────────────────────────────────────────────────────────
#  Agronomic knowledge base used for:
#    • Synthetic training-data generation (auto-train path)
#    • Fertiliser and farming-tip lookup (both paths)
# ──────────────────────────────────────────────────────────────────────────────
CROP_PROFILES: dict[str, dict] = {
    "Rice":       {"N":(60,100),  "P":(30,60),  "K":(35,55),  "temp":(20,35), "hum":(70,90), "ph":(5.5,7.0), "rain":(180,300)},
    "Wheat":      {"N":(70,110),  "P":(35,55),  "K":(30,50),  "temp":(10,25), "hum":(40,65), "ph":(6.0,7.5), "rain":(50,120)},
    "Maize":      {"N":(60,100),  "P":(30,55),  "K":(20,40),  "temp":(15,30), "hum":(50,75), "ph":(5.5,7.5), "rain":(60,150)},
    "Cotton":     {"N":(80,130),  "P":(35,55),  "K":(30,50),  "temp":(20,35), "hum":(50,70), "ph":(6.0,8.0), "rain":(50,120)},
    "Sugarcane":  {"N":(80,120),  "P":(30,50),  "K":(25,45),  "temp":(22,35), "hum":(60,85), "ph":(6.0,7.5), "rain":(70,150)},
    "Jute":       {"N":(60,90),   "P":(30,50),  "K":(25,45),  "temp":(22,35), "hum":(60,85), "ph":(5.5,7.0), "rain":(150,250)},
    "Potato":     {"N":(60,100),  "P":(30,50),  "K":(30,55),  "temp":(12,25), "hum":(60,85), "ph":(5.0,6.5), "rain":(50,120)},
    "Tomato":     {"N":(50,90),   "P":(25,50),  "K":(25,45),  "temp":(15,30), "hum":(50,75), "ph":(5.5,7.0), "rain":(40,100)},
    "Onion":      {"N":(50,80),   "P":(25,45),  "K":(25,45),  "temp":(13,28), "hum":(50,70), "ph":(5.8,7.0), "rain":(50,110)},
    "Banana":     {"N":(80,130),  "P":(35,60),  "K":(40,70),  "temp":(22,35), "hum":(70,90), "ph":(5.5,7.5), "rain":(100,200)},
    "Grapes":     {"N":(60,100),  "P":(30,55),  "K":(30,55),  "temp":(15,30), "hum":(50,70), "ph":(6.0,7.0), "rain":(40,100)},
    "Papaya":     {"N":(50,90),   "P":(25,50),  "K":(30,55),  "temp":(22,35), "hum":(60,85), "ph":(5.5,7.0), "rain":(80,180)},
    "Apple":      {"N":(10,40),   "P":(10,30),  "K":(15,35),  "temp":(5,20),  "hum":(60,85), "ph":(5.5,7.0), "rain":(80,120)},
    "Mango":      {"N":(60,100),  "P":(25,50),  "K":(30,55),  "temp":(22,38), "hum":(50,70), "ph":(5.5,7.5), "rain":(80,180)},
    "Orange":     {"N":(40,80),   "P":(20,45),  "K":(20,45),  "temp":(15,32), "hum":(55,80), "ph":(5.5,7.5), "rain":(80,150)},
    "Coffee":     {"N":(50,90),   "P":(25,50),  "K":(25,50),  "temp":(18,28), "hum":(70,90), "ph":(5.0,6.5), "rain":(120,250)},
    "Coconut":    {"N":(50,90),   "P":(20,45),  "K":(30,55),  "temp":(25,38), "hum":(70,90), "ph":(5.5,7.5), "rain":(100,250)},
    "Soybean":    {"N":(20,50),   "P":(20,45),  "K":(20,45),  "temp":(15,30), "hum":(60,85), "ph":(5.5,7.0), "rain":(60,150)},
    "Groundnut":  {"N":(20,50),   "P":(25,50),  "K":(25,50),  "temp":(18,32), "hum":(50,70), "ph":(5.5,7.5), "rain":(50,120)},
    "Chickpea":   {"N":(20,50),   "P":(25,55),  "K":(25,50),  "temp":(12,28), "hum":(40,65), "ph":(6.0,7.5), "rain":(40,100)},
}

CROP_INFO: dict[str, dict] = {
    "Rice":      {"description":"Staple cereal crop grown in flooded fields","soil":"Clayey, well-drained",
                  "tips":["Maintain 2-5 cm water level","Apply N in 3 splits","Use SRI method"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 50 kg/ha","MOP: 30 kg/ha"]},
    "Wheat":     {"description":"Major rabi cereal for bread production","soil":"Loamy, well-drained",
                  "tips":["Sow in October-November","Irrigate at critical stages","Use zero-tillage"],
                  "fertilizer":["Urea: 120 kg/ha","DAP: 60 kg/ha","MOP: 25 kg/ha"]},
    "Maize":     {"description":"Versatile cereal for food and fodder","soil":"Well-drained loamy",
                  "tips":["Maintain proper spacing","Apply N in splits","Control weeds early"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 50 kg/ha","MOP: 25 kg/ha"]},
    "Cotton":    {"description":"Important fibre crop","soil":"Black cotton soil",
                  "tips":["Use Bt cotton varieties","Monitor for bollworm","Proper plant population"],
                  "fertilizer":["Urea: 150 kg/ha","DAP: 60 kg/ha","MOP: 30 kg/ha"]},
    "Sugarcane": {"description":"Cash crop for sugar production","soil":"Deep loamy soil",
                  "tips":["Use sett treatment","Maintain adequate irrigation","Earthing up at 90 days"],
                  "fertilizer":["Urea: 200 kg/ha","DAP: 80 kg/ha","MOP: 40 kg/ha"]},
    "Jute":      {"description":"Natural fibre crop","soil":"Sandy loam, clay loam",
                  "tips":["Retting in clean water","Harvest at flowering stage","Maintain proper moisture"],
                  "fertilizer":["Urea: 60 kg/ha","DAP: 30 kg/ha","MOP: 25 kg/ha"]},
    "Potato":    {"description":"Important vegetable/tuber crop","soil":"Sandy loam",
                  "tips":["Use certified seed tubers","Hilling at 30-40 days","Control late blight"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 80 kg/ha","MOP: 80 kg/ha"]},
    "Tomato":    {"description":"Popular vegetable crop","soil":"Well-drained loamy",
                  "tips":["Stake plants for support","Mulch to retain moisture","Regular pest monitoring"],
                  "fertilizer":["Urea: 80 kg/ha","DAP: 50 kg/ha","MOP: 30 kg/ha"]},
    "Onion":     {"description":"Important bulb vegetable","soil":"Sandy loam",
                  "tips":["Transplant seedlings at 6 weeks","Regular irrigation","Harvest when tops fall"],
                  "fertilizer":["Urea: 60 kg/ha","DAP: 50 kg/ha","MOP: 40 kg/ha"]},
    "Banana":    {"description":"Tropical fruit crop","soil":"Deep, rich, well-drained",
                  "tips":["Use tissue culture plants","Provide propping support","Regular irrigation"],
                  "fertilizer":["Urea: 150 kg/ha","DAP: 80 kg/ha","MOP: 200 kg/ha"]},
    "Grapes":    {"description":"Vine fruit crop","soil":"Well-drained sandy loam",
                  "tips":["Prune for canopy management","Trellis system essential","Control powdery mildew"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 60 kg/ha","MOP: 80 kg/ha"]},
    "Papaya":    {"description":"Tropical fruit crop","soil":"Well-drained loamy",
                  "tips":["Plant in pits with organic matter","Maintain male-female ratio","Control ring spot virus"],
                  "fertilizer":["Urea: 80 kg/ha","DAP: 50 kg/ha","MOP: 80 kg/ha"]},
    "Apple":     {"description":"Temperate fruit crop","soil":"Well-drained loamy",
                  "tips":["Prune in dormant season","Control scab disease","Thinning for fruit quality"],
                  "fertilizer":["Urea: 40 kg/ha","DAP: 30 kg/ha","MOP: 35 kg/ha"]},
    "Mango":     {"description":"Tropical fruit king","soil":"Deep well-drained",
                  "tips":["Annual pruning","Control mango hopper","Fruiting every alternate year"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 60 kg/ha","MOP: 50 kg/ha"]},
    "Orange":    {"description":"Citrus fruit crop","soil":"Well-drained sandy loam",
                  "tips":["Budwood for quality","Regular irrigation","Control citrus canker"],
                  "fertilizer":["Urea: 80 kg/ha","DAP: 50 kg/ha","MOP: 60 kg/ha"]},
    "Coffee":    {"description":"Beverage crop","soil":"Well-drained loamy",
                  "tips":["Shade management essential","Pruning for productivity","Mulching recommended"],
                  "fertilizer":["Urea: 70 kg/ha","DAP: 40 kg/ha","MOP: 50 kg/ha"]},
    "Coconut":   {"description":"Tropical palm crop","soil":"Sandy loam to laterite",
                  "tips":["Regular irrigation","Organic matter application","Pest management"],
                  "fertilizer":["Urea: 100 kg/ha","DAP: 50 kg/ha","MOP: 150 kg/ha"]},
    "Soybean":   {"description":"Protein-rich legume crop","soil":"Well-drained loamy",
                  "tips":["Inoculate seeds with Rhizobium","Weed control early","Avoid excess nitrogen"],
                  "fertilizer":["DAP: 50 kg/ha","MOP: 20 kg/ha","Gypsum: 200 kg/ha"]},
    "Groundnut": {"description":"Oilseed legume crop","soil":"Sandy loam",
                  "tips":["Inoculate with Rhizobium","Gypsum at flowering","Earthing up for pod development"],
                  "fertilizer":["DAP: 40 kg/ha","MOP: 25 kg/ha","Gypsum: 250 kg/ha"]},
    "Chickpea":  {"description":"Important rabi pulse crop","soil":"Well-drained sandy loam",
                  "tips":["Inoculate with Rhizobium","Sow in October","Control pod borer"],
                  "fertilizer":["DAP: 50 kg/ha","MOP: 20 kg/ha","Sulphur: 20 kg/ha"]},
}

FEATURE_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


# ──────────────────────────────────────────────────────────────────────────────
#  Synthetic data generator (used only when no external pkl is available)
# ──────────────────────────────────────────────────────────────────────────────

def _generate_training_data(n_per_crop: int = 150) -> pd.DataFrame:
    rng = np.random.RandomState(42)
    rows = []
    for crop, p in CROP_PROFILES.items():
        for _ in range(n_per_crop):
            rows.append({
                "N":           rng.uniform(*p["N"]),
                "P":           rng.uniform(*p["P"]),
                "K":           rng.uniform(*p["K"]),
                "temperature": rng.uniform(*p["temp"]),
                "humidity":    rng.uniform(*p["hum"]),
                "ph":          rng.uniform(*p["ph"]),
                "rainfall":    rng.uniform(*p["rain"]),
                "label":       crop,
            })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
#  CropRecommender
# ──────────────────────────────────────────────────────────────────────────────

class CropRecommender:
    """
    Wraps a scikit-learn Pipeline (StandardScaler + RandomForestClassifier).

    Loading priority (resolved in load_or_train):
      1. External pkl at settings.CROP_MODEL_PATH  (user-supplied Kaggle model)
      2. Internal cache at _INTERNAL_CACHE          (auto-trained on startup)
      3. Train from scratch and save to internal cache
    """

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self._loaded = False

    # ── Loading ───────────────────────────────────────────────────────────────

    def _try_load_external(self) -> bool:
        """Return True if an external pkl was loaded successfully."""
        ext_path = Path(settings.CROP_MODEL_PATH)
        if not ext_path.exists():
            return False
        try:
            obj = joblib.load(ext_path)
            # Support two formats:
            #  (a) plain Pipeline / classifier  →  obj itself is the model
            #  (b) dict with "pipeline" key     →  our own saved format
            if isinstance(obj, dict):
                self.pipeline = obj.get("pipeline") or obj.get("model")
            else:
                self.pipeline = obj
            if self.pipeline is None:
                raise ValueError("Could not find pipeline/model key in loaded dict")
            self._loaded = True
            logger.info(
                "Crop model loaded from external pkl: %s  (classes: %s)",
                ext_path,
                list(getattr(self.pipeline, "classes_", getattr(
                    self.pipeline.named_steps.get("classifier"), "classes_", ["?"]
                ))),
            )
            return True
        except Exception as exc:
            logger.warning("Failed to load external crop model (%s): %s", ext_path, exc)
            return False

    def _try_load_internal_cache(self) -> bool:
        """Return True if the internal auto-trained cache was loaded."""
        if not _INTERNAL_CACHE.exists():
            return False
        try:
            obj = joblib.load(_INTERNAL_CACHE)
            self.pipeline = obj["pipeline"]
            self._loaded = True
            logger.info("Crop model loaded from internal cache: %s", _INTERNAL_CACHE)
            return True
        except Exception as exc:
            logger.warning("Internal cache load failed (%s): %s — will retrain.", _INTERNAL_CACHE, exc)
            return False

    def train(self) -> None:
        """Train Random Forest on synthetic agronomic data."""
        logger.info("Training crop recommendation model on synthetic data…")
        df = _generate_training_data()
        X = df[FEATURE_COLS]
        y = df["label"]
        self.pipeline = Pipeline([
            ("scaler",     StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=200, max_depth=14, random_state=42, n_jobs=-1)),
        ])
        self.pipeline.fit(X, y)
        self._loaded = True
        logger.info("Crop model trained on %d samples, %d crops.", len(df), len(y.unique()))

    def save_internal(self) -> None:
        """Persist the auto-trained model to the internal cache."""
        try:
            joblib.dump({"pipeline": self.pipeline}, _INTERNAL_CACHE)
            logger.info("Crop model saved to %s", _INTERNAL_CACHE)
        except Exception as exc:
            logger.warning("Could not save crop model: %s", exc)

    def load_or_train(self) -> None:
        """Resolve the model using the three-step priority chain."""
        if self._try_load_external():
            return
        if self._try_load_internal_cache():
            return
        self.train()
        self.save_internal()

    # ── Inference ─────────────────────────────────────────────────────────────

    def recommend(
        self,
        N: float, P: float, K: float,
        temperature: float, humidity: float,
        ph: float, rainfall: float,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Return top-k crop recommendations with confidence scores,
        farming tips, and fertiliser suggestions.

        The pipeline must expose `predict_proba` and `classes_`
        (satisfied by all scikit-learn Pipelines with a classifier step).
        """
        if not self._loaded:
            self.load_or_train()

        X = pd.DataFrame(
            [[N, P, K, temperature, humidity, ph, rainfall]],
            columns=FEATURE_COLS,
        )
        probs   = self.pipeline.predict_proba(X)[0]
        classes = self.pipeline.classes_

        top_idx = np.argsort(probs)[::-1][:top_k]
        results = []
        for idx in top_idx:
            crop = classes[idx]
            conf = float(probs[idx])
            if conf < 0.01:
                continue
            info = CROP_INFO.get(crop, {
                "description": f"{crop} crop",
                "soil":        "Various soil types",
                "tips":        ["Consult local agricultural extension"],
                "fertilizer":  ["Balanced NPK fertiliser"],
            })
            suitability = (
                "Excellent" if conf > 0.40 else
                "Good"      if conf > 0.20 else
                "Fair"
            )
            results.append({
                "crop":                 crop,
                "confidence":           round(conf, 4),
                "suitability":          suitability,
                "description":          info["description"],
                "farming_tips":         info["tips"],
                "fertilizer_suggestions": info["fertilizer"],
            })
        return results


# ── Singleton ─────────────────────────────────────────────────────────────────
recommender = CropRecommender()
