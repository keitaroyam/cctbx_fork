from scitbx import math
from scitbx.array_family import flex
from scitbx.array_family import shared
from stdlib import math as smath

from iotbx.xplor import map as xplor_map
from cctbx import uctbx



def xplor_map_type(xyz,m,N,radius,file_name='map.xplor'):
  gridding = xplor_map.gridding( [N*2+1]*3, [0]*3, [2*N]*3)
  grid = flex.grid(N*2+1, N*2+1,N*2+1)
  m.reshape( grid )
  uc = uctbx.unit_cell(" %s"%(radius*2.0)*3+"90 90 90")
  xplor_map.writer( file_name, ['no title lines'],uc, gridding,m)  # True)



def tst_nlm():
  nlm_array = math.nlm_array(10)
  nlm_array.set_coef(10,2,2, 3.0)
  a = nlm_array.get_coef(10,2,2)
  assert ( abs(a-3.0) ) <= 1e-5
  nlm_ind = shared.tiny_int_3( [(10,2,2),(8,2,2)]  )
  nlm_coef = flex.complex_double( [15.0+0j,15.0+0j] )
  assert nlm_array.load_coefs( nlm_ind , nlm_coef)
  a = nlm_array.get_coef(10, 2, 2)
  b = nlm_array.get_coef(8, 2, 2)
  assert ( abs(a-15.0) ) <= 1e-5
  assert ( abs(b-15.0) ) <= 1e-5
  nlm = nlm_array.nlm()
  cnlm = nlm_array.coefs()
  sel = nlm_array.select_on_nl(2,2)
  assert len(sel)==5
  assert 5 in sel
  assert 6 in sel
  assert 7 in sel
  assert 8 in sel
  assert 9 in sel


def tst_log_factorial():
  # Log factorial generator
  N=89
  lfg =  math.log_factorial_generator(N)
  ff = 1.0
  for ii in range(1,N):
    tmp = lfg.log_fact(ii)
    tmp2 = lfg.fact(ii)
    ff = ff*ii
    assert 1e10*abs(tmp2-ff)/ff<1


def tst_zernike_radial():
  N=50
  M=8
  lfg =  math.log_factorial_generator(N)
  for n in range(M):
    for l in range(n):
      if (n-l)%2==0:
        rzfa = math.zernike_radial(n,l, lfg)
        r = flex.double( flex.double(range(100000))/99999.0)
        a = rzfa.f( r )
        tmp = a*a*r*r
        tmp = flex.sum( tmp )/100000.0
        assert abs(tmp-1)<2e-2
        for nn in range(M):
          for ll in range(nn):
            if (nn-ll)%2==0:
              if (nn!=n):
                if ll==l:
                  rzfb = math.zernike_radial(nn,ll, lfg)
                  b = rzfb.f( r )
                  tmp = a*b*r*r
                  tmp = flex.sum( tmp )/100000.0
                  assert (tmp<1e-2)
                  #print n,l, nn,ll, tmp



def tst_zernike_grid():
  #THIS TEST TAKES A BIT OF TIME
  M=20
  N=4
  ddd = (M*2+1)
  zga = math.zernike_grid(M,N)
  zgb = math.zernike_grid(M,N)

  xyz = zga.xyz()
  coefs = zga.coefs()
  nlm = zga.nlm()

  for ii in range(nlm.size()):
    for jj in range(ii+1,nlm.size()):
      coefsa = coefs*0.0
      coefsb = coefs*0.0
      coefsa[ii]=1.0+1.0j
      coefsb[jj]=1.0+1.0j
      zga.load_coefs( nlm, coefsa )
      zgb.load_coefs( nlm, coefsb )
      fa = zga.f()
      fb = zgb.f()

      prodsum = flex.sum(fa*flex.conj(fb) )/xyz.size()
      prodsuma= flex.sum(fa*flex.conj(fa) )/xyz.size()
      prodsumb= flex.sum(fb*flex.conj(fb) )/xyz.size()

      t1 = abs(prodsum)
      t2 = abs(prodsuma)
      t3 = abs(prodsumb)
      t1 = 100.0*(t1/t2)
      t2 = 100.0*(abs(t2-t3)/t3)
      # unfortunately, this numerical integration scheme is not optimal. For certain
      # combinations of nlm, we see significant non-orthogonality that reduces when
      # we increase the number of points. A similar behavoir is seen in the radial
      # part of the Zernike polynome. If we compile withiout the radial function, similar
      # behavoir is seen using only the spherical harmonics functions.
      # For this reason, the liberal limts set below are ok
      assert t1<2.0
      assert t2<5.0


def tst_nl():
  this_nl_array = math.nl_array(5)
  nl = this_nl_array.nl()
  result= """"""
  for tnl in nl:
    result +=str(tnl)+"\n"
    assert (tnl[0]-tnl[1])%2==0
  expected_result = """(0, 0)
(1, 1)
(2, 0)
(2, 2)
(3, 1)
(3, 3)
(4, 0)
(4, 2)
(4, 4)
(5, 1)
(5, 3)
(5, 5)
"""
  assert result == expected_result
  coefs = this_nl_array.coefs()
  assert coefs.size() == nl.size()
  new_coefs = flex.double( range(nl.size() ) )
  assert this_nl_array.load_coefs( nl, new_coefs )
  new_nl = shared.tiny_int_2( [ (10,10) ] )
  new_coef = flex.double( [10.0] )
  assert not this_nl_array.load_coefs( new_nl, new_coef )
  coefs = this_nl_array.coefs()
  for x,y in zip(coefs,new_coefs):
    assert abs(x-y)<1e-5
  for tnl, cc in zip(nl,coefs):
    thc = this_nl_array.get_coef(tnl[0], tnl[1])
    assert abs(thc-cc)<1e-5
    this_nl_array.set_coef(tnl[0], tnl[1], 300 )
    thc = this_nl_array.get_coef(tnl[0], tnl[1])
    assert abs(thc-300)<1e-5






if __name__ == "__main__":
  tst_nl()
  tst_nlm()
  tst_log_factorial()
  tst_zernike_radial()
  tst_zernike_grid()

  print "OK"
