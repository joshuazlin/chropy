
import unittest
import chropy

class UtilsTests(unittest.TestCase):
    
    def test_finv(self):
        #finv will try and make the matched groups go as far to the right as possible        
        assert chropy.finv("yxxy","{a}x{b}") == {'a':'yx','b':'y'}

        #You don't need to 'match onto the whole string', and groups will fill up as much as possible
        assert chropy.finv("yxy","{a}x") == {'a':'y'}
        
        #Typical use-case
        assert chropy.finv("prop_2+1f_24nt64_IWASAKI_b2.13_ls16_M1.8_ms0.04_mu0.005_mv0.005_srcx8y8z8t5.975",
                 "ms{ms}_mu{mu}_mv{mv}_srcx{x}y{y}z{z}t{t}.{cfg}") == \
                 {'ms':'0.04','mu':'0.005','mv':'0.005','x':'8','y':'8','z':'8','t':'5','cfg':'975'}
        

    def test_split_list(self):
        test_list = list(range(5))
        assert chropy.split_list(test_list,1) == [[0,1,2,3,4]]
        assert chropy.split_list(test_list,2) == [[0,1],[2,3,4]]
        assert chropy.split_list(test_list,5) == [[0],[1],[2],[3],[4]]
        self.assertRaises(Exception,chropy.split_list,test_list,6)
