"""Download PlantVillage and train the configured MobileNetV2 disease model."""
import json
import os
import pathlib
import sys
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore")

from app.core.config import settings

BASE = pathlib.Path(__file__).parent
DATA = BASE.parent / "datasets" / "plantvillage"
MODEL_PATH = pathlib.Path(settings.DISEASE_MODEL_PATH)
if not MODEL_PATH.is_absolute():
    MODEL_PATH = BASE / MODEL_PATH
MODEL_PATH = MODEL_PATH.resolve()
CLASS_NAMES_PATH = MODEL_PATH.with_name(f"{MODEL_PATH.stem}.classes.json")
METRICS_PATH = MODEL_PATH.with_name(f"{MODEL_PATH.stem}.metrics.json")
CHECKPOINT_PATH = MODEL_PATH.with_name(f"{MODEL_PATH.stem}.checkpoint.keras")
IMAGE_SIZE = settings.DISEASE_MODEL_INPUT_SIZE
BATCH_SIZE = 32
HEAD_EPOCHS = 2
FINE_TUNE_EPOCHS = 1
DATASET_REF = "abdallahalidev/plantvillage-dataset"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def image_files(root: pathlib.Path) -> list[pathlib.Path]:
    return [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def find_dataset_root(root: pathlib.Path) -> pathlib.Path | None:
    candidates = [
        root / name
        for name in ("PlantVillage", "plant_village", "Color", "color")
    ]
    candidates.extend([
        root / "plantvillage dataset" / "color",
        root / "plantvillage dataset" / "Color",
    ])
    candidates.append(root)
    for candidate in candidates:
        if candidate.is_dir() and sum(child.is_dir() for child in candidate.iterdir()) == 38:
            return candidate

    fallback = None
    for current, dirs, _ in os.walk(root):
        if len(dirs) == 38:
            candidate = pathlib.Path(current)
            if candidate.name.casefold() == "color":
                return candidate
            fallback = fallback or candidate
    return fallback


def save_json(path: pathlib.Path, data: dict) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temporary_path, path)


print("=" * 64)
print("PlantVillage MobileNetV2 Training")
print("=" * 64)

print("\n[1/6] Authenticating to Kaggle...")
try:
    from kaggle.api.kaggle_api_extended import KaggleApi

    kaggle_api = KaggleApi()
    kaggle_api.authenticate()
    print("Kaggle authentication: PASS")
except Exception as exc:
    print(f"Kaggle authentication: FAIL ({type(exc).__name__})")
    sys.exit(1)

DATA.mkdir(parents=True, exist_ok=True)
downloaded_images = len(image_files(DATA))
if downloaded_images < 50_000:
    print(f"\n[2/6] Downloading {DATASET_REF}...")
    try:
        kaggle_api.dataset_download_files(
            DATASET_REF,
            path=str(DATA),
            unzip=True,
            quiet=True,
        )
    except Exception as exc:
        print(f"PlantVillage download: FAIL ({type(exc).__name__})")
        sys.exit(1)
    downloaded_images = len(image_files(DATA))

print(f"PlantVillage images found: {downloaded_images}")
if downloaded_images < 50_000:
    print("Dataset validation: FAIL (fewer than 50,000 real image files)")
    sys.exit(1)

print("\n[3/6] Validating dataset structure and creating stratified splits...")
dataset_root = find_dataset_root(DATA)
if dataset_root is None:
    print("Dataset validation: FAIL (expected 38 class directories)")
    sys.exit(1)

class_names = sorted(
    child.name for child in dataset_root.iterdir()
    if child.is_dir()
)
if len(class_names) != settings.DISEASE_MODEL_NUM_CLASSES:
    print(
        "Dataset validation: FAIL "
        f"(found {len(class_names)} classes; expected {settings.DISEASE_MODEL_NUM_CLASSES})"
    )
    sys.exit(1)

class_indices = {name: index for index, name in enumerate(class_names)}
paths: list[str] = []
labels: list[int] = []
for class_name in class_names:
    class_images = [
        path for path in (dataset_root / class_name).rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    paths.extend(str(path) for path in class_images)
    labels.extend([class_indices[class_name]] * len(class_images))

from sklearn.model_selection import train_test_split

train_validation_paths, test_paths, train_validation_labels, test_labels = train_test_split(
    paths,
    labels,
    test_size=0.15,
    random_state=42,
    stratify=labels,
)
train_paths, validation_paths, train_labels, validation_labels = train_test_split(
    train_validation_paths,
    train_validation_labels,
    test_size=0.15 / 0.85,
    random_state=42,
    stratify=train_validation_labels,
)
print(
    f"Dataset: {dataset_root} | {len(paths)} images | {len(class_names)} classes\n"
    f"Split: train={len(train_paths)}, validation={len(validation_paths)}, "
    f"test={len(test_paths)} (70/15/15)"
)

print("\n[4/6] Building the TensorFlow data pipeline...")
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

keras.utils.set_random_seed(42)
augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.12),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
])
autotune = tf.data.AUTOTUNE


