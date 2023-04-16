import numpy as np
import cv2

from ultralytics import YOLO
from ultralytics.yolo.utils.ops import scale_image


COLORS = ('E22B8A', '87B8DE', '1E69D2', '507FFF', '4763FF', 'ED9564', '3C14DC', '8B8B00', '0B86B8', 'A9A9A9',
          '6BB7BD', '008CFF', 'CC3299', '7A96E9', '8FBC8F', 'D1CE00', 'D30094', '9314FF', 'FFBF00', 'FF901E',
          '2222B2', '228B22', 'FF00FF', '00D7FF', '20A5DA', '7280FA', 'B469FF', '5C5CCD', '8CE6F0', 'DEC4B0',
          '00FC7C', 'E6D8AD', '8080F0', 'C1B6FF', '7AA0FF', 'AAB220', 'FACE87', '998877', 'FF00FF', '8CB4D2',
          'AACD66', 'D355BA', 'DB7093', 'DDA0DD', '808000', 'CCD148', '8515C7', 'B5E4FF', '008080', '238E6B',
          '00A5FF', '0045FF', 'D670DA', 'AAE8EE', '98FB98', '9370DB', 'B9DAFF', '3F85CD', 'CBC0FF', '71B33C',
          'E6E0B0', '800080', '0000FF', '8F8FBC', 'E16941', '13458B', '008000', '60A4F4', '578B2E', '2D52A0',
          'C0C0C0', 'EBCE87', 'CD5A6A', '908070', '908070', '7FFF00', 'B48246', '2FFFAD', 'EE687B', 'D8BFD8')
COLORS = [tuple(int(c[i:i+2], 16) for i in (4, 2, 0)) for c in COLORS]  # hex2rgb


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
    for j, (x1, y1, x2, y2, conf, cls) in enumerate(result.boxes.data):

        cls = int(cls.item())
        color = COLORS[cls]

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

        for j, (x1, y1, x2, y2, conf, cls) in enumerate(result.boxes.data):

            cls = int(cls.item())
            color = COLORS[cls]

            x1, y1, x2, y2 = int(x1.item()), int(y1.item()), int(x2.item()), int(y2.item())  # noqa
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            class_name = f"{result.names[cls]} {conf:.2f}"

            font_size, _ = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_PLAIN, 1, 1)  # noqa

            if y1 < 31:
                y1 += 30

            cv2.rectangle(image, (x1, y1 - 30), (x1 + font_size[0], y1), color, -1)   # noqa
            cv2.putText(image, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1,  # noqa
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
