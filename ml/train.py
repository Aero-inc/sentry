from ultralytics import YOLO

model = YOLO("../services/stream-worker/src/model/yolo11m.pt") 


if __name__ == "__main__":
    results = model.train(
        data='../data/merged_dataset/data.yaml',    # Path to your data config
        epochs=100,                   # Adjust based on dataset size
        imgsz=640,                  # Input resolution
        batch=0.8,                   # Reduce if you hit GPU memory limits
        patience=25,                # Early stopping if no improvement
        device=0,                   # GPU index (or 'cpu' if no GPU)
        workers=0,                  # DataLoader workers
        project='runs/train',       # Output directory
        name='test_v1',             # Experiment name
        exist_ok=True,              # Overwrite if exists
        rect=True,
        lr0=3e-4,
        lrf=0.01,
        
        # # Data augmentation (enabled by default, but you can tune)
        # augment=True,
        # hsv_h=0.015,              # Hue augmentation
        # hsv_s=0.7,                # Saturation augmentation
        # hsv_v=0.4,                # Value/brightness augmentation
        # degrees=10.0,             # Rotation range
        # scale=0.5,                # Scale augmentation
        # flipud=0.0,               # Vertical flip (usually 0 for surveillance)
        # fliplr=0.5,               # Horizontal flip
        # mosaic=1.0,               # Mosaic augmentation probability
    )

    print("Pipeline Test Complete")
