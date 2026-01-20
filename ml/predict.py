from ultralytics import YOLO
from PIL import Image
import os
from glob import glob
from tqdm import tqdm

model = YOLO("./runs/train/test_v1/weights/best.pt", task="detect")

if __name__ == "__main__":
    images = []
    for image in glob("../data/merged_dataset/val/images/*"):
        images.append(Image.open(image))

    for image in tqdm(images):
        model.predict(
            image,
            rect=True,
            conf=0.5,
            project='runs/detect/',
            name='valInspect_conf0.5',
            exist_ok=True,
            verbose=False,
            save=True,
            save_txt=True,
            save_conf=True
        )
