import datetime
import os.path
from functools import cmp_to_key

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
    elif longest_edge <= 32:
        final_size = 32
    elif longest_edge <= 64:
        final_size = 64
    elif longest_edge <= 256:
        final_size = 256
    else:
        print(top_left_x, top_left_y, bottom_right_x, bottom_right_y)
        print("longest_edge > 256 can not be resized, it need manually adjust")
        return top_left_x, top_left_y, bottom_right_x, bottom_right_y

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


def merge_image_area(to_merge_area_list, max_x, max_y):
    def compare(a, b):
        if a[0] > b[0]:
            return 1
        if a[0] == b[0] and a[3] > b[3]:
            return 1
        if a[0] == b[0] and a[3] == b[3]:
            return 0
        return -1

    to_merge_area_list = sorted(to_merge_area_list, key=cmp_to_key(compare))

    i = 0
    while i < len(to_merge_area_list):
        top_left_x, top_left_y, bottom_right_x, bottom_right_y = to_merge_area_list[i]
        j = i + 1
        while j < len(to_merge_area_list):
            another_top_left_x, another_top_left_y, another_bottom_right_x, another_bottom_right_y = to_merge_area_list[
                j]
            if top_left_x <= another_top_left_x <= bottom_right_x:
                if (top_left_y <= another_top_left_y <= bottom_right_y) or \
                        (top_left_y <= another_bottom_right_y <= bottom_right_y) or \
                        (another_top_left_y <= top_left_y and another_bottom_right_y >= bottom_right_y) or \
                        (another_top_left_y >= top_left_y and another_bottom_right_y <= bottom_right_y):
                    # 可以进行合并
                    small_x, small_y = min(top_left_x, another_top_left_x), min(top_left_y, another_top_left_y)
                    big_x, big_y = max(bottom_right_x, another_bottom_right_x), max(bottom_right_y,
                                                                                    another_bottom_right_y)
                    to_merge_area_list.pop(j)
                    top_left_x, top_left_y, bottom_right_x, bottom_right_y = count_extract_area(small_x, small_y, big_x,
                                                                                                big_y, max_x, max_y)
                    # 需要重新检查以前的所有元素
                    j = i + 1
                else:
                    j = j + 1
            else:
                # 后续元素不可能被合并
                break
        to_merge_area_list[i] = top_left_x, top_left_y, bottom_right_x, bottom_right_y
        i = i + 1
    print(to_merge_area_list)
    return to_merge_area_list


def extract_image_area(image, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    image_area = image[top_left_y: bottom_right_y + 1, top_left_x: bottom_right_x + 1]
    return image_area


def stamp_image_area(image_area, image, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    image[top_left_y: bottom_right_y + 1, top_left_x: bottom_right_x + 1] = image_area
    return image


def get_to_denoise_image(image, detect_results, save_path):
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    # with image_area_log_file = open(save_path + 'image_area_log.txt', 'w')
    to_merge_area_list = []
    for i, (top_left_x, top_left_y, bottom_right_x, bottom_right_y, _, _, _) in enumerate(detect_results):
        final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y = \
            count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, image.shape[1], image.shape[0])
        to_merge_area_list.append([final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y])
    # 输出中间结果（小图的坐标）
    print(to_merge_area_list)
    merged_area_list = merge_image_area(to_merge_area_list, image.shape[1], image.shape[0])
    for i, (top_left_x, top_left_y, bottom_right_x, bottom_right_y,) in enumerate(merged_area_list):
        final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y = \
            count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, image.shape[1], image.shape[0])
        image_area = extract_image_area(image, final_top_left_x, final_top_left_y, final_bottom_right_x,
                                        final_bottom_right_y)
        cv.imwrite(save_path + str(i) + ".png", image_area)


