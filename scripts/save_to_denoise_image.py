import datetime
import os.path

import cv2 as cv


def count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, max_x, max_y):
    # max_x x坐标的最大值
    # max_y y坐标的最大值
    top_left_x, top_left_y = int(top_left_x), int(top_left_y)
    bottom_right_x, bottom_right_y = int(bottom_right_x), int(bottom_right_y)
    center_x, center_y = (top_left_x + bottom_right_x) // 2, (top_left_y + bottom_right_y) // 2
    longest_edge = max(abs(bottom_right_y - top_left_y), abs(bottom_right_x - top_left_x), 0)

    final_size = None

    if longest_edge == 0:
        raise Exception("longest_edge = 0")
    elif longest_edge < 32:
        final_size = 32
    elif longest_edge < 64:
        final_size = 64
    else:
        final_size = 256
    final_top_left_x, final_bottom_right_x = center_x - final_size // 2, center_x + final_size // 2 - 1
    final_top_left_y, final_bottom_right_y = center_y - final_size // 2, center_y + final_size // 2 - 1
    if final_bottom_right_x > max_x:
        final_top_left_x -= (final_bottom_right_x - max_x)
        final_bottom_right_x = max_x

    if final_bottom_right_y > max_y:
        final_top_left_y -= (final_bottom_right_y - max_y)
        final_bottom_right_y = max_y

    if final_top_left_x < 0:
        final_bottom_right_x -= final_top_left_x
        final_top_left_x = 0

    if final_top_left_y < 0:
        final_bottom_right_y -= final_top_left_y
        final_top_left_y = 0

    return final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y


def merge_image_area(to_merge_area_list):
    # todo
    print(to_merge_area_list)
    # 合并具有重叠部分的区间
    merged_area_list = []
    # 暴力求解
    while True:
        merged_flag=False
        if not merged_flag:
            break

    return to_merge_area_list


def extract_image_area(image, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    image_area = image[top_left_y: bottom_right_y + 1, top_left_x: bottom_right_x + 1]
    return image_area


def stamp_image_area(image_area, image, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    image[top_left_y: bottom_right_y + 1, top_left_x: bottom_right_x + 1] = image_area
    return image


def main(image, detect_results, save_path):
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    to_merge_area_list = []
    for i, (top_left_x, top_left_y, bottom_right_x, bottom_right_y, _, _, _) in enumerate(detect_results):
        final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y = \
            count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, image.shape[1], image.shape[0])
        to_merge_area_list.append([final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y])
    merged_area_list = merge_image_area(to_merge_area_list)
    for (top_left_x, top_left_y, bottom_right_x, bottom_right_y,) in merged_area_list:
        final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y = \
            count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, image.shape[1], image.shape[0])
        image_area = extract_image_area(image, final_top_left_x, final_top_left_y, final_bottom_right_x,
                                        final_bottom_right_y)
        # cv.imwrite(save_path + str(i) + ".png", image_area)


if __name__ == '__main__':
    img = cv.imread('../datasets/attacked_image/1_img_input.png')
    detect_results = [[110.4054, 206.4721, 128.9373, 217.0720, 1.0000, 1.0000, 0.0000],
                     [198.4990, 203.3287, 206.6206, 209.6069, 1.0000, 1.0000, 0.0000],
                     [209.0470, 199.1367, 219.6318, 209.0477, 1.0000, 1.0000, 0.0000],
                     [124.9781, 203.6919, 137.3534, 212.5088, 0.9999, 0.9874, 1.0000],
                     [208.2764, 198.7971, 219.1568, 208.8763, 1.0000, 1.0000, 2.0000],
                     [123.0030, 204.0153, 136.4574, 211.8949, 0.8351, 0.9999, 7.0000]]
    main(img, detect_results, "tmp/" + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) + "/")
