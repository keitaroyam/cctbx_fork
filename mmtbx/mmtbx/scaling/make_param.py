import os,sys, string, iotbx.phil

class phil_lego(object):
  """
This class facilitates the construction of phil parameter files
for the FA estimation program FATSO.
"""
  def __init__(self):

    self.default_expert_level_for_parameters_that_should_be_sensible_defaults='1'

    self.scaling_input = """ scaling.input{
__REPLACE__

expert_level=0
.type=int
.expert_level=__EXPERT_LEVEL__
}
"""
    self.basic_info = """basic{
  n_residues=None
  .type=float
  n_bases=None
  .type=float
  n_copies_per_asu=None
  .type=float
}
"""
    self.xray_data_basic="""xray_data{
  unit_cell=None
  .type=unit_cell

  space_group=None
  .type=space_group

  __REPLACE__
}
"""

    self.data_type="""__REPLACE__{
  file_name=None
  .type=path
  labels=None
  .type=strings
}
"""
    self.scaling_strategy="""scaling_strategy
.expert_level=__EXPERT_LEVEL__
{
  __REPLACE__
}
"""

    self.pre_scaler_protocol="""pre_scaler_protocol
.expert_level=__EXPERT_LEVEL__
{
high_resolution=None
.type=float
low_resolution=None
.type=float
aniso_correction=True
.type=bool
outlier_level_wilson=1e-6
.type=float
 outlier_level_extreme=1e-2
.type=float
}"""

    self.scale_protocol="""__REPLACE__
.expert_level=__EXPERT_LEVEL__
{
           target = ls loc *ls_and_loc None
         .type=choice
         iterations = *auto specified_by_max_iterations
         .type=choice
         max_iterations = 2
         .type=int

         least_squares_options{
           use_experimental_sigmas=True
           .type=bool
           scale_data=*intensities amplitudes
           .type=choice
           scale_target=basic *fancy
           .type=choice
         }

         local_scaling_options{
           use_experimental_sigmas=True
           .type=bool
           scale_data=intensities *amplitudes
           .type=choice
           scale_target=local_moment local_lsq *local_nikonov
           .type=choice
           max_depth=10
           .type=int
           target_neighbours=100
           .type=int
           neighbourhood_sphere=1
           .type=int
         }

         outlier_rejection_options{
           cut_level_sigma=3
           .type=float
           cut_level_rms_primary=4
           .type=float
           cut_level_rms_secondary=4
           .type=float
           protocol=solve rms *rms_and_sigma
           .type=choice
         }


}"""

    self.fa_estimation="""fa_estimation
.expert_level=__EXPERT_LEVEL__
{
   number_of_temrs_in_normalisation_curve=23
   .type=int
}
"""


    self.output="""output
{
     log = 'fatso.log'
     .type = path
     hklout = 'fatso.mtz'
     .type = path
     outlabel = '_ATSO'
     .type = str

}
"""

  def add_wavelength_info(self):
    tmp= """
    use_anomalous=True
    .type=bool
    .expert_level=5
    use_in_dispersive=True
    .type=bool
    .expert_level=5
    wavelength=None
    .type=float
    .expert_level=15
    f_prime=None
    .type=float
    .expert_level=15
    f_double_prime=None
    .type=float
    .expert_level=15
    }
    """
    self.data_type =self.data_type.replace( '}', tmp)


  def default_sad(self):
    outer_level = self.scaling_input
    outer_level = outer_level.replace( '__EXPERT_LEVEL__',
      self.default_expert_level_for_parameters_that_should_be_sensible_defaults)

    basic = self.basic_info
    data = self.data_type.replace( '__REPLACE__',
                                      'reference' )
    data = self.xray_data_basic.replace('__REPLACE__',
                                           data )
    scaler = self.pre_scaler_protocol + \
             self.scale_protocol.replace('__REPLACE__',
                                         'ano_protocol' )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    scaler = self.scaling_strategy.replace('__REPLACE__',
                                           scaler )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    scaler = scaler.replace( 'ls loc *ls_and_loc None',
                              '*loc None' )
    output = self.output

    result = outer_level.replace('__REPLACE__',
                                 basic+data+scaler+output)
    return result

  def default_sir(self):
    outer_level = self.scaling_input
    outer_level = outer_level.replace( '__EXPERT_LEVEL__',
      self.default_expert_level_for_parameters_that_should_be_sensible_defaults)

    basic = self.basic_info
    data = self.data_type.replace( '__REPLACE__',
                                      'native' ) \
                                      + \
            self.data_type.replace( '__REPLACE__',
                                      'derivative' )


    data = self.xray_data_basic.replace('__REPLACE__',
                                           data )

    scaler = self.scale_protocol.replace('__REPLACE__','iso_protocol' )

    scaler = self.pre_scaler_protocol + scaler

    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    scaler = self.scaling_strategy.replace('__REPLACE__',
                                           scaler )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    output = self.output

    result = outer_level.replace('__REPLACE__',
                                 basic+data+scaler+output)
    return result


  def default_siras(self):
    outer_level = self.scaling_input
    outer_level = outer_level.replace( '__EXPERT_LEVEL__',
      self.default_expert_level_for_parameters_that_should_be_sensible_defaults)

    basic = self.basic_info
    data = self.data_type.replace( '__REPLACE__',
                                      'native' ) \
                                      + \
            self.data_type.replace( '__REPLACE__',
                                      'derivative' )

    data = self.xray_data_basic.replace('__REPLACE__',
                                           data )

    scaler = self.scale_protocol.replace('__REPLACE__',
                                         'ano_protocol' )
    scaler = scaler.replace('ls loc *ls_and_loc None',
                            '*loc None' )

    scaler = self.pre_scaler_protocol + scaler + \
             self.scale_protocol.replace('__REPLACE__','iso_protocol' )

    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    scaler = self.scaling_strategy.replace('__REPLACE__',
                                           scaler )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )

    fa = self.fa_estimation.replace('__EXPERT_LEVEL__',
                            '10' )
    output = self.output

    result = outer_level.replace('__REPLACE__',
                                 basic+data+scaler+fa+output)
    return result

  def default_2wmad(self):
    self.add_wavelength_info()

    outer_level = self.scaling_input
    outer_level = outer_level.replace( '__EXPERT_LEVEL__',
      self.default_expert_level_for_parameters_that_should_be_sensible_defaults)

    basic = self.basic_info
    data = self.data_type.replace( '__REPLACE__',
                                      'wavelength1' ) \
                                      + \
            self.data_type.replace( '__REPLACE__',
                                      'wavelength2' )

    data = self.xray_data_basic.replace('__REPLACE__',
                                           data )

    scaler = self.scale_protocol.replace('__REPLACE__',
                                         'ano_protocol' )
    scaler = scaler.replace('ls loc *ls_and_loc None',
                            '*loc None' )

    scaler = self.pre_scaler_protocol + scaler + \
             self.scale_protocol.replace('__REPLACE__','iso_protocol' )

    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    scaler = self.scaling_strategy.replace('__REPLACE__',
                                           scaler )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    output = self.output

    result = outer_level.replace('__REPLACE__',
                                 basic+data+scaler+output)
    return result


  def default_3wmad(self):
    self.add_wavelength_info()

    outer_level = self.scaling_input
    outer_level = outer_level.replace( '__EXPERT_LEVEL__',
      self.default_expert_level_for_parameters_that_should_be_sensible_defaults)

    basic = self.basic_info
    data = self.data_type.replace( '__REPLACE__',
                                      'wavelength1' ) \
                                      + \
            self.data_type.replace( '__REPLACE__',
                                      'wavelength2' )    \
                                      + \
            self.data_type.replace( '__REPLACE__',
                                      'wavelength3' )

    data = self.xray_data_basic.replace('__REPLACE__',
                                           data )

    scaler = self.scale_protocol.replace('__REPLACE__',
                                         'ano_protocol' )
    scaler = scaler.replace('ls loc *ls_and_loc None',
                            '*loc None' )

    scaler = self.pre_scaler_protocol + scaler + \
             self.scale_protocol.replace('__REPLACE__','iso_protocol' )

    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )

    scaler = self.scaling_strategy.replace('__REPLACE__',
                                           scaler )
    scaler = scaler.replace('__EXPERT_LEVEL__',
                            '1' )
    output = self.output

    result = outer_level.replace('__REPLACE__',
                                 basic+data+scaler+output)
    return result



