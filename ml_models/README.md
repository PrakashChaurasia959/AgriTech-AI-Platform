# ml_models/

Place your trained model files here. They are excluded from git (see `.gitignore`).

## Disease Detection Model

Filename: `plant_disease_model.keras`  (or `.h5`)

Train the MobileNetV2 model on the real **PlantVillage** dataset with
`backend/train_plant_disease_cnn.py`. Training creates the configured model
file plus adjacent `.classes.json` and `.metrics.json` files. The class file
keeps inference labels aligned with the output neurons; the metrics file
records held-out accuracy, macro precision/recall/F1, and the confusion matrix.
Training results depend on the dataset and run; do not infer them from the
untrained starter model.

### Quick training recipe (Google Colab / local GPU)

```python
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, Model

IMG_SIZE = 224
NUM_CLASSES = 38

base = MobileNetV2(include_top=False, weights='imagenet',
                   input_shape=(IMG_SIZE, IMG_SIZE, 3))
base.trainable = False

x = base.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(256, activation='relu')(x)
x = layers.Dropout(0.4)(x)
out = layers.Dense(NUM_CLASSES, activation='softmax')(x)

model = Model(base.input, out)
model.compile('adam', 'categorical_crossentropy', ['accuracy'])

# Use tf.keras.utils.image_dataset_from_directory on the PlantVillage folder
# ... (see full notebook in notebooks/train_disease_model.ipynb)

model.save('ml_models/plant_disease_model.keras')
```

Set `.env` (the trainer uses the configured model path and does not edit this
file):
```
DISEASE_MODEL_MODE=production
DISEASE_MODEL_PATH=ml_models/plant_disease_model.keras
DISEASE_MODEL_INPUT_SIZE=224
DISEASE_MODEL_NUM_CLASSES=38
```

## Crop Recommendation Model (optional)

Filename: `crop_recommendation_model.pkl`

If you have a pre-trained scikit-learn model saved as a joblib/pickle file that was
trained on the Kaggle Crop Recommendation Dataset, place it here and set:

```
CROP_MODEL_PATH=ml_models/crop_recommendation_model.pkl
```

If the file is absent the backend auto-trains a Random Forest on the built-in
agronomic dataset at startup (no action needed).
