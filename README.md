# 自动化推送运行脚本
脚本简介：
该脚本可以用于将于本地环境开发的项目推送到远端主机进行运行，方便项目的运行测试

### 1. 必要配置
* remote_python_interpreter 指定python解释器（如需要虚拟环境等需要根据远端服务器进行指定）
* remote_username 登录用户名
* remote_password 密码
* remote_current_working_directory 目标文件夹
* remote_ip 远端服务器ip地址

* enter_file 入口执行文件

### 2.自定义配置
* py_folders 需要推送的文件夹， 默认是当前脚本所在文件夹
* py_files 也可以单独指定文件
