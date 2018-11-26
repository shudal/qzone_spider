# QQ空间爬虫

### 功能简介

*  爬取指定qq的说说（含图片）
*  将爬取所得上传到本地的mysql服务器
* 可运行于windows或自己的vps上。默认运行在window下，运行在linux下需要注释第28行并取消注释31-34行的代码，并[配置linux下的chrome和chromedriver](https://www.jianshu.com/p/b5f3025b5cdd)

### 运行环境

* 库依赖 ：selenium,pymysql,configparser
* chrome游览器，并配置chromedriver （随便改改用其它游览区也可以啦），关于chromedrvier的身处何处的说明见源码28行左右。windows下将chromedriver与chrome.exe放置于同一目录，即chromedriver在chrome的安装目录。linux下需要填写config.ini中的env栏下chromedriver的地址，windows下不需要。
* mysql服务器

### 使用说明

* config.ini中，account栏填写qq号和密码，database栏填写数据库名，用户名，密码/
* 第十四行名 为qqs的列表中，填写需要爬取的qq的信息--qq号，备注。注意，必须要给要爬取信息的人备注，不然检测不到此人。格式参见源码中的

### 其他

* 推荐阅读，[meta标签的refferrer与防盗链](https://blog.lyz810.com/article/2016/08/referrer-policy-and-anti-leech/)
* 有些qq直接使用账号密码登录不可以，还需要验证码啥啥的，就不能使用这个程序。