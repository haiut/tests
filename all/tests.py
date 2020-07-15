from up9lib import *
from authentication import authenticate

# logging.basicConfig(level=logging.DEBUG)


@data_driven_tests
class Tests_trdemo_haiut_dev_spyd_io(unittest.TestCase):
  @clear_session({'spanId': 1})
  def test_1_get_(self):
    # endpoint 1
    trdemo_haiut_dev_spyd_io = get_http_target('TARGET_TRDEMO_HAIUT_DEV_SPYD_IO', authenticate)
    resp = trdemo_haiut_dev_spyd_io.get('/')
    resp.assert_status_code(200)
    resp.assert_cssselect('div.container-fluid div h1', expected_value='Welcome!')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

  @clear_session({'spanId': 3})
  def test_3_get_cart(self):
    # endpoint 3
    trdemo_haiut_dev_spyd_io = get_http_target('TARGET_TRDEMO_HAIUT_DEV_SPYD_IO', authenticate)
    resp = trdemo_haiut_dev_spyd_io.get('/cart')
    resp.assert_status_code(200)
    resp.assert_cssselect('div.container-fluid div h2', expected_value='Cart for alex.haiut@testr.io')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

  # authentication-related test
  @clear_session({'spanId': 5})
  def test_5_post_login(self):
    # endpoint 4
    trdemo_haiut_dev_spyd_io = get_http_target('TARGET_TRDEMO_HAIUT_DEV_SPYD_IO', dummy_auth)
    resp = trdemo_haiut_dev_spyd_io.get('/login')
    resp.assert_status_code(200)
    resp.assert_cssselect('div#logreg-forms h1.h3.font-weight-normal', expected_value=' Select user (temp) ')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
    user = cssselect('form#userform select.custom-select[name="user"] option[value] @value', resp)

    # endpoint 5
    resp = trdemo_haiut_dev_spyd_io.post('/login', data=[('user', user)])
    resp.assert_status_code(302)

  @clear_session({'spanId': 6})
  def test_6_get_(self):
    # endpoint 6
    trdemo_haiut_dev_spyd_io = get_http_target('TARGET_TRDEMO_HAIUT_DEV_SPYD_IO', authenticate)
    resp = trdemo_haiut_dev_spyd_io.get('/')
    resp.assert_status_code(307)

