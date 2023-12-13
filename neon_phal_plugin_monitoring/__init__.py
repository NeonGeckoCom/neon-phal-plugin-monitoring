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

from dataclasses import dataclass, asdict
from os import remove
from os.path import join, isfile
from time import time
from ovos_bus_client.message import Message
from ovos_utils.log import LOG
from ovos_utils.xdg_utils import xdg_data_home
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
        self._save_path = join(xdg_data_home(), get_xdg_base(),
                               "core_metrics.json")
        if self.save_local and isfile(self._save_path):
            try:
                with open(self._save_path) as f:
                    self._metrics = json.load(f)
                LOG.info(f"Loaded metrics from {self._save_path}")
            except Exception as e:
                LOG.exception(f"Failed to load {self._save_path}: {e}")
                remove(self._save_path)
        self.bus.on("neon.metric", self.on_metric)
        self.bus.on("neon.get_metric", self.get_metric)
        self.bus.on("neon.get_raw_metric", self.get_raw_metric)

    @property
    def save_local(self) -> bool:
        """
        Allow saving collected metrics locally, default True
        """
        return self.config.get("save_locally") is not False

    @property
    def max_num_history(self) -> int:
        """
        Get a maximum number of datapoints to handle in data parsing
        """
        return self.config.get("max_history") or 100

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
        metric_data = dict(message.data)
        try:
            metric_name = metric_data.pop("name")
            timestamp = message.context.get("timestamp") or time()
        except Exception as e:
            LOG.error(e)
            return
        metric = NeonMetric(metric_name, timestamp, metric_data)
        LOG.debug(f"Got metric: {metric}")
        self._metrics.setdefault(metric.name, list())
        self._metrics[metric_name].append(asdict(metric))
        # TODO: Support backends like InfluxDb
        if self.upload_enabled:
            report_metric(**asdict(metric))

    def get_raw_metric(self, message: Message):
        """
        Get values for the requested metric and emit them as a response
        @param message: `neon.get_raw_metric` Message
        """
        request = message.data.get("name")
        if request and request not in self._metrics:
            resp = message.response({"error": True,
                                     "message": f"{request} not found in "
                                                f"{self._metrics.keys()}"})
        elif not request:
            resp = message.response({"error": False, **self._metrics})
        else:
            resp = message.response({"error": False,
                                     request: self._metrics[request]})
        self.bus.emit(resp)

    def get_metric(self, message: Message):
        """
        Get parsed data for the requested metric
        @param message: `neon.get_metric` Message
        """
        request = message.data.get("name")
        if not request:
            resp = message.response({"error": True,
                                     "message": "A metric `name` is required"})
        elif request not in self._metrics:
            resp = message.response({"error": True,
                                     "message": f"{request} not found in "
                                                f"{self._metrics.keys()}"})
        else:
            LOG.debug(f"Generating response for metric: {request}")
            try:
                data: list = self._metrics[request]
                if len(data) > self.max_num_history:
                    LOG.info(f"Truncating data to {self.max_num_history} items")
                    data = data[-self.max_num_history:]
                flattened_lists = {}
                metrics = (d['data'] for d in data)
                for metric in metrics:
                    for key, val in metric.items():
                        if isinstance(val, dict):
                            for k, v in val.items():
                                flattened_lists.setdefault(f"{key}.{k}", list())
                                flattened_lists[f"{key}.{k}"].append(v)
                        else:
                            flattened_lists.setdefault(key, list())
                            flattened_lists[key].append(val)
                parsed_data = {k: {"min": min(v),
                                   "max": max(v),
                                   "avg": sum(v)/len(v)}
                               for k, v in flattened_lists.items()}
                resp = message.response({"error": False, **parsed_data})
            except Exception as e:
                LOG.exception(e)
                resp = message.response({"error": True,
                                         "message": repr(e)})
        self.bus.emit(resp)
        LOG.debug(f"Sent response: {resp.msg_type}")

    def _write_to_disk(self):
        # Truncate metrics to maximum configured length
        for name, metric in self._metrics.items():
            self._metrics[name] = metric[-self.max_num_history:]
        # Write metrics to disk
        with open(self._save_path, 'w+') as f:
            json.dump(self._metrics, f)
        LOG.info(f"Wrote metrics to {self._save_path}")

    def shutdown(self):
        if self.save_local:
            self._write_to_disk()
        PHALPlugin.shutdown(self)
