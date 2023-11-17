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

import unittest
from time import time
from unittest.mock import Mock

from ovos_bus_client import Message

from neon_phal_plugin_monitoring import CoreMonitor
from ovos_utils.messagebus import FakeBus


_test_metrics = \
    {"local_interaction": [{"name": "local_interaction",
                            "timestamp": 1700178575.3139226,
                            "data": {"timestamps": {"handle_utterance": 1700178569.8474872, "speech_start": 1700178570.3148665, "audio_begin": 1700178572.6613815, "audio_end": 1700178575.1817648},
                                     "durations": {"save_transcript": 1.6450881958007812e-05, "text_parsers": 0.032979726791381836, "transform_utterance": 0.032979726791381836, "get_tts": 1.4289357662200928}}},
                           {"name": "local_interaction",
                            "timestamp": 1700181101.1420398,
                            "data": {"timestamps": {"handle_utterance": 1700181095.9473078, "speech_start": 1700181096.5109103, "audio_begin": 1700181098.4522712, "audio_end": 1700181100.8959959},
                                     "durations": {"save_transcript": 8.58306884765625e-06, "text_parsers": 0.03899049758911133, "transform_utterance": 0.03899049758911133, "get_tts": 1.2423529624938965}}},
                           {"name": "local_interaction",
                            "timestamp": 1700181115.9253693,
                            "data": {"timestamps": {"handle_utterance": 1700181107.428496, "speech_start": 1700181109.1827643, "audio_begin": 1700181111.1001081, "audio_end": 1700181115.734644},
                                     "durations": {"save_transcript": 1.0013580322265625e-05, "text_parsers": 0.03647017478942871, "transform_utterance": 0.03647017478942871, "get_tts": 1.5272321701049805}}},
                          ],
     "get_tts": [{"name": "get_tts",
                  "timestamp": 1700180250.5474644,
                  "data": {"duration": 1.339482307434082}},
                 {"name": "get_tts",
                  "timestamp": 1700180350.5474644,
                  "data": {"duration": 3.339482307434082}}
                 ]}


class PluginTests(unittest.TestCase):
    bus = FakeBus()
    plugin = CoreMonitor(bus)

    def test_properties(self):
        # Test default values
        self.plugin.config['save_locally'] = None
        self.plugin.config['upload_enabled'] = None
        self.assertTrue(self.plugin.save_local)
        self.assertFalse(self.plugin.upload_enabled)

        # Test explicitly enabled
        self.plugin.config['save_locally'] = True
        self.plugin.config['upload_enabled'] = True
        self.assertTrue(self.plugin.save_local)
        self.assertTrue(self.plugin.upload_enabled)

        # Test explicitly disabled
        self.plugin.config['save_locally'] = False
        self.plugin.config['upload_enabled'] = False
        self.assertFalse(self.plugin.save_local)
        self.assertFalse(self.plugin.upload_enabled)

        # Test invalid param uses default
        self.plugin.config['save_locally'] = ""
        self.plugin.config['upload_enabled'] = ""
        self.assertTrue(self.plugin.save_local)
        self.assertFalse(self.plugin.upload_enabled)

        self.assertIsInstance(self.plugin.max_num_history, int)

    def test_init(self):
        self.assertIsInstance(self.plugin._metrics, dict)
        for event in ("neon.metric", "neon.get_metric", "neon.get_raw_metric"):
            self.assertEqual(len(self.plugin.bus.ee.listeners(event)), 1)

    def test_on_metric(self):
        self.plugin._metrics = {}

        message = Message("neon.metric",
                          {"name": "test", "time1": time(), "time2": time()})
        self.plugin.on_metric(message)
        self.assertEqual(len(self.plugin._metrics['test']), 1)
        metric = self.plugin._metrics['test'][0]
        self.assertEqual(metric['name'], 'test')
        self.assertIsInstance(metric['timestamp'], float)
        self.assertEqual(set(metric['data'].keys()), {'time1', 'time2'})
        message.context['timestamp'] = time()
        self.plugin.on_metric(message)
        self.assertEqual(len(self.plugin._metrics['test']), 2)
        metric2 = self.plugin._metrics['test'][1]
        self.assertNotEqual(metric, metric2)
        self.assertEqual(metric['name'], metric2['name'])
        self.assertEqual(metric['data'], metric2['data'])
        self.assertEqual(metric2['timestamp'], message.context['timestamp'])

    def test_get_raw_metric(self):
        self.plugin._metrics = {"test": [{"name": "test",
                                          "timestamp": time(),
                                          "data": {"value": time()}}],
                                "test2": [{"name": "test",
                                           "timestamp": time(),
                                           "data": {"value": time()}},
                                          {"name": "test",
                                           "timestamp": time(),
                                           "data": {"value": time()}}
                                          ]}
        on_raw_metric = Mock()
        self.bus.on("neon.get_raw_metric.response", on_raw_metric)

        test_all_metrics = Message("neon.get_raw_metric")
        self.plugin.get_raw_metric(test_all_metrics)
        resp = on_raw_metric.call_args[0][0]
        self.assertEqual(resp.data, {**self.plugin._metrics, "error": False})

        test_valid_metric = Message("neon.get_raw_metric", {"name": "test2"})
        self.plugin.get_raw_metric(test_valid_metric)
        resp = on_raw_metric.call_args[0][0]
        self.assertEqual(resp.data, {"test2": self.plugin._metrics['test2'],
                                     "error": False})

        test_invalid_metric = Message("neon.get_raw_metric", {"name": "test0"})
        self.plugin.get_raw_metric(test_invalid_metric)
        resp = on_raw_metric.call_args[0][0]
        self.assertTrue(resp.data["error"])
        self.assertTrue(all((x in resp.data['message']
                             for x in self.plugin._metrics.keys())))

    def test_get_metric(self):
        self.plugin._metrics = _test_metrics
        on_metric = Mock()
        self.bus.on("neon.get_metric.response", on_metric)

        test_simple_metric = Message("neon.get_metric",
                                     {"name": "get_tts"})
        self.plugin.get_metric(test_simple_metric)
        resp = on_metric.call_args[0][0]
        self.assertFalse(resp.data['error'])
        self.assertEqual(set(resp.data['duration'].keys()),
                         {"min", "max", "avg"})

        test_nested_metrics = Message("neon.get_metric",
                                      {"name": "local_interaction"})
        self.plugin.get_metric(test_nested_metrics)
        resp = on_metric.call_args[0][0]
        self.assertFalse(resp.data['error'])
        for metric in ("timestamps.handle_utterance", "timestamps.speech_start",
                       "timestamps.audio_begin", "timestamps.audio_end",
                       "durations.save_transcript", "durations.text_parsers",
                       "durations.transform_utterance", "durations.get_tts"):
            self.assertEqual(set(resp.data[metric].keys()),
                             {"min", "max", "avg"})

        test_invalid_metric = Message("neon.get_metric", {"name": "test"})
        self.plugin.get_metric(test_invalid_metric)
        resp = on_metric.call_args[0][0]
        self.assertTrue(resp.data['error'])
        self.assertTrue(all((x in resp.data['message']
                             for x in self.plugin._metrics.keys())))

        test_missing_metric = Message("neon.get_metric")
        self.plugin.get_metric(test_missing_metric)
        resp = on_metric.call_args[0][0]
        self.assertTrue(resp.data['error'])

    def test_write_to_disk(self):
        # TODO
        pass

    def test_shutdown(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
