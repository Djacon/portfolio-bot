import numpy as np
import cv2

from ultralytics import YOLO
from ultralytics.yolo.utils.ops import scale_image
from ultralytics.yolo.utils.plotting import colors

model = YOLO('yolov8s-seg.pt')


def overlay(image, mask, color, alpha=.5):
    colored_mask = np.expand_dims(mask, 0).repeat(3, axis=0)
    colored_mask = np.moveaxis(colored_mask, 0, -1)
    masked = np.ma.MaskedArray(image, mask=colored_mask, fill_value=color)
    image_overlay = masked.filled()

    return cv2.addWeighted(image, 1 - alpha, image_overlay, alpha, 0)


def segment_photo(img_path):
    result = model(img_path, conf=.5, line_thickness=2, retina_masks=True)[0]

    image = result.orig_img
    boxes = result.boxes.data
    for j, (x1, y1, x2, y2, conf, cls) in enumerate(boxes):

        cls = int(cls.item())
        color = colors(cls, bgr=True)

        x1, y1, x2, y2 = int(x1.item()), int(y1.item()), int(x2.item()), int(y2.item())  # noqa
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

        class_name = f"{result.names[cls]} {conf:.2f}"

        font_size, _ = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_PLAIN, 1, 1)  # noqa

        if y1 < 31:
            y1 += 30

        cv2.rectangle(image, (x1, y1 - 30), (x1 + font_size[0], y1),
                      color, -1)
        cv2.putText(image, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN,
                    1, (255, 255, 255), 1, cv2.LINE_AA)

        mask = result.masks.data[j].cpu().numpy()
        mask = scale_image(mask, image.shape)
        image = overlay(image, mask, color)

    cv2.imwrite(img_path, image)


def progressBar(iteration, total, length=15):
    percent = '{0:.1f}'.format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = '█' * filledLength + '-' * (length - filledLength)
    return f'`Загрузка: |{bar}| {percent}% ({iteration}/{total})`'


def segment_video(vid_path):
    cap = cv2.VideoCapture(vid_path)
    _, frame = cap.read()

    FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    new_path = 'videos/' + vid_path.split('/')[1].split('.')[0] + '_seg.mp4'
    cap_out = cv2.VideoWriter(new_path, cv2.VideoWriter_fourcc(*'MP4V'), cap.get(cv2.CAP_PROP_FPS),  # noqa
                              (frame.shape[1], frame.shape[0]))

    cap.release()
    del cap

    frames = model.predict(vid_path, stream=True, conf=.5,  line_thickness=2)

    for i, result in enumerate(frames):
        image = result.orig_img

        boxes = result.boxes.data
        for j, (x1, y1, x2, y2, conf, cls) in enumerate(boxes):

            cls = int(cls.item())
            color = colors(cls, bgr=True)

            x1, y1, x2, y2 = int(x1.item()), int(y1.item()), int(x2.item()), int(y2.item())  # noqa
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            class_name = f"{result.names[cls]} {conf:.2f}"

            font_size, _ = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_PLAIN, 1, 1)

            if y1 < 31:
                y1 += 30

            cv2.rectangle(image, (x1, y1 - 30), (x1 + font_size[0], y1), color, -1)
            cv2.putText(image, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1,
                        (255, 255, 255), 1, cv2.LINE_AA)

            # mask = result.masks.data[j].cpu().numpy()
            # mask = scale_image(mask, image.shape)
            # image = overlay(image, mask, color)

        cap_out.write(image)

        if i % 20 == 0:
            progress = progressBar(i, FRAMES)
            yield (progress, 0)

    cap_out.release()
    yield (new_path, 1)
