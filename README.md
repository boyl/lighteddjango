# lighteddjango
  - 轻量级django实践
  - 所涉及到的django、python、drf、backbone相关工具，都是时下（2019-03-13）最新版本，具体版本可以到项目中查看

# dom.html：
是target和currentTarget一个区别验证的实践页面

# notice
- In JS  (sting) "4" === (int) 4 is false, the type of each other should be in consistent

# how does it run:
- 获得项目后，在虚拟环境中执行`pip install -r requirements.txt`.
- 编辑settings文件，设置好本地数据库信息
- 在虚拟环境中迁移数据库（`python manage.py makemigrations, python manage.py migrate`）
- 启动本地服务`python manage.py runserver 127.0.0.1`，打开页面进行访问。
- url: localhost:8000/api 数据drf-api及相关操作
