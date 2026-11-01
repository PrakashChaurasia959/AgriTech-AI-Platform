"""Quick validation script — run with: python tests/validate_production.py"""
import sys

def check(label, cond, msg=""):
    if cond:
        print(f"  ✅  {label}")
    else:
        print(f"  ❌  {label}: {msg}")
        sys.exit(1)

print("\n=== SmartAgri Production ML Validation ===\n")

# 1. Imports
from app.ml.disease_model import (
    classify_disease, DISEASE_DATABASE, PLANTVILLAGE_CLASSES,
    _load_keras_model, _keras_model,
)
from app.ml.crop_model import recommender, CROP_PROFILES, CROP_INFO
from app.core.config import settings

check("disease_model imports", True)
check("crop_model imports", True)
check(f"DISEASE_DATABASE has entries", len(DISEASE_DATABASE) >= 30, len(DISEASE_DATABASE))
check(f"PLANTVILLAGE_CLASSES has 38 entries", len(PLANTVILLAGE_CLASSES) == 38, len(PLANTVILLAGE_CLASSES))
check(f"CROP_PROFILES has 20 entries", len(CROP_PROFILES) == 20, len(CROP_PROFILES))
check(f"DISEASE_MODEL_MODE in config", settings.DISEASE_MODEL_MODE in ("demo","production"))
check(f"DISEASE_MODEL_PATH in config", bool(settings.DISEASE_MODEL_PATH))
check(f"CROP_MODEL_PATH in config", bool(settings.CROP_MODEL_PATH))

# 2. Demo mode prediction
import numpy as np
from PIL import Image
from io import BytesIO

img_arr = np.zeros((256, 256, 3), dtype="uint8")
img_arr[:, :, 1] = 110   # mostly green leaf
buf = BytesIO()
Image.fromarray(img_arr).save(buf, "JPEG")
buf.seek(0)

result = classify_disease(buf.read(), "Tomato")
check("Demo prediction executes", True)
check("Demo disease_name present", bool(result.get("disease_name")))
check("Demo confidence in [0,1]", 0 <= result["confidence"] <= 1, result["confidence"])
check("Demo is_demo_mode=True", result["is_demo_mode"] is True)
check("Demo symptoms present", len(result.get("symptoms", [])) > 0)
print(f"     └─ Demo result: {result['disease_name']} ({result['confidence']*100:.1f}%)")

# 3. All DB entries have required keys
required_keys = {"crop","disease_name","is_healthy","symptoms","causes","treatment","prevention"}
for key, info in DISEASE_DATABASE.items():
    missing = required_keys - set(info.keys())
    check(f"DB entry '{key}' complete", not missing, f"missing {missing}")

# 4. PlantVillage class map coverage
for cls in PLANTVILLAGE_CLASSES:
    if cls not in DISEASE_DATABASE:
        print(f"  ⚠   PLANTVILLAGE class '{cls}' has no DB entry (will use fallback)")

# 5. Crop recommendation
recommender.load_or_train()
check("Recommender loaded", recommender._loaded)
recs = recommender.recommend(80, 45, 40, 25, 70, 6.5, 120, top_k=3)
check("Recommender returns 3 crops", len(recs) == 3, len(recs))
for r in recs:
    check(f"  Rec '{r['crop']}' has confidence", 0 < r["confidence"] <= 1)
    check(f"  Rec '{r['crop']}' has tips",       len(r["farming_tips"]) > 0)
    check(f"  Rec '{r['crop']}' has fertiliser", len(r["fertilizer_suggestions"]) > 0)
print(f"     └─ Top crop: {recs[0]['crop']} ({recs[0]['confidence']*100:.1f}%)")

# 6. Config new fields
check("OPENWEATHER_API_KEY field exists", hasattr(settings, "OPENWEATHER_API_KEY"))
check("OPENWEATHER_BASE field exists",    hasattr(settings, "OPENWEATHER_BASE"))
check("DISEASE_MODEL_INPUT_SIZE field",   hasattr(settings, "DISEASE_MODEL_INPUT_SIZE"))
check("DISEASE_MODEL_NUM_CLASSES field",  hasattr(settings, "DISEASE_MODEL_NUM_CLASSES"))

print("\n=== All validation checks passed ✅ ===\n")