def load_image(path: tf.Tensor, label: tf.Tensor, training: bool):
    image = tf.io.read_file(path)
    image = tf.io.decode_image(image, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
    if training:
        image = augmentation(image, training=True)
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    return image, tf.one_hot(label, len(class_names))


def make_dataset(
    image_paths: list[str],
    image_labels: list[int],
    training: bool,
) -> tf.data.Dataset:
    dataset = tf.data.Dataset.from_tensor_slices((image_paths, image_labels))
    if training:
        dataset = dataset.shuffle(
            min(len(image_paths), 8192),
            seed=42,
            reshuffle_each_iteration=True,
        )
    return (
        dataset
        .map(
            lambda path, label: load_image(path, label, training),
            num_parallel_calls=autotune,
        )
        .batch(BATCH_SIZE)
        .prefetch(autotune)
    )


train_dataset = make_dataset(train_paths, train_labels, training=True)
validation_dataset = make_dataset(validation_paths, validation_labels, training=False)
test_dataset = make_dataset(test_paths, test_labels, training=False)

print("\n[5/6] Training the MobileNetV2 CNN...")
base_model = MobileNetV2(
    input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
    include_top=False,
    weights="imagenet",
)
base_model.trainable = False

inputs = keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3))
features = base_model(inputs, training=False)
features = layers.GlobalAveragePooling2D()(features)
features = layers.Dense(512, activation="relu")(features)
features = layers.Dropout(0.4)(features)
outputs = layers.Dense(len(class_names), activation="softmax", name="predictions")(features)
model = keras.Model(inputs, outputs)
model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH.unlink(missing_ok=True)
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=4,
        restore_best_weights=True,
        verbose=1,
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        patience=2,
        factor=0.5,
        verbose=1,
    ),
    keras.callbacks.ModelCheckpoint(
        str(CHECKPOINT_PATH),
        monitor="val_accuracy",
        mode="max",
        save_best_only=True,
        verbose=1,
    ),
]

try:
    print(f"Head training: up to {HEAD_EPOCHS} epochs...")
    model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=HEAD_EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    print(f"Fine-tuning: up to {FINE_TUNE_EPOCHS} epochs...")
    base_model.trainable = True
    for layer in base_model.layers[:-40]:
        layer.trainable = False
    model.compile(
        optimizer=keras.optimizers.Adam(1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    print("\n[6/6] Evaluating on the held-out test split...")
    test_loss, _ = model.evaluate(test_dataset, verbose=1)
    test_probabilities = model.predict(test_dataset, verbose=1)
    y_true = np.asarray(test_labels)
    y_predicted = np.argmax(test_probabilities, axis=1)
    metrics = {
        "dataset": DATASET_REF,
        "dataset_root": str(dataset_root),
        "image_count": len(paths),
        "class_names": class_names,
        "split_counts": {
            "train": len(train_paths),
            "validation": len(validation_paths),
            "test": len(test_paths),
        },
        "test": {
            "loss": float(test_loss),
            "accuracy": float(accuracy_score(y_true, y_predicted)),
            "precision_macro": float(
                precision_score(y_true, y_predicted, average="macro", zero_division=0)
            ),
            "recall_macro": float(
                recall_score(y_true, y_predicted, average="macro", zero_division=0)
            ),
            "f1_macro": float(
                f1_score(y_true, y_predicted, average="macro", zero_division=0)
            ),
            "confusion_matrix": confusion_matrix(
                y_true,
                y_predicted,
                labels=list(range(len(class_names))),
            ).tolist(),
            "classification_report": classification_report(
                y_true,
                y_predicted,
                labels=list(range(len(class_names))),
                target_names=class_names,
                output_dict=True,
                zero_division=0,
            ),
        },
    }

    temporary_model_path = MODEL_PATH.with_name(f"{MODEL_PATH.stem}.tmp.keras")
    model.save(str(temporary_model_path))
    os.replace(temporary_model_path, MODEL_PATH)
    save_json(CLASS_NAMES_PATH, {"class_names": class_names})
    save_json(METRICS_PATH, metrics)
finally:
    CHECKPOINT_PATH.unlink(missing_ok=True)

print(f"Test accuracy:  {metrics['test']['accuracy']:.4f}")
print(f"Macro precision: {metrics['test']['precision_macro']:.4f}")
print(f"Macro recall:    {metrics['test']['recall_macro']:.4f}")
print(f"Macro F1-score:  {metrics['test']['f1_macro']:.4f}")
print(f"Confusion matrix: {len(class_names)} x {len(class_names)}")
print(f"Trained model: {MODEL_PATH}")
print(f"Class mapping: {CLASS_NAMES_PATH}")
print(f"Evaluation metrics: {METRICS_PATH}")
