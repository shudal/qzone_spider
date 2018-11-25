#coding:utf-8
#!/usr/bin/python3
from selenium import webdriver
import time
import re 
import pymysql
import os
import configparser 

cur_path=os.path.dirname(os.path.realpath(__file__))
config_path=os.path.join(cur_path,'config.ini')
conf=configparser.ConfigParser()
conf.read(config_path)
qqs=[{"qq":"2682373393","beizhu":"心协的墙"},{"qq":"1952356436","beizhu":"墙二"},{"qq":"2790117931","beizhu":"墙三"}] 
#从配置文件中获取数据信息
d_name = conf.get('database','name')
d_password = conf.get('database','password')
d_database_name = conf.get('database','database_name')

#连接数据库
db = pymysql.connect("localhost",d_name,d_password,d_database_name)
cursor = db.cursor()

yiChongfu=0
def startSpider(theqq):
    driver = webdriver.Chrome()  #chromedriver和chrome.exe在同一文件夹下,即chromedriver在chrome的安装目录
	#windows上只需要上面这一行就够了，linux上使用下面的：
    '''
    option = webdriver.ChromeOptions()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(executable_path='/root/dowload/chromedriver',chrome_options=option) #这个是chormedriver的地址
	'''
    driver.get('https://qzone.qq.com/')

    driver.switch_to.frame('login_frame')
    driver.find_element_by_id('switcher_plogin').click()
 
    myqqNum=conf.get('account','qq')
    myqqPas=conf.get('account','password')
    driver.find_element_by_id('u').clear()
    driver.find_element_by_id('u').send_keys(myqqNum)  
    driver.find_element_by_id('p').clear()
    driver.find_element_by_id('p').send_keys(myqqPas)   

    driver.find_element_by_id('login_button').click()
    time.sleep(2)

    
	
    #---------------获得g_qzonetoken 和 gtk
    html = driver.page_source

    g_qzonetoken=re.search('window\.g_qzonetoken = \(function\(\)\{ try\{return (.*?);\} catch\(e\)',html)#从网页源码中提取g_qzonetoken

    cookie = {}#初始化cookie字典
    for elem in driver.get_cookies():#取cookies
        cookie[elem['name']] = elem['value']

    gtk=getGTK(cookie)#通过getGTK函数计算gtk

    #--------------获得好友列表   注意下面的链接
    driver.get('https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_hat_get.cgi?hat_seed=1&uin='+myqqNum+'fupdate=1&g_tk='+str(gtk)+'&qzonetoken='+str(g_qzonetoken)+'&g_tk='+str(gtk))
    friend_list = driver.page_source
    friend_list = str( friend_list )
    abtract_pattern  =  re.compile('\"(.\d*)\":\{\\n"realname":"(.*?)"}',re.S)
    QQ_name_list = re.findall(abtract_pattern,str(friend_list)) 
    print(QQ_name_list)
    numList=dict()# numList => (QQnum:QQname)  #列表
    for i in QQ_name_list:
        numList[str(i[0])]=str(i[1])
    begin = 0
    last_source = ""
    tag = 1
    first = 0
    firstTime=""
    
    realqqi= theqq
    rqqnum = qqs[realqqi]["qq"] 
    
    shuoshu=0 #计数器
    tai=1  #方便跳出循环
    for key in numList.keys(): 
        QQnum = key
        QQname = numList[QQnum]

       
        if QQnum == rqqnum:  #根据qq号查找指定好友说说 
            begin = 0
            while tag==1 :
                if tai==0:
                    break;
                #-------------进入好友说说页面                                                                       #'+QQnum+'              '+str(begin)+'
                
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
                    
					#查询图片（如果有的话
                    pic_pattern = re.compile('"name":"'+qqs[realqqi]["beizhu"]+'","pic":\[\{(.*?\}\])',re.S)
                    pic_con =  re.findall(pic_pattern,str(text))
                    
                    realTime="" #先新作为空字符串，后面再赋值,是时间戳
                    isZhuan = 0 #是否是转发的状态
                    #print(msg_time)
                    if msg_time!=[]:
                        # 2、如果作者说说有文字，那么检查是否有转发内容
                        msg = str(msg_time[0][0]) 
                        realTime = str(msg_time[0][2]) 

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
                            
                        else:
                            #如果没有正文发送时间，那么就是说这条说为 =>转发，不配文字
                            isZhuan=1
							#管ta转发的什么，，，这条说说不要了

                    #写入数据库
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
                    if isZhuan!=1 :       #如果非转发消息
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
                    shuoshu = shuoshu + 1
               
                    print("\n\n shuoshu="+str(shuoshu))

                begin =  begin + 40

def getGTK(cookie):
    hashes = 5381
    for letter in cookie['p_skey']:
        hashes += (hashes << 5) + ord(letter)
    return hashes & 0x7fffffff
for i in range(len(qqs)):
  startSpider(i)
  print("爬取第"+str(i+1)+"结束")
db.close()
print("爬取全部结束")