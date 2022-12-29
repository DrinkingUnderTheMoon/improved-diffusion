import numpy as np
from PIL import Image
import os

# sample产生的结果是npz类型的文件，这个脚本负责将npz文件转换成对应的图片文件
result_file_name = "beta_size_256_diffusion_step_100_logs_resize_attacked_image_linear_noise/samples_5x256x256x3_100000.npz"
if __name__ == '__main__':
    result = np.load(result_file_name)
    result_file = result['arr_0']
    img_save_path = result_file_name[:-4]
    if len(result_file) != 0 and not os.path.exists(img_save_path):
        os.mkdir(img_save_path)
    for i in range(len(result_file)):
        img = Image.fromarray(result_file[i]).convert('RGB')  # 将数组转化回图片
        img.save(img_save_path + '/' + str.format("{}.png", i))
