from scitbx import math
from scitbx.array_family import flex
from scitbx.array_family import shared
from stdlib import math as smath

from cctbx import uctbx





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


def tst_zernike_radial_2d():
  N=50
  M=15
  lfg =  math.log_factorial_generator(N)
  NNN = int(1e5)
  for n in range(M):
    for l in range(n+1):
      if (n-l)%2==0:
        rzfa = math.zernike_2d_radial(n,l, lfg)
        r = flex.double( flex.double(range(NNN))/float(NNN-1) )
        a = rzfa.f( r )
        tmp = a*a*r
        tmp = flex.sum( tmp )/float(NNN)
        tmp = tmp*(2*n+2)
        nnlk = rzfa.Nnlk()
        assert abs(tmp-1)<2e-2
        for nn in range(M):
          for ll in range(nn):
            if (nn-ll)%2==0:
              if (nn!=n):
                if ll==l:
                  rzfb = math.zernike_radial(nn,ll, lfg)
                  rzfa = math.zernike_radial(n,l, lfg)
                  b = rzfb.f( r )
                  a = rzfa.f( r )
                  tmp = a*b*r
                  tmp = flex.sum( tmp )/float(NNN)
                  #print n,nn,l,ll,tmp

def triple_partity_check(n,nn,nnn):
  tot=0
  if (n%2==0):
    tot+=1
  if (nn%2==0):
    tot+=1
  if (nnn%2==0):
    tot+=1
  if tot==3:
    return True
  if tot==0:
    return True

def triple_integral():
  N=50
  M=1
  lfg =  math.log_factorial_generator(N)
  NNN = int(1e6)
  from stdlib import math as smath
  r = flex.double( flex.double(range(NNN))/float(NNN-1) )
  for n in range(M):
    for nn in range(n,M):
      for nnn in range(nn,M):
        if triple_partity_check(n,nn,nnn):
          for l in range(min(n+1,nn+1,nnn+1)):
           if (n-l)%2==0:
            rzfa = math.zernike_2d_radial(n,l,   lfg)
            rzfb = math.zernike_2d_radial(nn,l,  lfg)
            rzfc = math.zernike_2d_radial(nnn,l, lfg)
            a = rzfa.f(r)
            b = rzfb.f(r)
            c = rzfc.f(r)
            tmp = flex.sum(a*b*c*r)/float(NNN)
            sign = 1
            if tmp < 0:
              tmp=-tmp
              sign=-1
            print n,nn,nnn,l,tmp #smath.log( tmp ), sign

def tst_zernike_2d_polynome(n,l,nn,ll):
  assert (n,l)!=(nn,ll)
  N=50
  lfg =  math.log_factorial_generator(N)
  NN=85

  rzfa = math.zernike_2d_radial(n,l,lfg)
  rap = math.zernike_2d_polynome(n,l,rzfa)
  rzfb = math.zernike_2d_radial(nn,ll,lfg)
  rbp = math.zernike_2d_polynome(nn,ll,rzfb)
  tmp1=0; tmp2=0; tmp3=0
  count=0
  for x in range(-NN,NN+1):
    for y in range(-NN,NN+1):
      rr = smath.sqrt(x*x+y*y)/NN
      tt = smath.atan2(y,x)
      if rr<=1:
        tmp1 += rap.f(rr,tt)*(rap.f(rr,tt)).conjugate()
        tmp2 += rbp.f(rr,tt)*(rbp.f(rr,tt)).conjugate()
        tmp3 += rbp.f(rr,tt)*(rap.f(rr,tt)).conjugate()
        count += 1
  tmp1 = ( 0.5*(2*n+2)*tmp1/count ).real
  tmp2 = ( 0.5*(2*nn+2)*tmp2/count ).real
  tmp3 = ( 0.5*smath.sqrt( (2*n+2)*(2*nn+2) )*tmp3/count ).real
  assert abs(tmp1-1)<1e-2
  assert abs(tmp2-1)<1e-2
  assert abs(tmp3)<1e-2

def tst_zernike_grid(skip_iteration_probability=0.95):
  #THIS TEST TAKES A BIT OF TIME
  M=20
  N=4
  ddd = (M*2+1)
  zga = math.zernike_grid(M,N,False)
  zgb = math.zernike_grid(M,N,False)

  xyz = zga.xyz()
  coefs = zga.coefs()
  nlm = zga.nlm()

  import random
  rng = random.Random(x=None)
  for ii in range(nlm.size()):
    for jj in range(ii+1,nlm.size()):
      if (rng.random() < skip_iteration_probability):
        continue
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


def tst_nss_spherical_harmonics():
  N=50
  M=20
  lfg =  math.log_factorial_generator(N)
  nsssphe = math.nss_spherical_harmonics(M+5,50000,lfg)

  a = nsssphe.legendre_lm(8,2)
  b = nsssphe.legendre_lm_pc(8,2)
  for aa,bb in zip(a,b):
    assert abs(aa-bb)<1e-7

  a = nsssphe.legendre_lm(14,3)
  b = nsssphe.legendre_lm_pc(14,3)
  for aa,bb in zip(a,b):
    assert abs(aa-bb)<1e-7

  lm=[ (0,0), (3,3), (4,1) ]

  theta = flex.double(range(100))*3.14/100.0
  phi = flex.double(range(100))*6.28/100.0
  for tt in theta:
    for pp in phi:
      r  = nsssphe.spherical_harmonic(20,10,tt,pp)
      rr = nsssphe.spherical_harmonic_pc(20,10,tt,pp)
      #print tt,pp, r.real, r.imag, 100.0*abs(r.real-rr.real)/(max(abs(r.real),1e-12)) , 100.0*abs(rr.imag-r.imag)/(max(abs(r.imag),1e-12))
      assert 100.0*abs(r.real-rr.real)/(max(abs(r.real),1e-12))<2.0
      assert 100.0*abs(rr.imag-r.imag)/(max(abs(r.imag),1e-12))<2.0





if __name__ == "__main__":
  #triple_integral()
  tst_zernike_2d_polynome(0,0,2,0)
  tst_zernike_2d_polynome(4,4,3,1)
  tst_zernike_2d_polynome(10,0,2,0)
  tst_zernike_2d_polynome(11,1,2,0)
  tst_zernike_2d_polynome(14,4,3,1)
  tst_zernike_2d_polynome(13,1,3,1)
  tst_zernike_radial_2d()
  tst_nss_spherical_harmonics()
  tst_nl()
  tst_nlm()
  tst_log_factorial()
  tst_zernike_radial()
  tst_zernike_grid()

  print "OK"
