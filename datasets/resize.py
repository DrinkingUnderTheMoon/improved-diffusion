import cv2 as cv

if __name__ == '__main__':
    to_resize_image_path = '../scripts/tmp/2_img_att_pgd/2.png'
    to_resize_size_x = 256
    to_resize_size_y = 256
    to_save_resized_image_path = "attacked_image/resize_2_img_att_pgd_detect_area_image_2.png"

    to_resize_image = cv.imread(to_resize_image_path)
    resized_image = cv.resize(to_resize_image, (to_resize_size_x, to_resize_size_y), interpolation=cv.INTER_AREA)
    cv.imwrite(to_save_resized_image_path, resized_image)