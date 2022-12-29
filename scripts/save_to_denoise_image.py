import datetime
import os.path
from functools import cmp_to_key

import cv2 as cv
import numpy


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

    next_index = 0
    while next_index < len(to_merge_area_list):
        top_left_x, top_left_y, bottom_right_x, bottom_right_y = to_merge_area_list.pop(next_index)

        i = next_index
        k = next_index - 1  # 指向比当前框要前的第一个框
        while i < len(to_merge_area_list):
            another_top_left_x, another_top_left_y, another_bottom_right_x, another_bottom_right_y = to_merge_area_list[
                i]
            if top_left_x <= another_top_left_x <= bottom_right_x:
                if (top_left_y <= another_top_left_y <= bottom_right_y) or \
                        (top_left_y <= another_bottom_right_y <= bottom_right_y) or \
                        (another_top_left_y <= top_left_y and another_bottom_right_y >= bottom_right_y) or \
                        (another_top_left_y >= top_left_y and another_bottom_right_y <= bottom_right_y):
                    # 可以进行合并
                    small_x, small_y = min(top_left_x, another_top_left_x), min(top_left_y, another_top_left_y)
                    big_x, big_y = max(bottom_right_x, another_bottom_right_x), max(bottom_right_y,
                                                                                    another_bottom_right_y)
                    to_merge_area_list.pop(i)
                    if i < next_index:
                        next_index -= 1

                    top_left_x, top_left_y, bottom_right_x, bottom_right_y = count_extract_area(small_x, small_y, big_x,
                                                                                                big_y, max_x, max_y)
                    if k < len(to_merge_area_list):
                        while k >= 0:
                            check_top_left_x, check_top_left_y, check_bottom_right_x, check_bottom_right_y = \
                                to_merge_area_list[k]
                            if (check_top_left_x < top_left_x) or (
                                    check_top_left_x == top_left_x and check_bottom_right_x <= bottom_right_x):
                                break
                            k -= 1
                    i = k + 1
                else:
                    i = i + 1
            else:
                # 后续元素不可能被合并
                break
        to_merge_area_list.insert(min(k+1, len(to_merge_area_list)), [top_left_x, top_left_y, bottom_right_x, bottom_right_y])
        next_index = next_index + 1

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
    print('final result:')
    merged_area_list = merge_image_area(to_merge_area_list, image.shape[1], image.shape[0])
    for i, (top_left_x, top_left_y, bottom_right_x, bottom_right_y,) in enumerate(merged_area_list):
        final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y = \
            count_extract_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y, image.shape[1], image.shape[0])
        print(final_top_left_x, final_top_left_y, final_bottom_right_x, final_bottom_right_y)
        image_area = extract_image_area(image, final_top_left_x, final_top_left_y, final_bottom_right_x,
                                        final_bottom_right_y)
        cv.imwrite(save_path + str(i) + ".png", image_area)


