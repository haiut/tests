from up9lib import *
from authentication import authenticate

# logging.basicConfig(level=logging.DEBUG)


@data_driven_tests
class Tests_trdemo_client(unittest.TestCase):
  @clear_session({'spanId': 7})
  def test_7_get_(self):
    # endpoint 7
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', authenticate)
    resp = trdemo_client.get('/')
    resp.assert_status_code(200)
    resp.assert_cssselect('div.container-fluid div h1', expected_value='Welcome!')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

  @json_dataset('data/test_9_get_cart_add.json')
  @clear_session({'spanId': 9})
  def test_9_get_cart_add(self, data_row):
    product_id, source, startDate, = data_row

    # endpoint 15
    qstr = '?' + urlencode([('destination', '*'), ('endDate', ''), ('source', source), ('startDate', startDate)])
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', authenticate)
    resp = trdemo_client.get('/search' + qstr)
    resp.assert_status_code(200)
    resp.assert_cssselect('div#flightsearch-form form.form-search h1.h3.font-weight-normal', expected_value=' Search Flights')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
    X_Original_Uri = cssselect('div.container-fluid div table.table.table-striped tbody tr td a[href] @href', resp)

    # endpoint 9
    qstr = '?' + urlencode([('product_id', product_id)])
    resp = trdemo_client.get('/cart/add' + qstr, headers=dict([('X-Original-Uri', X_Original_Uri)]))
    resp.assert_status_code(302)
    resp.assert_cssselect('h1', expected_value='Redirecting...')
    resp.assert_cssselect('html head title', expected_value='Redirecting...')

  # authentication-related test
  @clear_session({'spanId': 11})
  def test_11_get_login(self):
    # endpoint 11
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', dummy_auth)
    resp = trdemo_client.get('/login')
    resp.assert_status_code(200)
    resp.assert_cssselect('div#logreg-forms h1.h3.font-weight-normal', expected_value=' Select user (temp) ')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

@data_driven_tests
class Tests_trdemo_flights(unittest.TestCase):
  @json_dataset('data/test_4_get_flight_product_id_param.json')
  @clear_session({'spanId': 4})
  def test_4_get_flight_product_id_param(self, data_row):
    param, = data_row

    # endpoint 2
    trdemo_users = get_http_target('TARGET_TRDEMO_USERS', authenticate)
    resp = trdemo_users.get('/user/all')
    resp.assert_status_code(200)
    _email = jsonpath('$.[*].email', resp)

    # endpoint 3
    trdemo_shoppingcart = get_http_target('TARGET_TRDEMO_SHOPPINGCART', authenticate)
    resp = trdemo_shoppingcart.get(f'/cart/{_email}')
    resp.assert_status_code(200)
    product_id = jsonpath('$.products.[*].product_id', resp)

    # endpoint 4
    trdemo_flights = get_http_target('TARGET_TRDEMO_FLIGHTS', authenticate)
    resp = trdemo_flights.get(f'/flight/{product_id}/{param}')
    resp.assert_status_code(200)

@data_driven_tests
class Tests_trdemo_users(unittest.TestCase):
  @clear_session({'spanId': 1})
  def test_1_get_user_email(self):
    # endpoint 2
    trdemo_users = get_http_target('TARGET_TRDEMO_USERS', authenticate)
    resp = trdemo_users.get('/user/all')
    resp.assert_status_code(200)
    _email = jsonpath('$.[*].email', resp)

    # endpoint 1
    resp = trdemo_users.get(f'/user/{_email}')
    resp.assert_status_code(200)
    resp.assert_jsonpath('$.airport', expected_value='TLV')

