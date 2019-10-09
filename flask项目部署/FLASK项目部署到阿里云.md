# FLASK项目部署到阿里云

基于ubuntu14.04,使用Gunicorn + Nginx 进行部署，云服务器为阿里云

### 阿里云服务器

1. 选择云服务器:阿里云服务器 <https://www.aliyun.com>
2. 个人免费获取 [<https://free.aliyun.com/>]
3. 创建服务器选择ubuntu14.04 的操作系统

#### 1.创建服务器（实名验证免费试用，土豪随意）

![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009095604.png)

- ##### 进入控制台查看实例（公网ip即为你的服务器的ip）

![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009095835.png)

- ##### 配置安全组（添加80，5000，5001）端口

  ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009100045.png)

  

  点击右方的配置规则

![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009100224.png)

​       点击添加安全组规则

![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009100310.png)

​		设置好端口范围和授权对象（三个），比如80端口，端口范围写80/80，授权对象写0.0.0.0/0，表示所有IP地址都能访问。



![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009100616.png)

- ##### 设置密码（远程连接密码和ubuntu的登录密码）

  - 远程连接密码，点击远程连接会出现一个6位数的密码，默认出现一次，请记牢

    ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009101334.png)

    

  - ubuntu密码，点击管理，点击更多，点击重置密码，这就是你的远程ubuntu登录密码，账号默认root

    ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009101548.png)

    ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009101707.png)

- ##### 到此，云服务器的基本设置完成了。点击 实例页面的远程连接，输入6位密码，就可以远程登录。然后会让你输入Ubuntu的账户名和密码。输入成功后就可以远程登录ubuntu的终端，可以像在本地一样通过各种命令操作。

  ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009102037.png)

### 2.项目资料上传和环境搭建

- ##### 把本地flask项目工程文件夹上传到你阿里云的服务器上

  这里要用到一个工具：Xftp，可以用来在本地和远程Linux之间拷贝文件。

  进入官网，<https://www.netsarang.com/products/xfp_overview.html> 。点击Free License，填写下姓名、邮箱就可以免费下载安装。

  ![](C:\Users\Shinelon\Desktop\flask项目部署\20181121162010326.png)

  安装成功后打开，点击文件-新建，输入名称（随便），主机（及你的阿里云的服务器的公网IP），输入ubuntu的账号和密码

  ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009102845.png)

  

  左边就是你的PC桌面，右边是阿里云ubuntu的root目录。可以直接按住把文件从左边拖到右边的文件夹中。因为本地是在虚拟机中运行的ubuntu，项目文件叫做myweb，先把文件从ubuntu中拷贝到windows桌面，再从windows桌面拖到阿里云ubuntu的home文件夹下。这里还有一点设置是如何显示ubuntu中的隐藏文件，在工具栏--选项--显示隐藏文件。
  ![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009103026.png)

- ##### 虚拟环境的安装

  在阿里云的服务器上安装虚拟环境。安装如下步骤如下：

  1. 安装virtualenv

     ```
     sudo pip install virtualenv
     sudo pip install virtualenvwrapper
     ```

  2. 在home下创建虚拟环境安装目录

     ```
     mkdir .virtualenvs
     ```

  3. 为virtualenv配置环境变量,打开.bashrc文件，在末尾加上三行代码，

     ```
     sudo vim ~/.bashrc
     ```

     在末尾添加三行

     ```
     export WORKON_HOME=$HOME/.virtualenvs
     export PROJECT_HOME=$HOME/workspace
     source /usr/local/bin/virtualenvwrapper.sh
     ```

     使配置文件生效

     ```
     source ~/.bashrc
     ```

  4. 创建虚拟环境，默认命令创建的是python2的虚拟环境，指定创建python3.6的虚拟环境可以使用以下命令（需要你的服务器上下载你项目的python版本，可以参考<https://blog.csdn.net/weixin_39278265/article/details/87659130>）

     ```
     mkvirtualenv -p /usr/bin/python3.6  XX  #XX是虚拟环境的名字，创建python3.5的虚拟环境
      
     其他命令：
     workon xx    #进入虚拟环境XX
     deactivate   #退出虚拟环境
     ```

- ##### 在虚拟环境中安装flask项目相应的python包

  1. 我们在本地写flask项目肯定是安装了一堆相应的包，需要把他们移植到阿里云上。首先在本地ubuntu进入虚拟环境，在项目根目录下，执行以下命令收集安装的包，就是生成一个包的清单文件requirements.txt。

     ```
     pip freeze > requirements.txt
     ```

     

  2.  然后用xftp把这个requirements.txt文件上传到阿里云项目的根目录home，然后进入虚拟环境myflask（myflask是我新建的虚拟环境的名字）。

     ```
     workon myflask		# 进入虚拟环境
     cd 进入flask项目工程文件夹
     pip install -r requirements.txt 	# flask项目所需的包都在此文件中
     
     ```

  3. 在安装 Flask-MySQLdb 的时候可能会报错，可能是依赖包没有安装，执行以下命令安装依赖包：

     ```
     sudo apt-get build-dep python-mysqldb
     ```