def run(args):
  okai=True
  if len(args)==0:
    print "Example parameter files lego-ed together from several phil blocks"
    print
    print "specifiy 'expert level' on command line via "
    print "    python make_param.py <expert_level>      "
    okai=False

  if okai:
    tester = phil_lego()
    print " ---------- SAD ----------"
    master_params = iotbx.phil.parse( tester.default_sad() )
    master_params.show(expert_level = int(args[0]) )
    print " ---------- SIR ----------"
    del master_params
    del tester
    tester = phil_lego()
    master_params = iotbx.phil.parse( tester.default_sir() )
    master_params.show(expert_level=int(args[0]))
    print " ---------- SIRAS ----------"
    del master_params
    del tester
    tester = phil_lego()
    master_params = iotbx.phil.parse( tester.default_siras() )
    master_params.show(expert_level=int(args[0]))
    print " ---------- 2WMAD ----------"
    del master_params
    del tester
    tester = phil_lego()
    master_params = iotbx.phil.parse( tester.default_2wmad() )
    master_params.show(expert_level=int(args[0]))
    print " ---------- 3WMAD ----------"
    del master_params
    del tester
    tester = phil_lego()
    master_params = iotbx.phil.parse( tester.default_3wmad() )
    master_params.show(expert_level=int(args[0]))
    print " ---------- 3WMAD ----------"
    del master_params
    del tester
    tester = phil_lego()
    master_params = iotbx.phil.parse( tester.default_3wmad() )
    master_params.show(expert_level=int(args[0]))


if (__name__ == "__main__"):
  run(sys.argv[1:])
