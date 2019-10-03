from PIL import Image
import numpy as np
import pandas as pd

# 分割出每一行
def segrow(mimgarr):
    rbegin = False
    rpoint1 = 0
    rpoint2 = 0
    simglst=[]
    for rpos in range(np.size(mimgarr,axis = 0)):
        rjudge = np.sum(mimgarr[rpos,:])
        if rjudge > 1000 and not rbegin:
            rpoint1 = rpos
            rbegin = True
        elif rjudge < 500 and rbegin:
            rpoint2 = rpos
            rbegin = False
        
        if rpoint1 != 0 and rpoint2 != 0:
            if rpoint2 - rpoint1 < 10:
                rpoint1 = 0
                rpoint2 = 0
                rbegin = False
                continue
            simgarr = mimgarr[rpoint1:rpoint2, :]
            rpoint1 = 0
            rpoint2 = 0
            rbegin = False
            
            simglst.append(simgarr)
    return simglst

# 分割出每一行里的单个单词
def segcol(simgarr, norimglst):
    ans=''
    cbegin = False
    cpoint1 = 0
    cpoint2 = 0
    cnum = 0
    weakvalue = 2550
    weakpos = 0
    cpos = 0
    # 分割出每一行里的单个单词
    while cpos < np.size(simgarr,axis = 1):
        cjudge = np.sum(simgarr[:,cpos])
        if cjudge != 0 and not cbegin:
            cpoint1 = cpos
            cbegin = True
        elif cjudge == 0 and cbegin:
            cpoint2 = cpos
            cbegin = False
            weakvalue = 2550
            weakpos = 0
        elif cbegin and 10 < cpos-cpoint1 < 21:
            if cjudge < weakvalue:
                weakpos = cpos
                weakvalue=cjudge
        elif cbegin and cpos-cpoint1 > 20:
            cpoint2 = weakpos
            cpos = weakpos-1
            cbegin = False
            weakvalue = 2550
            weakpos = 0

        if cpoint1 != 0 and cpoint2 != 0:
            charimgarr = simgarr[:, cpoint1:cpoint2]
            # 再次检验去掉首尾空白
            top = 0
            for i in range(3):
                if np.sum(charimgarr[i,:]) == 0:
                    top = i+1

            bottom = np.size(charimgarr,axis = 0)
            for i in range(bottom-2, bottom):
                if np.sum(charimgarr[i,:]) == 0:
                    bottom = i-1
            # 增加对大字符的容错
            if 30 < bottom -top < 40:
                diff = (bottom-top-29)//2
                top = top + diff
                bottom = bottom - diff
            charimgarr = charimgarr[top:bottom, :]
                    
            cbegin = False
            cpoint1 = 0
            cpoint2 = 0
            cnum = cnum+1
            # 比对识别
            ans = ans + ocr(charimgarr, norimglst)
        cpos = cpos+1

    ans = ans.replace('dot', '.')
    ans = ans.replace('neg', '-')
    ans = ans.replace('stop', ',')
    return ans

# 计算图片相似度的MSE算法
def mse(imgarrA, imgarrB):
	err = np.sum((imgarrA - imgarrB) ** 2)
	err /= float(np.size(imgarrA,axis = 0) * np.size(imgarrA,axis = 1))
	return err

# 字符识别
def ocr(charimgarr, norimglst):
    err = 100000
    # 将两张图片放在同样大小的背景中比对
    imgarr = np.zeros((30, 20))
    row = np.size(charimgarr,axis = 0)
    col = np.size(charimgarr,axis = 1)
    rstart = (30 - row)//2
    cstart = (20 - col)//2
    imgarr[rstart:rstart+row, cstart:cstart+col] = imgarr[rstart:rstart+row, cstart:cstart+col] + charimgarr
    for (f, norimg) in norimglst:
        temerr = mse(imgarr, norimg)
        if temerr < err:
            char = f
            err = temerr
    return char

# 加载标准图片
def loadnor(norimg):
    norimglst = []
    for f in norimg:
        path = 'data//num//'+f+'.jpg'
        img = Image.open(path)
        img = np.asarray(img).astype('float')
        norimglst.append((f, img))
    return norimglst

# 寻找表格线
def getline(temp, part):
    cpos = part['cstart']
    linepos = []
    if part['colnum'] == 6:
        linepos.append(part['cstart'])
    rnum = part['rend'] - part['rstart']

    while cpos < part['cend']:
        cpos = cpos + 1
        rpos = 0
        counter = 0
        while rpos < rnum:
            # cpos+7对表格线错位进行容错
            if np.sum(temp[rpos, cpos:cpos+7]) == 0:
                counter = counter + 1
            # counter=40对表格线中断容错
            if counter == 40:
                break
            rpos = rpos + 1
        if rpos == rnum:
            linepos.append(cpos+3)
            cpos = cpos + part['cgap']

    if part['colnum'] == 6:
        linepos.append(part['cend'])
    return linepos

def main(limgarr, part, norimg):
    df = pd.DataFrame(columns = part['columns'])
    temp = limgarr[part['rstart']:part['rend'], :]
    linepos = getline(temp, part)

    for i in range(part['colnum']):
        # 将大图分为小图
        cn1 = linepos[i] + 10
        cn2 = linepos[i+1] - 10
        # 得到每一列
        mimgarr = temp[:, cn1:cn2]*255
        # 得到每一行的字符
        simglst = segrow(mimgarr)
        norimglst = loadnor(norimg)
        lst=[]
        for r in range(len(simglst)):
            ans = segcol(simglst[r], norimglst)
            lst.append(ans)
        # 将结果存进dataframe
        df[part['columns'][i]] = lst
    return df


# 所有字符列表
norimg = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'dot', 'neg', 'stop']
# 四部分表格参数
part1 = {'columns': ['企业单位数','工业总产值（不变价）',
                     '工业总产值（现价）','工业净产值'],
         'cstart': 500,
         'cend': 2000,
         'cgap': 200,
         'rstart': 820,
         'rend': 2690,
         'colnum': 4}
part2 = {'columns': ['全部职工年末人数','全部职工平均人数','全部职工工资总额',
                     '年末固定资产原值','其中：生产用固定资产','年末固定资产净值'],
         'cstart': 230,
         'cend': 1950,
         'cgap': 200,
         'rstart': 820,
         'rend': 2650,
         'colnum': 6}
part3 = {'columns': ['流动资金全年平均余额','其中：定额流动资金全年平均余额',
                     '全部资金','产品销售收入'],
         'cstart': 500,
         'cend': 2000,
         'cgap': 200,
         'rstart': 840,
         'rend': 2690,
         'colnum': 4}
part4 = {'columns': ['产品销售税金','产品销售工厂成本','利润总额',
                     '利税总额','已交利税费','企业留利'],
         'cstart': 230,
         'cend': 1950,
         'cgap': 200,
         'rstart': 830,
         'rend': 2650,
         'colnum': 6}
partlst = [part1, part2, part3, part4]

root = "data//"
for n in range(217,218):
    p = n % 4
    if p == 0:
        p = 4
    name = str(n)+'p'+str(p)
    path = root+name+'.bmp'
    image = Image.open(path)
    limgarr = np.asarray(image).astype('float')
    df = main(limgarr, partlst[p-1], norimg)
    df.to_excel('result//'+name+'.xlsx', sheet_name='Sheet1')
