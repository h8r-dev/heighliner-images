"""
该脚本用于在阿里云香港创建一个 4 核 8G 内存的 ECS 实例。
"""
# coding=utf-8

import json
import time
import traceback
import os

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest

RUNNING_STATUS = 'Running'
CHECK_INTERVAL = 3
CHECK_TIMEOUT = 180
IP_FILE = './ecs-ip.txt'
ID_FILE = './ecs-id.txt'

REGION = 'cn-hongkong'


class AliyunRunInstances(object):
    def __init__(self):
        self.access_id = os.getenv('ALICLOUD_ACCESS_KEY')
        self.access_secret = os.getenv('ALICLOUD_SECRET_KEY')

        # 资源组: dev
        self.resource_group_id = 'rg-aekzqwl4vqocsqi'

        # 是否只预检此次请求。true：发送检查请求，不会创建实例，也不会产生费用；false：发送正常请求，通过检查后直接创建实例，并直接产生费用
        self.dry_run = False
        # 实例所属的地域ID
        self.region_id = REGION
        # 实例的资源规格
        self.instance_type = 'ecs.c7.xlarge'
        # 实例的计费方式
        self.instance_charge_type = 'PostPaid'

        # 镜像ID, Custom image, with k3s, infra components installed.
        #  self.image_id = 'm-j6caa0e3yg1nxr7a3nqv'

        # Base Ubuntu Image.
        self.image_id = 'ubuntu_20_04_x64_20G_alibase_20220524.vhd'

        # 指定新创建实例所属于的安全组ID
        self.security_group_id = 'sg-j6c0ccak9v1pjsyrsliv'

        # 购买资源的时长
        self.period = 1
        # 购买资源的时长单位
        self.period_unit = 'Hourly'
        # 实例所属的可用区编号
        self.zone_id = 'random'
        # 网络计费类型
        self.internet_charge_type = 'PayByTraffic'
        # 虚拟交换机ID
        self.vswitch_id = 'vsw-j6cab7hd2zgdhhc26ra8m'
        # 实例名称
        self.instance_name = 'h8r-k8s-node'
        # 指定创建ECS实例的数量
        self.amount = 1
        # 公网出带宽最大值
        self.internet_max_bandwidth_out = 100
        # 云服务器的主机名
        self.host_name = 'h8r-k8s-node'
        # 是否为I/O优化实例
        self.io_optimized = 'optimized'
        # 密钥对名称
        self.key_pair_name = 'h8r-dev-ssh-key'
        # 是否开启安全加固
        self.security_enhancement_strategy = 'Deactive'
        # 系统盘大小
        self.system_disk_size = '80'
        # 系统盘的磁盘种类
        self.system_disk_category = 'cloud_essd'
        # 性能级别
        self.system_disk_performance_level = 'PL0'
        
        self.client = AcsClient(self.access_id, self.access_secret, self.region_id)

    def run(self):
        try:
            print("Start creating new ecs...")
            start = time.time()
            ids = self.run_instances()
            self._check_instances_status(ids)
            print("Time Consumed: {} seconds".format(time.time() - start))
        except ClientException as e:
            print('Fail. Something with your connection with Aliyun go incorrect.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except ServerException as e:
            print('Fail. Business error.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except Exception:
            print('Unhandled error')
            print(traceback.format_exc())

    def run_instances(self):
        """
        调用创建实例的API，得到实例ID后继续查询实例状态
        :return:instance_ids 需要检查的实例ID
        """
        request = RunInstancesRequest()
       
        request.set_DryRun(self.dry_run)
        
        request.set_ResourceGroupId(self.resource_group_id)
        request.set_InstanceType(self.instance_type)
        request.set_InstanceChargeType(self.instance_charge_type)
        request.set_ImageId(self.image_id)
        request.set_SecurityGroupId(self.security_group_id)
        request.set_Period(self.period)
        request.set_PeriodUnit(self.period_unit)
        request.set_ZoneId(self.zone_id)
        request.set_InternetChargeType(self.internet_charge_type)
        request.set_VSwitchId(self.vswitch_id)
        request.set_InstanceName(self.instance_name)
        request.set_Amount(self.amount)
        request.set_InternetMaxBandwidthOut(self.internet_max_bandwidth_out)
        request.set_HostName(self.host_name)
        request.set_IoOptimized(self.io_optimized)
        request.set_KeyPairName(self.key_pair_name)
        request.set_SecurityEnhancementStrategy(self.security_enhancement_strategy)
        request.set_SystemDiskSize(self.system_disk_size)
        request.set_SystemDiskCategory(self.system_disk_category)
        request.set_SystemDiskPerformanceLevel(self.system_disk_performance_level)
         
        body = self.client.do_action_with_exception(request)
        data = json.loads(body)
        instance_ids = data['InstanceIdSets']['InstanceIdSet']
        print('Success. Instance creation succeed. InstanceIds: {}'.format(', '.join(instance_ids)))
        return instance_ids

    def store_id_ip(self, instance):
        """
        存储 instance id, 公共 ip 地址。
        """
        instance_id = instance['InstanceId']
        instance_ip = instance['PublicIpAddress']['IpAddress'][0]
        print("Store id and public ip address of ecs instance:\n")
        print("ECS Id: {}\nECS IP: {}\n".format(instance_id, instance_ip))
        with open(IP_FILE, 'w') as fd:
            fd.write(instance_ip)
        with open(ID_FILE, 'w') as fd:
            fd.write(instance_id)

    def _check_instances_status(self, instance_ids):
        """
        每3秒中检查一次实例的状态，超时时间设为3分钟。
        :param instance_ids 需要检查的实例ID
        :return:
        """
        start = time.time()
        while True:
            request = DescribeInstancesRequest()
            request.set_InstanceIds(json.dumps(instance_ids))
            body = self.client.do_action_with_exception(request)
            data = json.loads(body)
            for instance in data['Instances']['Instance']:
                if RUNNING_STATUS in instance['Status']:
                    instance_ids.remove(instance['InstanceId'])
                    self.store_id_ip(instance)
                    print('Instance boot successfully: {}'.format(instance['InstanceId']))

            if not instance_ids:
                print('Instances all boot successfully')
                break

            if time.time() - start > CHECK_TIMEOUT:
                print('Instances boot failed within {timeout}s: {ids}'
                      .format(timeout=CHECK_TIMEOUT, ids=', '.join(instance_ids)))
                break

            print("Check running status of ECS instance")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    AliyunRunInstances().run()
