import hashlib
import re

#把url转为md5方式
def get_md5(url):
    m = hashlib.md5()
    m.update(url.encode("utf-8"))
    return m.hexdigest()

# 提取数字
def get_nums(value):
    match_int = re.findall(r'\d+', value)
    if match_int:
        nums = int(''.join(match_int))
    else:
        nums = 0

    return nums

def deal_nums(value):
    r = re.findall('\d+', value)
    r = '.'.join(r)
    number = float(r)
    if "万" in value:
        number *= 10000
    return int(number)
