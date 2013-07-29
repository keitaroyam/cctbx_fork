"""
Below are flex arrays with x,y,z points for numerical integration on a sphere with unit weights, a so called
spherical t-design

The design implemented below contains 241 points and provides exact integrals over the surface for polynomial
functions on that sphere up to order 21.

The design has been taken from

http://www2.research.att.com/~njas/sphdesigns/dim3/

"""

from scitbx.array_family import flex

t_x = flex.double([ 0.892653535763 , 0.412534053425 , -0.892653535806 , -0.181618610614 , -0.412534053477 , -0.181618610451 , -0.412534053317 , 0.1816186104 , 0.412534053328 , 0.181618610581 , 0.892653535868 , -0.892653535855 , -0.292093742593 , -0.295767028027 , 0.292093742448 , 0.909507070148 , 0.295767028145 , 0.909507070189 , 0.295767027907 , -0.909507070101 , -0.295767027835 , -0.909507070219 , -0.292093742541 , 0.292093742862 , -0.575225718038 , 0.0241205727861 , 0.575225718116 , 0.817639022556 , -0.0241205730415 , 0.817639022458 , -0.0241205728182 , -0.817639022544 , 0.024120572713 , -0.8176390226 , -0.575225717925 , 0.575225717908 , -0.128833161725 , 0.0522476406944 , 0.12883316184 , 0.99028894795 , -0.0522476403885 , 0.990288947978 , -0.0522476403904 , -0.990288947961 , 0.0522476405278 , -0.990288947971 , -0.12883316179 , 0.128833161857 , 0.718006386035 , 0.657446876287 , -0.718006386109 , -0.228539787737 , -0.657446876241 , -0.228539787679 , -0.657446876361 , 0.228539787703 , 0.657446876304 , 0.228539787785 , 0.718006385881 , -0.718006385891 , 0.863176473118 , 0.468181816438 , -0.863176473194 , 0.189029529126 , -0.468181816393 , 0.189029528792 , -0.468181816411 , -0.189029528898 , 0.468181816509 , -0.189029529002 , 0.863176473135 , -0.863176473123 , 0.772632856847 , -0.517059450567 , -0.772632856806 , 0.368358511648 , 0.517059450494 , 0.36835851172 , 0.517059450583 , -0.368358511567 , -0.517059450502 , -0.36835851147 , 0.772632856935 , -0.772632856927 , -0.847819231915 , -0.0663257759136 , 0.847819231883 , -0.526121128349 , 0.0663257758461 , -0.526121128459 , 0.0663257759458 , 0.52612112845 , -0.0663257758772 , 0.526121128505 , -0.847819231822 , 0.84781923185 , 0.00980574322923 , 0.942983815809 , -0.00980574337969 , 0.332694109227 , -0.942983815774 , 0.332694109398 , -0.942983815776 , -0.332694109319 , 0.942983815775 , -0.332694109456 , 0.00980574330114 , -0.00980574328771 , 0.785599248371 , -0.405156944932 , -0.785599248202 , -0.467634120611 , 0.405156945136 , -0.467634120812 , 0.405156944842 , 0.467634120787 , -0.405156945 , 0.467634120894 , 0.785599248313 , -0.785599248281 , -0.737331999131 , 0.620851500949 , 0.73733199906 , -0.266242251949 , -0.620851501079 , -0.266242252012 , -0.620851501072 , 0.266242252114 , 0.620851501187 , 0.266242251932 , -0.737331998948 , 0.737331998835 , 0.726871469166 , -0.0274882821828 , -0.726871469173 , -0.68622318645 , 0.0274882823516 , -0.686223186546 , 0.0274882822668 , 0.686223186661 , -0.027488282251 , 0.686223186609 , 0.72687146907 , -0.72687146908 , 0.665363385721 , 0.580860267577 , -0.665363385677 , 0.468927408341 , -0.580860267528 , 0.468927408373 , -0.580860267641 , -0.468927408468 , 0.580860267387 , -0.468927408376 , 0.665363385652 , -0.665363385752 , -0.580125367305 , -0.779099598054 , 0.580125367187 , 0.237609710696 , 0.779099598065 , 0.237609710819 , 0.77909959817 , -0.237609710812 , -0.779099598075 , -0.237609710609 , -0.58012536709 , 0.580125367218 , 0.95866802536 , 0.10111360589 , -0.958668025326 , -0.265954236634 , -0.101113606003 , -0.265954236715 , -0.101113605825 , 0.265954236287 , 0.101113605802 , 0.265954236516 , 0.95866802545 , -0.958668025479 , -0.784431814417 , 0.284319024823 , 0.784431814443 , 0.551207239435 , -0.28431902464 , 0.551207239408 , -0.284319024715 , -0.551207239418 , 0.284319024477 , -0.551207239227 , -0.784431814655 , 0.784431814542 , 0.166663878535 , 0.979468778892 , -0.166663878322 , 0.113419851853 , -0.979468778908 , 0.113419852024 , -0.979468778891 , -0.113419851942 , 0.979468778888 , -0.113419851887 , 0.166663878513 , -0.166663878526 , 0.903542635391 , 0.0990026905112 , -0.903542635384 , 0.416904273958 , -0.0990026904149 , 0.416904273844 , -0.0990026904642 , -0.416904274206 , 0.099002690128 , -0.416904274114 , 0.903542635279 , -0.903542635234 , 0.278762404536 , 0.349312185586 , -0.278762404541 , -0.894579520734 , -0.349312185467 , -0.894579520789 , -0.349312185551 , 0.894579520785 , 0.34931218555 , 0.894579520782 , 0.278762404438 , -0.278762404443 , 0.555896230179 , -0.676833211682 , -0.555896230315 , 0.48257246591 , 0.676833211458 , 0.482572465903 , 0.676833211636 , -0.482572466151 , -0.676833211438 , -0.482572465972 , 0.555896230193 , -0.555896230194 , ])
t_y = flex.double([ 0.412534053657 , -0.181618610642 , -0.412534053628 , 0.89265353574 , -0.181618610423 , -0.892653535763 , 0.181618610612 , -0.892653535812 , 0.18161861042 , 0.892653535811 , -0.412534053473 , 0.412534053535 , -0.295767027993 , 0.909507070089 , 0.29576702804 , -0.292093742927 , 0.909507070084 , 0.292093742689 , -0.909507070148 , 0.292093743159 , -0.909507070047 , -0.292093742722 , 0.295767027793 , -0.295767027748 , 0.0241205728251 , 0.817639022511 , -0.0241205729792 , -0.575225718103 , 0.817639022441 , 0.575225718229 , -0.817639022581 , 0.575225718124 , -0.817639022527 , -0.575225718035 , -0.0241205727111 , 0.0241205725942 , 0.0522476407202 , 0.990288947959 , -0.05224764032 , -0.128833161925 , 0.990288947968 , 0.128833161878 , -0.990288947962 , 0.128833161897 , -0.990288947953 , -0.128833161936 , -0.0522476403376 , 0.0522476405515 , 0.657446876256 , -0.228539787832 , -0.657446876171 , 0.718006385947 , -0.228539787714 , -0.718006386031 , 0.228539787861 , -0.718006385857 , 0.228539787874 , 0.718006385814 , -0.657446876363 , 0.657446876372 , 0.468181816653 , 0.189029529197 , -0.468181816576 , 0.863176473064 , 0.189029528897 , -0.863176473144 , -0.189029529128 , -0.86317647309 , -0.189029528931 , 0.863176473107 , -0.468181816649 , 0.468181816699 , -0.517059450696 , 0.368358511586 , 0.517059450647 , 0.772632856806 , 0.368358511817 , -0.772632856802 , -0.368358511487 , -0.772632856859 , -0.368358511666 , 0.772632856856 , 0.517059450692 , -0.517059450634 , -0.0663257759002 , -0.526121128258 , 0.0663257758199 , -0.847819231767 , -0.526121128407 , 0.847819231709 , 0.526121128344 , 0.847819231701 , 0.526121128306 , -0.847819231665 , 0.066325775941 , -0.0663257759967 , 0.942983815843 , 0.33269410954 , -0.942983815787 , 0.00980574320427 , 0.332694109636 , -0.00980574329891 , -0.33269410963 , -0.00980574318851 , -0.332694109635 , 0.00980574338976 , -0.942983815753 , 0.942983815791 , -0.405156945312 , -0.46763412065 , 0.405156945434 , 0.785599248335 , -0.467634120868 , -0.785599248146 , 0.467634120861 , -0.78559924825 , 0.467634120871 , 0.785599248234 , 0.405156945117 , -0.405156945197 , 0.620851501014 , -0.266242252155 , -0.620851501089 , -0.737331999103 , -0.266242252234 , 0.737331998996 , 0.266242252223 , 0.737331998833 , 0.266242252328 , -0.737331998939 , -0.620851501183 , 0.620851501306 , -0.0274882823504 , -0.686223186448 , 0.0274882823719 , 0.726871469185 , -0.686223186491 , -0.72687146909 , 0.68622318647 , -0.726871468983 , 0.686223186523 , 0.726871469033 , 0.0274882823356 , -0.0274882823097 , 0.580860267739 , 0.468927408489 , -0.58086026772 , 0.665363385822 , 0.468927408679 , -0.665363385699 , -0.468927408553 , -0.665363385848 , -0.468927408655 , 0.665363385651 , -0.580860267791 , 0.580860267548 , -0.779099597924 , 0.23760971091 , 0.779099597978 , -0.580125367276 , 0.237609711147 , 0.580125367047 , -0.23760971085 , 0.580125367157 , -0.237609711045 , -0.580125367022 , 0.779099598152 , -0.779099597967 , 0.101113605901 , -0.265954236477 , -0.101113606095 , 0.958668025295 , -0.265954236656 , -0.958668025246 , 0.265954236415 , -0.958668025394 , 0.265954236261 , 0.958668025323 , -0.101113605909 , 0.101113605789 , 0.284319025007 , 0.551207239321 , -0.284319024888 , -0.784431814292 , 0.551207239348 , 0.784431814401 , -0.55120723916 , 0.784431814427 , -0.551207239394 , -0.784431814511 , -0.284319024758 , 0.28431902469 , 0.979468778867 , 0.113419852011 , -0.979468778877 , 0.166663878465 , 0.113419852233 , -0.166663878213 , -0.113419852089 , -0.166663878384 , -0.113419852253 , 0.16666387842 , -0.979468778859 , 0.979468778852 , 0.0990026906796 , 0.416904273754 , -0.0990026906479 , 0.903542635194 , 0.4169042737 , -0.903542635238 , -0.416904273937 , -0.90354263511 , -0.416904274064 , 0.903542635131 , -0.0990026904671 , 0.0990026902458 , 0.349312185537 , -0.894579520609 , -0.349312185503 , 0.278762404728 , -0.894579520678 , -0.278762404659 , 0.894579520683 , -0.27876240468 , 0.894579520679 , 0.278762404556 , -0.349312185507 , 0.349312185429 , -0.676833211737 , 0.48257246604 , 0.676833211523 , 0.555896230165 , 0.482572466093 , -0.555896230368 , -0.482572466072 , -0.55589623023 , -0.482572466328 , 0.555896230268 , 0.676833211589 , -0.676833211456 , ])
t_z = flex.double([ -0.181618610454 , 0.892653535832 , -0.181618610307 , 0.412534053635 , -0.892653535852 , -0.412534053658 , 0.892653535888 , 0.412534053574 , -0.892653535922 , -0.412534053497 , 0.181618610358 , 0.181618610278 , 0.90950707017 , -0.292093742812 , 0.909507070202 , -0.295767027734 , 0.292093742707 , 0.295767027842 , -0.292093742749 , -0.295767027647 , 0.292093743136 , 0.295767027718 , -0.909507070252 , -0.909507070164 , 0.817639022597 , -0.575225718162 , 0.817639022538 , 0.0241205726715 , 0.575225718252 , -0.0241205729845 , -0.575225718061 , 0.0241205726061 , 0.575225718143 , -0.0241205727922 , -0.81763902268 , -0.817639022696 , 0.990288947974 , -0.12883316185 , 0.99028894798 , 0.0522476406846 , 0.128833161908 , -0.052247640269 , -0.128833161948 , 0.0522476405472 , 0.128833161961 , -0.0522476402555 , -0.990288947985 , -0.990288947966 , -0.228539787596 , 0.718006385932 , -0.228539787605 , 0.657446876302 , -0.718006386011 , -0.657446876231 , 0.718006385854 , 0.657446876413 , -0.718006385902 , -0.657446876432 , 0.228539787771 , 0.228539787715 , 0.18902952894 , 0.863176473178 , 0.18902952878 , 0.468181816677 , -0.863176473268 , -0.468181816665 , 0.863176473208 , 0.468181816722 , -0.863176473198 , -0.468181816649 , -0.189029528872 , -0.189029528802 , 0.368358511462 , 0.772632856874 , 0.368358511616 , -0.517059450625 , -0.772632856813 , 0.517059450578 , 0.77263285691 , -0.517059450602 , -0.772632856879 , 0.517059450677 , -0.368358511284 , -0.36835851138 , -0.526121128113 , -0.847819231824 , -0.526121128174 , -0.0663257759179 , 0.847819231736 , 0.0663257757814 , -0.847819231767 , -0.0663257759656 , 0.847819231796 , 0.0663257759818 , 0.526121128258 , 0.526121128205 , 0.332694109444 , 0.00980574321495 , 0.332694109596 , 0.94298381592 , -0.0098057433158 , -0.942983815858 , 0.00980574330467 , 0.942983815887 , -0.00980574323076 , -0.942983815837 , -0.332694109697 , -0.332694109587 , -0.467634120466 , 0.785599248458 , -0.467634120645 , -0.405156945215 , -0.785599248222 , 0.40515694535 , 0.785599248378 , -0.405156945177 , -0.785599248291 , 0.405156945084 , 0.467634120732 , 0.467634120717 , -0.266242251992 , -0.737331999127 , -0.266242252015 , 0.620851501066 , 0.737331998989 , -0.620851501166 , -0.737331998999 , 0.620851501316 , 0.737331998864 , -0.620851501268 , 0.266242252105 , 0.266242252132 , -0.686223186468 , 0.726871469191 , -0.686223186459 , -0.0274882822863 , -0.726871469144 , 0.0274882824203 , 0.726871469167 , -0.0274882823482 , -0.726871469117 , 0.0274882823239 , 0.68622318657 , 0.68622318656 , 0.468927408353 , 0.665363385766 , 0.468927408438 , 0.580860267633 , -0.665363385675 , -0.580860267748 , 0.665363385665 , 0.5808602675 , -0.665363385816 , -0.5808602678 , -0.468927408386 , -0.468927408545 , 0.237609710919 , -0.580125367136 , 0.237609711033 , -0.779099598014 , 0.580125367023 , 0.779099598147 , -0.580125367003 , -0.779099598067 , 0.580125367051 , 0.779099598229 , -0.237609710698 , -0.237609710992 , -0.26595423639 , 0.958668025337 , -0.265954236438 , 0.101113605881 , -0.958668025275 , -0.101113606126 , 0.958668025361 , 0.101113605856 , -0.958668025406 , -0.101113605926 , 0.265954236065 , 0.265954236005 , 0.551207239203 , -0.784431814401 , 0.551207239226 , 0.284319024903 , 0.784431814448 , -0.284319024653 , -0.784431814553 , 0.284319024564 , 0.784431814475 , -0.284319024701 , -0.551207238993 , -0.551207239188 , 0.113419851953 , 0.166663878345 , 0.113419852175 , 0.97946877889 , -0.166663878101 , -0.979468778913 , 0.166663878297 , 0.979468778894 , -0.166663878207 , -0.979468778894 , -0.113419852053 , -0.11341985209 , 0.416904273508 , 0.903542635296 , 0.416904273531 , 0.0990026905819 , -0.903542635331 , -0.0990026906638 , 0.903542635216 , 0.0990026903016 , -0.903542635195 , -0.0990026904964 , -0.4169042738 , -0.41690427395 , -0.894579520698 , 0.278762404762 , -0.89457952071 , 0.349312185292 , -0.27876240469 , -0.349312185207 , 0.278762404568 , 0.349312185199 , -0.278762404581 , -0.349312185307 , 0.894579520741 , 0.894579520769 , 0.482572465815 , 0.555896230051 , 0.482572465958 , -0.676833211681 , -0.555896230278 , 0.676833211519 , 0.555896230079 , -0.676833211456 , -0.555896230097 , 0.676833211552 , -0.482572466006 , -0.482572466192 , ])
