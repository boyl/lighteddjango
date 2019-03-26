# lighteddjango
  - 轻量级django实践|bookname:轻量级django
  - 所涉及到的django、python、drf、backbone相关工具，都是时下（2019-03-13）最新版本，具体版本可以到项目中查看

# dom.html：
是target和currentTarget一个区别验证的实践页面

# notice
- DB I use mysql. not postgresql in book.
- In JS  (sting) "4" === (int) 4 is false, the type of each other should be in consistent
- Downgrade Tornado==4.2, due to tornadoredis imcompatible with tornado==6.0.2
- redis on windows, there is a link for download:https://github.com/MicrosoftArchive/redis/releases

# how does it run:
- 获得项目后，在虚拟环境中执行`pip install -r requirements.txt`.
- 编辑settings文件，设置好本地数据库信息
- 在虚拟环境中迁移数据库（`python manage.py makemigrations, python manage.py migrate`）
- 启动本地服务`python manage.py runserver 127.0.0.1`，打开页面进行访问。
- url: localhost:8000/api 数据drf-api及相关操作
# others:
- If you finish section 8:tornado communicate with django, then you should setup redis and run it to get the whole features.
- There's a original examples from this book at this link: https://github.com/lightweightdjango/examples

#  exhibition:
* login view:![loginpage](https://github.com/boyl/lighteddjango/blob/master/exhibition/images/homepage.png)
* home view: ![homepage](https://github.com/boyl/lighteddjango/blob/master/exhibition/images/loginpage.png)
* sprint-create view: ![sprintaddpage](https://github.com/boyl/lighteddjango/blob/master/exhibition/images/sprintcreatepage.png)
* sprint-detail view: ![sprintdetailpage](https://github.com/boyl/lighteddjango/blob/master/exhibition/images/sprintdetailpage.png)
* task-create-update view: ![taskcreateupdatepage](https://github.com/boyl/lighteddjango/blob/master/exhibition/images/taskaddupdatepage.png)

- GIF: ![display](https://github.com/boyl/lighteddjango/blob/master/exhibition/gif/display.gif)
# TODO:
- Using python3.7 features.
- Using JS ES6 syntax.
-
