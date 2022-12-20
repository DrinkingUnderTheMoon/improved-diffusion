import cv2 as cv

if __name__ == '__main__':
    to_resize_image_path = '../result/size_256_diffusion_step_100_logs_resize_attacked_image_cosine_noise/samples_5x256x256x3_080000/2.png'
    to_resize_size = 417
    to_save_resized_image_path = "../result/size_256_diffusion_step_100_logs_resize_attacked_image_cosine_noise/resize_080000/2.png"

    to_resize_image = cv.imread(to_resize_image_path)
    resized_image = cv.resize(to_resize_image, (to_resize_size, to_resize_size), interpolation=cv.INTER_AREA)
    cv.imwrite(to_save_resized_image_path, resized_image)