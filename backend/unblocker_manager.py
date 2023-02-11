import argparse
import json
import logging
import os
import platform
import time

import schedule
from requests import get

prefix = "apple-auto_"
parser = argparse.ArgumentParser(description="")
parser.add_argument("-api_url", help="API URL", required=True)
parser.add_argument("-api_key", help="API key", required=True)
args = parser.parse_args()
api_url = args.api_url
api_key = args.api_key


def info(text):
    print("[INFO] " + text)
    logging.info(text)


def error(text):
    print("[ERROR] " + text)
    logging.critical(text)


class API:
    def __init__(self):
        self.url = api_url
        self.key = api_key

    def get_task_list(self):
        try:
            result = json.loads(get(f"{self.url}/api/?key={self.key}&action=get_task_list", verify=False).text)
        except Exception as e:
            error("获取任务列表失败")
            return False
        else:
            if result['status'] == "fail":
                error("获取任务列表失败")
                return False
            elif result['data'] == "":
                return []
            else:
                return result['data'].split(",")

    def get_tasks_intervals(self):
        try:
            result = json.loads(get(f"{self.url}/api/?key={self.key}&action=get_tasks_check_intervals", verify=False).text)
        except Exception as e:
            error("获取任务间隔时间失败")
            return False
        else:
            if result['status'] == "fail":
                error("获取任务列表失败")
                return False
            elif result['data'] == "":
                return {}
            else:
                if type(result['data']) == str:
                    data = json.loads(result['data'])
                    ret = {}
                    for k,v in data.items():
                        ret[k] = int(v)
                    return ret
                else:
                    return result['data']


class local_docker:
    def __init__(self, api):
        self.api = api
        self.local_list = self.get_local_list()
        self.restart_invervals_min = -1
        self.tasks_intervals = self.get_tasks_intervals()
        

    def deploy_docker(self, id):
        info(f"部署容器{id}")
        os.system(f"docker run -d --name={prefix}{id} \
        -e api_url={self.api.url} \
        -e api_key={self.api.key} \
        -e taskid={id} \
        --log-opt max-size=1m \
        --log-opt max-file=1 \
        --restart=on-failure \
        xuelangwang/ppyy776:v1")

    def remove_docker(self, id):
        info(f"删除容器{id}")
        os.system(f"docker stop {prefix}{id} && docker rm {prefix}{id}")

    def restart_docker(self, id):
        info(f"重新启动容器{id}")
        os.system(f"docker restart {prefix}{id}")

    def restart_docker_delay(self, id, delay_min):
        info(f"一定时间后重启容器{id}")
        delay_second = delay_min
        os.system(f"docker restart -t {delay_second} {prefix}{id}")

    def get_local_list(self):
        local_list = []
        result = os.popen("docker ps --format \"{{.Names}}\" -a")
        for line in result.readlines():
            if line.find(prefix) != -1:
                local_list.append(line.strip().split("_")[1])
        info(f"本地存在{len(local_list)}个容器")
        return local_list

    def get_local_running_list(self):
        local_running_list = []
        result = os.popen("docker ps --format \"{{.Names}}\" ")
        for line in result.readlines():
            if line.find(prefix) != -1:
                local_running_list.append(line.strip().split("_")[1])
        info(f"本地存在{len(local_running_list)}个容器正在运行中")
        return local_running_list

    def get_remote_list(self):
        result_list = self.api.get_task_list()
        if not result_list:
            info("获取云端任务列表失败，使用本地列表")
            return self.local_list
        else:
            info(f"从云端获取到{len(result_list)}个任务")
            return result_list

    def get_tasks_intervals(self):
        task_intervals = self.api.get_tasks_intervals()
        if not task_intervals:
            info("获取云端任务间隔时间失败")
            return {}
        else:
            info("获取云端任务间隔时间成功")
            dic = task_intervals
            for k,v in dic.items():
                if v > self.restart_invervals_min:
                    self.restart_invervals_min = v
            return task_intervals

    def restart_all_task_delay(self):
        self.tasks_intervals = self.get_tasks_intervals()
        if self.restart_invervals_min <= 0:
            return
        self.local_list = self.get_local_list()
        all_keys = self.tasks_intervals.keys()
        for id in self.local_list:
            if id in all_keys:
                # self.restart_docker_delay(id, self.tasks_intervals[id])
                self.restart_docker_delay(id, 40)
                time.sleep(1)

    def sync(self):
        info("开始同步")
        self.local_list = self.get_local_list()
        local_running_list = self.get_local_running_list()
        # 处理需要删除的容器（本地存在，云端不存在）
        for id in self.local_list:
            if id not in self.get_remote_list():
                self.remove_docker(id)
                self.local_list.remove(id)
                if id in local_running_list:
                    local_running_list.remove(id)
        # 如果存在停止的容器，就重新启动一次
        if (len(self.local_list) != len(local_running_list)):
            for id in self.local_list:
                if id not in local_running_list:
                    self.restart_docker(id)
        # 处理需要部署的容器（本地不存在，云端存在）
        remote_list = self.get_remote_list()
        for id in remote_list:
            if id not in self.local_list:
                self.deploy_docker(id)
                self.local_list.append(id)
        info("同步完成")
    
    def restart_all_docker(self):
        info("重启所有的容器")
        self.local_list = self.get_local_list()
        for id in self.local_list:
            self.restart_docker(id)
        info("重启完成")

    def clean_local_docker(self):
        info("开始清理本地容器")
        self.local_list = self.get_local_list()
        for name in self.local_list:
            self.remove_docker(name)
        info("清理完成")

    def update(self):
        info("开始检查更新")
        self.local_list = self.get_local_list()
        if len(self.local_list) == 0:
            info("没有容器需要更新")
            return
        local_list_str = " ".join(self.local_list)
        os.system(f"docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        containrrr/watchtower \
        --cleanup \
        --run-once \
        {local_list_str}")


def job():
    global Local
    info("开始定时任务")
    Local.sync()

def update():
    global Local
    info("开始更新任务")
    Local.update()
    
def restartAll():
    global Local
    info("重启所有")
    Local.restart_all_docker()

def restartAllDelay():
    schedule.clear("restart_all_task_job")
    global Local
    info("延迟重启所有容器")
    Local.restart_all_task_delay()
    intervals = 30
    if Local.restart_invervals_min > 0:
        intervals = Local.restart_invervals_min * 2 - 1
    info("延迟重启执行结束，每个容器将在指定间隔期间重启")
    schedule.every(intervals).minutes.do(restartAllDelay).tag("restart_all_task_job")

info("AppleAuto后端管理服务启动")
api = API()
Local = local_docker(api)
info("拉取最新镜像")
os.system(f"docker pull xuelangwang/ppyy776:v1")
info("删除本地所有容器")
Local.clean_local_docker()
job()
schedule.every(10).minutes.do(job)
schedule.every(30).minutes.do(restartAllDelay).tag("restart_all_task_job")

# schedule.every(2).hours.do(restartAll)
# schedule.every().day.at("00:00").do(update)
while True:
    schedule.run_pending()
    time.sleep(1)
