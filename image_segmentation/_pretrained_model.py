import cv2
import imageio
import numpy as np

from ultralytics import YOLO
from ultralytics.yolo.utils.ops import scale_image

from aiogram.utils.exceptions import FileIsTooBig


COLORS = ('E22B8A', '87B8DE', '1E69D2', '507FFF', '4763FF', 'ED9564', '3C14DC', '8B8B00', '0B86B8', 'A9A9A9',  # noqa
          '6BB7BD', '008CFF', 'CC3299', '7A96E9', '8FBC8F', 'D1CE00', 'D30094', '9314FF', 'FFBF00', 'FF901E',  # noqa
          '2222B2', '228B22', 'FF00FF', '00D7FF', '20A5DA', '7280FA', 'B469FF', '5C5CCD', '8CE6F0', 'DEC4B0',  # noqa
          '00FC7C', 'E6D8AD', '8080F0', 'C1B6FF', '7AA0FF', 'AAB220', 'FACE87', '998877', 'FF00FF', '8CB4D2',  # noqa
          'AACD66', 'D355BA', 'DB7093', 'DDA0DD', '808000', 'CCD148', '8515C7', 'B5E4FF', '008080', '238E6B',  # noqa
          '00A5FF', '0045FF', 'D670DA', 'AAE8EE', '98FB98', '9370DB', 'B9DAFF', '3F85CD', 'CBC0FF', '71B33C',  # noqa
          'E6E0B0', '800080', '0000FF', '8F8FBC', 'E16941', '13458B', '008000', '60A4F4', '578B2E', '2D52A0',  # noqa
          'C0C0C0', 'EBCE87', 'CD5A6A', '908070', '908070', '7FFF00', 'B48246', '2FFFAD', 'EE687B', 'D8BFD8')  # noqa
COLORS = [tuple(int(c[i:i+2], 16) for i in (4, 2, 0))
          for c in COLORS]  # hex2rgb

MAX_ACCESS_FRAMES = 300

model = YOLO('yolov8s.pt')
model_seg = YOLO('yolov8s-seg.pt')


def overlay(image, mask, color, alpha=.5):
    colored_mask = np.expand_dims(mask, 0).repeat(3, axis=0)
    colored_mask = np.moveaxis(colored_mask, 0, -1)
    masked = np.ma.MaskedArray(image, mask=colored_mask, fill_value=color)
    image_overlay = masked.filled()

    return cv2.addWeighted(image, 1 - alpha, image_overlay, alpha, 0)


def segment_result(result, with_mask=False):
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

        if with_mask:
            mask = result.masks.data[j].cpu().numpy()
            mask = scale_image(mask, image.shape)
            image = overlay(image, mask, color)

    return image


def segment_photo(img_path):
    result = model_seg(img_path, conf=.5, line_thickness=2)[0]
    image = segment_result(result, with_mask=True)
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
    FPS = int(cap.get(cv2.CAP_PROP_FPS))

    cap.release()

    if FRAMES > MAX_ACCESS_FRAMES:
        raise FileIsTooBig(f'Видео содержит слишком много кадров ({FRAMES} > {MAX_ACCESS_FRAMES})')  # noqa

    new_path = f"videos/{vid_path.split('/')[1].split('.')[0]}_seg.mp4"
    cap_out = cv2.VideoWriter(new_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS,
                              (frame.shape[1], frame.shape[0]))

    frames = model.predict(vid_path, stream=True, conf=.5, line_thickness=2)

    for i, result in enumerate(frames):
        image = segment_result(result)
        cap_out.write(image)

        if i % 15 == 0:
            progress = progressBar(i, FRAMES)
            yield (progress, 0)

    cap_out.release()
    yield (new_path, 1)


def segment_gif(vid_path):
    cap = cv2.VideoCapture(vid_path)

    FRAMES = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()

    if FRAMES > MAX_ACCESS_FRAMES:
        raise FileIsTooBig(f'Видео содержит слишком много кадров ({FRAMES} > {MAX_ACCESS_FRAMES})')  # noqa

    new_path = f"animations/{vid_path.split('/')[1].split('.')[0]}_seg.gif"

    frames = model.predict(vid_path, stream=True, conf=.5,  line_thickness=2)

    with imageio.get_writer(new_path, mode='I') as writer:
        for i, result in enumerate(frames):
            image = segment_result(result)[:, :, ::-1]
            writer.append_data(image)

            if i % 15 == 0:
                progress = progressBar(i, FRAMES)
                yield (progress, 0)

    yield (new_path, 1)
