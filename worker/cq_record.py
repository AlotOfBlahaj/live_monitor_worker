from config import config


def txt_recorder(event_info, video_dict):
    with open(f'{config["cq_ddir"]}/{video_dict["Title"]}.txt', 'a') as f:
        f.write(f"{event_info['time']}: {event_info['msg']} \n")
    print(f"{event_info['time']}: {event_info['msg']}")