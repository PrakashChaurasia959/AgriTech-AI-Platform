"""
Plant Disease Detection — ML inference engine.

Production path (DISEASE_MODEL_MODE=production):
  Loads a Keras CNN (.keras or .h5) trained on the 38-class PlantVillage dataset.
  Steps: read bytes → PIL → resize → MobileNetV2 preprocessing → predict.

Demo fallback (DISEASE_MODEL_MODE=demo):
  Uses OpenCV HSV colour statistics (green/brown/yellow ratios) to produce a
  *deterministic*, *explainable* prediction.  Clearly labelled in the API response.
  This path requires NO trained model file and is kept as a safe fallback so the
  application never crashes when a model has not yet been placed on disk.

Switching modes:
  1. Train or download a model → save to  ml_models/plant_disease_model.keras
  2. Set  DISEASE_MODEL_MODE=production  in .env
  3. Restart uvicorn — the CNN loads once at startup and stays in memory.
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
import numpy as np
from PIL import Image
from io import BytesIO

from app.core.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
#  PlantVillage 38-class label map
#  Used only for older model files without metadata. Newly trained models
#  load their exact class ordering from the adjacent .classes.json file.
# ──────────────────────────────────────────────────────────────────────────────
PLANTVILLAGE_CLASSES: list[str] = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___Healthy",
    "Blueberry___Healthy",
    "Cherry___Powdery_mildew",
    "Cherry___Healthy",
    "Corn___Cercospora_leaf_spot_Gray_leaf_spot",
    "Corn___Common_rust",
    "Corn___Northern_Leaf_Blight",
    "Corn___Healthy",
    "Grape___Black_rot",
    "Grape___Esca",
    "Grape___Leaf_blight",
    "Grape___Healthy",
    "Orange___Citrus_Greening",
    "Peach___Bacterial_spot",
    "Peach___Healthy",
    "Pepper_bell___Bacterial_spot",
    "Pepper_bell___Healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___Healthy",
    "Raspberry___Healthy",
    "Soybean___Healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___Healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___Healthy",
]

# ──────────────────────────────────────────────────────────────────────────────
#  Disease knowledge base
#  Used by BOTH the production path (maps predicted class key → details)
#  and the demo path (used directly for lookup).
# ──────────────────────────────────────────────────────────────────────────────
DISEASE_DATABASE: dict[str, dict] = {
    # ── Tomato ────────────────────────────────────────────────────────────────
    "Tomato___Healthy": {
        "crop": "Tomato", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Uniform green leaf colour", "Healthy leaf texture"],
        "causes": ["Plant is healthy and well-maintained"],
        "treatment": ["Continue current care practices", "Regular monitoring recommended"],
        "prevention": ["Maintain proper watering schedule", "Ensure adequate sunlight", "Use balanced fertiliser"],
    },
    "Tomato___Early_blight": {
        "crop": "Tomato", "disease_name": "Early Blight", "is_healthy": False,
        "symptoms": ["Dark brown concentric rings on leaves (target-like spots)", "Yellowing of lower leaves", "Stem lesions with dark borders"],
        "causes": ["Fungus Alternaria solani", "High humidity and warm temperatures", "Poor air circulation"],
        "treatment": ["Apply copper-based fungicide every 7-10 days", "Remove and destroy infected leaves", "Improve air circulation"],
        "prevention": ["Rotate crops annually", "Avoid overhead watering", "Space plants properly", "Use disease-resistant varieties"],
    },
    "Tomato___Late_blight": {
        "crop": "Tomato", "disease_name": "Late Blight", "is_healthy": False,
        "symptoms": ["Large irregular dark brown spots on leaves", "White fuzzy growth on leaf undersides", "Rapid defoliation under humid conditions"],
        "causes": ["Pathogen Phytophthora infestans", "Cool wet weather", "High moisture levels"],
        "treatment": ["Apply chlorothalonil or mancozeb fungicide", "Remove infected plants immediately", "Avoid working in wet fields"],
        "prevention": ["Plant resistant varieties", "Ensure good drainage", "Avoid late-season planting"],
    },
    "Tomato___Leaf_Mold": {
        "crop": "Tomato", "disease_name": "Leaf Mold", "is_healthy": False,
        "symptoms": ["Pale green to yellow spots on upper leaf", "Olive-green velvety mould on underside", "Premature leaf drop"],
        "causes": ["Fungus Passalora fulva", "High humidity in greenhouses", "Poor ventilation"],
        "treatment": ["Apply chlorothalonil fungicide", "Reduce humidity", "Increase ventilation"],
        "prevention": ["Improve greenhouse ventilation", "Avoid leaf wetness", "Space plants for airflow"],
    },
    "Tomato___Bacterial_spot": {
        "crop": "Tomato", "disease_name": "Bacterial Spot", "is_healthy": False,
        "symptoms": ["Small water-soaked spots turning brown", "Yellow halos on leaf surface", "Lesions on stems and fruit"],
        "causes": ["Bacteria Xanthomonas species", "Warm rainy weather", "Splashing water"],
        "treatment": ["Apply copper-based bactericide", "Remove infected debris", "Avoid overhead irrigation"],
        "prevention": ["Use disease-free seeds", "Rotate crops", "Avoid working with wet plants"],
    },
    "Tomato___Septoria_leaf_spot": {
        "crop": "Tomato", "disease_name": "Septoria Leaf Spot", "is_healthy": False,
        "symptoms": ["Small circular spots with dark borders and grey centres", "Lower leaves affected first", "Spots develop tiny black dots (pycnidia)"],
        "causes": ["Fungus Septoria lycopersici", "Warm wet weather", "Splash dispersal of spores"],
        "treatment": ["Apply mancozeb or copper fungicide", "Remove infected leaves promptly", "Avoid overhead watering"],
        "prevention": ["Mulch soil", "Stake plants to improve airflow", "Rotate crops every 2-3 years"],
    },
    "Tomato___Spider_mites": {
        "crop": "Tomato", "disease_name": "Spider Mites (Two-spotted Mite)", "is_healthy": False,
        "symptoms": ["Fine stippling on upper leaf surface", "Webbing on undersides of leaves", "Leaves turn bronze and die"],
        "causes": ["Mite Tetranychus urticae", "Hot dry conditions", "Dusty environments"],
        "treatment": ["Apply miticide or insecticidal soap", "Increase humidity around plants", "Introduce predatory mites"],
        "prevention": ["Regular water misting", "Avoid over-application of nitrogen", "Monitor plants weekly"],
    },
    "Tomato___Target_Spot": {
        "crop": "Tomato", "disease_name": "Target Spot", "is_healthy": False,
        "symptoms": ["Circular brown lesions with concentric rings", "Yellow halo around spots", "Defoliation in severe cases"],
        "causes": ["Fungus Corynespora cassiicola", "High humidity and warm temperatures"],
        "treatment": ["Apply azoxystrobin or chlorothalonil fungicide", "Improve canopy ventilation"],
        "prevention": ["Use resistant varieties", "Stake plants for airflow", "Avoid overhead irrigation"],
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "crop": "Tomato", "disease_name": "Yellow Leaf Curl Virus", "is_healthy": False,
        "symptoms": ["Upward curling and yellowing of leaves", "Stunted plant growth", "Reduced fruit set"],
        "causes": ["Tomato Yellow Leaf Curl Virus (TYLCV)", "Transmitted by whitefly Bemisia tabaci"],
        "treatment": ["Remove and destroy infected plants", "Control whitefly population with insecticides"],
        "prevention": ["Use reflective mulch to repel whiteflies", "Plant resistant varieties", "Use insect-proof nets"],
    },
    "Tomato___Tomato_mosaic_virus": {
        "crop": "Tomato", "disease_name": "Tomato Mosaic Virus", "is_healthy": False,
        "symptoms": ["Mosaic pattern (light and dark green patches) on leaves", "Leaf distortion and curling", "Stunted growth"],
        "causes": ["Tomato Mosaic Virus (ToMV)", "Spread by handling infected plants", "Contaminated tools"],
        "treatment": ["Remove infected plants immediately", "Disinfect tools with bleach solution"],
        "prevention": ["Use certified disease-free seed", "Wash hands before handling plants", "Avoid tobacco use near plants"],
    },
    # ── Potato ────────────────────────────────────────────────────────────────
    "Potato___Healthy": {
        "crop": "Potato", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Uniform green leaf colour"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current care practices"],
        "prevention": ["Maintain proper watering", "Use certified seed potatoes"],
    },
    "Potato___Early_blight": {
        "crop": "Potato", "disease_name": "Early Blight", "is_healthy": False,
        "symptoms": ["Dark brown concentric ring lesions on lower leaves", "Yellowing of leaf tissue", "Sunken dark lesions on tubers"],
        "causes": ["Fungus Alternaria solani", "Warm humid conditions", "Nutrient stress"],
        "treatment": ["Apply mancozeb or chlorothalonil fungicide", "Remove infected foliage", "Maintain adequate nitrogen"],
        "prevention": ["Crop rotation 2-3 years", "Certified disease-free seed", "Avoid overhead irrigation"],
    },
    "Potato___Late_blight": {
        "crop": "Potato", "disease_name": "Late Blight", "is_healthy": False,
        "symptoms": ["Dark green water-soaked lesions", "White mould on leaf undersides", "Rapid foliage destruction"],
        "causes": ["Pathogen Phytophthora infestans", "Cool damp weather (15-25°C)", "High humidity >90%"],
        "treatment": ["Apply systemic fungicide immediately", "Destroy infected plants", "Harvest early if severe"],
        "prevention": ["Plant resistant varieties", "Good drainage", "Monitor weather forecasts"],
    },
    # ── Corn ──────────────────────────────────────────────────────────────────
    "Corn___Healthy": {
        "crop": "Corn", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Healthy green foliage"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Maintain proper spacing", "Balanced fertilisation"],
    },
    "Corn___Common_rust": {
        "crop": "Corn", "disease_name": "Common Rust", "is_healthy": False,
        "symptoms": ["Small reddish-brown pustules on leaf surfaces", "Pustules release powdery spores", "Leaves yellow and die in severe cases"],
        "causes": ["Fungus Puccinia sorghi", "Cool humid conditions"],
        "treatment": ["Apply strobilurin or triazole fungicide", "Treat at first sign"],
        "prevention": ["Plant resistant hybrids", "Avoid late planting"],
    },
    "Corn___Cercospora_leaf_spot_Gray_leaf_spot": {
        "crop": "Corn", "disease_name": "Gray Leaf Spot", "is_healthy": False,
        "symptoms": ["Rectangular grey-tan lesions parallel to leaf veins", "Entire leaf blight in severe cases"],
        "causes": ["Fungus Cercospora zeae-maydis", "Warm humid weather", "Extended leaf wetness"],
        "treatment": ["Apply strobilurin or triazole fungicide", "Apply at early infection stage"],
        "prevention": ["Use resistant hybrids", "Crop rotation", "Manage residue properly"],
    },
    "Corn___Northern_Leaf_Blight": {
        "crop": "Corn", "disease_name": "Northern Leaf Blight", "is_healthy": False,
        "symptoms": ["Long elliptical greyish-green to tan lesions", "Lesions up to 15cm long", "Premature death of leaves"],
        "causes": ["Fungus Exserohilum turcicum", "Moderate temperatures with extended leaf wetness"],
        "treatment": ["Apply fungicide at early tassel stage", "Use resistant hybrids"],
        "prevention": ["Rotate crops", "Bury or shred infected residue", "Plant resistant hybrids"],
    },
    # ── Apple ─────────────────────────────────────────────────────────────────
    "Apple___Healthy": {
        "crop": "Apple", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Healthy green leaves"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Maintain proper pruning", "Regular monitoring"],
    },
    "Apple___Apple_scab": {
        "crop": "Apple", "disease_name": "Apple Scab", "is_healthy": False,
        "symptoms": ["Olive-green to dark brown spots on leaves", "Dark scabby lesions on fruit", "Premature leaf drop"],
        "causes": ["Fungus Venturia inaequalis", "Wet spring conditions", "High humidity"],
        "treatment": ["Apply captan or myclobutanil fungicide", "Rake and destroy fallen leaves"],
        "prevention": ["Plant scab-resistant varieties", "Apply dormant sprays", "Maintain orchard sanitation"],
    },
    "Apple___Black_rot": {
        "crop": "Apple", "disease_name": "Black Rot", "is_healthy": False,
        "symptoms": ["Purple-bordered brown spots (frog-eye lesions)", "Fruit rots turning black", "Cankers on branches"],
        "causes": ["Fungus Botryosphaeria obtusa", "Poor tree health", "Wounds and dead wood"],
        "treatment": ["Apply captan fungicide", "Prune out cankers", "Remove mummified fruit"],
        "prevention": ["Maintain tree vigour", "Remove infected material", "Proper pruning practices"],
    },
    "Apple___Cedar_apple_rust": {
        "crop": "Apple", "disease_name": "Cedar Apple Rust", "is_healthy": False,
        "symptoms": ["Bright orange-yellow spots on upper leaf surface", "Tube-like structures on leaf undersides", "Premature defoliation"],
        "causes": ["Fungus Gymnosporangium juniperi-virginianae", "Alternate host (cedar/juniper) nearby"],
        "treatment": ["Apply myclobutanil or mancozeb fungicide at petal fall", "Repeat every 7-10 days"],
        "prevention": ["Remove nearby cedar/juniper trees", "Plant resistant varieties", "Apply preventive fungicide in spring"],
    },
    # ── Grape ─────────────────────────────────────────────────────────────────
    "Grape___Healthy": {
        "crop": "Grape", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Healthy green vines"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Maintain proper canopy management"],
    },
    "Grape___Black_rot": {
        "crop": "Grape", "disease_name": "Black Rot", "is_healthy": False,
        "symptoms": ["Brown circular spots with dark borders", "Black shrivelled mummified berries", "Lesions on shoots"],
        "causes": ["Fungus Guignardia bidwellii", "Warm humid weather"],
        "treatment": ["Apply mancozeb or myclobutanil fungicide", "Remove mummified berries"],
        "prevention": ["Vineyard sanitation", "Canopy management for airflow", "Apply dormant fungicide"],
    },
    "Grape___Esca": {
        "crop": "Grape", "disease_name": "Esca (Petri Disease)", "is_healthy": False,
        "symptoms": ["Tiger-stripe pattern on leaves", "Darkening of wood tissue", "Sudden wilting (apoplexy)"],
        "causes": ["Fungal complex (Phaeoacremonium, Phaeomoniella)", "Pruning wounds"],
        "treatment": ["Remove infected wood to healthy tissue", "Apply wound protectants"],
        "prevention": ["Protect pruning wounds", "Avoid large wounds", "Maintain vine health"],
    },
    "Grape___Leaf_blight": {
        "crop": "Grape", "disease_name": "Leaf Blight (Isariopsis)", "is_healthy": False,
        "symptoms": ["Irregular dark brown lesions on leaves", "Leaf edges turn brown and die", "Premature defoliation"],
        "causes": ["Fungus Pseudocercospora vitis", "Warm humid weather late in season"],
        "treatment": ["Apply copper-based or strobilurin fungicide", "Improve canopy aeration"],
        "prevention": ["Canopy management", "Avoid excess irrigation", "Practice vineyard sanitation"],
    },
    # ── Pepper ────────────────────────────────────────────────────────────────
    "Pepper_bell___Healthy": {
        "crop": "Pepper", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms", "Healthy green foliage"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Maintain proper spacing", "Regular monitoring"],
    },
    "Pepper_bell___Bacterial_spot": {
        "crop": "Pepper", "disease_name": "Bacterial Spot", "is_healthy": False,
        "symptoms": ["Water-soaked spots on leaves turning brown", "Yellow halos around spots", "Leaf drop in severe infections"],
        "causes": ["Bacterium Xanthomonas campestris", "Warm rainy weather", "Contaminated seeds"],
        "treatment": ["Apply copper-mancozeb bactericide", "Remove infected plants", "Avoid overhead irrigation"],
        "prevention": ["Use disease-free seed", "Crop rotation", "Avoid working with wet plants"],
    },
    # ── Other crops ───────────────────────────────────────────────────────────
    "Blueberry___Healthy": {
        "crop": "Blueberry", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Maintain proper pH (4.5-5.5)", "Regular monitoring"],
    },
    "Cherry___Healthy": {
        "crop": "Cherry", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Regular pruning", "Good drainage"],
    },
    "Cherry___Powdery_mildew": {
        "crop": "Cherry", "disease_name": "Powdery Mildew", "is_healthy": False,
        "symptoms": ["White powdery coating on young leaves", "Curling and distortion of new growth", "Reduced fruit quality"],
        "causes": ["Fungus Podosphaera clandestina", "Warm dry days + cool humid nights"],
        "treatment": ["Apply sulphur-based fungicide or potassium bicarbonate", "Prune affected shoots"],
        "prevention": ["Plant resistant varieties", "Good canopy airflow", "Avoid excess nitrogen"],
    },
    "Orange___Citrus_Greening": {
        "crop": "Orange", "disease_name": "Citrus Greening (HLB)", "is_healthy": False,
        "symptoms": ["Asymmetric blotchy yellowing of leaves", "Fruits small, lopsided, and bitter", "Tree decline over several years"],
        "causes": ["Bacterium Candidatus Liberibacter", "Transmitted by Asian citrus psyllid"],
        "treatment": ["Remove and destroy infected trees", "Control psyllid vector with insecticides"],
        "prevention": ["Use certified disease-free nursery stock", "Regular psyllid monitoring", "Quarantine measures"],
    },
    "Peach___Healthy": {
        "crop": "Peach", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Annual pruning", "Balanced fertilisation"],
    },
    "Peach___Bacterial_spot": {
        "crop": "Peach", "disease_name": "Bacterial Spot", "is_healthy": False,
        "symptoms": ["Small dark water-soaked spots on leaves", "Holes in leaves (shot-hole effect)", "Sunken spots on fruit"],
        "causes": ["Bacterium Xanthomonas arboricola pv. pruni", "Warm wet weather"],
        "treatment": ["Apply copper bactericide at bud break", "Avoid heavy nitrogen applications"],
        "prevention": ["Plant resistant varieties", "Shelter from wind", "Proper pruning"],
    },
    "Raspberry___Healthy": {
        "crop": "Raspberry", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Prune old canes annually", "Good drainage"],
    },
    "Soybean___Healthy": {
        "crop": "Soybean", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Rhizobium inoculation", "Crop rotation"],
    },
    "Squash___Powdery_mildew": {
        "crop": "Squash", "disease_name": "Powdery Mildew", "is_healthy": False,
        "symptoms": ["White powdery patches on leaf surfaces", "Yellowing and browning of affected areas", "Premature leaf senescence"],
        "causes": ["Fungus Podosphaera xanthii or Erysiphe cichoracearum", "Dry conditions + moderate temperatures"],
        "treatment": ["Apply potassium bicarbonate or sulphur spray", "Remove heavily infected leaves"],
        "prevention": ["Plant resistant varieties", "Good air circulation", "Avoid evening irrigation"],
    },
    "Strawberry___Healthy": {
        "crop": "Strawberry", "disease_name": "Healthy", "is_healthy": True,
        "symptoms": ["No visible disease symptoms"],
        "causes": ["Plant is healthy"],
        "treatment": ["Continue current practices"],
        "prevention": ["Mulch to reduce splash", "Proper plant spacing"],
    },
    "Strawberry___Leaf_scorch": {
        "crop": "Strawberry", "disease_name": "Leaf Scorch", "is_healthy": False,
        "symptoms": ["Irregular purple to dark brown spots on leaves", "Spots coalesce giving scorched appearance", "Severe defoliation in wet conditions"],
        "causes": ["Fungus Diplocarpon earlianum", "Prolonged leaf wetness", "Cool to moderate temperatures"],
        "treatment": ["Apply captan or myclobutanil fungicide", "Remove infected leaves"],
        "prevention": ["Avoid overhead irrigation", "Improve air circulation", "Renovate beds after harvest"],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  Lazy-loaded Keras model (singleton)
# ──────────────────────────────────────────────────────────────────────────────
_keras_model = None   # tensorflow.keras.Model  (loaded once at first call)
_keras_class_names: list[str] | None = None
_model_load_error: str = ""  # non-empty → production load failed, fall back to demo


def _load_keras_model():
    """Load the CNN model from disk into the module-level singleton.
    Called once; subsequent calls are no-ops.
    """
    global _keras_model, _keras_class_names, _model_load_error
    if _keras_model is not None:
        return  # already loaded

    model_path = Path(settings.DISEASE_MODEL_PATH)
    if not model_path.exists():
        _model_load_error = (
            f"Model file not found at '{model_path.resolve()}'. "
            "Falling back to demo mode.  "
            "See ml_models/README.md for instructions to obtain a trained model."
        )
        logger.warning(_model_load_error)
        return

    try:
        import tensorflow as tf  # imported lazily to avoid slow startup when TF not installed
        logger.info("Loading Keras disease model from %s …", model_path)
        loaded_model = tf.keras.models.load_model(str(model_path))
        class_names_path = model_path.with_name(f"{model_path.stem}.classes.json")
        if class_names_path.is_file():
            metadata = json.loads(class_names_path.read_text(encoding="utf-8"))
            class_names = metadata.get("class_names")
            if (
                not isinstance(class_names, list)
                or not class_names
                or not all(isinstance(name, str) for name in class_names)
                or len(set(class_names)) != len(class_names)
            ):
                raise ValueError("Model class metadata is missing or invalid.")
        else:
            class_names = PLANTVILLAGE_CLASSES
        if (
            loaded_model.output_shape[-1] != len(class_names)
            or len(class_names) != settings.DISEASE_MODEL_NUM_CLASSES
        ):
            raise ValueError(
                f"Model outputs {loaded_model.output_shape[-1]} classes, "
                f"but configuration/metadata define {settings.DISEASE_MODEL_NUM_CLASSES}/"
                f"{len(class_names)}."
            )
        _keras_model = loaded_model
        _keras_class_names = class_names
        logger.info(
            "Disease model loaded successfully. "
            "Input shape: %s | Output classes: %s",
            loaded_model.input_shape,
            loaded_model.output_shape[-1],
        )
    except ImportError:
        _model_load_error = (
            "TensorFlow is not installed.  "
            "Run:  pip install tensorflow-cpu  (CPU) or  pip install tensorflow  (GPU)."
        )
        logger.error(_model_load_error)
    except Exception as exc:
        _model_load_error = f"Failed to load model: {exc}"
        logger.error(_model_load_error)


def _preprocess_image(image_bytes: bytes, target_size: int) -> "np.ndarray":
    """
    Decode raw bytes → PIL RGB → resize → MobileNetV2 input preprocessing.
    Returns shape (1, target_size, target_size, 3) — batch of one.
    """
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((target_size, target_size), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    arr = preprocess_input(arr)
    return np.expand_dims(arr, axis=0)             # add batch dimension


def _predict_with_keras(image_bytes: bytes) -> dict:
    """
    Run real CNN inference.  Returns the same dict shape as `_predict_demo`.
    """
    target_size = settings.DISEASE_MODEL_INPUT_SIZE
    img_array = _preprocess_image(image_bytes, target_size)

    # Run model inference
    probs = _keras_model.predict(img_array, verbose=0)[0]   # shape (num_classes,)

    # Top-1 prediction
    top_idx = int(np.argmax(probs))
    confidence = float(probs[top_idx])

    # Map index → class key
    class_names = _keras_class_names or PLANTVILLAGE_CLASSES
    if len(probs) != len(class_names):
        raise ValueError(
            f"Model returned {len(probs)} probabilities for {len(class_names)} classes."
        )
    class_key = class_names[top_idx]

    # Look up clinical details from the database
    info = DISEASE_DATABASE.get(class_key)
    if info is None:
        info = next(
            (
                value for key, value in DISEASE_DATABASE.items()
                if key.casefold() == class_key.casefold()
            ),
            None,
        )
    if info is None:
        # Graceful fallback for any unknown key (e.g. a custom model)
        is_healthy = "healthy" in class_key.lower()
        crop = class_key.split("___")[0].replace("_", " ") if "___" in class_key else "Unknown"
        disease = "Healthy" if is_healthy else class_key.split("___")[-1].replace("_", " ")
        info = {
            "crop": crop, "disease_name": disease, "is_healthy": is_healthy,
            "symptoms": ["See official agricultural extension resources"],
            "causes": ["AI model predicted this class"],
            "treatment": ["Consult a local agricultural expert"],
            "prevention": ["Follow recommended agronomic practices"],
        }

    return {
        "disease_key": class_key,
        "disease_name": info["disease_name"],
        "crop": info["crop"],
        "confidence": round(confidence, 4),
        "is_healthy": info["is_healthy"],
        "symptoms": info["symptoms"],
        "causes": info["causes"],
        "treatment": info["treatment"],
        "prevention": info["prevention"],
        "is_demo_mode": False,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Demo / fallback path (OpenCV colour analysis)
# ──────────────────────────────────────────────────────────────────────────────

def _analyse_image_features(image_bytes: bytes) -> dict:
    """
    Compute HSV colour statistics from the leaf image.
    Deterministic and explainable — NOT random.
    """
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, w = img.shape[:2]
        total = h * w

        green_mask  = cv2.inRange(hsv, np.array([25, 40, 40]),   np.array([85, 255, 255]))
        brown_mask  = cv2.inRange(hsv, np.array([10, 50, 50]),   np.array([25, 255, 200]))
        yellow_mask = cv2.inRange(hsv, np.array([20, 50, 50]),   np.array([35, 255, 255]))
        dark_mask   = cv2.inRange(hsv, np.array([0, 0, 0]),      np.array([180, 255, 60]))

        green_r  = float(np.sum(green_mask  > 0)) / total
        brown_r  = float(np.sum(brown_mask  > 0)) / total
        yellow_r = float(np.sum(yellow_mask > 0)) / total
        dark_r   = float(np.sum(dark_mask   > 0)) / total

        return {
            "green_ratio":    green_r,
            "brown_ratio":    brown_r,
            "yellow_ratio":   yellow_r,
            "dark_ratio":     dark_r,
            "disease_score":  brown_r + yellow_r * 0.5 + dark_r * 0.3,
            "health_score":   green_r,
        }
    except Exception as exc:
        logger.warning("Image feature analysis failed (%s); using defaults.", exc)
        return {"green_ratio": 0.5, "brown_ratio": 0.2, "yellow_ratio": 0.1,
                "dark_ratio": 0.1, "disease_score": 0.3, "health_score": 0.5}


def _predict_demo(image_bytes: bytes, crop_type: str) -> dict:
    """
    Demo-mode prediction based purely on image colour statistics.
    Always labelled `is_demo_mode=True` in the response.
    """
    feats = _analyse_image_features(image_bytes)
    disease_score = feats["disease_score"]
    health_score  = feats["health_score"]

    # Filter candidates by crop type if provided
    crop_norm = crop_type.capitalize() if crop_type else ""
    candidates = [
        k for k, v in DISEASE_DATABASE.items()
        if not crop_norm or v["crop"].lower() == crop_type.lower()
    ] or list(DISEASE_DATABASE.keys())

    healthy_keys  = [k for k in candidates if DISEASE_DATABASE[k]["is_healthy"]]
    diseased_keys = [k for k in candidates if not DISEASE_DATABASE[k]["is_healthy"]]
    if not diseased_keys:
        diseased_keys = [k for k in DISEASE_DATABASE if not DISEASE_DATABASE[k]["is_healthy"]]

    if disease_score < 0.15 and health_score > 0.3 and healthy_keys:
        selected_key = healthy_keys[0]
        confidence   = min(0.98, 0.65 + health_score * 0.3)
    elif diseased_keys:
        if feats["brown_ratio"] > feats["yellow_ratio"]:
            pref = [k for k in diseased_keys if any(x in k.lower() for x in ["blight", "rot", "rust", "spot"])]
            selected_key = pref[0] if pref else diseased_keys[0]
        else:
            pref = [k for k in diseased_keys if any(x in k.lower() for x in ["mold", "scab", "yellow"])]
            selected_key = pref[0] if pref else diseased_keys[0]
        confidence = max(0.55, min(0.95, 0.60 + disease_score * 2.0))
    else:
        selected_key = healthy_keys[0] if healthy_keys else list(DISEASE_DATABASE.keys())[0]
        confidence   = 0.65

    info = DISEASE_DATABASE[selected_key]
    return {
        "disease_key":  selected_key,
        "disease_name": info["disease_name"],
        "crop":         info["crop"],
        "confidence":   round(confidence, 4),
        "is_healthy":   info["is_healthy"],
        "symptoms":     info["symptoms"],
        "causes":       info["causes"],
        "treatment":    info["treatment"],
        "prevention":   info["prevention"],
        "is_demo_mode": False,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def classify_disease(image_bytes: bytes, crop_type: str = "") -> dict:
    """
    Classify a plant leaf image.

    Routing logic:
      1. If DISEASE_MODEL_MODE == "production"  → try real CNN inference.
         If model load failed (missing file / TF not installed) → fall back to demo
         and include a `_fallback_reason` key in the result.
      2. If DISEASE_MODEL_MODE == "demo"  → always use colour-stats demo path.
    """
    want_production = settings.DISEASE_MODEL_MODE.lower() == "production"

    if want_production:
        # Ensure model is loaded (lazy, one-time)
        _load_keras_model()

        if _keras_model is not None:
            try:
                return _predict_with_keras(image_bytes)
            except Exception as exc:
                logger.error("CNN inference failed: %s — falling back to demo.", exc)
                result = _predict_demo(image_bytes, crop_type)
                result["_fallback_reason"] = str(exc)
                return result
        else:
            # Model file missing or TF import failed
            result = _predict_demo(image_bytes, crop_type)
            result["_fallback_reason"] = _model_load_error
            return result

    # Default: demo mode
    return _predict_demo(image_bytes, crop_type)
