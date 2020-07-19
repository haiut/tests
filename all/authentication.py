from up9lib import *


def authenticate(target_key, target):
        if target_key == 'TARGET_TRDEMO_CLIENT':
            # endpoint 11
            resp = target.get('/login')
            resp.assert_status_code(200)
            resp.assert_cssselect('div#logreg-forms h1.h3.font-weight-normal', expected_value=' Select user (temp) ')
            resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
            user = cssselect('form#userform select.custom-select[name="user"] option[value] @value', resp)
        
            # endpoint 12
            resp = target.post('/login', data=[('user', user)])
            resp.assert_status_code(302)
            resp.assert_cssselect('h1', expected_value='Redirecting...')
            resp.assert_cssselect('html head title', expected_value='Redirecting...')
        
        else:
          pass
        


