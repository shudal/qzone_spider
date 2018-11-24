#coding:utf-8
#!/usr/bin/python3
from selenium import webdriver
import time
import re
#import importlib2
import sys
import pymysql
import os
import configparser
#importlib2.reload(sys)

cur_path=os.path.dirname(os.path.realpath(__file__))
config_path=os.path.join(cur_path,'config.ini')
conf=configparser.ConfigParser()
conf.read(config_path)


db = pymysql.connect("localhost","root","123456","biaobai")
cursor = db.cursor()

yiChongfu=0
def startSpider():
    driver = webdriver.Chrome() #这个是chormedriver的地址
    driver.get('https://qzone.qq.com/')

    driver.switch_to.frame('login_frame')
    driver.find_element_by_id('switcher_plogin').click()
 
    myqqNum=conf.get('account','qq')
    myqqPas=conf.get('account','password')
    driver.find_element_by_id('u').clear()
    driver.find_element_by_id('u').send_keys(myqqNum)  #这里填写你的QQ号
    driver.find_element_by_id('p').clear()
    driver.find_element_by_id('p').send_keys(myqqPas)  #这里填写你的QQ密码

    driver.find_element_by_id('login_button').click()
    time.sleep(2)

    
	
    #---------------获得g_qzonetoken 和 gtk
    html = driver.page_source

    g_qzonetoken=re.search('window\.g_qzonetoken = \(function\(\)\{ try\{return (.*?);\} catch\(e\)',html)#从网页源码中提取g_qzonetoken
    #g_qzonetoken = "e794139a284d6ea9e0b26826e541b55df37d0667a3544f534de25aebdb64628d3ab75e1d7104bbb22a"

    cookie = {}#初始化cookie字典
    for elem in driver.get_cookies():#取cookies
        cookie[elem['name']] = elem['value']

    gtk=getGTK(cookie)#通过getGTK函数计算gtk
    #print(g_qzonetoken)
    #print(gtk)

    #--------------获得好友列表   注意下面的链接
    driver.get('https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_hat_get.cgi?hat_seed=1&uin='+myqqNum+'fupdate=1&g_tk='+str(gtk)+'&qzonetoken='+str(g_qzonetoken)+'&g_tk='+str(gtk))
    friend_list = driver.page_source
    friend_list = str( friend_list )
    abtract_pattern  =  re.compile('\"(.\d*)\":\{\\n"realname":"(.*?)"}',re.S)
    QQ_name_list = re.findall(abtract_pattern,str(friend_list)) #数组
    print(QQ_name_list)
    numList=dict()# numList => (QQnum:QQname)  #列表
    for i in QQ_name_list:
        numList[str(i[0])]=str(i[1])
    begin = 0
    last_source = ""
    tag = 1
    first = 0
    firstTime=""

    #如果要爬取自己的说说，手动添加自己的qq号
    #numList['你的qq号']='你的名字'
    #print(numList)

    
    beizhu1="章鱼哥"
    beizhu2="心协的墙"
    beizhu=beizhu2
    qqnum1= "2682373393" #心协的墙
    qqnum2= "1849045415"
    qqnum3= "2508416399"
    qqs=[{"qq":"2682373393","beizhu":"心协的墙","filen":"xinXieDeQiang"},{"qq":"1952356436","beizhu":"墙二","filen":"qiangtwo"}] #qq号，备注，要保存为的文件的名字（不含扩展名
    realqqi=1
    rqqnum = qqs[realqqi]["qq"]
    #设置爬取内容保存路径
    sql = "select * from content where qq='"+rqqnum+"' order by id desc limit 0,1"
    cursor.execute(sql)
    zuiJinTime=cursor.fetchall()
    if zuiJinTime != ():
        if zuiJinTime[0] != []:
	        zuiJinTime=zuiJinTime[0][1]
    else:
        zuiJinTime=""

    f = open('c:/Users/Junhao/Documents/paqu/'+qqs[realqqi]["filen"]+'.html','w',encoding="utf-8")
    #f = open('c:/Users/Junhao/Documents/paqu/'+qqs[realqqi]["filen"]+'.html','w' )
    shuoshu=0
    tai=1
    for key in numList.keys(): 
        QQnum = key
        QQname = numList[QQnum]

       
        if QQnum == rqqnum:  #根据qq号查找指定好友说说
            count = 1
            begin = 0
            while tag==1 :
                if tai==0:
                    break;
                #-------------进入好友说说页面                                                                       #'+QQnum+'              '+str(begin)+'
                #print("Begin:"+str(begin))
                driver.get('https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?uin='+QQnum+'&ftype=0&sort=0&pos='+str(begin)+'&num=40&replynum=200&g_tk='+str(gtk)+'&callback=_preloadCallback&code_version=1&format=jsonp&need_private_comment=1&qzonetoken='+str(g_qzonetoken)+'&g_tk='+str(gtk))

                try:
                    msg_list_json = driver.page_source
                except:
                    begin = begin + 40
                    continue
                

                msg_list_json = str(msg_list_json)
                if last_source==msg_list_json :
                    break
                else:
                    last_source=msg_list_json

                #检测是否没有权限访问
                abtract_pattern  =  re.compile(',"message":"(.*?)","name":',re.S)
                message = re.findall(abtract_pattern,str(msg_list_json))
                if message!=[]:
                    if str(message[0])=='对不起,主人设置了保密,您没有权限查看':#对不起,主人设置了保密,您没有权限查看
                        break  
                #解析JSON
                #webDriver没有现成的JSON解析器，所以采用获取源码的方式，然后使用正则表达式获取具体细节
                msg_list_json =  msg_list_json.split("msglist")[1]#拆分json，缩小范围，也能加快解析速度
                msg_list_json =  msg_list_json.split("smoothpolicy")[0]
                msg_list_json =  msg_list_json.split("commentlist")[1:]

                #说说动态分4种：1、文字说说（或带有配图的文字说说）
                #              2、只有图片的说说
                #              3、转发，并配有文字
                #      				4、转发，不配文字
                
                for text in msg_list_json:
                    # 1、先检查说说，用户是否发送了文字，如果没有文字，正则表达式匹配无效
                    abtract_pattern  =  re.compile('\}\],"content":"(.*?)","createTime":"(.*?)","created_time":(.*?),"',re.S)
                    msg_time = re.findall(abtract_pattern,str(text))
                    
                    pic_pattern = re.compile('"name":"'+qqs[realqqi]["beizhu"]+'","pic":\[\{(.*?\}\])',re.S)
                    pic_con =  re.findall(pic_pattern,str(text))
                    
                    realTime=""
                    isZhuan = 0
                    #print(msg_time)
                    if msg_time!=[]:
                        # 2、如果作者说说有文字，那么检查是否有转发内容
                        msg = str(msg_time[0][0])
                        sendTime = str(msg_time[0][1])
                        realTime = str(msg_time[0][2])
                        '''
                        abtract_pattern  = re.compile('\}\],"content":"(.*?)"},"rt_createTime":"(.*?)","',re.S)
						
                        text = text.split("created_time")[1]
                        msg_time2 = re.findall(abtract_pattern,str(text))

                        #合并发送内容 格式：评论+转发内容
                        if msg_time2!=[]:
                            msg = msg +"  转发内容:"+str(msg_time2[0][0])
					    '''

                    else:
                        # 3、说说内容为空，检查是否为 =>只有图片的说说 or 转发，不配文字
                        #获取正文发送时间 （发送时间分为：正文发送时间 or 转发时间）
                        abtract_pattern  =  re.compile('"conlist":null,"content":"","createTime":"(.*?)",',re.S)
                        msgNull_time = re.findall(abtract_pattern,str(text))

                        if msgNull_time!=[]:
                            #如果有正文发送时间，那么就是这条说说仅含有图片  =>只有图片的说说
                            msg = ""
                            print("仅图片")
                            #print(str(text))
                            abtract_pattern  =  re.compile('"created_time":(.*?),"',re.S)
                            realTime = re.findall(abtract_pattern,str(text))
                            print(realTime)
                            print(text)
                            if len(realTime)==1:
                                realTime=realTime[0]
                            else :
                                realTime=realTime[0][0] 
                            sendTime = str(msgNull_time[0])
                            
                        else:
                            #如果没有正文发送时间，那么就是说这条说为 =>转发，不配文字
                            isZhuan=1
                            abtract_pattern  =  re.compile('\}\],"content":"(.*?)"},"rt_createTime":"(.*?)","',re.S)
                            msg_time = re.findall(abtract_pattern,str(text))
                            msg ="  转发内容:"+str(msg_time[0][0])
                            sendTime = str(msg_time[0][1])

                    #写入本地文件
                    picss=""
                    if pic_con !=[] :
                        pic_con =  re.findall(r'"url1":"(.*?)"',str(pic_con))
                        picss = ""
                        for i in range(len(pic_con)):    #对每个url遍历
                            realU = ""                   #对每个url处理
                            jias=pic_con[i].split('\\\\')
                            for k in range(len(jias)):
                                realU = realU + jias[k]
                            picss = picss + realU+","
                        #msg = msg+picss
                    #msg = msg+"------<br>"+str(text)+"<br>------" 
                    #print(type(zuiJinTime))
             
                    if isZhuan!=1 :       
                        sql = "select * from content where time='"+realTime+"'"
                        cursor.execute(sql)
                        allAs=cursor.fetchall()
                        print(len(allAs))
                        if len(allAs)!=0:
                            tai=0
                            print("realTime="+realTime)
                            print("text="+str(text))
                            break;
                        
                        sql = "INSERT INTO content(time,qq,img,text)values('"+realTime+"','"+rqqnum+"','"+picss+"','"+msg+"')"
                        cursor.execute(sql)
                        db.commit()
                    #
                    f.write('{},{},{},{}<br>'.format(str(QQname),str(QQnum),sendTime,msg))


                    #print(str(count)+" : "+str(QQname)+" : "+str(QQnum)+" : "+sendTime+" : "+msg)
                    count = count + 1
                    shuoshu = shuoshu + 1
               
                    print("\n\n shuoshu="+str(shuoshu))

                begin =  begin + 40

def getGTK(cookie):
    hashes = 5381
    for letter in cookie['p_skey']:
        hashes += (hashes << 5) + ord(letter)
    return hashes & 0x7fffffff
startSpider()
db.close()
print("爬取结束")
