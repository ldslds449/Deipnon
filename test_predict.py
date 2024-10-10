from PIL import Image
from src.predict import Captcha

if __name__ == "__main__":
    import glob
    import os

    IMAGE_FOLDER = "test"
    images = list(
        map(Image.open, glob.glob(os.path.join(IMAGE_FOLDER, "*.jpeg")))
    )

    captcha = Captcha("models/yolo11m_fake_5000_real_550.pt")
    results = captcha.predict(images)
    for r in results:
        print(r)
