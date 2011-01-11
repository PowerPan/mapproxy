# This file is part of the MapProxy project.
# Copyright (C) 2010 Omniscale <http://omniscale.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement, division
import os

from mapproxy.request.wms import WMS111FeatureInfoRequest
from mapproxy.test.system import module_setup, module_teardown, SystemTest
from mapproxy.test.http import mock_httpd
from mapproxy.test.helper import strip_whitespace

from nose.tools import eq_

test_config = {}


xsl_input = """
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:template match="/">
   <baz>
     <foo><xsl:value-of select="/a/b/text()" /></foo>
   </baz>
 </xsl:template>
</xsl:stylesheet>""".strip()


xsl_output = """
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:template match="/">
    <bars>
      <xsl:apply-templates/> 
    </bars>
 </xsl:template>

 <xsl:template match="foo">
     <bar><xsl:value-of select="text()" /></bar>
 </xsl:template>
</xsl:stylesheet>""".strip()


def setup_module():
    module_setup(test_config, 'xsl_featureinfo.yaml')
    with open(os.path.join(test_config['base_dir'], 'fi_in.xsl'), 'w') as f:
        f.write(xsl_input)
    with open(os.path.join(test_config['base_dir'], 'fi_out.xsl'), 'w') as f:
        f.write(xsl_output)

def teardown_module():
    module_teardown(test_config)

TESTSERVER_ADDRESS = 'localhost', 42423

class TestWMSWithRoot(SystemTest):
    config = test_config
    def setup(self):
        SystemTest.setup(self)
        self.common_fi_req = WMS111FeatureInfoRequest(url='/service?',
            param=dict(x='10', y='20', width='200', height='200', layers='fi_layer',
                       format='image/png', query_layers='fi_layer', styles='',
                       bbox='1000,400,2000,1400', srs='EPSG:900913'))

    def test_get_featureinfo(self):
        fi_body = "<a><b>Bar</b></a>"
        expected_req = ({'path': r'/service_a?LAYERs=a_one&SERVICE=WMS&FORMAT=image%2Fpng'
                                  '&REQUEST=GetFeatureInfo&HEIGHT=200&SRS=EPSG%3A900913'
                                  '&VERSION=1.1.1&BBOX=1000.0,400.0,2000.0,1400.0&styles='
                                  '&WIDTH=200&QUERY_LAYERS=a_one&X=10&Y=20'},
                        {'body': fi_body, 'headers': {'content-type': 'text/plain'}})
        with mock_httpd(('localhost', 42423), [expected_req]):
            resp = self.app.get(self.common_fi_req)
            print resp.body
            eq_(resp.content_type, 'text/plain')
            eq_(strip_whitespace(resp.body), '<bars><bar>Bar</bar></bars>')

    def test_get_multiple_featureinfo(self):
        fi_body1 = "<a><b>Bar1</b></a>"
        fi_body2 = "<a><b>Bar2</b></a>"
        expected_req1 = ({'path': r'/service_a?LAYERs=a_one&SERVICE=WMS&FORMAT=image%2Fpng'
                                  '&REQUEST=GetFeatureInfo&HEIGHT=200&SRS=EPSG%3A900913'
                                  '&VERSION=1.1.1&BBOX=1000.0,400.0,2000.0,1400.0&styles='
                                  '&WIDTH=200&QUERY_LAYERS=a_one&X=10&Y=20'},
                        {'body': fi_body1, 'headers': {'content-type': 'text/plain'}})
        expected_req2 = ({'path': r'/service_b?LAYERs=b_one&SERVICE=WMS&FORMAT=image%2Fpng'
                                  '&REQUEST=GetFeatureInfo&HEIGHT=200&SRS=EPSG%3A900913'
                                  '&VERSION=1.1.1&BBOX=1000.0,400.0,2000.0,1400.0&styles='
                                  '&WIDTH=200&QUERY_LAYERS=b_one&X=10&Y=20'},
                        {'body': fi_body2, 'headers': {'content-type': 'text/plain'}})
        with mock_httpd(('localhost', 42423), [expected_req1, expected_req2]):
            self.common_fi_req.params['layers'] = 'fi_multi_layer'
            self.common_fi_req.params['query_layers'] = 'fi_multi_layer'
            resp = self.app.get(self.common_fi_req)
            print resp.body
            eq_(resp.content_type, 'text/plain')
            eq_(strip_whitespace(resp.body),
                '<bars><bar>Bar1</bar><bar>Bar2</bar></bars>')