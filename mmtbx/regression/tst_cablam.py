from __future__ import division
#from mmtbx.kinemage import validation
from mmtbx.cablam import cablam_annote, cablam_res, cablam_math
#import cablam_annote, cablam_res, cablam_math
from libtbx.test_utils import show_diff
from iotbx import pdb
import libtbx.load_env
import os

ref_cablam_annote_text = """pdb:chainID:resnum:1st:2nd:3rd:4th:5th:6th:7th:8th
pdb103l.ent:  :   3:H 0.4305:T 0.3676:S 0.0358:G 0.0345:E 0.0010:B 0.0002:X 0.0001:I 0.0000
pdb103l.ent:  :   4:H 0.9810:T 0.0062:G 0.0038:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  :   5:H 0.9913:T 0.0036:G 0.0021:S 0.0002:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :   6:H 0.9447:T 0.0251:G 0.0145:S 0.0009:E 0.0001:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  :   7:H 0.9416:T 0.0292:G 0.0152:S 0.0032:E 0.0002:X 0.0001:I 0.0001:B 0.0000
pdb103l.ent:  :   8:H 0.8657:G 0.0783:T 0.0299:S 0.0005:E 0.0002:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :   9:H 0.9906:T 0.0038:G 0.0017:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  :  10:H 0.8299:T 0.1028:G 0.0106:S 0.0084:I 0.0009:E 0.0002:X 0.0001:B 0.0001
pdb103l.ent:  :  11:S 0.4115:H 0.2430:T 0.1182:X 0.0788:E 0.0611:B 0.0162:G 0.0039:I 0.0002
pdb103l.ent:  :  12:X 0.8504:E 0.1166:B 0.0289:H 0.0011:T 0.0008:S 0.0003:G 0.0001:I 0.0000
pdb103l.ent:  :  13:X 0.5354:E 0.4724:B 0.0281:T 0.0124:S 0.0028:G 0.0004:H 0.0000:I 0.0000
pdb103l.ent:  :  14:E 0.8112:X 0.1826:B 0.0082:T 0.0001:G 0.0000:S 0.0000:I 0.0000:H 0.0000
pdb103l.ent:  :  15:T 0.3197:H 0.2165:G 0.1379:S 0.0828:X 0.0489:E 0.0098:B 0.0001:I 0.0000
pdb103l.ent:  :  16:S 0.8921:B 0.0506:E 0.0434:X 0.0104:T 0.0071:G 0.0007:H 0.0003:I 0.0000
pdb103l.ent:  :  17:X 0.4538:E 0.3993:T 0.0498:B 0.0177:S 0.0029:G 0.0013:H 0.0000:I 0.0000
pdb103l.ent:  :  18:E 0.7341:X 0.2589:B 0.0332:T 0.0001:G 0.0001:S 0.0000:H 0.0000:I 0.0000
pdb103l.ent:  :  19:X 0.6607:E 0.2734:B 0.0653:T 0.0008:S 0.0001:G 0.0000:I 0.0000:H 0.0000
pdb103l.ent:  :  20:X 0.8628:E 0.1199:B 0.0325:H 0.0021:T 0.0012:G 0.0001:S 0.0001:I 0.0000
pdb103l.ent:  :  21:T 0.5679:S 0.3229:H 0.1634:G 0.0193:E 0.0084:B 0.0011:X 0.0006:I 0.0002
pdb103l.ent:  :  22:T 0.6408:G 0.1635:H 0.1102:S 0.0536:B 0.0025:E 0.0011:X 0.0003:I 0.0001
pdb103l.ent:  :  23:T 0.4410:S 0.3021:X 0.1106:E 0.0127:G 0.0028:B 0.0025:H 0.0000:I 0.0000
pdb103l.ent:  :  24:X 0.8981:S 0.0472:E 0.0440:B 0.0310:T 0.0001:H 0.0001:G 0.0000:I 0.0000
pdb103l.ent:  :  25:X 0.4548:E 0.2814:T 0.2253:S 0.0232:B 0.0179:G 0.0010:H 0.0000:I 0.0000
pdb103l.ent:  :  26:E 0.7824:X 0.1856:B 0.0154:T 0.0004:S 0.0003:G 0.0001:I 0.0000:H 0.0000
pdb103l.ent:  :  27:E 0.5738:X 0.3440:T 0.0334:B 0.0290:S 0.0153:G 0.0032:H 0.0016:I 0.0000
pdb103l.ent:  :  28:S 0.2700:T 0.2278:H 0.1560:G 0.1026:E 0.0849:B 0.0145:I 0.0011:X 0.0003
pdb103l.ent:  :  29:T 0.8302:S 0.0852:G 0.0553:B 0.0289:E 0.0093:H 0.0069:X 0.0001:I 0.0000
pdb103l.ent:  :  30:T 0.4539:S 0.2089:G 0.1171:X 0.1048:E 0.0600:H 0.0075:B 0.0067:I 0.0000
pdb103l.ent:  :  31:X 0.8778:E 0.1176:B 0.0274:S 0.0003:T 0.0001:G 0.0001:H 0.0000:I 0.0000
pdb103l.ent:  :  32:E 0.8486:X 0.1287:B 0.0078:T 0.0007:S 0.0000:G 0.0000:I 0.0000:H 0.0000
pdb103l.ent:  :  40:H 0.9914:G 0.0018:T 0.0017:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  41:H 0.9962:T 0.0105:G 0.0075:S 0.0004:E 0.0001:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  42:H 0.9942:T 0.0012:G 0.0012:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  43:H 0.9924:G 0.0042:T 0.0028:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  44:H 0.9928:T 0.0027:G 0.0019:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  45:H 0.9953:G 0.0017:T 0.0016:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  46:H 0.9899:G 0.0036:T 0.0026:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  47:H 0.9935:G 0.0015:T 0.0014:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  48:H 0.9936:G 0.0015:T 0.0014:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  49:H 0.8816:T 0.0594:G 0.0208:S 0.0019:I 0.0001:E 0.0001:X 0.0001:B 0.0000
pdb103l.ent:  :  50:H 0.4103:T 0.3517:S 0.0870:G 0.0170:E 0.0036:X 0.0025:B 0.0020:I 0.0001
pdb103l.ent:  :  51:S 0.5070:G 0.1887:T 0.1792:H 0.0421:X 0.0141:E 0.0100:B 0.0009:I 0.0000
pdb103l.ent:  :  52:S 0.7035:E 0.1795:B 0.0431:X 0.0288:T 0.0009:H 0.0001:G 0.0000:I 0.0000
pdb103l.ent:  :  53:X 0.5268:E 0.2677:T 0.1685:G 0.0286:B 0.0246:S 0.0228:H 0.0002:I 0.0000
pdb103l.ent:  :  54:X 0.8014:E 0.2069:B 0.0230:T 0.0002:S 0.0002:G 0.0001:H 0.0000:I 0.0000
pdb103l.ent:  :  55:T 0.5044:X 0.1638:E 0.1522:S 0.1435:G 0.0230:B 0.0162:H 0.0039:I 0.0000
pdb103l.ent:  :  56:T 0.7966:S 0.1395:G 0.0327:H 0.0040:E 0.0040:X 0.0007:B 0.0006:I 0.0000
pdb103l.ent:  :  57:E 0.5391:X 0.4446:B 0.0260:T 0.0004:S 0.0001:H 0.0000:G 0.0000:I 0.0000
pdb103l.ent:  :  58:E 0.7279:X 0.2126:B 0.0278:T 0.0001:S 0.0001:G 0.0000:I 0.0000:H 0.0000
pdb103l.ent:  :  59:X 0.8214:E 0.1232:B 0.0360:T 0.0003:S 0.0000:G 0.0000:H 0.0000:I 0.0000
pdb103l.ent:  :  60:H 0.6388:T 0.1531:G 0.0636:S 0.0214:E 0.0005:X 0.0000:B 0.0000:I 0.0000
pdb103l.ent:  :  61:H 0.9795:G 0.0067:T 0.0034:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  62:H 0.9939:G 0.0016:T 0.0015:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  63:H 0.9931:G 0.0021:T 0.0015:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  64:H 0.9803:G 0.0081:T 0.0055:S 0.0003:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  65:H 0.9716:G 0.0088:T 0.0057:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  66:H 0.9926:T 0.0020:G 0.0017:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  67:H 0.9820:G 0.0056:T 0.0029:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  68:H 0.9934:G 0.0016:T 0.0015:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  69:H 0.9945:T 0.0012:G 0.0011:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  70:H 0.9892:T 0.0081:G 0.0061:S 0.0004:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  71:H 0.9950:G 0.0015:T 0.0014:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  72:H 0.9936:G 0.0017:T 0.0013:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  73:H 0.9908:G 0.0035:T 0.0027:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  74:H 0.9912:G 0.0024:T 0.0022:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  75:H 0.9939:T 0.0020:G 0.0013:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  76:H 0.9939:T 0.0016:G 0.0014:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  77:H 0.9899:G 0.0030:T 0.0018:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  78:H 0.9931:G 0.0014:T 0.0014:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  79:H 0.9938:T 0.0020:G 0.0013:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  80:T 0.4467:G 0.2735:H 0.1473:S 0.0178:X 0.0013:E 0.0012:B 0.0001:I 0.0000
pdb103l.ent:  :  81:X 0.7320:E 0.1639:S 0.0585:B 0.0311:T 0.0011:H 0.0002:G 0.0001:I 0.0000
pdb103l.ent:  :  82:S 0.3026:T 0.2933:H 0.2896:G 0.0176:X 0.0164:E 0.0123:B 0.0003:I 0.0003
pdb103l.ent:  :  83:H 0.9263:T 0.0433:G 0.0065:S 0.0033:I 0.0003:E 0.0001:X 0.0001:B 0.0000
pdb103l.ent:  :  84:H 0.5524:T 0.2772:G 0.0760:S 0.0748:E 0.0028:I 0.0007:X 0.0007:B 0.0002
pdb103l.ent:  :  85:H 0.5843:G 0.4075:T 0.1727:S 0.0132:E 0.0018:X 0.0003:I 0.0001:B 0.0001
pdb103l.ent:  :  86:H 0.9939:T 0.0015:G 0.0014:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  87:H 0.9945:T 0.0015:G 0.0011:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  88:H 0.9915:G 0.0023:T 0.0018:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  89:H 0.9689:G 0.0133:T 0.0064:S 0.0002:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  90:T 0.3957:G 0.3016:H 0.1270:S 0.0154:E 0.0012:X 0.0012:B 0.0001:I 0.0000
pdb103l.ent:  :  91:S 0.6602:E 0.1588:X 0.0980:B 0.0507:T 0.0002:G 0.0001:H 0.0001:I 0.0000
pdb103l.ent:  :  92:X 0.8714:E 0.0755:B 0.0220:T 0.0006:S 0.0004:H 0.0003:G 0.0000:I 0.0000
pdb103l.ent:  :  93:H 0.5658:T 0.2993:S 0.0578:G 0.0396:E 0.0020:B 0.0004:X 0.0001:I 0.0000
pdb103l.ent:  :  94:H 0.9853:T 0.0086:G 0.0037:S 0.0005:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  :  95:H 0.9662:G 0.0158:T 0.0135:S 0.0008:E 0.0001:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  96:H 0.7706:G 0.1658:T 0.0499:S 0.0008:E 0.0004:X 0.0001:I 0.0000:B 0.0000
pdb103l.ent:  :  97:H 0.9722:G 0.0108:T 0.0047:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  98:H 0.9823:G 0.0053:T 0.0030:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  :  99:H 0.9936:G 0.0017:T 0.0016:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 100:H 0.9819:G 0.0069:T 0.0036:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 101:H 0.9795:G 0.0066:T 0.0040:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 102:H 0.9951:T 0.0014:G 0.0012:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 103:H 0.9932:G 0.0019:T 0.0017:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 104:H 0.9576:T 0.0192:G 0.0121:S 0.0005:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 105:H 0.7787:T 0.1203:S 0.0208:G 0.0035:I 0.0026:E 0.0004:B 0.0004:X 0.0001
pdb103l.ent:  : 106:H 0.5261:T 0.2474:S 0.1687:G 0.0228:E 0.0206:B 0.0118:X 0.0072:I 0.0004
pdb103l.ent:  : 107:X 0.8786:E 0.0919:B 0.0256:H 0.0021:T 0.0015:S 0.0006:G 0.0001:I 0.0000
pdb103l.ent:  : 108:T 0.4508:H 0.3363:G 0.0328:S 0.0311:E 0.0009:B 0.0001:X 0.0001:I 0.0000
pdb103l.ent:  : 109:H 0.9837:G 0.0114:T 0.0111:S 0.0005:E 0.0001:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 110:H 0.9870:T 0.0047:G 0.0026:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 111:H 0.9087:T 0.0381:G 0.0341:S 0.0035:E 0.0004:X 0.0001:I 0.0001:B 0.0000
pdb103l.ent:  : 112:H 0.4403:G 0.3656:T 0.0864:S 0.0018:E 0.0007:X 0.0001:I 0.0000:B 0.0000
pdb103l.ent:  : 113:T 0.4442:G 0.3430:H 0.0784:S 0.0163:X 0.0022:E 0.0018:B 0.0001:I 0.0000
pdb103l.ent:  : 114:X 0.9281:E 0.0557:S 0.0329:B 0.0262:T 0.0196:G 0.0157:H 0.0033:I 0.0000
pdb103l.ent:  : 115:H 0.3550:T 0.2247:X 0.1956:S 0.0530:E 0.0433:G 0.0158:B 0.0006:I 0.0001
pdb103l.ent:  : 116:H 0.9938:T 0.0022:G 0.0012:S 0.0001:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 117:H 0.9894:G 0.0030:T 0.0023:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 118:H 0.9741:G 0.0112:T 0.0061:S 0.0002:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 119:H 0.9933:G 0.0022:T 0.0016:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 120:H 0.9922:G 0.0020:T 0.0018:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 121:H 0.9936:G 0.0015:T 0.0013:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 122:H 0.9902:G 0.0023:T 0.0017:S 0.0000:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 123:T 0.6611:H 0.1861:G 0.0175:S 0.0138:B 0.0004:E 0.0003:X 0.0002:I 0.0000
pdb103l.ent:  : 124:T 0.5109:X 0.3676:E 0.0204:S 0.0164:B 0.0039:G 0.0001:I 0.0000:H 0.0000
pdb103l.ent:  : 125:X 0.9195:E 0.1270:B 0.0269:T 0.0006:G 0.0003:S 0.0001:H 0.0000:I 0.0000
pdb103l.ent:  : 126:X 0.2797:H 0.2395:T 0.1995:S 0.1843:E 0.0657:G 0.0161:B 0.0011:I 0.0002
pdb103l.ent:  : 127:H 0.9939:T 0.0021:G 0.0011:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 128:H 0.9794:T 0.0171:G 0.0130:S 0.0012:E 0.0001:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 129:H 0.9752:G 0.0103:T 0.0052:S 0.0002:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 130:H 0.9659:G 0.0114:T 0.0063:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 131:H 0.9934:T 0.0028:G 0.0013:S 0.0001:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 132:H 0.9873:T 0.0041:G 0.0039:S 0.0002:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 133:H 0.7881:G 0.1156:T 0.0405:S 0.0010:E 0.0004:X 0.0001:I 0.0000:B 0.0000
pdb103l.ent:  : 134:G 0.3769:T 0.2873:H 0.1745:S 0.0093:E 0.0018:X 0.0005:B 0.0000:I 0.0000
pdb103l.ent:  : 135:T 0.4498:G 0.3119:X 0.1370:S 0.0916:H 0.0208:E 0.0060:B 0.0021:I 0.0000
pdb103l.ent:  : 136:S 0.4700:E 0.2798:X 0.1802:B 0.0545:G 0.0002:T 0.0001:H 0.0000:I 0.0000
pdb103l.ent:  : 137:H 0.4908:T 0.1826:G 0.1786:S 0.0443:E 0.0009:X 0.0001:B 0.0001:I 0.0000
pdb103l.ent:  : 138:H 0.8451:G 0.0676:T 0.0307:S 0.0006:E 0.0001:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 139:H 0.9927:T 0.0033:G 0.0014:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 140:H 0.9870:T 0.0054:G 0.0024:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 141:H 0.7277:T 0.1542:S 0.0249:G 0.0061:I 0.0027:B 0.0006:E 0.0005:X 0.0001
pdb103l.ent:  : 142:X 0.3308:S 0.2345:T 0.2301:E 0.0934:H 0.0104:B 0.0091:G 0.0081:I 0.0001
pdb103l.ent:  : 143:H 0.3572:T 0.2401:X 0.1914:S 0.0547:G 0.0327:E 0.0320:B 0.0004:I 0.0001
pdb103l.ent:  : 144:H 0.9696:T 0.0099:G 0.0062:S 0.0003:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 145:H 0.9894:T 0.0058:G 0.0019:S 0.0004:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 146:H 0.9896:G 0.0031:T 0.0020:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 147:H 0.9744:G 0.0104:T 0.0045:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 148:H 0.9668:T 0.0152:G 0.0104:S 0.0006:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 149:H 0.9917:T 0.0035:G 0.0016:S 0.0002:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 150:H 0.9888:G 0.0033:T 0.0021:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 151:H 0.9869:G 0.0066:T 0.0036:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 152:H 0.9801:G 0.0049:T 0.0044:S 0.0001:E 0.0000:X 0.0000:I 0.0000:B 0.0000
pdb103l.ent:  : 153:H 0.9948:T 0.0026:G 0.0013:S 0.0001:E 0.0000:I 0.0000:X 0.0000:B 0.0000
pdb103l.ent:  : 154:H 0.6979:T 0.1918:G 0.0176:S 0.0155:I 0.0015:B 0.0003:E 0.0003:X 0.0001
pdb103l.ent:  : 155:H 0.3873:T 0.3213:S 0.1828:E 0.0215:X 0.0158:G 0.0097:B 0.0069:I 0.0003
pdb103l.ent:  : 156:S 0.5548:X 0.1971:T 0.1411:E 0.0228:G 0.0052:B 0.0027:H 0.0007:I 0.0000
pdb103l.ent:  : 157:X 0.3154:S 0.3040:E 0.2772:B 0.0402:T 0.0002:G 0.0001:H 0.0001:I 0.0000
pdb103l.ent:  : 158:T 0.4112:S 0.3172:X 0.1118:E 0.0110:B 0.0020:G 0.0004:H 0.0000:I 0.0000
pdb103l.ent:  : 159:H 0.3794:T 0.1899:G 0.1526:X 0.0729:S 0.0291:E 0.0014:B 0.0003:I 0.0001
pdb103l.ent:  : 160:H 0.9135:G 0.0341:T 0.0163:S 0.0003:E 0.0001:X 0.0000:I 0.0000:B 0.0000
"""

