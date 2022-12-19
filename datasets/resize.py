import cv2 as cv

if __name__ == '__main__':
    to_resize_image_path = 'attacked_image/8_img_att_fgsm.png'
    to_resize_size = 256
    to_save_resized_image_path = "attacked_image/resized_8_img_att_fgsm.png"

    to_resize_image = cv.imread(to_resize_image_path)
    resized_image = cv.resize(to_resize_image, (to_resize_size, to_resize_size), interpolation=cv.INTER_AREA)
    cv.imwrite(to_save_resized_image_path, resized_image)