- **Mysql数据库的安装和数据的迁移** 

  安装Mysql：输入以下命令，安装过程会设置密码，设置成和原来本地一样的，就不用在setting中修改了。

  ```
  sudo apt-get update
  apt-get install mysql-server
  apt-get install libmysqlclient-dev
  ```

  创建数据库：先登录数据库， 然后创建数据库information，数据库名字也创建成和原来本地一样的，我的叫information。

  ```
  create database 名称 [character 字符集 collate 校队规则;
  ```

  数据的迁移：把本地数据库中的数据复制到阿里云上的数据库中。先在本地生成备份文件，information是要备份的数据库，information.sql是生成的备份文件。然后用Xftp把information.sql文件上传到阿里云。

  ```
  mysqldump -u root -p information > information.sql
  ```

  数据还原：阿里云终端 cd到information.sql所在目录，输入以下命令

  ```
  mysql -u root -p information < information.sql
  ```

  mysql配置：找到mysqld.cnf文件注释掉bind-address这一行

  ```
  /etc/mysql/mysql.conf.d/mysqld.cnf   #配置文件路径
   
  #bind-address		= 127.0.0.1   #注释掉这一行
  ```



- ##### Redis的安装

  ```
  sudo apt-get install redis-server
  ```

  

  至此，我们已经完成了项目文件迁移、环境建立、数据库迁移 。可以在阿里云的终端中运行Django项目，先进入虚拟环境，然后cd到项目目录下，python manage.py runserver 看能不能启动项目，如果可以说明项目本身已经没有问题了。如果不能说明项目本身还有问题。有些包安装好后需要设置配置文件，看是不是没设置。到目前为止的操作其实基本都和本地是一样



### 3.Nginx

- ##### 安装Nginx

  ```
  sudo apt-get update
  sudo apt-get install nginx
  ```

- ##### 安装成功后，用浏览器访问你的阿里云IP地址，可以看到以下提示 ：

  ![](C:\Users\Shinelon\Desktop\flask项目部署\20181122151828409.png)

- ##### nginx常用命令：

  ```
  service nginx start   #启动
  service nginx stop    #停止
  service nginx reload  #重启
  ```

  

- ##### nginx配置：打开配置文件default，路径/etc/nginx/sites-available/default

  ```
  # 如果是多台服务器的话，则在此配置，并修改 location 节点下面的 proxy_pass 
  upstream flask {
          server 127.0.0.1:5000;
          server 127.0.0.1:5001;
  }
  server {
          # 监听80端口
          listen 80 default_server;
          listen [::]:80 default_server;
  		
  		# /home/newworld 为你flask项目的路径
          root /home/newworld
  
          index index.html index.htm index.nginx-debian.html;
  
          server_name _;
  
          location / {
                  # 请求转发到gunicorn服务器
                  proxy_pass http://127.0.0.1:5000;
                  # 请求转发到多个gunicorn服务器
                  # proxy_pass http://flask;
                  # 设置请求头，并将头信息传递给服务器端 
                  proxy_set_header Host $host;
                  # 设置请求头，传递原始请求ip给 gunicorn 服务器
                  proxy_set_header X-Real-IP $remote_addr;
          }
  }
  ```

- ##### 重启nginx

  ```
  service nginx reload
  ```

  

### 4.Gunicorn

Gunicorn（绿色独角兽）是一个Python WSGI的HTTP服务器

从Ruby的独角兽（Unicorn ）项目移植

该Gunicorn服务器与各种Web框架兼容，实现非常简单，轻量级的资源消耗

Gunicorn直接用命令启动，不需要编写配置文件

- ##### 安装(在虚拟环境)

  ```
  pip install gunicorn
  ```

- ##### 查看选项

  ```
  gunicorn -h
  ```

- ##### 运行（虚拟环境），

  ```
  # -w: 表示进程（worker） -b：表示绑定ip地址和端口号（bind），manage：运行的文件名称，app：flask程序实例名
  gunicorn -w 2 -b 127.0.0.1:5000 manage:app
  ```

- ##### 参考阅读： Gunicorn相关配置：<https://blog.csdn.net/y472360651/article/details/78538188>

### 5.在浏览器中输入阿里云服务器公网IP

​	

![](C:\Users\Shinelon\Desktop\flask项目部署\QQ图片20191009100616.png)