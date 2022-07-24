from requests import session
from muggle_ocr import SDK
from muggle_ocr import ModelType
import time
import csv
from json import loads
from threading import Thread
import re


def encodeInp(input_a):
    keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    output = ''
    i = 0
    while(i < len(input_a)):
        chr1 = str(ord(input_a[i]))
        i += 1
        chr2 = str(ord(input_a[i]))
        i += 1
        chr3 = str(ord(input_a[i]))
        i += 1
        enc1 = int(chr1) >> 2
        enc2 = ((int(chr1) & 3) << 4) | (int(chr2) >> 4)
        enc3 = ((int(chr2) & 15) << 2) | (int(chr3) >> 6)
        enc4 = int(chr3) & 63
        if not chr2.isdigit():
            enc3 = enc4 = 64
        elif not chr3.isdigit():
            enc4 = 64
        output = output + keyStr[enc1] + \
            keyStr[enc2] + keyStr[enc3] + keyStr[enc4]
        chr1 = chr2 = chr3 = ""
        enc1 = enc2 = enc3 = enc4 = ""
    return output


def GetVerify(verify_url, index_url, headers=None):
    session.get(index_url, headers=headers)
    sdk = SDK(model_type=ModelType.Captcha)
    req = session.get(verify_url)
    verify_code = sdk.predict(image_bytes=req.content)
    print(verify_code)
    return verify_code


def GetCourse(cookie_url, headers, href):
    req = session.get(cookie_url, headers=headers, params={
                      'jx0502zbid': href.split('jx0502zbid=')[1]})
    print(session.cookies)


def GetCookie(login_url, headers=None, data=None):
    login_req = session.post(login_url, headers=headers, params={
                             'method': 'logon'}, data=data)
    print(session.cookies)


def GetSelectList():
    lists = []
    url = 'https://xjwis.ynufe.edu.cn/jsxsd/xsxk/xklc_list'
    req = session.get(url)
    req.encoding = 'UTF-8'
    names = re.findall(r'<td>(.+?)</td>', req.text)
    hrefs = re.findall(r'<a href="(.+?)"', req.text)
    start = 0
    for i in range(3, len(names) + 3, 3):
        lists.append((str(start), names[:i - 1], hrefs[start]))
        start += 1
    for list in lists:
        print(list)
    select = input("请输入选课代号(第一位数字)：")
    print("已选择：", lists[int(select)][1])
    return lists[int(select)][2]


def PublicWriteToFile(name, courses):
    with open(f"{name}.csv", 'w', encoding='utf-8-sig', newline='') as datacsv:
        csvwriter = csv.writer(datacsv)
        csvwriter.writerow(
            ('课程编号', '课程名', '教师姓名', '上课地点', 'jx0404id', '时间冲突', '类别'))
        for course in courses:
            csvwriter.writerow(
                (course[:-1]))

def DoSelect(course_check_url, course):
    select = session.get(course_check_url, params={
                    'kcid': course[-1],
                    'cfbs': 'null',
                    'jx0404id': course[4],
                    '_': int(round(time.time() * 1000))
                })
    print("选课结果如下：")
    print(select.text)
    

def SelectCourse(course_list_url, course_check_url, data, inquiry_params):
    req = session.post(course_list_url, data=data, params=inquiry_params)
    courses = []
    try:
        courses_dict = loads(req.text)
        print("获取课程成功!")
    except:
        print("登录失败！，执行二次登录")
        GetCookie(login_url, headers=headers, data=login_data)
    courses_dict = loads(req.text)
    for i in courses_dict['aaData']:
        courses.append((i['kch'], i['kcmc'], i['skls'], i['kkapList'][0]
                       ['jsmc'], i['jx0404id'], i['ctsm'], i['kcxzmc'], i['jx02id']))
    write = Thread(
        target=PublicWriteToFile, args=('公选列表', courses))
    write.start()
    print("正在写入文件")
    print("生成成功！")
    jx0404id = ''
    while jx0404id != '0':
        time.sleep(1)
        jx0404id = input("请输入jx0404id：(输入0退出选课)：")
        for course in courses:
            if jx0404id == course[4]:
                for i in range(3):
                    th = Thread(target=DoSelect , args = (course_check_url, course))
                    th.start()
                break


def main():
    global login_url , headers , login_data
    stu_num = input("请输入学号：")
    stu_pwd = input("请输入登录密码：")
    login_url = 'https://xjwis.ynufe.edu.cn/jsxsd/xk/LoginToXk'
    verify_url = 'https://xjwis.ynufe.edu.cn/jsxsd/verifycode.servlet'
    index_url = 'https://xjwis.ynufe.edu.cn/'
    cookie_url = 'https://xjwis.ynufe.edu.cn/jsxsd/xsxk/xsxk_index'
    public_course_url = 'https://xjwis.ynufe.edu.cn/jsxsd/xsxkkc/xsxkGgxxkxk'
    public_check_url = 'https://xjwis.ynufe.edu.cn/jsxsd/xsxkkc/ggxxkxkOper'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
    }
    verify_code = GetVerify(verify_url, index_url, headers=headers)
    login_data = {
        'userAccount': f'{stu_num}',
        'userPassword': '',
        'RANDOMCODE': f'{verify_code}',
        'encoded': f"{encodeInp(stu_num) + '%%%' + encodeInp(stu_pwd)}"
    }
    must_data = {
        'sEcho': '1',
        'iColumns': '11',
        'iDisplayStart': '0',
        'iDisplayLength': '120'
    }
    public_param = {
        'sfym': 'false',
        'sfct': 'false',
        'sfxx': 'false',

    }
    GetCookie(login_url, headers=headers, data=login_data)
    print("登录")
    href = GetSelectList()
    GetCourse(cookie_url, headers=headers, href=href)
    SelectCourse(public_course_url, public_check_url,
                 data=must_data, inquiry_params=public_param)


if __name__ == "__main__":
    session = session()
    main()
