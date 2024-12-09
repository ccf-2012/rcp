from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class QbitConfig():
    # id : int
    qbitname : str 
    host : str
    port : str
    username : str 
    password : str
    docker_from : str 
    docker_to : str
    link_dir : str
    auto_delete : bool = False
    islocal : bool = True
    run_torcp_by_api : bool = False
    disk_free_margin : int = 5
    add_pause : bool = False
    default : bool = True

    def to_dict(self):
        return {
            'qbitname': self.qbitname,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'docker_from': self.docker_from,
            'docker_to': self.docker_to,
            'link_dir': self.link_dir,
            'auto_delete': self.auto_delete,
            'islocal': self.islocal,
        }
