from PIL import Image
import numpy as np
import os


file=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'dot', 'neg', 'stop']
for f in file:
    fpath = "data//num//" + f
    average = np.zeros((30, 20))
    # 获取图片名列表
    for root, dirs, files in os.walk(fpath):
        lst = files
    # 计算图片的平均图并存储
    for fimg in lst:
        imgpath = root + '//' + fimg
        image = Image.open(imgpath)
        image = np.asarray(image).astype('float')
        row = np.size(image,axis = 0)
        col = np.size(image,axis = 1)
        rstart = (30 - row)//2
        cstart = (20 - col)//2
        average[rstart:rstart+row, cstart:cstart+col] = average[rstart:rstart+row, cstart:cstart+col] + image
    average = average / len(lst)
    image = Image.fromarray(average.astype('uint8'))
    path = root+'.jpg'
    image.save(path)