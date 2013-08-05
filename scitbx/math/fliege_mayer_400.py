"""
Below are flex arrays with x,y,z points and weights for numerical integration on a sphere.

The design has been taken from

http://www.personal.soton.ac.uk/jf1w07/nodes/nodes.html

"""
from scitbx.array_family import flex

t_x = flex.double([ 0.0 , 0.967072165324 , -0.325877858598 , -0.465895885493 , -0.85198350649 , 0.275670752317 , 0.898715311595 , 0.192728626005 , -0.168367811523 , -0.283008836843 , -0.302201464779 , -0.916960825913 , 0.394668106954 , -0.950570477288 , -0.878810277936 , 0.344190731596 , -0.654046858982 , -0.579461964337 , 0.482073401974 , -0.734678363253 , 0.374519354899 , 0.64270900995 , 0.627702146868 , -0.41873383622 , 0.710854178043 , -0.288753769561 , 0.525261703962 , 0.445239596428 , -0.029973261712 , 0.975887110684 , -0.144145837616 , -0.416658282183 , -0.426150939244 , -0.379117309254 , 0.591425373396 , 0.903544494333 , 0.479503564788 , 0.823871133541 , -0.592667032273 , 0.080079826279 , -0.02729478229 , -0.093655784716 , -0.172409360366 , 0.44156434564 , 0.717429715443 , -0.093029348553 , 0.851013598084 , 0.601849567186 , 0.279543053968 , -0.786176595207 , 0.808494047649 , 0.746754235545 , 0.132877643504 , 0.502979630153 , 0.440541896461 , 0.182423903766 , 0.988665449887 , 0.676155338597 , -0.993400080117 , 0.793434016296 , 0.838642497582 , 0.857006915043 , -0.439957728759 , 0.570009893008 , -0.339614288702 , -0.247122362237 , -0.114460347028 , 0.425171339955 , -0.198286482924 , 0.849531544496 , 0.606952289677 , 0.789326504327 , -0.775667052285 , 0.270997254308 , 0.210446446122 , 0.438172930518 , 0.958694980186 , 0.755731460731 , -0.348236560158 , -0.659619116761 , -0.159073745936 , 0.7764462287 , -0.241695731238 , 0.474452149951 , -0.397862662165 , 0.501290463315 , 0.115909301025 , 0.619838138113 , -0.329249102887 , 0.995125161047 , -0.483639120832 , 0.310642980181 , 0.174073420907 , -0.682149103951 , -0.440625848452 , -0.32421952993 , 0.92938716504 , -0.904069717573 , 0.335532749442 , -0.618842843891 , 0.931394889497 , 0.903972820281 , -0.647909259142 , 0.008927307868 , 0.980013390421 , -0.522328894921 , -0.941908835826 , -0.624922989317 , -0.706235670187 , -0.145591723319 , -0.133281574103 , -0.369244148358 , -0.58596448381 , 0.186916760814 , -0.066894520775 , 0.463939931465 , 0.216681253458 , -0.83915464479 , -0.601388116878 , 0.097556611477 , 0.271864241521 , 0.070086166441 , 0.58989699819 , 0.390917683592 , 0.14811283864 , 0.453105056063 , -0.985585426278 , 0.790758047648 , -0.163459317276 , -0.7388667281 , -0.235351436839 , 0.072497985353 , -0.29624405679 , 0.058042436105 , 0.857437145037 , -0.498347388546 , -0.988732057464 , 0.539075627432 , 0.25838141503 , -0.126339976959 , 0.559393823719 , -0.742247333019 , 0.257239729482 , -0.429358468322 , 0.826226169176 , 0.161466880121 , -0.503056515869 , 0.607152726376 , -0.005414696447 , -0.498812307828 , -0.78793569011 , -0.188756728243 , -0.547290916806 , 0.232528427092 , -0.869617075008 , 0.270808392928 , -0.283708622494 , -0.64288574335 , -0.566340745779 , 0.41379045773 , -0.534358338287 , -0.049216770805 , 0.877744218442 , -0.799002497491 , -0.13600830038 , 0.275940226729 , -0.490784072954 , -0.704900625991 , 0.143945344241 , -0.283364934192 , -0.789345542026 , 0.132873120742 , 0.519203240644 , -0.56875757391 , -0.622893162743 , -0.0671518107 , -0.818004056152 , 0.964314161277 , 0.069828514341 , 0.491095353469 , 0.689682221146 , -0.217468798972 , -0.544144644612 , -0.231298423007 , 0.177931612725 , -0.565438603088 , -0.256134218733 , -0.970710702678 , -0.963595909288 , 0.077136177594 , -0.310692206856 , 0.766155600886 , -0.140060940277 , -0.610586196784 , -0.73786078046 , 0.051718254618 , 0.175963270759 , -0.093355356434 , 0.354697316868 , -0.717241573451 , 0.049670589154 , 0.687281353355 , 0.537483805407 , -0.48504772073 , -0.436614520747 , -0.074869094233 , 0.311193598173 , -0.645688534029 , 0.322371842277 , 0.140924647422 , 0.355390935351 , -0.592489317527 , 0.001860048688 , -0.805454348124 , 0.542737287571 , 0.548005956081 , -0.175480953365 , -0.105455338868 , -0.666180238749 , -0.861899163285 , -0.96342904885 , -0.142553483138 , -0.404003134827 , -0.018102252447 , -0.530678946358 , 0.899993184526 , -0.676514154804 , 0.746299487591 , -0.966240452778 , -0.036940461666 , 0.504121067847 , 0.179134455124 , -0.339542085167 , -0.298224337317 , -0.706927780642 , 0.319861251196 , -0.195560428101 , -0.049238325552 , 0.240217380438 , 0.44085024306 , -0.811675093973 , -0.907221369891 , 0.862528759055 , 0.354313586344 , 0.617283943581 , 0.492386073362 , 0.36436067469 , -0.897315135643 , 0.947748239282 , 0.151596655612 , -0.904159270844 , -0.496893215745 , -0.378124528491 , -0.038753553755 , 0.751012897022 , 0.333975247852 , -0.878793552126 , 0.44394092823 , 0.695849482264 , -0.13017699596 , 0.162716873695 , 0.44086999985 , -0.230685535127 , -0.284188527678 , 0.179725565166 , -0.741454489073 , 0.72195505303 , -0.408821656742 , 0.623775032307 , -0.454370539272 , -0.414991032657 , -0.395442595694 , 0.824665438724 , -0.32894223542 , 0.06016284735 , -0.832162077883 , -0.546772481423 , -0.826060494789 , -0.333444005267 , 0.65822449047 , 0.729899722438 , 0.051827048059 , 0.003106199196 , 0.539224048427 , 0.692352785123 , 0.026744187859 , 0.248382339915 , 0.672554049981 , 0.597960642832 , 0.331753207167 , 0.436850065531 , 0.093354145246 , -0.442682260731 , 0.996211996599 , 0.808719443615 , -0.901344389501 , -0.799478165019 , -0.722857782468 , 0.232039658458 , -0.234697705358 , -0.233520519764 , -0.171132627185 , 0.029257377789 , 0.662622408651 , -0.232612644157 , 0.045000227059 , -0.714730276434 , 0.897030104277 , -0.859188005786 , 0.011414065983 , 0.76348042248 , 0.409110434609 , 0.53478484977 , 0.596166182931 , 0.827481932647 , 0.29351730977 , 0.355134590914 , -0.671802415023 , 0.968055632967 , 0.913945243798 , 0.82881235232 , -0.922953781566 , -0.210562105517 , -0.003662864833 , 0.160662771504 , -0.133846566731 , 0.709883588106 , 0.871648243333 , -0.735664158308 , 0.345293646106 , 0.599271984907 , 0.445170047535 , 0.725847463195 , -0.844379019201 , -0.940869855481 , 0.254940864351 , 0.595842184645 , -0.939854688295 , 0.12415643048 , 0.917931159983 , -0.566064208639 , -0.561973055326 , -0.326395691726 , -0.352760165083 , -0.756876519184 , -0.610053444187 , 0.643920943084 , 0.366306399462 , -0.036810809776 , -0.9965192572 , -0.677325090134 , -0.370258063332 , 0.736246899426 , 0.882860465682 , 0.663926630815 , 0.677245724311 , 0.92254507735 , -0.723062343169 , -0.061075706073 , 0.962777791149 , 0.821102557358 , 0.375693727587 , 0.333676419873 , -0.801645009883 , 0.260260527317 , -0.584534685189 , -0.512854734676 , -0.047455220905 , -0.454422901732 , -0.13881838946 , 0.182022978182 , 0.738658232796 , -0.900679768691 , 0.921064456803 , 0.474631465186 , -0.949184554164 , -0.697916566759 , 0.010814022265 , 0.800934758265 , 0.563478512015 , 0.244421903893 , 0.088965153902 , 0.940450241877 , -0.497267500364 , 0.574936563637 , -0.880982363893 , -0.832714917528 , 0.72452117193 , -0.969234908294 , -0.803628878418 , -0.60180663818 , -0.073704165396 , -0.316315055549 , -0.685987342602 , 0.107457609069 , -0.462057771315 , -0.450456114334 , -0.796908968623 , -0.255407117664 , -0.899773345313 , ])
t_y = flex.double([ 0.0 , 0.0 , 0.93901002623 , 0.154249023925 , -0.288269348664 , -0.433619357311 , 0.047711893668 , -0.733265517804 , -0.054393480418 , -0.904123053293 , -0.108322813989 , 0.081032571895 , -0.877107064415 , -0.197654554269 , -0.378322501765 , 0.880429735011 , 0.669271417132 , 0.342022680966 , 0.395167230829 , 0.292656579894 , -0.671934671013 , 0.383882323549 , 0.767224472522 , -0.840296640395 , 0.252623955315 , -0.926661656189 , 0.092199244761 , 0.87887176082 , -0.208949824461 , -0.218174601933 , -0.981731064006 , 0.383386832023 , 0.869737541531 , -0.294751844253 , 0.780260489478 , 0.419195267922 , 0.665704229368 , -0.547703365436 , 0.776946394615 , -0.600228160427 , 0.999627273827 , -0.994418164299 , 0.7210934572 , -0.817661736202 , 0.657949443921 , -0.920714339859 , 0.220298187816 , -0.32511146236 , 0.950603423065 , 0.398881762537 , 0.584278101992 , -0.664670256784 , 0.519693226219 , -0.652445227831 , -0.786847206643 , 0.941369301332 , -0.079944713374 , -0.25331184405 , -0.066698957863 , -0.432179700336 , -0.110100366331 , 0.369106273155 , -0.231317372114 , 0.258020092446 , 0.64647300429 , -0.254893607967 , -0.648717295199 , 0.785723639493 , -0.781612639081 , -0.472805803228 , -0.793810825025 , -0.27452072363 , -0.483836162599 , 0.948024233833 , -0.689620451738 , -0.37009194656 , 0.283465751773 , -0.574803158295 , -0.72761523941 , 0.175055831355 , 0.917729360748 , -0.612270177709 , 0.785519212981 , 0.56237752863 , 0.915028117813 , -0.703802411634 , -0.43756905637 , -0.067435037877 , 0.851729933833 , 0.089258444479 , -0.030742187021 , 0.735449660391 , 0.05189390538 , -0.358169933317 , -0.865198561173 , -0.663141519456 , -0.350746169732 , -0.425644774651 , 0.684385228182 , 0.04103705942 , 0.188494963453 , 0.040472269506 , -0.570531720574 , -0.977016366554 , 0.142833808266 , -0.685581067888 , 0.303696069908 , 0.650129956579 , -0.705963121644 , -0.966673991132 , 0.981108892091 , 0.647922630851 , -0.80867046555 , -0.958015855529 , -0.868720522333 , 0.871424291986 , -0.939521934499 , 0.524850144395 , -0.467484315576 , -0.150727369506 , -0.862542752475 , -0.923959893307 , 0.24047657941 , -0.60205531777 , -0.984094855973 , -0.075122157965 , 0.118460247417 , -0.457321066943 , -0.403388085958 , -0.386722419846 , 0.931450265409 , -0.067008455085 , -0.954005158829 , -0.650308698773 , -0.113183169766 , 0.544500195501 , -0.120665083085 , 0.787080219462 , -0.889549214456 , -0.936964386999 , -0.782857088506 , 0.609869836002 , -0.541108020267 , 0.328308388936 , 0.226249071968 , 0.661567131991 , 0.861042919081 , -0.712381813053 , 0.689178399943 , 0.666350835063 , -0.566040097715 , 0.680403347597 , 0.627832402383 , 0.528179178353 , -0.326375804866 , -0.095685076335 , 0.252654684847 , 0.455441791666 , -0.785489659306 , -0.529834833131 , -0.723025468863 , -0.369259190348 , 0.472958189151 , -0.187786907331 , -0.673209757408 , 0.393967821818 , 0.514635376 , -0.668349756044 , -0.259756235786 , 0.934729393217 , 0.523044743832 , -0.84227234448 , 0.524693370819 , 0.816980120108 , -0.539851777568 , -0.539506777008 , -0.55701579949 , -0.184197866111 , 0.984170340292 , 0.690721384132 , -0.698558753683 , 0.975441191133 , -0.2966330317 , 0.417717428738 , 0.781153693538 , 0.039342536663 , -0.865244257438 , 0.238448884757 , 0.162152994343 , 0.986528172342 , 0.531868404314 , 0.634266071828 , 0.246669319246 , 0.746452280319 , 0.515419489916 , 0.551841090819 , 0.984285516684 , 0.310950277038 , 0.076277498615 , 0.687173391799 , 0.887823160965 , 0.724888548132 , -0.817380621577 , 0.775605242158 , -0.518150968686 , -0.519226683829 , 0.548580604091 , 0.493812768153 , -0.793442361457 , 0.394159305139 , 0.880963980087 , -0.159358665796 , 0.762941456886 , -0.591392102196 , 0.839720269632 , -0.566301393678 , -0.754851917431 , 0.977389875518 , 0.744219755181 , 0.481089415309 , -0.009610242077 , 0.885737791935 , 0.053967218067 , 0.632574968301 , -0.354064822002 , 0.353847258549 , -0.612324847064 , 0.533610980238 , -0.249066704655 , 0.089050231759 , -0.856513340379 , 0.875421484053 , 0.766149692663 , -0.945867239005 , 0.314024298221 , -0.219377908555 , 0.579064977401 , 0.479890105567 , -0.596044564903 , -0.441952325385 , -0.258831315032 , 0.420620397975 , -0.504989812509 , -0.239339122763 , 0.559908866876 , 0.791704410445 , 0.588557700482 , 0.263498394724 , -0.244485951652 , -0.816097491133 , -0.136659334193 , -0.628259942678 , -0.762438003699 , 0.951875677529 , -0.094405327555 , -0.936358418134 , -0.458053845702 , -0.085475764801 , 0.664560218099 , 0.552074760326 , 0.934005393166 , -0.895846507438 , -0.843614671446 , -0.602671486636 , 0.670667689621 , 0.644180397901 , -0.616015726584 , -0.807382208514 , 0.6775801695 , -0.889635777431 , 0.741982190241 , -0.458809736082 , 0.512209118853 , 0.236415914535 , -0.997105364078 , 0.186166154054 , -0.452590271307 , -0.066616481479 , -0.101606704039 , -0.740226903972 , -0.234189192932 , 0.248487547312 , 0.866581981253 , -0.223008248956 , -0.430367857939 , -0.738103917181 , -0.06909386223 , 0.084892861629 , -0.12978740344 , 0.391707137498 , 0.225322547144 , 0.359560819898 , -0.88424391664 , -0.047711204524 , 0.068944381591 , -0.103309771467 , 0.121027150873 , -0.07285879027 , 0.227422315494 , -0.442997215253 , 0.395934649934 , 0.832176587986 , -0.973958460746 , -0.58188571701 , 0.084106963348 , 0.187297356104 , 0.002132866931 , -0.315636308265 , 0.233106075333 , 0.943283301866 , 0.385231857546 , 0.249402240166 , 0.058616935634 , -0.689083588754 , 0.379645414538 , -0.383449391098 , 0.079165037057 , -0.657045388377 , 0.060428718932 , 0.202530118179 , -0.287408034275 , 0.342855672718 , -0.268061052286 , -0.772999869486 , 0.09735128645 , -0.068832911841 , -0.399696212953 , -0.413572527811 , 0.126490356293 , 0.796878888865 , 0.675260674216 , 0.412535158025 , -0.068589086567 , 0.438352476256 , -0.200718329719 , 0.243148735813 , 0.41688173553 , 0.177648630264 , 0.791958806623 , -0.14219915659 , -0.753245550196 , 0.39033011094 , 0.862227590731 , -0.393474104773 , -0.43979682176 , -0.133362256576 , 0.537717460508 , -0.904040654874 , -0.843509235197 , 0.057807682144 , -0.27725114828 , 0.489777171553 , 0.54028409602 , -0.26838330368 , -0.552983835838 , 0.092983152843 , 0.333608064495 , -0.189149557678 , 0.802772674721 , 0.223661800522 , 0.514878099084 , 0.926647059693 , -0.746818175912 , -0.506115488047 , -0.963858106987 , -0.797444913074 , 0.767290885213 , 0.406083639791 , 0.858425711163 , 0.134379221242 , -0.29930275365 , 0.231107403008 , -0.381757414331 , -0.380235829472 , -0.26842445964 , -0.293445372217 , -0.700598936353 , -0.358494735945 , 0.066999853856 , -0.498292469373 , 0.850752724425 , -0.911649164752 , -0.101638931175 , 0.209785182564 , -0.405905555724 , 0.357385256732 , 0.00262986207 , 0.406130943018 , -0.020239716796 , 0.594688268322 , 0.221882191017 , -0.208510564069 , 0.07781625036 , 0.551646275317 , -0.493500262302 , -0.12853144365 , -0.600162574188 , 0.358254981948 , -0.543632154647 , 0.052158824137 , ])
t_z = flex.double([ 1.0 , -0.254502312474 , -0.109835294486 , 0.871291146804 , 0.43706393959 , 0.857892702663 , 0.435929310677 , 0.652056253031 , 0.984222347506 , -0.320105455707 , -0.947069396958 , 0.390661702798 , -0.273715697224 , -0.239475353399 , 0.290799896925 , 0.326153678488 , -0.352559890609 , -0.739759635011 , -0.78195146575 , -0.612045610075 , 0.638935873697 , -0.662992828163 , -0.131744539094 , 0.344330554186 , 0.656404962473 , 0.240664570541 , 0.845931109261 , 0.171307121294 , -0.977466917312 , 0.006647576371 , 0.124201833577 , -0.824263557923 , -0.248901558519 , -0.877149597351 , 0.203493479654 , 0.088784424941 , -0.571764121257 , 0.145799104279 , -0.212367814773 , -0.795809887381 , 0.000555231302 , -0.048591238944 , 0.671043395349 , 0.369391680753 , 0.228904199705 , -0.37898633839 , -0.476701756155 , -0.729437890104 , 0.134940034959 , -0.472037816985 , 0.070402233271 , 0.023907351235 , 0.843956445842 , -0.566856874645 , -0.4321970741 , 0.283805140624 , 0.127080568949 , 0.69184323929 , -0.093314145997 , 0.428582743938 , -0.533438534962 , -0.359582684073 , 0.86771508588 , 0.780073300253 , 0.683179910151 , 0.934858163948 , -0.752372713399 , -0.449296888507 , 0.591408617724 , -0.233988947047 , 0.038383487709 , 0.549183067714 , 0.405269283022 , -0.166764925038 , -0.692918412123 , 0.819168135399 , -0.023475573205 , 0.313801351933 , -0.591022302072 , -0.730929597644 , 0.363962036172 , -0.149186069813 , -0.569686527434 , 0.677219811212 , 0.066549573006 , 0.503358755529 , -0.891682877958 , 0.781826833901 , -0.407616422707 , 0.04193857341 , 0.874727453975 , -0.602175004376 , 0.983364361119 , -0.637484822444 , -0.239333055428 , 0.674629543962 , -0.114963567604 , -0.038528840867 , 0.647328844945 , 0.784442154858 , -0.311405216032 , -0.425670219294 , 0.504685196669 , 0.212977282025 , -0.138463922422 , -0.507100704874 , -0.143444909691 , 0.432206312983 , -0.053359619881 , -0.210581207542 , -0.14021898539 , -0.66622445417 , 0.051939405662 , 0.217411464929 , 0.490764482382 , -0.159309269438 , -0.265231538463 , 0.142659763265 , 0.647912607971 , 0.983749951786 , -0.426743288565 , 0.376013357255 , -0.77083885883 , -0.696213156296 , -0.098081096432 , 0.888286254286 , -0.120783017395 , -0.406889606416 , 0.900310559586 , 0.551834873939 , -0.277506944501 , -0.995115023033 , 0.045974076871 , 0.75744945172 , 0.501987163574 , 0.674662447027 , 0.088593771042 , -0.299836949089 , 0.376750898377 , 0.325785125072 , -0.272421234417 , 0.277718706178 , -0.80064338627 , 0.841347079055 , 0.515908591518 , 0.732295962363 , -0.074426025977 , 0.351962667461 , -0.724571469294 , 0.554222740574 , 0.242396278912 , -0.708111701726 , -0.553442975292 , -0.816674528897 , -0.370465891619 , 0.95786595121 , 0.92502704163 , -0.615849572056 , 0.249527863763 , 0.740305684628 , 0.437830261263 , -0.928022284116 , -0.076652712319 , 0.571253959669 , 0.726835858196 , 0.876724783866 , -0.703051508429 , -0.237536757311 , -0.954885561647 , 0.214441776542 , -0.321493096713 , 0.522419401926 , -0.674629425332 , 0.095175130515 , -0.56618386242 , 0.839299155178 , -0.143536626815 , -0.190182397928 , -0.162888673252 , 0.530781803856 , 0.190667515555 , 0.034954314678 , -0.784802809784 , 0.878642810955 , 0.598447364657 , -0.82385153453 , 0.430984497359 , 0.029374496844 , 0.212577821114 , 0.144264255035 , -0.787773033996 , -0.103499494484 , -0.958925012684 , 0.264562827137 , 0.435780011099 , -0.832344059042 , -0.014796924984 , 0.945830165852 , -0.931864559156 , 0.115573590914 , -0.457496303183 , 0.046700472355 , 0.207364602562 , 0.403937144804 , 0.735450429277 , -0.851350849843 , 0.776026974577 , 0.582439067227 , 0.516261188115 , -0.908173268667 , -0.312409585096 , 0.789658929065 , 0.646464905144 , 0.038712718167 , 0.017495869503 , 0.615623426795 , -0.631984982224 , 0.183270845304 , -0.04838228497 , -0.160258562352 , -0.267791170652 , -0.441754534084 , -0.913164282276 , 0.774287555069 , 0.770076592108 , 0.254567054868 , -0.4091294172 , -0.397864796872 , -0.065917858331 , -0.995341880218 , -0.110665472057 , 0.448941056538 , 0.545642576081 , -0.128052375259 , 0.63375220164 , -0.921716937688 , 0.791479545477 , 0.875945816747 , 0.766176537611 , -0.781235691249 , -0.5236314469 , 0.005278903357 , -0.032084717018 , 0.903979350896 , 0.552686704917 , 0.36160763438 , -0.721693239502 , 0.354110354726 , 0.20493875764 , -0.557676733398 , -0.404747130101 , 0.598653970649 , 0.52508107133 , -0.304024434215 , 0.653503835211 , -0.108136240971 , 0.133822894826 , -0.89196992431 , -0.272310878506 , -0.823569917332 , -0.318052109806 , 0.05561185435 , -0.484869539159 , -0.745670141505 , -0.719655175292 , -0.187821339556 , -0.315127793136 , -0.425439563691 , 0.389602134198 , -0.045777686232 , -0.526540475349 , -0.795687614323 , -0.239934851028 , -0.914278142094 , 0.046490049749 , 0.522348963068 , -0.704415999163 , -0.559630506088 , 0.937278599481 , -0.137130050614 , -0.642185189099 , -0.967247587705 , 0.499025070808 , 0.8120989758 , 0.579164163071 , -0.674156773947 , -0.966194727485 , -0.735162738378 , -0.790947722376 , -0.858198886021 , -0.870856917062 , 0.928440100577 , 0.14881233793 , -0.072700060487 , -0.584139995007 , 0.420601215684 , -0.58837665862 , 0.687144979612 , 0.945746629557 , -0.865257449767 , -0.888090040385 , 0.527442651215 , -0.224830875518 , 0.471530015899 , -0.96892588803 , 0.981271970435 , -0.699396942249 , -0.309371480464 , -0.455475057885 , 0.331792603171 , -0.518357078105 , 0.877739810476 , -0.842952679166 , -0.41200690533 , 0.413694344127 , -0.875679252542 , 0.931457094688 , 0.342012971658 , 0.243344737789 , 0.351689696422 , -0.480069480884 , 0.174946576926 , -0.940110031841 , 0.634395606224 , -0.982196620275 , -0.988608682352 , -0.579920881404 , 0.263034416257 , 0.665431015167 , 0.495738171256 , -0.429995476678 , 0.794756800645 , -0.68442749607 , 0.308011653176 , 0.272903036189 , -0.935886664055 , 0.686426769276 , -0.2917432588 , -0.59781805709 , -0.37038059533 , -0.334951418579 , 0.729265856585 , 0.387336332151 , 0.848963129237 , -0.483442540824 , -0.781056530449 , -0.544266250766 , 0.22029551981 , -0.535851784005 , 0.060063648865 , 0.681441503764 , 0.789320776847 , 0.407472206014 , 0.385393046697 , -0.503398754664 , 0.729857768466 , -0.193949064348 , -0.664381887713 , -0.593149046066 , 0.151770629097 , 0.246355704995 , -0.013395887925 , -0.575258775637 , -0.318138949028 , 0.056938629386 , -0.149669009564 , -0.385025607708 , -0.912602914472 , 0.237918315388 , 0.981158335666 , 0.936635199569 , -0.633224591592 , -0.207454165717 , 0.084029640011 , -0.838256095547 , 0.113747508374 , 0.148571855423 , 0.933469111017 , 0.59499120379 , -0.658935946404 , -0.465271678465 , -0.401224378371 , 0.324380748848 , -0.841852249661 , 0.710414405559 , -0.310073947278 , 0.553695719644 , 0.556890230251 , 0.245303987756 , -0.022945354476 , 0.767200797414 , 0.975238965933 , 0.945457252769 , -0.474455216769 , 0.863081892615 , -0.877486344031 , -0.660979707406 , 0.486404629539 , 0.79951940857 , -0.433229020414 , ])
t_w = flex.double([ 0.022397902133 , 0.0295515597543 , 0.031153685179 , 0.0308883279592 , 0.0336628680339 , 0.0352783705447 , 0.0287400094077 , 0.0376372192552 , 0.0404966997263 , 0.0340224312794 , 0.036164910039 , 0.0345967287527 , 0.0405167727536 , 0.0358475332373 , 0.0292411661561 , 0.0297919036341 , 0.0258879071664 , 0.0343873536505 , 0.0348859636523 , 0.0365298951172 , 0.0317961983778 , 0.0301233404265 , 0.0333151712301 , 0.0257272057778 , 0.0270531718977 , 0.0403834656229 , 0.0273753359581 , 0.0326775276817 , 0.0341384222788 , 0.0299626864383 , 0.0272123392682 , 0.0285868826488 , 0.0278708428044 , 0.0291255774065 , 0.0315772847063 , 0.0240943845236 , 0.0325123484021 , 0.0352738342821 , 0.0309307966425 , 0.0277802542645 , 0.0293427922209 , 0.0412384722113 , 0.0327452643297 , 0.0321088738403 , 0.0271083036301 , 0.0313939339778 , 0.0269384757657 , 0.0228035341154 , 0.0324750349634 , 0.0295454268162 , 0.0346479404741 , 0.0262158333089 , 0.0300432322176 , 0.0275585196099 , 0.0257529679696 , 0.0267963333388 , 0.0285033828544 , 0.030927712394 , 0.0285221485361 , 0.0336680312694 , 0.0305099284089 , 0.0324789951088 , 0.0332214657718 , 0.0372580440848 , 0.0275249552024 , 0.0319350213413 , 0.0308136539859 , 0.0308080267467 , 0.0253508792568 , 0.0262055274854 , 0.0274355573547 , 0.0329818729153 , 0.0295498843827 , 0.0337460700694 , 0.02954711478 , 0.0193233122238 , 0.0398793419543 , 0.0266129741434 , 0.0347766847422 , 0.0272640156262 , 0.037380444018 , 0.0335449603662 , 0.0336996775634 , 0.0362242278331 , 0.0260466499315 , 0.0360514157356 , 0.0354149728089 , 0.0350051674064 , 0.030601228471 , 0.0289594944289 , 0.035883601331 , 0.0294159520449 , 0.0311734108955 , 0.0332830858703 , 0.0282759185433 , 0.0295042644521 , 0.0376370342528 , 0.034942787014 , 0.033330011746 , 0.0281922982725 , 0.0400198926464 , 0.025937849667 , 0.0364432598505 , 0.0418052586838 , 0.0273742818989 , 0.0264279128635 , 0.0295240630884 , 0.0381498144832 , 0.0382414449754 , 0.0271529507767 , 0.0268131102191 , 0.0305896609517 , 0.0277594671408 , 0.0274744445045 , 0.0419613862072 , 0.0307415399113 , 0.0286968075028 , 0.0288653988164 , 0.0284841284211 , 0.0449294310374 , 0.0289904877586 , 0.0251823838602 , 0.0318807554799 , 0.0274648714301 , 0.0380802267027 , 0.0291260272188 , 0.0352683964077 , 0.0406800011105 , 0.0367819775316 , 0.0314755549319 , 0.0356352823443 , 0.029643849577 , 0.0282777618309 , 0.0330370951345 , 0.0344863678167 , 0.0334953622713 , 0.034371519299 , 0.0306221747756 , 0.0383211766307 , 0.0222885444481 , 0.0220081786617 , 0.0304816610843 , 0.0354584632223 , 0.0314336524883 , 0.0352895963458 , 0.0372314469544 , 0.0365095344247 , 0.0255133103565 , 0.0323019703492 , 0.0264673925845 , 0.036265497674 , 0.0313826922211 , 0.0333226031462 , 0.0261997054261 , 0.0314419915626 , 0.0216457955986 , 0.0363000759207 , 0.0249854469415 , 0.039015138459 , 0.0371945383123 , 0.0305702472745 , 0.0268300011925 , 0.0343194778509 , 0.0285543023929 , 0.0400582624603 , 0.0395964467901 , 0.0345445328958 , 0.0268606816261 , 0.0320593815865 , 0.0303549882271 , 0.0280872216486 , 0.0305212206475 , 0.0260213044187 , 0.0316297283972 , 0.0365522853026 , 0.0233115830802 , 0.0314113775471 , 0.0260165492371 , 0.0376401249561 , 0.0280280939666 , 0.0370323920854 , 0.0376536545302 , 0.038247545839 , 0.0271332013676 , 0.024029505026 , 0.034459195536 , 0.0315536234356 , 0.0290504565164 , 0.0347860242655 , 0.0370851692957 , 0.0312018258527 , 0.0260175872184 , 0.0289387203309 , 0.0264895360945 , 0.0246277449348 , 0.0311033280567 , 0.0259641395836 , 0.0287723704841 , 0.0366057089532 , 0.0371895846392 , 0.0349059982982 , 0.0342828353074 , 0.034367047009 , 0.0297512352445 , 0.0358269588383 , 0.0314615973058 , 0.0251899500696 , 0.0337335426085 , 0.0256398457556 , 0.0329412782801 , 0.0319675386784 , 0.0285120739242 , 0.0352995008407 , 0.0269122158913 , 0.0293609881993 , 0.0241136254878 , 0.0295179078123 , 0.0276337796735 , 0.0260457147927 , 0.0293797829472 , 0.0307071237262 , 0.0289205929967 , 0.029889531814 , 0.0255698563908 , 0.031529191098 , 0.0349248534357 , 0.03000511884 , 0.0273300429223 , 0.0312021925374 , 0.0367684898562 , 0.0343884728921 , 0.035383525161 , 0.0385435787103 , 0.0303217459359 , 0.0323320674863 , 0.0333828551195 , 0.0336157575823 , 0.0369922758696 , 0.0239943738676 , 0.0315730942713 , 0.0341218173903 , 0.0357673704547 , 0.0304810614802 , 0.0427804562305 , 0.0296723821782 , 0.0308639753374 , 0.0353060070548 , 0.0280179361837 , 0.0358451562678 , 0.0282309742421 , 0.0282365931158 , 0.0286374669977 , 0.036843186958 , 0.0309070257943 , 0.0286614260095 , 0.0223775755941 , 0.0297673650765 , 0.0222567159217 , 0.033693787349 , 0.0310458490678 , 0.0260615715478 , 0.0329779947416 , 0.0305710221266 , 0.0310815573771 , 0.0340455668172 , 0.0381876873222 , 0.0285507130087 , 0.0303183446673 , 0.035329751947 , 0.0378717900375 , 0.0273186033546 , 0.0320652636768 , 0.0347680051293 , 0.0340886759041 , 0.0206215775876 , 0.0295523404415 , 0.0238444578085 , 0.0309990951362 , 0.0255613141636 , 0.0366040625448 , 0.0381971366114 , 0.0303456344439 , 0.0325600097941 , 0.0300238108654 , 0.0267457914061 , 0.0352601792537 , 0.0321845534649 , 0.0292124529626 , 0.0385434049296 , 0.0328001234451 , 0.0261149485849 , 0.0274937196959 , 0.0277986045703 , 0.0377045627254 , 0.0382393912215 , 0.0305244682943 , 0.0300008081587 , 0.0340961653278 , 0.025888897155 , 0.0344048845872 , 0.0325675834667 , 0.0263162184783 , 0.0285118117132 , 0.0380964393773 , 0.0306108105192 , 0.0390230943581 , 0.0340081030651 , 0.0302116807794 , 0.0291408689786 , 0.0283510785995 , 0.0339925289886 , 0.0274292593127 , 0.0360747220412 , 0.0419221531054 , 0.0262039028839 , 0.0260163689155 , 0.040294535312 , 0.0264335518334 , 0.0364984244161 , 0.0295207579158 , 0.0253783206426 , 0.0300178394583 , 0.0317239825758 , 0.0246154358595 , 0.0285345446266 , 0.0262041553758 , 0.0311591871359 , 0.0315535430143 , 0.0314694994457 , 0.0339083957766 , 0.0313890315808 , 0.0301664047229 , 0.0237083748639 , 0.0352450310145 , 0.0339742162325 , 0.0316626009916 , 0.0286269019114 , 0.0293381205079 , 0.0283672555963 , 0.0386328552757 , 0.0386815948902 , 0.0280606802702 , 0.026880224465 , 0.0286720772557 , 0.0271961492268 , 0.0276751437547 , 0.0334079344157 , 0.0268580458885 , 0.0306209806564 , 0.0309541436482 , 0.033929764728 , 0.0327747090553 , 0.0312759169891 , 0.0285055470994 , 0.022158602111 , 0.0320366951346 , 0.0241879825157 , 0.028780622368 , 0.0310448620883 , 0.0278394781801 , 0.0335407215192 , 0.0321706593516 , 0.0386582578913 , 0.0368921837138 , 0.0382652890723 , 0.0275491100267 , 0.0361144532848 , 0.0319864907005 , 0.0373270215564 , 0.0297378914693 , 0.0220387378256 , 0.0308849038573 , 0.0266333543898 , 0.027863263095 , 0.0358390315496 , 0.0288187622648 , 0.0293401473673 , 0.0337006654923 , 0.0322745446642 , 0.0405330223879 , 0.0348649080932 , 0.0361417582081 , 0.0300460546833 , 0.0308950798398 , 0.0388184479486 , 0.0360243186886 , 0.0318336375388 , 0.0353191116995 , 0.0276729972982 , 0.0292001173848 , 0.0335246645525 , 0.023807204716 , 0.0277555772247 , 0.0358515957913 , 0.0360129687129 , 0.0289321991578 , 0.033207648519 , 0.0339371276818 , 0.029458733055 , 0.034983819658 , ])
