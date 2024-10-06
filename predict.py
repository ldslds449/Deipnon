from typing import Union
from ultralytics import YOLO
from PIL import Image


class Captcha:
    def __init__(self, model_path: str) -> None:
        self.model = YOLO(model_path)

    def NMS(
        self,
        data: list[tuple[float, list[float, float, float, float], float]],
        IOU_THRESHOLD: float = 0.6,
    ):
        index = list(range(len(data)))
        arange_arr = list(zip(index, data))
        arange_arr = sorted(arange_arr, key=lambda x: x[1][2], reverse=True)
        index = list(map(lambda x: x[0], arange_arr))

        def IOU(xyxy1: list, xyxy2: list) -> float:
            overlap_width = max(
                min(xyxy1[2], xyxy2[2]) - max(xyxy1[0], xyxy2[0]), 0
            )
            overlap_height = max(
                min(xyxy1[3], xyxy2[3]) - max(xyxy1[1], xyxy2[1]), 0
            )
            overlap_area = overlap_width * overlap_height
            area1 = (xyxy1[2] - xyxy1[0]) * (xyxy1[3] - xyxy1[1])
            area2 = (xyxy2[2] - xyxy2[0]) * (xyxy2[3] - xyxy2[1])
            return overlap_area / (area1 + area2 - overlap_area)

        selected_data = []
        while len(index) > 0:
            idx = index.pop(0)
            selected_data.append(data[idx])

            survival_index = []
            for other_idx in index:
                if IOU(data[idx][1], data[other_idx][1]) < IOU_THRESHOLD:
                    survival_index.append(other_idx)
            index = survival_index

        return selected_data

    def predict(
        self,
        images: Union[Image.Image, list[Image.Image]],
        detail: bool = False,
    ) -> Union[str, list[str], tuple[str, list], list[tuple[str, list]]]:
        if isinstance(images, Image.Image):
            input_data = [images]
        else:
            input_data = images

        # predict by model
        results = self.model.predict(input_data)

        result_str_list = []
        data_list = []
        for r in results:
            boxes = r.boxes.numpy()
            data = list(
                zip(
                    boxes.cls.tolist(),
                    boxes.xyxy.tolist(),
                    boxes.conf.tolist(),
                )
            )
            # NMS
            data = self.NMS(data)
            # sort by x value
            data = sorted(data, key=lambda x: x[1][0])
            data_list.append(data)
            # generate the string
            result_str = "".join(
                map(lambda x: chr(ord("A") + int(x[0])), data)
            )
            result_str_list.append(result_str)

        if isinstance(images, Image.Image):
            return (
                result_str_list[0]
                if detail is False
                else (result_str_list[0], data_list[0])
            )
        else:
            return (
                result_str_list
                if detail is False
                else (result_str_list, data_list)
            )


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
