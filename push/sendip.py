import re
import subprocess
import time
import smtplib
import email.mime.multipart
import email.mime.text

ADSL_IFNAME = 'ppp0' #拨号网卡
ADSL_BASH = 'adsl-stop;adsl-start'
ADSL_CYCLE = 30*60 #半个小时拨号一次


class Sender():


    def get_ip(self, ifname=ADSL_IFNAME):
        (status, output) = subprocess.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?addr:.*?(\d+\.\d+\.\d+\.\d+).*?P-t-P', re.S)
            result = re.search(pattern, output)
            if result:
                ip = result.group(1)
                return ip


    def adsl(self):
        while True:
            print('ADSL Start, Please wait')
            (status, output) = subprocess.getstatusoutput(ADSL_BASH)
            if status == 0:
                print('ADSL Successfully')
                ip = self.get_ip()
                if ip:
                    print('New IP', ip)
                    try:
                        self.send_email(ip)
                        print('Successfully Sent email')
                    except:
                        print('Sent email Failed')
                    time.sleep(ADSL_CYCLE)
                else:
                    print('Get IP Failed')

            else:
                print('ADSL Failed, Please Check')
            time.sleep(1)

    def send_email(self, ip):
        msg = email.mime.multipart.MIMEMultipart()
        msgFrom = 'crawlzhihu@163.com'  # 从该邮箱发送
        msgTo = 'getproxy@163.com'  # 发送到该邮箱
        smtpSever = 'smtp.163.com'  # 163邮箱的smtp Sever地址
        smtpPort = '25'  # 开放的端口
        sqm = 'crawlzhihu666'  # 在登录smtp时需要login中的密码应当使用授权码而非账户密码

        msg['from'] = msgFrom
        msg['to'] = msgTo
        msg['subject'] = 'Python自动邮件-'
        name = 'vps1'
        content = name + ' ' + ip + ':8686'
        txt = email.mime.text.MIMEText(content)
        msg.attach(txt)
        smtp = smtplib.SMTP()
        smtp.connect(smtpSever, smtpPort)
        smtp.login(msgFrom, sqm)
        smtp.sendmail(msgFrom, msgTo, str(msg))
        smtp.quit()



def run():
    sender = Sender()
    sender.adsl()

run()