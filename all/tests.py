from up9lib import *
from authentication import authenticate

# logging.basicConfig(level=logging.DEBUG)


@data_driven_tests
class Tests_trdemo_client(unittest.TestCase):
  @json_dataset('data/test_9_get_cart_add.json')
  @clear_session({'spanId': 9})
  def test_9_get_cart_add(self, data_row):
    product_id, startDate, = data_row

    # endpoint 15
    qstr = '?' + urlencode([('destination', '*'), ('endDate', ''), ('source', '*'), ('startDate', startDate)])
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

  @json_dataset('data/test_10_get_flight.json')
  @clear_session({'spanId': 10})
  def test_10_get_flight(self, data_row):
    startDate, = data_row

    # endpoint 7
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', authenticate)
    resp = trdemo_client.get('/')
    resp.assert_status_code(200)
    resp.assert_cssselect('div.container-fluid div h1', expected_value='Welcome!')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

    # endpoint 8
    resp = trdemo_client.get('/cart')
    resp.assert_status_code(200)
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
    X_Original_Uri = cssselect('div.container-fluid div table.table.table-striped.table-responsive-md.btn-table tbody tr td a[href] @href', resp)

    # endpoint 15
    qstr = '?' + urlencode([('destination', '*'), ('endDate', ''), ('source', '*'), ('startDate', startDate)])
    resp = trdemo_client.get('/search' + qstr)
    resp.assert_status_code(200)
    resp.assert_cssselect('div#flightsearch-form form.form-search h1.h3.font-weight-normal', expected_value=' Search Flights')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
    flight_id = url_part('?product_id', cssselect('div.container-fluid div table.table.table-striped tbody tr td a[href] @href', resp))

    # endpoint 10
    qstr = '?' + urlencode([('flight_id', flight_id)])
    resp = trdemo_client.get('/flight' + qstr, headers=dict([('X-Original-Uri', X_Original_Uri)]))
    resp.assert_status_code(200)
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

  # authentication-related test
  @clear_session({'spanId': 12})
  def test_12_post_login(self):
    # endpoint 11
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', dummy_auth)
    resp = trdemo_client.get('/login')
    resp.assert_status_code(200)
    resp.assert_cssselect('div#logreg-forms h1.h3.font-weight-normal', expected_value=' Select user (temp) ')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
    user = cssselect('form#userform select.custom-select[name="user"] option[value] @value', resp)

    # endpoint 12
    resp = trdemo_client.post('/login', data=[('user', user)])
    resp.assert_status_code(302)
    resp.assert_cssselect('h1', expected_value='Redirecting...')
    resp.assert_cssselect('html head title', expected_value='Redirecting...')

  @clear_session({'spanId': 13})
  def test_13_get_logout(self):
    # endpoint 13
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', authenticate)
    resp = trdemo_client.get('/logout')
    resp.assert_status_code(200)
    resp.assert_cssselect('div.container-fluid div h1', expected_value='Welcome!')
    resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')

  @clear_session({'spanId': 14})
  def test_14_get_logout(self):
    # endpoint 14
    trdemo_client = get_http_target('TARGET_TRDEMO_CLIENT', authenticate)
    resp = trdemo_client.get('/logout')
    resp.assert_status_code(302)
    resp.assert_cssselect('h1', expected_value='Redirecting...')
    resp.assert_cssselect('html head title', expected_value='Redirecting...')

@data_driven_tests
class Tests_trdemo_shoppingcart(unittest.TestCase):
  @json_dataset('data/test_4_put_cart_email.json')
  @clear_session({'spanId': 4})
  def test_4_put_cart_email(self, data_row):
    param, = data_row

    # endpoint 1
    trdemo_users = get_http_target('TARGET_TRDEMO_USERS', authenticate)
    resp = trdemo_users.get('/user/all')
    resp.assert_status_code(200)
    _email = jsonpath('$.[*].email', resp)

    # endpoint 3
    trdemo_shoppingcart = get_http_target('TARGET_TRDEMO_SHOPPINGCART', authenticate)
    resp = trdemo_shoppingcart.get(f'/cart/{_email}')
    resp.assert_status_code(200)
    count = jsonpath('$.products.[*].count', resp)
    product_id = jsonpath('$.products.[*].product_id', resp)

    # endpoint 6
    trdemo_flights = get_http_target('TARGET_TRDEMO_FLIGHTS', authenticate)
    resp = trdemo_flights.get(f'/flight/{product_id}')
    resp.assert_status_code(200)

    # endpoint 5
    resp = trdemo_flights.get(f'/flight/{product_id}/{param}')
    resp.assert_status_code(200)
    product_id1 = jsonpath('$.[*].flight_id', resp)

    # endpoint 4
    with open('data/payload_for_endp_4.json', 'r') as json_payload_file:
        json_payload = json.load(json_payload_file)
    apply_into_json(json_payload, '$.count', count)
    apply_into_json(json_payload, '$.product_id', product_id1)
    resp = trdemo_shoppingcart.put(f'/cart/{_email}', json=json_payload)
    resp.assert_status_code(201)

@data_driven_tests
class Tests_trdemo_users(unittest.TestCase):
  @clear_session({'spanId': 2})
  def test_2_get_user_email(self):
    # endpoint 1
    trdemo_users = get_http_target('TARGET_TRDEMO_USERS', authenticate)
    resp = trdemo_users.get('/user/all')
    resp.assert_status_code(200)
    _email = jsonpath('$.[*].email', resp)

    # endpoint 2
    resp = trdemo_users.get(f'/user/{_email}')
    resp.assert_status_code(200)

