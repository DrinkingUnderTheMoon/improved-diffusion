import cv2 as cv

if __name__ == '__main__':
    img = cv.imread('traffic/traffic.png')
    # cv.imshow('Image', img)
    # cv.waitKey(-1)
    shrink_img = cv.resize(img, (512, 512), interpolation=cv.INTER_AREA)
    height, width = img.shape[:2]
    print(height, width)
    cv.imshow('shrink_img', shrink_img)
    shrink_img = cv.resize(shrink_img, (width, height), interpolation=cv.INTER_CUBIC)
    cv.imshow('img', img)
    cv.imshow('shrink_resize_img', shrink_img)
    cv.waitKey(10000)
