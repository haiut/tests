from up9lib import *


def authenticate(target_key, target):
        if target_key == 'TARGET_TRDEMO_HAIUT_DEV_SPYD_IO':
            # endpoint 4
            resp = target.get('/login')
            resp.assert_status_code(200)
            resp.assert_cssselect('div#logreg-forms h1.h3.font-weight-normal', expected_value=' Select user (temp) ')
            resp.assert_cssselect('html head title', expected_value=' TestR Demo app ')
            user = cssselect('form#userform select.custom-select[name="user"] option[value] @value', resp)
        
            # endpoint 5
            resp = target.post('/login', data=[('user', user)])
            resp.assert_status_code(302)
        
        else:
          pass
        


