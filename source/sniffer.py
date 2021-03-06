# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

"""
Module implementing sniffer.
"""
from pcap import *
import dpkt, datetime
from util import *
import time, re, json, codecs,os
import struct
import threading, Queue
from PyQt5.QtCore import pyqtSlot

from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog, QLineEdit,QFileDialog


from Ui_main import Ui_snifferUI


class sniffer(QDialog, Ui_snifferUI):
    btn_stop = True
    filter='-1'
    package_tcp={}
    package_udp={}
    package_icmp={}

    file_tcp={}
    def __init__(self, parent=None):
        super(sniffer, self).__init__(parent)
        self.setupUi(self)
        # global q
        # q = Queue.Queue()

        super(sniffer, self).__init__(parent)
        self.setupUi(self)
        devs = findalldevs()
        for eth in devs:
            self.choose_eth.addItem(eth)

        self.package_info.setColumnWidth(5,500)
        self.package_info.setColumnWidth(2,150)
        self.package_info.setColumnWidth(1,150)
        self.package_info.setColumnHidden(6,True)
        self.package_info.setColumnHidden(7,True)
    def get_pkg_icmp(self):
        return self.package_icmp
    def set_pkg_icmp(self,icmp):
        self.package_icmp=icmp
    def del_pkg_icmp(self,id):
        self.package_icmp.pop(id)

    def get_pkg_tcp(self):
        return self.package_tcp
    def set_pkg_tcp(self,tcp):
        self.package_tcp=tcp
    def del_pkg_tcp(self,id):
        self.package_tcp.pop(id)



    def get_pkg_udp(self):
        return self.package_udp
    def set_pkg_udp(self,udp):
        self.package_udp=udp
    def del_pkg_udp(self,id):
        self.package_udp.pop(id)

    def get_file_tcp(self):
        return self.file_tcp
    def set_file_tcp(self,tcp):
        self.file_tcp = tcp
    def del_file_tcp(self,id):
        self.file_tcp.pop(id)

    def get_btnStop(self):
         return self.btn_stop
    def set_btnStop(self, stop):
         self.btn_stop = stop

    def set_filter(self, filter):
         self.filter = filter
    def get_filter(self):
         return self.filter
    def deal_package(self,timestamp,pkg):
        if(self.get_btnStop()==True):
            return
        package={}
        info={}
        timestamp,buf = timestamp,pkg
        timestamp = str(datetime.datetime.fromtimestamp(timestamp))
        r =r'\d{2}:\d{2}:\d{2}'
        stand_time =re.findall(r,timestamp)[0]
        timestamp = stand_time

        package['timestamp']=timestamp
        package['len']=len(buf)
        org= dpkt.hexdump(str(buf), 20)
        package['buf']=org
        #print type(buf)
        eth = dpkt.ethernet.Ethernet(buf)
        #print type(eth)
      # Make sure the Ethernet data contains an IP packet
        if eth.data.__class__.__name__=="ARP" :
             arp = eth.data
             package['protocol']='ARP'
             #ARP包解析
             info['hrd_type']=arp.hrd         #硬件类型
             info['pro_type']=arp.pro         #协议类型
             info['mac_addr_len']=arp.hln     #MAC地址长度
             info['pro_addr_len']=arp.pln     #协议地址长度
             info['op']=arp.op                #操作码
             info['sha']=mac_addr(arp.sha)    #发送方MAC地址
             info['spa']=inet_to_str(arp.spa) #发送方IP地址
             info['tha']=mac_addr(arp.tha)    #接收方MAC地址
             info['tpa']=inet_to_str(arp.tpa) #接收方IP地址
             data = arp.data
             package['info']=info
             timeItem = QTableWidgetItem("  "+package['timestamp'])
             srcItem = QTableWidgetItem("  "+info['sha'])
             dstItem = QTableWidgetItem("  "+info['tha'])
             protocolItem = QTableWidgetItem(" "+package['protocol'])
             lenItem = QTableWidgetItem("  "+str(package['len']))
             #i  = self.package_info.currentRow()+1
             i = self.package_info.rowCount()
             self.package_info.insertRow(i)

             self.package_info.setItem(i, 0, timeItem)
             self.package_info.setItem(i, 1, srcItem)
             self.package_info.setItem(i, 2, dstItem)
             self.package_info.setItem(i, 3, protocolItem)
             self.package_info.setItem(i, 4, lenItem)

             show=str(info['spa'])+" --> "+str(info['tpa'])+ \
                  ' protocol_type:' +str(info['pro_type']) + \
                  ' op_code : ' +str(info['op'])
             infoItem = QTableWidgetItem(show)
             self.package_info.setItem(i, 5, infoItem)

             saveItem = QTableWidgetItem( json.dumps(package) )
             self.package_info.setItem(i, 6, saveItem)
             dataItem = QTableWidgetItem( data )
             self.package_info.setItem(i, 7, dataItem)
             return "ARP"
        elif eth.data.__class__.__name__=="IP6":


             ip6 = eth.data
             #print 'get 6' + str(ip6.nxt)
             package['ip_ver'] = 6
             #IP6包解析
             info['fc']= ip6.fc              #优先级
             info['flow']=ip6.flow           #流量标识
             info['payload_len']=ip6.plen    #有效载荷长度
             info['next_hdr']=ip6.nxt        #下一包头
             info['hop_lim']=ip6.hlim        #条数限制
             info['src']=inet_to_str(ip6.src)#起始地址
             info['dst']=inet_to_str(ip6.dst)#目的地址
             #info['extend_4'] = ip6.data
             if ip6.nxt != 1 and ip6.nxt !=2 and ip6.nxt !=17 and ip6.nxt !=6:
                  print 'return '
                  return
             package['ipv6_info']= info

             if ip6.nxt == 1:
                   icmp = ip6.data
                   package['protocol']='ICMP'
                   info['type']=icmp.type       #类型
                   info['code']=icmp.code       #代码
                   info['checksum']=icmp.sum    #校验和
                   data=icmp.data
                   package['info']=info

             elif ip6.nxt == 6:
                    tcp = ip6.data

                    package['protocol']='TCP'
                    info['sport']=tcp.sport    #源端口
                    info['dport']=tcp.dport    #目的端口
                    info['seq']= tcp.seq       #seq
                    info['ack']= tcp.ack       #ack
                    info['flags']=tcp.flags    #标志位
                    info['window']=tcp.win     #窗口大小
                    info['checksum']=tcp.sum   #校验和
                    data=tcp.data#数据
                    info['packet_type'] = []   #具体
                    if  tcp.flags & dpkt.tcp.TH_SYN :
                        info['packet_type'].append("SYN")  #SYN
                    if tcp.flags & dpkt.tcp.TH_FIN:
                        info['packet_type'].append("FIN")  #FIN
                    if tcp.flags & dpkt.tcp.TH_RST:
                        info['packet_type'].append("RST")  #RST
                    if tcp.flags & dpkt.tcp.TH_PUSH:
                        info['packet_type'].append("PSH")  #PSH
                    if tcp.flags & dpkt.tcp.TH_ACK:
                       info['packet_type'].append("ACK")   #ACK
                    if tcp.flags & dpkt.tcp.TH_URG:
                        info['packet_type'].append("URG")  #URG
                    package['info']=info
             #elif  isinstance(ip6.data, dpkt.udp.UDP):
             elif ip6.nxt == 17:
                   udp = ip6.data

                   package['protocol']='UDP'
                   info['sport']=udp.sport         #源端口
                   info['dport']=udp.dport         #目的端口
                   info['ulen']=udp.ulen           #长度
                   info['checksum']=udp.sum        #校验和
                   data= udp.data
                   package['info']=info
                   print package
             #elif isinstance(ip6.data, dpkt.igmp.IGMP):
             elif ip6.nxt == 2:
                   igmp = ip6.data
                   package['protocol']='IGMP'
                   info['type']=igmp.type           #类型
                   info['maxresp']=igmp.maxresp     #最大响应延迟
                   info['checksum'] =igmp.sum       #校验和
                   info['group']=igmp.group         #组地址
                   data = igmp.data
                   package['info']=info

             if package:
                  #i  = self.package_info.currentRow()+1
                  i = self.package_info.rowCount()
                  self.package_info.insertRow(i)
                  timeItem = QTableWidgetItem("  "+package['timestamp'])

                  srcItem = QTableWidgetItem("  "+info['src'])
                  dstItem = QTableWidgetItem("  "+info['dst'])
                  protocolItem = QTableWidgetItem(" "+package['protocol'])
                  lenItem = QTableWidgetItem("  "+str(package['len']))

                  self.package_info.setItem(i, 0, timeItem)
                  self.package_info.setItem(i, 1, srcItem)
                  self.package_info.setItem(i, 2, dstItem)
                  self.package_info.setItem(i, 3, protocolItem)
                  self.package_info.setItem(i, 4, lenItem)
           #self.package_info.
                  if (package['protocol'])=='UDP':
                       info=package['info']
                       show=str(info['sport'])+' -> '+str(info['dport'])+'  len :'+str(info['ulen'])+'   sum : ' + str(info['checksum'])
                       infoItem = QTableWidgetItem(show)
                       self.package_info.setItem(i, 5, infoItem)


                  elif (package['protocol'])=='TCP':
                       info=package['info']
                       show=str(info['sport'])+' -> '+str(info['dport']) + '  ['+','.join(info['packet_type'])+']  seq :'+str(info['seq'])+'   ack : ' + str(info['ack'])+\
                          ' window : '+ str(info['window'])
                       infoItem = QTableWidgetItem(show)
                       self.package_info.setItem(i, 5, infoItem)

                  elif (package['protocol'])=='ICMP':
                       info=package['info']
                       show='type : '+str(info['type'])+ \
                          '  code : '+str(info['code']) + \
                          '  sum : '+str(info['checksum'])
                       infoItem = QTableWidgetItem(show)
                       self.package_info.setItem(i, 5, infoItem)
                  print data
                  dataItem = QTableWidgetItem(data)
                  self.package_info.setItem(i, 7, dataItem)
                  saveItem = QTableWidgetItem(json.dumps(package))
                  self.package_info.setItem(i, 6, saveItem)




        else:
           ip = eth.data
           package['ip_ver']= 4                                #版本
           if isinstance(eth.data, dpkt.ip.IP):
             package['ip_hl'] = ip.hl                          #头长度
             package['ip_tos'] = ip.tos                        #服务类型
             package['ip_len'] =  ip.len                       #总长度
             package['ip_id'] = ip.id                          #标识
             package['ip_DF']=bool(ip.off & dpkt.ip.IP_DF)     #DF标识位
             package['ip_MF']=bool(ip.off & dpkt.ip.IP_MF)     #MF标识位
             #package['ip_offset']=ip.off & dpkt.ip.IP_OFFMASK  #分段偏移量
             package['ip_offset']=ip.offset
             package['ip_ttl'] =  ip.ttl                       #生存期
             package['ip_protocol'] = ip.p                     #协议类型
             package['ip_sum'] = ip.sum                        #头校验和
             package['src_ip']=inet_to_str(ip.src)             #源地址
             package['dst_ip']=inet_to_str(ip.dst)             #目的地址

           if isinstance(ip.data, dpkt.icmp.ICMP):
             icmp = ip.data
             package['protocol']='ICMP'
             #package['src_ip'] = inet_to_str(ip.src)
             #package['dst_ip'] = inet_to_str(ip.dst)
             #print 'get icmp'
             info['type']=icmp.type       #类型
             info['code']=icmp.code       #代码
             info['checksum']=icmp.sum    #校验和
             pkg={}
             data=icmp.data
             pkg['ip_offset']=ip.offset
             pkg['ip_MF'] = ip.mf
             tmp_pkt_icmp={}
             if(ip.offset!=0 and ip.mf==0):
                 print 'end of package'
                 list = self.get_pkg_icmp()[ip.id]
                 offset = []
                 list.sort(key=lambda k:k.get('ip_offset')) #按照offset大小排序
                 print len(list)
                 data=''
                 for slice in list:
                      if isinstance(slice['ip_data'],dpkt.icmp.ICMP.Echo):
                          data = data+(slice['ip_data']['data'])  # 数据重组
                          print'echo'
                      elif isinstance(slice['ip_data'],dpkt.icmp.ICMP.Unreach):
                          data = data+slice['ip_data']['data']
                          print'unreach'
                      elif isinstance(slice['ip_data'],dpkt.icmp.ICMP.Quench):
                           data= data+slice['ip_data']['data']
                           print'quench'
                      elif isinstance(slice['ip_data'],dpkt.icmp.ICMP.Redirect):
                           data= data+slice['ip_data']['data']
                           print'redirect'
                      elif isinstance(slice['ip_data'],dpkt.icmp.ICMP.TimeExceed):
                           data= data+slice['ip_data']['data']
                           print'timeexceed'
                      else:
                           data = data+slice['ip_data']
                           print'prue data'
    
                 #组装完成
                 data=data+icmp.data
                 #以下为测试分片重组用
                 #data="数据部分长度:"+str(len(data))
                 #print "组装数据:"+data
                 package['info']=info
                 self.del_pkg_icmp(ip.id)
            # 收集分片
             elif(ip.mf!=0) :  #如果允许分段 并且MF标记为为1，说明是分片包，将其存入内存
                pkg['ip_data']=(icmp.data)
                if self.get_pkg_icmp().has_key(ip.id):
                  list = []
                  for i in self.get_pkg_icmp()[ip.id] :
                      list.append(i)
                  list.append(pkg)
                else:
                  list=[]
                  list.append(pkg)
                print len(list)
                tmp_pkt_icmp[ip.id]=list

                self.set_pkg_icmp(tmp_pkt_icmp)
                print 'package length= '+ str(len(self.get_pkg_icmp()))
                #清空数据，等待组装完毕再返回
                package['info']=info
             else:
                #如果不涉及ip分片,则直接返回
                print '不涉及分片'
                package['info']=info

           elif isinstance(ip.data, dpkt.tcp.TCP):
             tcp = ip.data
             package['protocol']='TCP'
             if isinstance(ip.data,dpkt.tftp.TFTP):
                 print 'ftp'
             info['sport']=tcp.sport    #源端口
             info['dport']=tcp.dport    #目的端口
             info['seq']= tcp.seq       #seq
             info['ack']= tcp.ack       #ack
             info['flags']=tcp.flags    #标记
             info['window']=tcp.win     #窗口大小
             info['checksum']=tcp.sum   #校验和
             data= tcp.data#数据
             info['packet_type'] = []   #具体lean  l
             if  tcp.flags & dpkt.tcp.TH_SYN :
                    info['packet_type'].append("SYN")
             if tcp.flags & dpkt.tcp.TH_FIN:
                    info['packet_type'].append("FIN")
             if tcp.flags & dpkt.tcp.TH_RST:
                    info['packet_type'].append("RST")
             if tcp.flags & dpkt.tcp.TH_PUSH:
                    info['packet_type'].append("PSH")
             if tcp.flags & dpkt.tcp.TH_ACK:
                    info['packet_type'].append("ACK")
             if tcp.flags & dpkt.tcp.TH_URG:
                    info['packet_type'].append("URG")
             ####################IP分片检测与重组####################
             pkg={}
             tmp_pkt_tcp={}
             pkg['ip_offset']=ip.offset
             if(ip.offset!=0 and ip.mf==0):
                 print 'end of package'
                 list = self.get_pkg_tcp()[ip.id]
                 data = ''
                 list.sort(key=lambda k:k.get('ip_offset')) #按照offset大小排序
                 for slice in list:
                        data = data+slice['ip_data']
                 #组装完成
                 print data
                 data= data
                 info['data']=data
                 package['info']=info
                 #清理内存数据
                 self.del_pkg_tcp(ip.id)
             # 收集分片
             elif(ip.mf!=0 and ip.df!=1) :  #如果允许分段 并且MF标记为为1，说明是分片包，将其存入内存
                pkg['ip_data']=(tcp.data)
                if self.get_pkg_tcp().has_key(ip.id):
                  list = []
                  for i in self.get_pkg_tcp()[ip.id] :
                      list.append(i)
                  list.append(pkg)
                else:
                  list=[]
                  list.append(pkg)
                #print len(list)
                tmp_pkt_tcp[ip.id]=list
                self.set_pkg_tcp(tmp_pkt_tcp)
                print 'package length= '+ str(len(self.get_pkg_tcp()))
                #清空数据，等待组装完毕再返回
                package.clear()
             ######################################################
             else:
                #如果不涉及ip分片,则直接返回
                package['info']=info

           elif isinstance(ip.data, dpkt.udp.UDP):
                 udp = ip.data
                 package['protocol']='UDP'

                 info['sport']=udp.sport  #源端口
                 info['dport']=udp.dport  #目的端口
                 info['ulen']=udp.ulen    #长度
                 info['checksum']=udp.sum #校验和
                 data=udp.data
                 pkg={}
                 tmp_pkt_udp={}
                 pkg['ip_offset']=ip.offset
                 if(ip.offset!=0 and ip.mf==0):
                     print 'end of package'
                     list = self.get_pkg_udp()[ip.id]
                     data = ''
                     list.sort(key=lambda k:k.get('ip_offset')) #按照offset大小排序
                     for slice in list:
                            data = data+slice['ip_data']
                     #组装完成
                     info['data']=data
                     package['info']=info
                     #清理内存数据
                     self.del_pkg_udp(ip.id)
                 # 收集分片
                 elif(ip.mf!=0 and ip.df!=1) :  #如果允许分段 并且MF标记为为1，说明是分片包，将其存入内存
                    pkg['ip_data']=(udp.data)
                    if self.get_pkg_udp().has_key(ip.id):
                      list = []
                      for i in self.get_pkg_udp()[ip.id] :
                          list.append(i)
                      list.append(pkg)
                    else:
                      list=[]
                      list.append(pkg)
                    #print len(list)
                    tmp_pkt_udp[ip.id]=list
                    self.set_pkg_udp(tmp_pkt_udp)
                    print 'package length= '+ str(len(self.get_pkg_udp()))
                    #清空数据，等待组装完毕再返回
                    package.clear()
                 ######################################################
                 else:
                    #如果不涉及ip分片,则直接返回
                    package['info']=info

           elif isinstance(ip.data, dpkt.igmp.IGMP):
                 igmp = ip.data
                 package['protocol']='IGMP'
                 info['type']=igmp.type       #类型
                 info['maxresp']=igmp.maxresp #最大响应延迟
                 info['checksum'] =igmp.sum   #校验和
                 info['group']=igmp.group     #组地址
                 data = igmp.data
                 package['info']=info

           else:
                 package['protocol']=eth.data.__class__.__name__

           if package:
               #i  = self.package_info.currentRow()+1
               i = self.package_info.rowCount()
               self.package_info.insertRow(i)
               timeItem = QTableWidgetItem("  "+package['timestamp'])

               srcItem = QTableWidgetItem("  "+package['src_ip'])
               dstItem = QTableWidgetItem("  "+package['dst_ip'])
               protocolItem = QTableWidgetItem(" "+package['protocol'])
               lenItem = QTableWidgetItem("  "+str(package['len']))

               self.package_info.setItem(i, 0, timeItem)
               self.package_info.setItem(i, 1, srcItem)
               self.package_info.setItem(i, 2, dstItem)
               self.package_info.setItem(i, 3, protocolItem)
               self.package_info.setItem(i, 4, lenItem)
               #self.package_info.
               if (package['protocol'])=='UDP':
                     info=package['info']
                     show =str(info['sport'])+ " ->" + str(info['dport']) + ' id:'+str(package['ip_id'])+' MF:'+str(package['ip_MF'])
                     infoItem = QTableWidgetItem(show)
                     self.package_info.setItem(i, 5, infoItem)

               elif (package['protocol'])=='TCP':
                 info=package['info']
                 show=str(info['sport'])+' -> '+str(info['dport']) + '  ['+','.join(info['packet_type'])+']  id :'+str(package['ip_id'])+' MF:'+str(package['ip_MF'])+\
                      ' window : '+ str(info['window'])
                 infoItem = QTableWidgetItem(show)
                 self.package_info.setItem(i, 5, infoItem)

               elif (package['protocol'])=='ICMP':
                 info=package['info']
                 show='type : '+str(info['type'])+ \
                      '  code : '+str(info['code']) + \
                      '  sum : '+str(info['checksum'])+ \
                       ' offset: '+str(ip.offset)+ \
                      '    ttl :'+str(package['ip_ttl'])
                 infoItem = QTableWidgetItem(show)
                 self.package_info.setItem(i, 5, infoItem)


               saveItem = QTableWidgetItem(json.dumps(package))
               self.package_info.setItem(i, 6, saveItem)
               dataItem = QTableWidgetItem( str(data)  )
               self.package_info.setItem(i, 7, dataItem)


    def package_reader(self):
        while(self.get_btnStop()==False):
           rule = str(self.get_filter())
           try:
               if rule != "-1":
                   print 'rule:'+rule
                   pc=pcap(self.choose_eth.currentText(), immediate=True)
                   pc.setfilter(rule)
                   pc.loop(10,self.deal_package)
               else:
                   print 'no rule'
                   pcap(self.choose_eth.currentText(), immediate=True).loop(5,self.deal_package)
           except Exception, e:
                   #QMessageBox.information(self,"提示","出现错误")
                   print e
                   self.set_filter("-1")

    @pyqtSlot()
    def on_btn_begin_clicked(self):
         self.set_btnStop(False)
         print '设置符号为:', self.btn_stop
         th =threading.Thread(target = self.package_reader)
         th.start()


    @pyqtSlot()
    def on_btn_clear_history_clicked(self):
        ## 清屏
        self.textEdit.clear()
        self.textEdit_2.clear()
        self.textBrowser_2.clear()
        #self.package_info.clear()
        self.package_info.setRowCount(0)
        self.package_info.removeRow(0)
    @pyqtSlot()
    def on_btn_stop_clicked(self):
        self.set_btnStop(True)
        print '设置符号为:', self.btn_stop


    @pyqtSlot()
    def on_btn_filter_clicked(self):
        list = ["指定源IP地址","指定目的IP地址", "指定源端口","指定目的端口","指定协议类型","自定义规则"]

         #第三个参数可选 有一般显示 （QLineEdit.Normal）、密碼显示（ QLineEdit. Password）与不回应文字输入（ QLineEdit. NoEcho）
        #stringNum,ok3 = QInputDialog.getText(self, "标题","姓名:",QLineEdit.Normal, "王尼玛")
         #1为默认选中选项目，True/False  列表框是否可编辑。
        item, ok = QInputDialog.getItem(self, "选项","规则列表", list, 1, False)
        type=0
        if ok:
            if item=="指定源IP地址":
                 filter,ok_1 = QInputDialog.getText(self, "标题","请输入指定源IP地址:",QLineEdit.Normal, "*.*.*.*")
                 rule = "src host "+filter
            elif item =="指定目的IP地址"  :
                 filter,ok_2 = QInputDialog.getText(self, "标题","请输入指定目的IP地址:",QLineEdit.Normal, "*.*.*.*")
                 rule= "dst host "+filter
            elif item =="指定源端口":
                 filter,ok_3 = QInputDialog.getInt(self, "标题","请输入指定源端口:",80, 0, 65535)
                 rule="src port "+str(filter)
            elif item =="指定目的端口":
                 filter,ok_4 = QInputDialog.getInt(self, "标题","请输入指定目的端口:",80, 0, 65535)
                 rule ="dst port "+str(filter)
            elif item =="指定协议类型" :
                 filter,ok_2 = QInputDialog.getText(self, "标题","请输入指定协议类型:",QLineEdit.Normal, "icmp")
                 rule =filter
            elif item =="自定义规则":
                 filter,ok_2 = QInputDialog.getText(self, "标题","请输入规则:",QLineEdit.Normal, "host 202.120.2.1")
                 rule=filter
            rule=rule.lower()
            self.set_filter(rule)

    @pyqtSlot()
    def on_btn_search_clicked(self):
        #todo
        filter,ok = QInputDialog.getText(self, "搜索时将停止抓包","请输入需要搜索的字段:",QLineEdit.Normal, "password")
        if ok and filter:
          self.set_btnStop(True)
          for row in range(self.package_info.rowCount()):
            if(self.package_info.item(row, 7))!=None:
              data = bytes((self.package_info.item(row, 7).text()))
              if data is None :
                      self.package_info.setRowHidden(row,True)
              else:
                    obj= re.search(filter,data)

                    if  obj is None:
                      self.package_info.setRowHidden(row,True)
                    else:
                      print 'data find=' + data

    #查看全部抓包日志
    @pyqtSlot()
    def on_btn_viewlog_clicked(self):
        current= self.package_info.rowCount()
        for row in range(current):
          self.package_info.setRowHidden(row,False)

    #文件重组
    @pyqtSlot()
    def on_btn_recover_clicked(self):
       #重组文件时暂停抓包
       # self.btn_stop=True
       #遍历TCP包 寻找满足条件的包：源目的地址相同，源目的端口相同，包数据部分非空
       #进行传输标识进行重组
       current= self.package_info.rowCount()

       tmp_pkt_name=[]
       for row in range(current):
         if (self.package_info.item(row, 6)):
           package = json.loads(self.package_info.item(row, 6).text())
           protocol = package['protocol']
           if package is not None and protocol =="TCP":
                ip_ver = package['ip_ver']
                info=package['info']
                if ip_ver ==4:
                   src_ip = package['src_ip']
                   dst_ip = package['dst_ip']
                   id = package['ip_id']
                else:
                   src_ip = info['src']
                   dst_ip = info['dst']                
                sport = info['sport']
                dport = info['dport']
                #形成特征字段
                pkg={}
                key = str(ip_ver)+str(src_ip)+str(dst_ip)+str(sport)+str(dport)
                print key
                pkg['tcp_data']=bytes(self.package_info.item(row, 7).text())
                f_retr = r'RETR\s+'
                f_stor = r'STOR\s+'
                if pkg['tcp_data'] and (dport ==21 or sport ==21):
                     s = re.search(f_retr,pkg['tcp_data'])
                     if s is not None :
                         file_name=pkg['tcp_data'].replace('RETR ','')
                         tmp_pkt_name.append(file_name)
                         print file_name
                if pkg['tcp_data'] and (dport == 21 or sport ==21):
                     s = re.search(f_stor,pkg['tcp_data'])
                     if s is not None :
                         file_name=pkg['tcp_data'].replace('STOR ','')
                         tmp_pkt_name.append(file_name)
                         print file_name
                pkg['id']=id
                #如果含有特征字段，则继续往后添加
                if self.get_file_tcp().has_key(key):
                  list = []
                  for i in self.get_file_tcp()[key] :
                      list.append(i)
                  if(len(tmp_pkt_name)>=1):
                   pkg['filename']=tmp_pkt_name[0]
                   tmp_pkt_name.pop(0)

                  list.append(pkg)
                  print len(list)
                #如果不含特征字段，
                else:
                  if len(self.package_info.item(row, 7).text())<100:
                        #print 'len<100,so continue'
                        continue
                  else:
                      list=[]
                      list.append(pkg)
                _ = self.get_file_tcp()
                _[key]=list
                self.set_file_tcp(_)
                #print 'package length= '+ str(len(self.get_file_tcp()))
       # print self.get_file_tcp()
       #print 'package length= '+ str(len(self.get_file_tcp()))
       if len(self.get_file_tcp())>=1:
                for key in  self.get_file_tcp().keys():
                     list = self.get_file_tcp()[key]
                     data = ''
                     #TODO SECOND
                     recover=[]
                     file_name_= None
                     print 'list lst='+str(list)
                     for i in list: #便利list中的字典
                         if i.has_key('filename'): #如果存在文件名的项
                              file_name_ = i['filename']
                         elif i.has_key('id'):
                             recover.append(i)
                     if file_name_ is None:
                          continue
                     list =recover
                     list.sort(key=lambda k:k.get('id')) #按照offset大小排序
                     #print list
                     for slice in list:
                            data = data+slice['tcp_data']
                     #组装完成
                     #print data
                     self.del_file_tcp(key)
                     #if file_name_ is None :
                     #    file_name_ = key
                     file = open('./'+file_name_, 'w')
                     file.write(data)
                     file.close()
                     QMessageBox.information(self,"提示","文件重组成功:"+file_name_)
       else:
            QMessageBox.information(self,"提示","找不到可重组的包！")





    #选中信息保存文件
    @pyqtSlot()
    def on_btn_save_clicked(self):
        fileName, ok = QFileDialog.getSaveFileName(self,"文件保存","./","All Files (*);;Text Files (*.txt)")
        if fileName is None:
              QMessageBox.information(self,"Error Message","Plesase Select a Text File");
        else:
            if ok :
              #
              # data = self.package_info.get
              # file.write("Test")
              flg=-1
              for item in self.package_info.selectedItems():
                   row=item.row()
                   if row != flg :
                     flg=row
                     if self.package_info.item(row,6):
                         package = json.loads(self.package_info.item(row,6).text())
                         data=self.package_info.item(row,7).text()
                         saveContent = deal_save(package,data)
                         file = open(fileName, 'a')
                         file.write(saveContent)
                         file.close()

    @pyqtSlot()
    def on_btn_exit_clicked(self):
        pass

    @pyqtSlot(int)
    def on_choose_eth_activated(self, p0):
        pass

    @pyqtSlot(int)
    def on_choose_eth_currentIndexChanged(self, p0):
        print self.choose_eth.currentText()

    @pyqtSlot(int, int)
    def on_package_info_cellClicked(self, row, column):
      self.textEdit.clear()
      self.textBrowser_2.clear()
      data=''
      if self.package_info.item(row, 6) != None:
        package = json.loads(self.package_info.item(row, 6).text())
        protocol = package['protocol']
        if self.package_info.item(row, 7)!= None:
            data = self.package_info.item(row, 7).text()
            print data

        if protocol != 'ARP':
             ip_ver = package['ip_ver']
        if protocol == 'ARP' :
             info=package['info']
             buf = package['buf']
             self.textBrowser_2.append("<pre>"+ buf+"</pre>")
             self.textEdit.append("<h3>   协议：ARP" +"</h3>")
             self.textEdit.append("<pre> 硬件类型: "+ str(info['hrd_type'])+ "  协议类型:"+ str(info['pro_type'])+\
                   " MAC地址长度："+str(info['mac_addr_len'])+" 协议地址长度："+str(info['pro_addr_len'])+" 操作码："+str(info['op'])+"</pre>" )
             self.textEdit.append("<pre> 发送方MAC地址 "+info['sha'] +"  发送方IP地址 "+info['spa'] +"</pre>")
             self.textEdit.append("<pre> 接收方MAC地址 "+info['tha'] +"  接收方IP地址 "+info['tpa'] +"</pre>")
             self.textEdit_2.setPlainText(data)
        elif protocol =='UDP' :
             ip_ver = package['ip_ver']
             buf = package['buf']
             self.textBrowser_2.append("<pre>"+ buf+"</pre>")
             if ip_ver == 4 :
                   info=package['info']
                   # ipv4头部信息
                   self.textEdit.append("<h3> IP首部:       IP version 4 "+"</h3>")
                   self.textEdit.append("<pre> 头长度:" + str(package['ip_hl'])  + \
                                           " 服务类型："+str(package['ip_tos'])+" 总长度："+ str(package['ip_len'])+" 标识："+str(package['ip_id'])+ \
                                           " DF标志位:"+str(package['ip_DF'])+" MF标志位:"+str(package['ip_MF'])+" 分段偏移量:"+str(package['ip_offset'])+"</pre>" )
                   self.textEdit.append("<pre> 生存期:"+ str(package['ip_ttl'])+" 协议类型:" + str(package['ip_protocol'])+" 头部校验和:"+str(package['ip_sum'])+"</pre>" )
                   self.textEdit.append("<pre> 源地址: "+str(package['src_ip'])+" 目的地址: "+str(package['dst_ip'])+"</pre>")

                   # UDP头部信息
                   self.textEdit.append("<h3> UDP首部：</h3>")
                   self.textEdit.append("<pre> 源端口: "+str(info['sport']) +"  目的端口："+str(info['dport'])+\
                                            " 包长度："+str(info['ulen']) + " 校验和："+str(info['checksum'])+"</pre>")
                   #

                   self.textEdit_2.setPlainText(data)
                   #self.textEdit.append("<pre> 抓包时间："+package['timestamp']+"</pre>")
             elif ip_ver == 6 :
                   info=package['info']
                   # ipv6头部信息
                   self.textEdit.append("<h3> IP首部:       IP version 6 "+"</h3>")
                   self.textEdit.append("<pre> 优先级:"+str(info['fc'])+" 流量标识: "+ str(info['flow'])+" 有效载荷长度:"+ str(info['payload_len'])+\
                                             " 下一包头："+str(info['next_hdr'])+" 跳数限制："+str(info['hop_lim'])+"</pre>" )
                   self.textEdit.append("<pre> 起始地址："+str(info['src']) +"</pre>")
                   self.textEdit.append("<pre> 目的地址："+str(info['dst'])+ "</pre>")
                   # UDP头部信息
                   self.textEdit.append("<h3> UDP首部：</h3>")
                   self.textEdit.append("<pre> 源端口: "+str(info['sport']) +"  目的端口："+str(info['dport'])+\
                                            " 包长度："+str(info['ulen']) + " 校验和："+str(info['checksum'])+"</pre>")
                   #


                   self.textEdit_2.setPlainText(data)
                   #self.textEdit.append("<pre> 抓包时间："+package['timestamp']+"</pre>")



        elif protocol=='TCP' :
                   buf = package['buf']
                   self.textBrowser_2.append("<pre>"+ buf+"</pre>")
                   info=package['info']
                   if ip_ver ==4:
                       self.textEdit.append("<h5> IP首部:       IP version 4 "+"</h5>")
                       self.textEdit.append("<pre> 头长度:" + str(package['ip_hl'])  + \
                                           " 服务类型："+str(package['ip_tos'])+" 总长度："+ str(package['ip_len'])+" 标识："+str(package['ip_id'])+ \
                                           " DF标志位:"+str(package['ip_DF'])+" MF标志位:"+str(package['ip_MF'])+" 分段偏移量:"+str(package['ip_offset'])+\
                                           " 生存期:"+ str(package['ip_ttl'])+" 协议类型:" + str(package['ip_protocol'])+" 头部校验和:"+str(package['ip_sum'])+"</pre>" )
                       self.textEdit.append("<pre> 源地址: "+str(package['src_ip'])+" 目的地址: "+str(package['dst_ip'])+"</pre>")
                       self.textEdit.append("<h5> TCP协议:"+"</h5>")
                       self.textEdit.append("<pre> 源端口: "+str(info['sport']) +"  目的端口："+str(info['dport'])+\
                                            " seq："+str(info['seq']) + " ack："+str(info['ack'])+"</pre>")

                       self.textEdit.append("<pre> 标记: "+str(info['flags']) +"  窗口大小："+str(info['window'])+\
                                            " 标记类型："+','.join(info['packet_type']) + " 校验和："+str(info['checksum'])+"</pre>")

                       self.textEdit_2.setPlainText(data)
                   elif ip_ver == 6 :

                       self.textEdit.append("<h5> IP首部:       IP version 6 "+"</h5>")
                       self.textEdit.append("<pre> 优先级:"+str(info['fc'])+" 流量标识: "+ str(info['flow'])+" 有效载荷长度:"+ str(info['payload_len'])+\
                                                 " 下一包头："+str(info['next_hdr'])+" 跳数限制："+str(info['hop_lim'])+"</pre>" )
                       self.textEdit.append("<pre> 起始地址："+str(info['src']) +"</pre>")
                       self.textEdit.append("<pre> 目的地址："+str(info['dst'])+ "</pre>")

                       self.textEdit.append("<h5> TCP协议:"+"</h5>")
                       self.textEdit.append("<pre> 源端口: "+str(info['sport']) +"  目的端口："+str(info['dport'])+\
                                            " seq："+str(info['seq']) + " ack："+str(info['ack'])+\
                                            " 标记: "+str(info['flags']) +"  窗口大小："+str(info['window'])+\
                                            " 标记类型："+','.join(info['packet_type']) + " 校验和："+str(info['checksum'])+"</pre>")

                       self.textEdit_2.setPlainText(data)



        elif protocol == 'ICMP' :
               buf = package['buf']
               self.textBrowser_2.append("<pre>"+ buf+"</pre>")
               ip_ver = package['ip_ver']
               info=package['info']
               if ip_ver == 4:
                   self.textEdit.append("<h3> IP首部:       IP version 4 "+"</h3>")
                   self.textEdit.append("<pre> 头长度:" + str(package['ip_hl'])  + \
                                           " 服务类型："+str(package['ip_tos'])+" 总长度："+ str(package['ip_len'])+" 标识："+str(package['ip_id'])+ \
                                           " DF标志位:"+str(package['ip_DF'])+" MF标志位:"+str(package['ip_MF'])+" 分段偏移量:"+str(package['ip_offset'])+"</pre>" )
                   self.textEdit.append("<pre> 生存期:"+ str(package['ip_ttl'])+" 协议类型:" + str(package['ip_protocol'])+" 头部校验和:"+str(package['ip_sum'])+"</pre>" )
                   self.textEdit.append("<pre> 源地址: "+str(package['src_ip'])+" 目的地址: "+str(package['dst_ip'])+"</pre>")

                   self.textEdit.append("<h3>"+"ICMP协议:" +"</pre>")
                   self.textEdit.append("<pre>"+" 类型: "+str(info['type'])+" 代码："+str(info['code'])+" 校验和： "+str(info['checksum'])+ "</pre>")
                   self.textEdit_2.setPlainText((data))
               elif ip_ver == 6 :
                       self.textEdit.append("<h3> IP首部:       IP version 6 "+"</h3>")
                       self.textEdit.append("<pre> 优先级:"+str(info['fc'])+" 流量标识: "+ str(info['flow'])+" 有效载荷长度:"+ str(info['payload_len'])+\
                                                 " 下一包头："+str(info['next_hdr'])+" 跳数限制："+str(info['hop_lim'])+"</pre>" )
                       self.textEdit.append("<pre> 起始地址："+str(info['src']) +"</pre>")
                       self.textEdit.append("<pre> 目的地址："+str(info['dst'])+ "</pre>")

                       self.textEdit.append("<h3> ICMP协议:"+"</h3>")
                       self.textEdit.append("<pre>"+" 类型: "+str(info['type'])+" 代码："+str(info['code'])+" 校验和： "+str(info['checksum'])+ "</pre>")
                       self.textEdit_2.setPlainText((data))



        elif protocol =='IGMP' :
                   buf = package['buf']
                   self.textBrowser_2.append("<pre>"+ buf+"</pre>")
                   info=package['info']
                   if ip_ver ==4:
                       self.textEdit.append("<h3> IP首部:       IP version 4 "+"</h3>")
                       self.textEdit.append("<pre> 头长度:" + str(package['ip_hl'])  + \
                                           " 服务类型："+str(package['ip_tos'])+" 总长度："+ str(package['ip_len'])+" 标识："+str(package['ip_id'])+ \
                                           " DF标志位:"+str(package['ip_DF'])+" MF标志位:"+str(package['ip_MF'])+" 分段偏移量:"+str(package['ip_offset'])+"</pre>" )
                       self.textEdit.append("<pre> 生存期:"+ str(package['ip_ttl'])+" 协议类型:" + str(package['ip_protocol'])+" 头部校验和:"+str(package['ip_sum'])+"</pre>" )
                       self.textEdit.append("<pre> 源地址: "+str(package['src_ip'])+" 目的地址: "+str(package['dst_ip'])+"</pre>")
                       self.textEdit.append("<h3>"+"IGMP协议:" +"</pre>")
                       self.textEdit.append("<pre>"+" 类型: "+str(info['type'])+" 最大响应延迟："+str(info['maxresp'])+" 校验和： "+str(info['checksum'])+" 组地址:"+str(info['group'])+ "</pre>")
                       self.textEdit_2.setPlainText((data))
                   elif ip_ver == 6 :
                       self.textEdit.append("<h3> IP首部:       IP version 6 "+"</h3>")
                       self.textEdit.append("<pre> 优先级:"+str(info['fc'])+" 流量标识: "+ str(info['flow'])+" 有效载荷长度:"+ str(info['payload_len'])+\
                                                 " 下一包头："+str(info['next_hdr'])+" 跳数限制："+str(info['hop_lim'])+"</pre>" )
                       self.textEdit.append("<pre> 起始地址："+str(info['src']) +"</pre>")
                       self.textEdit.append("<pre> 目的地址："+str(info['dst'])+ "</pre>")
                       self.textEdit.append("<h3>"+"IGMP协议:" +"</pre>")
                       self.textEdit.append("<pre>"+" 类型: "+str(info['type'])+" 最大响应延迟："+str(info['maxresp'])+" 校验和： "+str(info['checksum'])+" 组地址:"+str(info['group'])+ "</pre>")
                       self.textEdit_2.setPlainText((data))

        else:
             print "error"
             print protocol


if __name__ == "__main__":
 import sys
 from PyQt5.QtWidgets import QApplication
 app = QApplication(sys.argv)
 dlg = sniffer()
 dlg.show()
 sys.exit(app.exec_())