class cablam_test_string():
  #I wrote the regression test to use a class with a custom .write() method as a
  #  proof of principle for learning OOP and to see if I could. Possible because
  #  all my print functions accept an optional writeto= variable.
  def write(self,string):
    self.test_cablam_annote_text += str(string)
  def __init__(self):
    self.test_cablam_annote_text = ""

def exercise_cablam():
  regression_pdb = libtbx.env.find_in_repositories(
    relative_path="phenix_regression/pdb/pdb103l.ent",
    test=os.path.isfile) #This is the same file used for tst_kinemage.py
  if (regression_pdb is None):
    print "Skipping exercise_cablam(): input pdb (pdb103l.ent) not available"
    return
  #-----
  output = cablam_test_string()
  pdb_io = pdb.input(regression_pdb)
  pdbid = os.path.basename(regression_pdb)
  hierarchy = pdb_io.construct_hierarchy()
  resdata = cablam_res.construct_linked_residues(
    hierarchy, targetatoms=["CA","O","C","N"], pdbid=pdbid)

  cablam_math.CApseudos(resdata, dodihedrals=True, doangles=True)

  dsspcodes = ['H','G','I','E','B','S','T','X']
  for dsspcode in dsspcodes:
    cablam_annote.annote_dssp_3d(resdata,dsspcode)

  reskeys = resdata.keys()
  reskeys.sort()

  cablam_annote.print_annoted_text_human(resdata, writeto=output)
  assert not show_diff(output.test_cablam_annote_text, ref_cablam_annote_text)

def run():
  ##if (not libtbx.env.has_module(name="probe")):
  ##  print \
  ##    "Skipping kinemage test:" \
  ##    " probe not available"
  ##elif (not libtbx.env.has_module(name="reduce")):
  ##  print \
  ##    "Skipping kinemage test:" \
  ##    " reduce not available"
  ##else:
  ##  exercise_kinemage()
  ##print "OK"
  exercise_cablam()
  print "OK"

if (__name__ == "__main__"):
  run()
