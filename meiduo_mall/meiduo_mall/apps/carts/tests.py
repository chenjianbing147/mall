from django.test import TestCase

# Create your tests here.

import pickle
import base64

if __name__ == '__main__':

    dict = {
        'name':'zs',
        'age':123
    }


    # python中常见的类型转为bytes
    result = pickle.dumps(dict)
    print(type(result), result)

    result1 = base64.b64encode(result)
    print(type(result1), result1)

    # result2 = base64.b64decode(result1)
    result2 = result1.decode()

    print(type(result2), result2)


    result3 = result2.encode()
    print(type(result3), result3)

    result4 = base64.b64decode(result3)
    print(type(result4), result4)