def simple_merge_by_box_center(box_list):
    origin_length = 0
    while origin_length != len(box_list):
        origin_length = len(box_list)
        center_list = []
        for top_left_x, top_left_y, bottom_right_x, bottom_right_y in box_list:
            center_list.append(((top_left_x + bottom_right_x) // 2, (top_left_y + bottom_right_y) // 2))
        distance_matrix = numpy.zeros((origin_length, origin_length))
        for i in range(origin_length):
            for j in range(origin_length):
                if i < j:
                    center_a = center_list[i]
                    center_b = center_list[j]
                    distance_matrix[i][j] = abs((center_b[0] - center_a[0])) + abs((center_b[1] - center_a[1]))
                elif i == j:
                    pass
                else:
                    distance_matrix[i][j] = distance_matrix[j][i]

        new_box_list = []
        has_been_merged_set = set()
        for i in range(origin_length):
            i_to_merge_list = []
            small_x, small_y, big_x, big_y = box_list[i]
            if i in has_been_merged_set:
                # 已经被其他中心合并
                continue
            for j in range(origin_length):
                if i < j and j not in has_been_merged_set and distance_matrix[i][j] <= 5:
                    i_to_merge_list.append(j)
                    has_been_merged_set.add(j)
            if len(i_to_merge_list) != 0:
                has_been_merged_set.add(i)
                for to_merge in i_to_merge_list:
                    top_left_x, top_left_y, bottom_right_x, bottom_right_y = box_list[to_merge]
                    if top_left_x < small_x:
                        small_x = top_left_x
                    if top_left_y < small_y:
                        small_y = top_left_y
                    if bottom_right_x > big_x:
                        big_x = bottom_right_x
                    if bottom_right_y > big_y:
                        big_y = bottom_right_y
            new_box_list.append([small_x, small_y, big_x, big_y])
        box_list = new_box_list
    return box_list


if __name__ == '__main__':
    # test case 1
    # img = cv.imread('../datasets/attacked_image/2_img_att_fgsm.png')
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

    # test case 5
    # img = cv.imread('../datasets/attacked_image/0_img_att_pgd.png')
    # detect_results = [[8.6343e+00, 1.4309e+02, 6.9442e+01, 1.6617e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
    #                   [4.0893e+01, 1.4439e+02, 1.0085e+02, 1.7029e+02, 1.0000e+00, 9.9999e-01, 0.0000e+00],
    #                   [3.1260e+02, 1.4675e+02, 3.5234e+02, 1.6257e+02, 1.0000e+00, 9.9999e-01, 0.0000e+00],
    #                   [3.1056e+00, 1.4731e+02, 8.5410e+01, 2.1434e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
    #                   [3.3912e+02, 1.4410e+02, 3.7731e+02, 1.6266e+02, 9.9999e-01, 9.9801e-01, 0.0000e+00],
    #                   [2.5671e+02, 1.4608e+02, 2.6721e+02, 1.5754e+02, 9.9997e-01, 2.0012e-01, 0.0000e+00],
    #                   [1.5443e+02, 1.4505e+02, 2.0474e+02, 1.7075e+02, 9.9900e-01, 9.9999e-01, 0.0000e+00],
    #                   [1.9962e+02, 1.4287e+02, 2.2808e+02, 1.6024e+02, 9.9814e-01, 1.0000e+00, 0.0000e+00],
    #                   [2.4459e+02, 1.9497e+02, 2.7634e+02, 2.4964e+02, 1.0000e+00, 9.9998e-01, 3.0000e+00],
    #                   [3.3708e+02, 2.2872e+02, 3.5441e+02, 2.6483e+02, 1.0000e+00, 9.9424e-01, 3.0000e+00],
    #                   [2.8903e+02, 1.5303e+02, 3.1714e+02, 1.7998e+02, 9.9968e-01, 8.8030e-03, 3.0000e+00],
    #                   [3.3666e+02, 2.2806e+02, 3.5399e+02, 2.5998e+02, 1.0000e+00, 9.9991e-01, 5.0000e+00],
    #                   [2.8214e+02, 1.4907e+02, 3.0903e+02, 1.8676e+02, 9.9999e-01, 7.6812e-01, 5.0000e+00],
    #                   [3.7638e+02, 2.2371e+02, 3.9312e+02, 2.4671e+02, 9.9956e-01, 1.0618e-01, 5.0000e+00],
    #                   [2.0322e+02, 1.4324e+02, 2.2427e+02, 1.5904e+02, 9.9999e-01, 9.9202e-01, 7.0000e+00]]

    # test case 6
    # img = cv.imread('../datasets/attacked_image/1_img_att_pgd.png')
    # detect_results = [[7.3589e+01, 2.1077e+02, 9.2442e+01, 2.2077e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
    #                   [3.9656e+02, 1.9372e+02, 4.1678e+02, 2.2086e+02, 1.0000e+00, 9.6900e-01, 0.0000e+00],
    #                   [1.3018e+02, 2.0593e+02, 1.4262e+02, 2.1379e+02, 1.0000e+00, 9.9999e-01, 0.0000e+00],
    #                   [2.5257e+02, 2.0371e+02, 2.8793e+02, 2.1272e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
    #                   [1.5187e+02, 1.9529e+02, 1.7491e+02, 2.1391e+02, 9.9996e-01, 8.7658e-01, 0.0000e+00],
    #                   [2.0036e+02, 1.9667e+02, 2.1091e+02, 2.0845e+02, 1.0000e+00, 9.9992e-01, 2.0000e+00],
    #                   [1.5050e+02, 1.9487e+02, 1.7718e+02, 2.1273e+02, 9.9999e-01, 9.9840e-01, 2.0000e+00],
    #                   [2.2677e+02, 2.0114e+02, 2.3112e+02, 2.1093e+02, 1.0000e+00, 1.0000e+00, 5.0000e+00],
    #                   [3.3431e+02, 2.0764e+02, 3.5335e+02, 2.3195e+02, 1.0000e+00, 5.9654e-01, 5.0000e+00],
    #                   [1.5233e+02, 1.9598e+02, 1.7543e+02, 2.1315e+02, 1.0000e+00, 1.6890e-01, 6.0000e+00]]

    # test case 7
    img = cv.imread('../datasets/attacked_image/2_img_att_pgd.png')
    detect_results = [[2.2081e+02, 2.0881e+02, 2.3668e+02, 2.2035e+02, 1.0000e+00, 9.9994e-01, 0.0000e+00],
                      [7.3643e+01, 1.4452e+02, 1.0455e+02, 1.6574e+02, 1.0000e+00, 9.8026e-01, 0.0000e+00],
                      [3.7673e+02, 1.4237e+02, 4.1299e+02, 1.6324e+02, 1.0000e+00, 1.0000e+00, 0.0000e+00],
                      [1.4592e+02, 2.0894e+02, 1.6965e+02, 2.3133e+02, 1.0000e+00, 9.0269e-01, 0.0000e+00],
                      [2.9115e+02, 1.4262e+02, 3.0607e+02, 1.5904e+02, 9.9992e-01, 9.7422e-01, 0.0000e+00],
                      [2.7220e+02, 1.4378e+02, 2.9028e+02, 1.5492e+02, 9.9979e-01, 9.9999e-01, 0.0000e+00],
                      [2.6883e+02, 2.0028e+02, 3.3682e+02, 2.5816e+02, 9.9963e-01, 1.2560e-02, 2.0000e+00],
                      [3.5597e+02, 2.3399e+02, 3.6614e+02, 2.5845e+02, 1.0000e+00, 9.9999e-01, 3.0000e+00],
                      [2.7406e+02, 1.4219e+02, 2.8993e+02, 1.5615e+02, 9.9998e-01, 9.4428e-01, 4.0000e+00],
                      [5.2630e+00, 2.1802e+02, 4.4847e+01, 2.6908e+02, 1.0000e+00, 3.8185e-01, 5.0000e+00],
                      [2.8805e+02, 1.4231e+02, 3.0492e+02, 1.6337e+02, 1.0000e+00, 9.9457e-01, 5.0000e+00],
                      [3.5559e+02, 2.3669e+02, 3.6516e+02, 2.5813e+02, 9.9999e-01, 9.9841e-01, 5.0000e+00],
                      [1.4278e+02, 2.1225e+02, 1.7077e+02, 2.3214e+02, 9.9959e-01, 5.1471e-01, 5.0000e+00],
                      [2.8203e+02, 2.0776e+02, 3.2770e+02, 2.5822e+02, 9.9920e-01, 1.7879e-01, 5.0000e+00],
                      [1.4426e+02, 2.1080e+02, 1.6814e+02, 2.3159e+02, 1.0000e+00, 5.8493e-01, 7.0000e+00],
                      [6.7187e+00, 2.2040e+02, 4.5788e+01, 2.6807e+02, 1.0000e+00, 4.0118e-01, 7.0000e+00],
                      [6.9754e+01, 1.4589e+02, 1.0568e+02, 1.6482e+02, 9.9652e-01, 9.9997e-01, 7.0000e+00],
                      [2.7207e+02, 2.0343e+02, 3.3214e+02, 2.5224e+02, 9.9266e-01, 9.9998e-01, 7.0000e+00]]

    box_list = []
    for top_left_x, top_left_y, bottom_right_x, bottom_right_y, _, _, _ in detect_results:
        box_list.append([int(top_left_x), int(top_left_y), int(bottom_right_x), int(bottom_right_y)])
    box_list = simple_merge_by_box_center(box_list)
    print('after simple merge by box center, box_list:', box_list)
    for box in box_list:
        box.append(0)
        box.append(0)
        box.append(0)
    get_to_denoise_image(img, box_list, "tmp/" + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) + "/")

    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_0_linear_noise/samples_5x32x32x3_100000/1_selected.png')
    # img = stamp_image_area(img_area, img, 103, 195, 134, 226)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_0_linear_noise/samples_5x32x32x3_100000/denoise_image_area_0_attacked_image.png', img)

    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_1_linear_noise/samples_5x32x32x3_100000/0_selected.png')
    # img = stamp_image_area(img_area, img, 186, 190, 217, 221)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_1_linear_noise/samples_5x32x32x3_100000/denoise_image_area_1_attacked_image.png', img)

    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_2_linear_noise/samples_5x32x32x3_100000/1_selected.png')
    # img = stamp_image_area(img_area, img, 198, 188, 229, 219)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_2_linear_noise/samples_5x32x32x3_100000/denoise_image_area_2_attacked_image.png', img)
    #
    # img_area = cv.imread('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_3_linear_noise/samples_5x32x32x3_100000/0_selected.png')
    # img = stamp_image_area(img_area, img, 114, 191, 145, 222)
    # cv.imwrite('../result/size_32_diffusion_step_100_logs_attacked_detect_area_image_3_linear_noise/samples_5x32x32x3_100000/denoise_image_area_3_attacked_image.png', img)
