# Live_monitor_worker - Vtuber直播监控工作端

## 介绍

这是由[Auto_Record_Matsuri](https://github.com/fzxiao233/Auto_Record_Matsuri)解耦合后的工作模块，配合Server端使用可实现包括但不限于bot提醒，视频下载，视频上传，同传记录等功能

目前已实现的worker:

- bot(QQ机器人提醒)

- 直播录制/上传

- 同传记录

## 特性

- 通过redis中间件实现C/S交互

- 多线程不阻塞

## 配置文件示例

```python
config = {
    'enable_proxy': False, # 是否启用代理
    'proxy': '', # 代理地址
    'bot_host': '', # CQbot后端地址
    'group_id': ('',), # 默认通知的QQ群
    'bot_token': '', # bot的token验证
    'ddir': '/home/ubuntu/Matsuri', # 视频下载地址
    'youtube_quality': '720p', # youtube下载画质
    'enable_upload': 'True', # 是否启用上传
    'upload_by': 'bd', # 上传方式
    's3_access_key': '', # s3上传access
    's3_secret_key': '', # s3上传secret
    'enable_mongodb': False, # 是否启用mongodb记录
    # 用户列表，用于与服务器识别和个别功能配置
    'users': [
        {
            'user': 'natsuiromatsuri', # 用户名称，注意与服务端保持一致
            'bot_notice': True, # 是否启动与bot提醒
            'download': True # 是否下载直播
        },
        {
            'user': 'bilibili',
            'ddir': '', # 下载至子目录
            'bot_notice': True,
            'download': False
        }
    ]
}
```
