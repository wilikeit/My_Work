#!/usr/bin/env python
# --*-- coding: utf-8 --*--

import global_setting
from conf import hosts
import redis_connector as redis
import json
import time

def fetch_monitored_list():
	for h in hosts.monitored_hosts:
		print '\033[42;1m--------%s---------\033[0m' % h.hostname
		for service_name,v in h.services.items():	### 循环这个主机的所有监控项
			#print service_name,v.interval
			service_key = '%s::%s' % (h.hostname,service_name)
			service_data = redis.r.get(service_key)
			if service_data is not None:
				service_data = json.loads(service_data)
				time_pass_since_last_recv = time.time() - service_data['recv_time']
				if time_pass_since_last_recv >= v.interval +10:	### 怕有延时，所以在监控间隔的基础上再加上10s，意思是已经这么长时间没有收到这个服务的数据了
					print '\033[41;1mService %s has not data for %ss\033[0m' % (service_name, time_pass_since_last_recv)
				else:	### 代表数据是按监控间隔发送过来的
					if service_data['data']['status'] == 0:	### 有效数据
						for index,val in v.triggers.items():	### loop all the indexes in the loop
							#print '===========>',index,val	
							data_type, warning,critical = val
							index_val = service_data['data'][index]
							if data_type == 'percentage' or data_type is int:
								index_val = float(index_val)
							### 把指标当次的值存到linux中的temp_data中去
							if service_data['recv_time'] != v.temp_data[index]['last_item_saving']: ### 意思是不重复的客户端时间
								v.temp_data[index]['status_data'].append(index_val)
								v.temp_data[index]['last_item_saving'] = service_data['recv_time']
							### 判断列表中获取到的数值个数是否到达10个
							if len(v.temp_data[index]['status_data']) > 10:
								del v.temp_data[index]['status_data'][0]
							### 循环temp_data 列表，检查有多少个超过了阈值
							cross_warning_count =0
							cross_critical_count =0
							for item in v.temp_data[index]['status_data']:
								if index in v.lt_operrator: ### 使用linux模块中的小于运算判断
									if item < critical:
										print '\033[31;1mService %s crossed critical line %s,current value is %s\033[0m' % (index,critical,item)
										cross_critical_count +=1
									elif item < warning:
										print '\033[33;1mService %s crossed critical line %s,current value is %s\033[0m' % (index,warning,item)
										cross_warning_count +=1
								else:		
									if item > critical: ### 如果超过了critical阈值
										print '\033[31;1mService %s crossed critical line %s,current value is %s\033[0m' % (index,critical,item)
										cross_critical_count +=1
									elif item > warning: ### 如果超过了warning阈值
										print '\033[33;1mService %s crossed critical line %s,current value is %s\033[0m' % (index,warning,item)
										cross_warning_count +=1
							print "\033[44;1m----temp data length----\033[0m",service_name,index,len(v.temp_data[index]['status_data'])
							print "Warning count:",cross_warning_count
							print "Critical count:",cross_critical_count
					else:	## 无效数据
						print '\033[31;1m%s data is not vaild\033[0m' % service_name, service_data
					
			else:
				pass

if __name__ == '__main__':	
	while True:
		fetch_monitored_list()
		time.sleep(3)
