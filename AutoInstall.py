# -*- coding: utf-8 -*-
# Author : https://github.com/tenyue/CloudMonitor
# 自动部署脚本
import os
import json
import datetime
import hashlib


def scp_put(local_path, remote_path, host, root, passwd):
    scp_put = '''
    set timeout -1
    spawn scp %s %s@%s:%s
    expect "(yes/no)?" {
    send "yes\r"
    expect "password:"
    send "%s\r"
    } "password:" {send "%s\r"}
    expect eof
    exit'''

    os.system("echo '%s' > scp_put.cmd" % (
        scp_put % (os.path.expanduser(local_path), root, host, remote_path, passwd, passwd)))
    os.system('expect scp_put.cmd')
    os.system('rm scp_put.cmd')

    shell_exe = '''
    set timeout -1
    spawn ssh %s@%s
    expect "(yes/no)?" {
    send "yes\r"
    expect "password:"
    send "%s\r"
    } "password:" {send "%s\r"}
    expect "#"
    send "mv /root/client-temp.py /root/client.py\r"
    expect "#"
    send "yum -y install epel-release\r"
    expect "#"
    send "yum -y install python-pip\r"
    expect "#"
    send "yum clean all\r"
    expect "#"
    send "yum -y install gcc\r"
    expect "#"
    send "yum -y install python-devel\r"
    expect "#"
    send "pip install psutil\r"
    expect "#"
    send "apt-get -y install python-setuptools python-dev build-essential\r"
    expect "#"
    send "apt-get -y install python-pip\r"
    expect "#"
    send "pip install psutil\r"
    expect "#"
    send "nohup python /root/client.py &> /dev/null &\r"
    expect "#"
    send "exit\r"
    expect eof
    exit'''

    os.system("echo '%s' > shell_exe.cmd" % (
        shell_exe % (root, host, passwd, passwd)))
    os.system('expect shell_exe.cmd')
    os.system('rm shell_exe.cmd')

if __name__ == '__main__':
    while True:
        print 'Please input the website path for CloudMonitor(Eg: /home/wwwroot/default):'
        webdir = raw_input('the website path is:')
        if os.path.exists(webdir) == True:
            mvcomment = 'mv web/* %s' % webdir
            os.system(mvcomment)
            break
        else:
            print 'the website path is\'t exist!'
    server_ipstr = raw_input('the server\'s ip address:')
    count = 0
    config_list = []
    while True:
        count += 1
        print 'Deploy the %s client for CloudMonitor: ' % count
        client_ipstr = raw_input('the client\'s ip address: ')
        rootstr = raw_input('the client\'s root: ')
        passwdstr = raw_input('the client\'s password: ')

        name = raw_input('the client\'s name: ')
        type = raw_input('the client\'s type: ')
        host = raw_input('the client\'s host: ')
        location = raw_input('the client\'s location: ')

        xstr = ('CloudMonitor%s' + client_ipstr + rootstr + passwdstr+ str(datetime.datetime.now()))% count
        hash_user = 'CloudMonitor%s' % count
        hash_passwd = hashlib.md5(xstr).hexdigest()

        xjson = {
            "username": hash_user,
            "name": name,
            "type": type,
            "host": host,
            "location": location,
            "password": hash_passwd,
        }
        config_list.append(xjson)
        is_add = raw_input('Whether to continue to add the client(y/n): ')

        new_config_str = ''
        # 读取客户端配置
        with open('client/client.py','r') as f:
            for line in f.readlines():
                if 'SERVER = "127.0.0.1"' in line:
                    new_config_str = new_config_str + ('SERVER = "%s"') % server_ipstr + '\n'
                elif 'USER = "USER"' in line:
                    new_config_str = new_config_str + ('USER = "%s"') % hash_user + '\n'
                elif 'PASSWORD = "PASSWORD"' in line:
                    new_config_str = new_config_str + ('PASSWORD = "%s"') % hash_passwd + '\n'
                else:
                    new_config_str = new_config_str + line
        # 写入临时客户端配置
        with open('client/client-temp.py','wt') as f:
            f.write(new_config_str)
        # 上传配置到客户机,并执行脚本
        scp_put('client-temp.py', '/root/', client_ipstr, rootstr, passwdstr)
        # 清理临时客户端配置
        os.remove('client/client-temp.py')
        if is_add == 'n' or is_add == 'N' or is_add == 'not' or is_add == 'NOT':
            break
    config_dict = {"servers": config_list}
    config_json = json.dumps(config_dict)
    with open('config.json','wt') as f:
        f.write(config_json)
    # 启动主服务
    os.system('server/make')
    if os.path.exists('server/sergate') == True:
        os.system('server/sergate --config=config.json --web-dir=%s') % webdir
        print 'Successed start CloudMonitor!'
    else:
        print 'Failed start CloudMonitor!'

