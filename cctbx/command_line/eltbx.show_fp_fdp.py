from __future__ import division
from cctbx.eltbx import henke, sasaki, wavelengths
from libtbx.option_parser import option_parser
from libtbx.utils import Sorry

parser = option_parser()
parser.add_option('--elements')
parser.add_option('--xray_source')
parser.add_option('--wavelength')
options, args = parser.parse_args()

print "Source: %s" % options.xray_source
print
for element in options.elements.split(','):
  print "Element: %s" % element
  fdp = []
  for table_name, table in (('Henke et al.', henke.table),
                            ('Sasaki et al.', sasaki.table)):
    inelastic_scattering = table(element)
    if (options.xray_source) :
      fp_fdp = inelastic_scattering.at_angstrom(
        wavelengths.characteristic(options.xray_source).as_angstrom())
    elif (options.wavelength) :
      fp_fdp = inelastic_scattering.at_angstrom(float(options.wavelength))
    else :
      raise Sorry("Either --xray_source=... or --wavelength=... required")
    print "  %-14s: f'=%-9.6g, f''=%-9.6f" % (
      table_name, fp_fdp.fp(), fp_fdp.fdp())
    fdp.append(fp_fdp.fdp())
  print "  diff f''=%.2f %%" % ((fdp[1] - fdp[0])/(fdp[1] + fdp[0]) * 100)
