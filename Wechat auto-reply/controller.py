# -*- coding: utf-8 -*-
# 部分代码参考自B站up主：知名的阿呆同学
# author = anorangewolf
import config
import pandas as pd
import numpy as np
import time
import random
import uiautomation as auto
wx = auto.WindowControl(Name='微信',searchDepth=1) # 绑定微信窗口
wx.SwitchToThisWindow() # 切换到微信窗口
wx.Maximize() # 最大化微信窗口
hw = wx.ListControl(Name='会话',searchDepth=9) # 绑定会话控件
df = pd.read_csv('config.csv',encoding='gb18030') # 读取数据
env = 0 # 设定一个状态变量

# 发送消息
def send(msg):
    wx.SendKeys(str(msg),waitTime=0)
    wx.SendKeys('{Enter}',waitTime=0)

# ai警告
def ai():
    send('[Replied by ai]')

# 写入文件
def writeonce(file_name,context):
    f = open(file_name,"+a")
    f.write(str(context))
    f.write('\n')
    f.close    
    
# 定义一个重置函数，用于在未匹配时重置监测状态
def reset():
    time.sleep(0.5)
    wx.ListItemControl(Name=config.reset_name).Click()
    wx.ListItemControl(Name=config.reset_name).Click() # 执行两次确保成功点击
    print('Reset!')
      
# 帮助菜单
def help():
    wx.SendKeys(config.menu.replace('\n','{Shift}{Enter}'),waitTime=0)
    wx.SendKeys('{Shift}{Enter}',waitTime=0)
    ai()

# 价格计算模块
def price(msg):
    sent = str(msg)[:-3]
    num1 = int(sent[:-2])
    type1 = sent[-2:]
    if type1 == '黑白':
        if num1 <= 5:
            num2 = 0.2*num1
            send(num2)
            ai()
        else:
            num2 = 0.1*(5+num1)
            send(num2)
            ai()
    elif type1 == '彩色':
        if num1 <= 3:
            num2 = 0.4*num1
            send(num2)
            ai()
        else:
            num2 = 0.2*(3+num1)
            send(num2)
            ai()
    else:
        send('未找到相关价格公式，请检查您的格式是否为“张数+打印方式+？？？”，如“7黑白？？？”。或者您打印的不是普通A4纸？如果确实如此请发送“转人工”。')
        ai()
    
# 打印任务数据库模块
def print_df(name,msg):
    if '面' not in msg:
        send('请问要打单面还是双面呢？打单面请回复“单面打印”，打双面请回复“双面打印”。默认黑白打印，如需彩打请在开头加上“彩色”，如“彩色单面打印”。')
        ai()
    else:
        send('已接收，将在24小时内回复')
        ai()
        writeonce(config.loc1,name)

# 转人工请求模块
def human_request_df(name):
    send('已接收，将在24小时内回复')
    ai()
    writeonce(config.loc2,name)
    
# 自动收款模块
def get(name,msg):
    if msg == '收到红包，请在手机上查看':
        writeonce(config.loc3,name)
        send('已接收，将在24小时内领取') 
        ai()
    elif msg == '微信转账': 
        file_rect = wx.ListControl(Name='消息').GetChildren()[-1].BoundingRectangle
        print(file_rect)
        file_x = 700
        file_y = (file_rect.top+file_rect.bottom)//2
        print(file_y)
        auto.Click(file_x,file_y,waitTime=1)
        auto.Click(1500,800,waitTime=2) 
        auto.Click(500,1200,waitTime=1)
        send(config.autoreply[random.randint(0,len(config.autoreply)-1)]) 
        ai()      

# 控制器，专门写个函数方便修改调整
def controller(name,msg):
    env = 0
    if name not in config.whitelist:
        if '帮助' in msg:
            env+=1
            help()
            reset()
        if '？？？' in msg:
            env+=1
            price(msg)
            reset()
        if '打印' in msg:
            env+=1
            print_df(name,msg)
            reset()
        if '转人工' in msg: 
            env+=1
            human_request_df(name)
            reset()
        if msg == '微信转账' or msg == '收到红包，请在手机上查看':
            env+=1
            get(name,msg)
            reset()
    else:
        env+=1 
    return env
 

# 主程序 
time.sleep(0.5) 
reset()
env = 0
dep = config.depth

while True:
    unread = hw.TextControl(searchDepth=dep) # 启动时检索所有未读消息
    while not unread.Exists(0): #维持程序
        pass
    
    if unread.Name:
        # 存在未读消息
        unread.Click(simulateMove=False) # 模拟点击，不启用随机偏移
        last_msg = wx.ListControl(Name='消息').GetChildren()[-1].Name # 获取消息类的子类的倒数第一个对象的名称，即最后一条消息的内容
        while True:
            # 遍历ListItem，找到被选中项
            env+=1
            guest = hw.ListItemControl(foundIndex=env) # 遍历list中的对象
            selec_patn = guest.GetPattern(auto.PatternId.SelectionItemPattern) # 抽取对象的SelectionItemPattern属性
            is_selec = selec_patn.IsSelected # 判断SelectionItemPattern属性中的IsSelected属性
            if is_selec== True:
                break    
        print(guest.Name,last_msg)
        
        env = controller(guest.Name,last_msg)
        
        if env == 0:
            #controller未读取到数据
            if '[文件]' == last_msg:
                send('已接收，打印请发送“打印”以获取更多信息')
                ai()
                reset()
            else:
                reply = df.apply(lambda x: str(x['回复内容']) if str(x['关键词']) in str(last_msg) else None,axis=1) #提取关键词并对应回复
                reply.dropna(inplace=True) # 简单清洗一下数据，覆盖原数据
                ar = np.array(reply).tolist() # 列表
                print(ar)
                if ar:
                    # 能够匹配到数据
                    if guest.Name not in config.whitelist:
                        # 不在白名单内
                        loc = 0
                        for i in ar:
                            wx.SendKeys(ar[loc],waitTime=0)
                            wx.SendKeys('{Shift}{Enter}',waitTime=0) # 遍历并合并回复
                            loc+=1
                        ai()               
                else:
                    # 没有匹配到数据
                    help()            