import numpy as np
from PIL import Image
import os

result_file_name = "diffusion_step_100_loop_100000_samples_2x64x64x3/samples_2x64x64x3.npz"
if __name__ == '__main__':
    result = np.load(result_file_name)
    result_file = result['arr_0']
    img_save_path = result_file_name[:-4]
    if len(result_file) != 0 and not os.path.exists(img_save_path):
        os.mkdir(img_save_path)
    for i in range(len(result_file)):
        img = Image.fromarray(result_file[i]).convert('RGB')  # 将数组转化回图片
        img.save(img_save_path + '/' + str.format("{}.png", i))
