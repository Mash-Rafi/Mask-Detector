from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import AveragePooling2D
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import os

#initialize LR,EPOCH and Batch Size
INIT_LR = 1e-4
EPOCHS = 20
BS = 32

DIRECTORY = r"C:\Mask Detector\dataset"
CATEGORIES = ["with_mask","without_mask"]

#Grab and list the data
print("Loading Images! Hold Tight!")

data = []
labels = []

for category in CATEGORIES:
    path = os.path.join(DIRECTORY, category)
    for img in os.listdir(path):
    	img_path = os.path.join(path, img)
    	image = load_img(img_path, target_size=(224, 224))
    	image = img_to_array(image)
    	image = preprocess_input(image)

    	data.append(image)
    	labels.append(category)


#One hot-encoding
lb = LabelBinarizer()
labels = lb.fit_transform(labels)
labels = to_categorical(labels)

data = np.array(data, dtype="float32")
labels = np.array(labels)

(trainX, testX, trainY, testY) = train_test_split(data, labels,
	test_size=0.20, stratify=labels, random_state=42)

#Training Construct of image generator
aug = ImageDataGenerator(
    rotation_range=20,
    zoom_range=0.15,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.15,
    horizontal_flip=True,
    fill_mode="nearest"
)

#load the MobilenetV2 network
baseModel = MobileNetV2(weights="imagenet", include_top = False,
                        input_tensor=Input(shape=(224,224,3)))

#Head of the model for the base model
headmodel = baseModel.output
headmodel = AveragePooling2D(pool_size=(7,7))(headmodel)
headmodel = Flatten(name="flatten")(headmodel)
headmodel = Dense(128,activation="relu")(headmodel)
headmodel = Dropout(0.5)(headmodel)
headmodel = Dense(2, activation="softmax")(headmodel)

#Placing the headmodel on the basemodel
model = Model(inputs=baseModel.input, outputs=headmodel)

#loop over the layers
for layer in baseModel.layers:
    layer.trainable = False

#Compile our model
print("Compiling Model...")
opt = Adam(learning_rate=INIT_LR, decay= INIT_LR / EPOCHS)
model.compile(loss="binary_crossentropy", optimizer=opt, metrics=["accuracy"])

#Train the Network Head
print("Training Head...")
H = model.fit(
	aug.flow(trainX, trainY, batch_size=BS),
	steps_per_epoch=len(trainX) // BS,
	validation_data=(testX, testY),
	validation_steps=len(testX) // BS,
	epochs=EPOCHS)


#Make prediction on testing set
print("Evaluating Network...")
preIDxs = model.predict(testX, batch_size=BS)

preIDxs= np.argmax(preIDxs, axis=1)

#Classification Report
print(classification_report(testY.argmax(axis=1), preIDxs, target_names=lb.classes_))

#serialize the model to disk
print(" Saving Mask Detector Model...")
model.save("mask_detector.model", save_format="h5")

#plot the training loss and accuracy
N = EPOCHS
plt.style.use("ggplot")
plt.figure()
plt.plot(np.arange(0, N), H.history["loss"], label="train_loss")
plt.plot(np.arange(0, N), H.history["val_loss"], label="val_loss")
plt.plot(np.arange(0, N), H.history["accuracy"], label="train_acc")
plt.plot(np.arange(0, N), H.history["val_accuracy"], label="val_acc")
plt.title("Training Loss and Accuracy")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend(loc="lower left")
plt.savefig("Accuracy_and_loss.png")
