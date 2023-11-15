# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json

from dataclasses import dataclass
from os import remove
from os.path import join, isfile
from time import time
from ovos_bus_client.message import Message
from ovos_utils.log import LOG
from ovos_utils.xdg_utils import xdg_state_home
from ovos_config.meta import get_xdg_base
from ovos_plugin_manager.phal import PHALPlugin
from neon_utils.metrics_utils import report_metric


@dataclass
class NeonMetric:
    name: str
    timestamp: float
    data: dict


class CoreMonitor(PHALPlugin):
    def __init__(self, bus=None, name="neon-phal-plugin-core-monitor",
                 config=None):
        PHALPlugin.__init__(self, bus, name, config)
        self._metrics = dict()
        self._save_path = join(xdg_state_home(), get_xdg_base(),
                               "core_metrics.json")
        if self.save_local and isfile(self._save_path):
            try:
                with open(self._save_path) as f:
                    self._metrics = json.load(f)
            except Exception as e:
                LOG.exception(f"Failed to load {self._save_path}: {e}")
                remove(self._save_path)
        self.bus.on("neon.metric", self.on_metric)

    @property
    def save_local(self) -> bool:
        """
        Allow saving collected metrics locally, default True
        """
        return self.config.get("save_locally") is not False

    @property
    def upload_enabled(self) -> bool:
        """
        Allow uploading collected metrics to a remote MQ server, default False
        """
        return self.config.get("upload_enabled") is True

    def on_metric(self, message: Message):
        """
        Handle a metric reported on the messagebus
        @param message: `neon.metric` Message
        """
        metric_data = message.data
        try:
            metric_name = metric_data.pop("name")
            timestamp = message.context.get("timestamp") or time()
        except Exception as e:
            LOG.error(e)
            return
        self._metrics.setdefault(metric_name, list())
        self._metrics[metric_name].append(NeonMetric(metric_name, timestamp,
                                                     metric_data))
        if self.upload_enabled:
            report_metric(name=metric_name, timestamp=timestamp, **metric_data)

    def shutdown(self):
        if self.save_local:
            with open(self._save_path, 'w+') as f:
                json.dump(self._metrics, f)
        PHALPlugin.shutdown(self)
