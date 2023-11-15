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

from neon_phal_plugin_monitoring import CoreMonitor
from ovos_utils.messagebus import FakeBus


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


if __name__ == '__main__':
    unittest.main()