if __name__ == '__main__':
    # test case 1
    img = cv.imread('../datasets/attacked_image/2_img_att_fgsm.png')
    # detect_results = [[110.4054, 206.4721, 128.9373, 217.0720, 1.0000, 1.0000, 0.0000],
    #                   [198.4990, 203.3287, 206.6206, 209.6069, 1.0000, 1.0000, 0.0000],
    #                   [209.0470, 199.1367, 219.6318, 209.0477, 1.0000, 1.0000, 0.0000],
    #                   [124.9781, 203.6919, 137.3534, 212.5088, 0.9999, 0.9874, 1.0000],
    #                   [208.2764, 198.7971, 219.1568, 208.8763, 1.0000, 1.0000, 2.0000],
    #                   [123.0030, 204.0153, 136.4574, 211.8949, 0.8351, 0.9999, 7.0000]]

    # test case 2
    # img = cv.imread('../datasets/attacked_image/0_img_att_fgsm.png')
    # detect_results = [[196.7677, 211.8132, 234.0015, 227.2941, 1.0000, 1.0000, 0.0000],
    #                   [59.9453, 220.8628, 106.8329, 238.5493, 1.0000, 1.0000, 0.0000],
    #                   [1.1631, 217.9459, 30.9825, 247.1632, 1.0000, 1.0000, 0.0000],
    #                   [26.8245, 219.8532, 66.2187, 242.2104, 1.0000, 0.9955, 0.0000],
    #                   [241.7142, 209.6059, 260.1054, 222.5255, 1.0000, 1.0000, 0.0000],
    #                   [58.9597, 217.8770, 105.7518, 239.7415, 1.0000, 0.9990, 6.0000]]

    # test case 3
    # img = cv.imread('../datasets/attacked_image/19_img_att_fgsm.png')
    # detect_results = [[250.7827, 206.7079, 317.8695, 250.0758, 1.0000, 1.0000, 0.0000],
    #                   [184.3919, 206.2972, 193.4888, 213.0766, 1.0000, 1.0000, 0.0000],
    #                   [1.3225, 228.1617, 131.8484, 262.4686, 0.9571, 0.9981, 0.0000],
    #                   [-4.2483, 143.8718, 147.8828, 268.7448, 1.0000, 0.9923, 1.0000],
    #                   [213.7691, 201.9505, 229.2172, 217.0006, 1.0000, 1.0000, 1.0000],
    #                   [344.0506, 207.0439, 352.7533, 224.3783, 0.9998, 0.8272, 3.0000],
    #                   [343.0685, 207.4971, 354.4904, 226.1065, 0.9996, 0.8183, 7.0000]]

    # test case 4
    # img = cv.imread('../datasets/attacked_image/26_img_att_fgsm.png')
    # detect_results = [[1.8492e+02, 2.0398e+02, 1.9364e+02, 2.0874e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
    #                   [2.1339e+02, 1.9762e+02, 2.4047e+02, 2.1570e+02, 1.0000e+00, 6.0951e-01, 1.0000e+00],
    #                   [2.1395e+02, 1.9673e+02, 2.4036e+02, 2.1489e+02, 9.9999e-01, 9.6155e-01, 2.0000e+00],
    #                   [2.1204e+02, 1.9699e+02, 2.4058e+02, 2.1615e+02, 1.0000e+00, 3.3577e-02, 5.0000e+00]]

    # get_to_denoise_image(img, detect_results, "tmp/" + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) + "/")



    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_0_linear_noise/samples_5x32x32x3_100000/1_selected.png')
    # img = stamp_image_area(img_area, img, 103, 195, 134, 226)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_0_linear_noise/samples_5x32x32x3_100000/denoise_image_area_0_attacked_image.png', img)

    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_1_linear_noise/samples_5x32x32x3_100000/0_selected.png')
    # img = stamp_image_area(img_area, img, 186, 190, 217, 221)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_1_linear_noise/samples_5x32x32x3_100000/denoise_image_area_1_attacked_image.png', img)

    img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_2_linear_noise/samples_5x32x32x3_100000/1_selected.png')
    img = stamp_image_area(img_area, img, 198, 188, 229, 219)
    cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_2_linear_noise/samples_5x32x32x3_100000/denoise_image_area_2_attacked_image.png', img)

    img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_3_linear_noise/samples_5x32x32x3_100000/0_selected.png')
    img = stamp_image_area(img_area, img, 114, 191, 145, 222)
    cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_3_linear_noise/samples_5x32x32x3_100000/denoise_image_area_3_attacked_image.png', img)
