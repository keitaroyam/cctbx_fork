from __future__ import division
from libtbx import easy_run
from libtbx.test_utils import approx_equal

pdb_str_1 = """
CRYST1   50.273   31.111   38.194  90.00  90.00  90.00 P 1
ATOM      1  N   ALA A   1      45.103  22.406  32.854  1.00  1.00
ATOM      2  CA  ALA A   1      44.740  21.164  32.193  1.00  1.00
ATOM      3  C   ALA A   1      43.346  21.306  31.578  1.00  1.00
ATOM      4  O   ALA A   1      43.133  20.945  30.422  1.00  1.00
ATOM      5  CB  ALA A   1      44.821  20.010  33.194  1.00  1.00
ATOM      6  N   ALA A   2      42.432  21.834  32.380  1.00  1.00
ATOM      7  CA  ALA A   2      41.065  22.029  31.929  1.00  1.00
ATOM      8  C   ALA A   2      41.064  22.917  30.683  1.00  1.00
ATOM      9  O   ALA A   2      40.403  22.606  29.694  1.00  1.00
ATOM     10  CB  ALA A   2      40.231  22.620  33.067  1.00  1.00
ATOM     11  N   ALA A   3      41.815  24.006  30.772  1.00  1.00
ATOM     12  CA  ALA A   3      41.909  24.941  29.664  1.00  1.00
ATOM     13  C   ALA A   3      42.418  24.205  28.422  1.00  1.00
ATOM     14  O   ALA A   3      41.862  24.354  27.336  1.00  1.00
ATOM     15  CB  ALA A   3      42.812  26.111  30.059  1.00  1.00
ATOM     16  N   ALA A   4      43.471  23.427  28.626  1.00  1.00
ATOM     17  CA  ALA A   4      44.061  22.667  27.537  1.00  1.00
ATOM     18  C   ALA A   4      42.999  21.751  26.925  1.00  1.00
ATOM     19  O   ALA A   4      42.854  21.689  25.705  1.00  1.00
ATOM     20  CB  ALA A   4      45.273  21.890  28.054  1.00  1.00
ATOM     21  N   ALA A   5      42.282  21.062  27.802  1.00  1.00
ATOM     22  CA  ALA A   5      41.237  20.153  27.363  1.00  1.00
ATOM     23  C   ALA A   5      40.213  20.923  26.527  1.00  1.00
ATOM     24  O   ALA A   5      39.820  20.475  25.451  1.00  1.00
ATOM     25  CB  ALA A   5      40.605  19.475  28.580  1.00  1.00
ATOM     26  N   ALA A   6      39.811  22.071  27.055  1.00  1.00
ATOM     27  CA  ALA A   6      38.840  22.908  26.370  1.00  1.00
ATOM     28  C   ALA A   6      39.374  23.272  24.983  1.00  1.00
ATOM     29  O   ALA A   6      38.655  23.168  23.990  1.00  1.00
ATOM     30  CB  ALA A   6      38.541  24.144  27.222  1.00  1.00
ATOM     31  N   ALA A   7      40.631  23.689  24.959  1.00  1.00
ATOM     32  CA  ALA A   7      41.270  24.068  23.710  1.00  1.00
ATOM     33  C   ALA A   7      41.223  22.887  22.739  1.00  1.00
ATOM     34  O   ALA A   7      40.866  23.049  21.573  1.00  1.00
ATOM     35  CB  ALA A   7      42.699  24.537  23.988  1.00  1.00
ATOM     36  N   ALA A   8      41.588  21.722  23.256  1.00  1.00
ATOM     37  CA  ALA A   8      41.591  20.514  22.449  1.00  1.00
ATOM     38  C   ALA A   8      40.189  20.278  21.885  1.00  1.00
ATOM     39  O   ALA A   8      40.031  20.003  20.696  1.00  1.00
ATOM     40  CB  ALA A   8      42.085  19.337  23.293  1.00  1.00
ATOM     41  N   ALA A   9      39.204  20.394  22.765  1.00  1.00
ATOM     42  CA  ALA A   9      37.820  20.198  22.369  1.00  1.00
ATOM     43  C   ALA A   9      37.471  21.177  21.246  1.00  1.00
ATOM     44  O   ALA A   9      36.882  20.789  20.239  1.00  1.00
ATOM     45  CB  ALA A   9      36.912  20.361  23.589  1.00  1.00
ATOM     46  N   ALA A  10      37.849  22.430  21.459  1.00  1.00
ATOM     47  CA  ALA A  10      37.584  23.468  20.477  1.00  1.00
ATOM     48  C   ALA A  10      38.222  23.078  19.143  1.00  1.00
ATOM     49  O   ALA A  10      37.585  23.167  18.095  1.00  1.00
ATOM     50  CB  ALA A  10      38.099  24.810  21.001  1.00  1.00
ATOM     51  N   ALA A  11      39.475  22.654  19.225  1.00  1.00
ATOM     52  CA  ALA A  11      40.208  22.250  18.037  1.00  1.00
ATOM     53  C   ALA A  11      39.449  21.122  17.334  1.00  1.00
ATOM     54  O   ALA A  11      39.260  21.158  16.119  1.00  1.00
ATOM     55  CB  ALA A  11      41.629  21.842  18.427  1.00  1.00
ATOM     56  N   ALA A  12      39.035  20.146  18.129  1.00  1.00
ATOM     57  CA  ALA A  12      38.301  19.010  17.599  1.00  1.00
ATOM     58  C   ALA A  12      37.041  19.508  16.888  1.00  1.00
ATOM     59  O   ALA A  12      36.744  19.086  15.771  1.00  1.00
ATOM     60  CB  ALA A  12      37.983  18.032  18.732  1.00  1.00
ATOM     61  N   ALA A  13      36.333  20.401  17.565  1.00  1.00
ATOM     62  CA  ALA A  13      35.112  20.962  17.012  1.00  1.00
ATOM     63  C   ALA A  13      35.424  21.632  15.672  1.00  1.00
ATOM     64  O   ALA A  13      34.716  21.422  14.688  1.00  1.00
ATOM     65  CB  ALA A  13      34.494  21.933  18.019  1.00  1.00
ATOM     66  N   ALA A  14      36.486  22.426  15.677  1.00  1.00
ATOM     67  CA  ALA A  14      36.900  23.127  14.474  1.00  1.00
ATOM     68  C   ALA A  14      37.166  22.111  13.361  1.00  1.00
ATOM     69  O   ALA A  14      36.709  22.286  12.233  1.00  1.00
ATOM     70  CB  ALA A  14      38.126  23.989  14.783  1.00  1.00
ATOM     71  N   ALA A  15      37.905  21.070  13.719  1.00  1.00
ATOM     72  CA  ALA A  15      38.237  20.026  12.765  1.00  1.00
ATOM     73  C   ALA A  15      36.947  19.426  12.202  1.00  1.00
ATOM     74  O   ALA A  15      36.813  19.254  10.992  1.00  1.00
ATOM     75  CB  ALA A  15      39.121  18.977  13.443  1.00  1.00
ATOM     76  N   ALA A  16      36.028  19.124  13.109  1.00  1.00
ATOM     77  CA  ALA A  16      34.753  18.547  12.718  1.00  1.00
ATOM     78  C   ALA A  16      34.051  19.488  11.736  1.00  1.00
ATOM     79  O   ALA A  16      33.555  19.052  10.699  1.00  1.00
ATOM     80  CB  ALA A  16      33.912  18.273  13.966  1.00  1.00
ATOM     81  N   ALA A  17      34.033  20.763  12.099  1.00  1.00
ATOM     82  CA  ALA A  17      33.401  21.769  11.263  1.00  1.00
ATOM     83  C   ALA A  17      34.050  21.757   9.878  1.00  1.00
ATOM     84  O   ALA A  17      33.357  21.760   8.862  1.00  1.00
ATOM     85  CB  ALA A  17      33.503  23.136  11.943  1.00  1.00
ATOM     86  N   ALA A  18      35.376  21.744   9.881  1.00  1.00
ATOM     87  CA  ALA A  18      36.127  21.731   8.637  1.00  1.00
ATOM     88  C   ALA A  18      35.717  20.510   7.811  1.00  1.00
ATOM     89  O   ALA A  18      35.455  20.624   6.615  1.00  1.00
ATOM     90  CB  ALA A  18      37.625  21.751   8.945  1.00  1.00
ATOM     91  N   ALA A  19      35.674  19.368   8.483  1.00  1.00
ATOM     92  CA  ALA A  19      35.299  18.128   7.827  1.00  1.00
ATOM     93  C   ALA A  19      33.908  18.281   7.209  1.00  1.00
ATOM     94  O   ALA A  19      33.693  17.917   6.054  1.00  1.00
ATOM     95  CB  ALA A  19      35.368  16.977   8.832  1.00  1.00
ATOM     96  N   ALA A  20      32.998  18.820   8.008  1.00  1.00
ATOM     97  CA  ALA A  20      31.633  19.027   7.555  1.00  1.00
ATOM     98  C   ALA A  20      31.642  19.910   6.305  1.00  1.00
ATOM     99  O   ALA A  20      30.979  19.602   5.317  1.00  1.00
ATOM    100  CB  ALA A  20      30.804  19.630   8.690  1.00  1.00
TER
ATOM      1  N   ALA B   1       5.652   7.138  18.311  1.00  1.00           N
ATOM      2  CA  ALA B   1       6.710   6.420  17.620  1.00  1.00           C
ATOM      3  C   ALA B   1       7.114   7.197  16.366  1.00  1.00           C
ATOM      4  O   ALA B   1       8.300   7.396  16.108  1.00  1.00           O
ATOM      5  CB  ALA B   1       6.239   5.000  17.301  1.00  1.00           C
ATOM      6  N   ALA B   2       6.103   7.617  15.618  1.00  1.00           N
ATOM      7  CA  ALA B   2       6.338   8.368  14.397  1.00  1.00           C
ATOM      8  C   ALA B   2       7.143   9.628  14.724  1.00  1.00           C
ATOM      9  O   ALA B   2       8.122   9.938  14.047  1.00  1.00           O
ATOM     10  CB  ALA B   2       5.000   8.689  13.729  1.00  1.00           C
ATOM     11  N   ALA B   3       6.700  10.320  15.765  1.00  1.00           N
ATOM     12  CA  ALA B   3       7.367  11.539  16.190  1.00  1.00           C
ATOM     13  C   ALA B   3       8.832  11.229  16.510  1.00  1.00           C
ATOM     14  O   ALA B   3       9.731  11.947  16.077  1.00  1.00           O
ATOM     15  CB  ALA B   3       6.624  12.137  17.385  1.00  1.00           C
ATOM     16  N   ALA B   4       9.024  10.158  17.267  1.00  1.00           N
ATOM     17  CA  ALA B   4      10.363   9.744  17.649  1.00  1.00           C
ATOM     18  C   ALA B   4      11.197   9.499  16.390  1.00  1.00           C
ATOM     19  O   ALA B   4      12.332   9.963  16.290  1.00  1.00           O
ATOM     20  CB  ALA B   4      10.279   8.506  18.543  1.00  1.00           C
ATOM     21  N   ALA B   5      10.600   8.770  15.457  1.00  1.00           N
ATOM     22  CA  ALA B   5      11.273   8.458  14.208  1.00  1.00           C
ATOM     23  C   ALA B   5      11.667   9.759  13.506  1.00  1.00           C
ATOM     24  O   ALA B   5      12.799   9.904  13.047  1.00  1.00           O
ATOM     25  CB  ALA B   5      10.365   7.581  13.343  1.00  1.00           C
ATOM     26  N   ALA B   6      10.710  10.674  13.446  1.00  1.00           N
ATOM     27  CA  ALA B   6      10.944  11.959  12.808  1.00  1.00           C
ATOM     28  C   ALA B   6      12.121  12.657  13.492  1.00  1.00           C
ATOM     29  O   ALA B   6      13.019  13.166  12.823  1.00  1.00           O
ATOM     30  CB  ALA B   6       9.662  12.794  12.858  1.00  1.00           C
ATOM     31  N   ALA B   7      12.079  12.657  14.816  1.00  1.00           N
ATOM     32  CA  ALA B   7      13.131  13.284  15.598  1.00  1.00           C
ATOM     33  C   ALA B   7      14.475  12.646  15.241  1.00  1.00           C
ATOM     34  O   ALA B   7      15.458  13.347  15.005  1.00  1.00           O
ATOM     35  CB  ALA B   7      12.805  13.160  17.087  1.00  1.00           C
ATOM     36  N   ALA B   8      14.475  11.320  15.211  1.00  1.00           N
ATOM     37  CA  ALA B   8      15.682  10.580  14.886  1.00  1.00           C
ATOM     38  C   ALA B   8      16.184  11.010  13.507  1.00  1.00           C
ATOM     39  O   ALA B   8      17.372  11.280  13.329  1.00  1.00           O
ATOM     40  CB  ALA B   8      15.396   9.079  14.960  1.00  1.00           C
ATOM     41  N   ALA B   9      15.254  11.061  12.563  1.00  1.00           N
ATOM     42  CA  ALA B   9      15.588  11.455  11.205  1.00  1.00           C
ATOM     43  C   ALA B   9      16.218  12.850  11.222  1.00  1.00           C
ATOM     44  O   ALA B   9      17.248  13.078  10.591  1.00  1.00           O
ATOM     45  CB  ALA B   9      14.333  11.392  10.332  1.00  1.00           C
ATOM     46  N   ALA B  10      15.569  13.747  11.951  1.00  1.00           N
ATOM     47  CA  ALA B  10      16.053  15.113  12.060  1.00  1.00           C
ATOM     48  C   ALA B  10      17.479  15.103  12.612  1.00  1.00           C
ATOM     49  O   ALA B  10      18.360  15.777  12.082  1.00  1.00           O
ATOM     50  CB  ALA B  10      15.095  15.927  12.932  1.00  1.00           C
ATOM     51  N   ALA B  11      17.663  14.329  13.672  1.00  1.00           N
ATOM     52  CA  ALA B  11      18.968  14.221  14.304  1.00  1.00           C
ATOM     53  C   ALA B  11      19.990  13.737  13.273  1.00  1.00           C
ATOM     54  O   ALA B  11      21.079  14.297  13.161  1.00  1.00           O
ATOM     55  CB  ALA B  11      18.875  13.292  15.514  1.00  1.00           C
ATOM     56  N   ALA B  12      19.602  12.699  12.545  1.00  1.00           N
ATOM     57  CA  ALA B  12      20.470  12.133  11.527  1.00  1.00           C
ATOM     58  C   ALA B  12      20.836  13.218  10.513  1.00  1.00           C
ATOM     59  O   ALA B  12      22.003  13.372  10.155  1.00  1.00           O
ATOM     60  CB  ALA B  12      19.779  10.933  10.875  1.00  1.00           C
ATOM     61  N   ALA B  13      19.815  13.943  10.077  1.00  1.00           N
ATOM     62  CA  ALA B  13      20.014  15.010   9.111  1.00  1.00           C
ATOM     63  C   ALA B  13      21.014  16.023   9.674  1.00  1.00           C
ATOM     64  O   ALA B  13      21.945  16.433   8.983  1.00  1.00           O
ATOM     65  CB  ALA B  13      18.667  15.648   8.770  1.00  1.00           C
ATOM     66  N   ALA B  14      20.785  16.398  10.926  1.00  1.00           N
ATOM     67  CA  ALA B  14      21.654  17.355  11.589  1.00  1.00           C
ATOM     68  C   ALA B  14      23.089  16.823  11.587  1.00  1.00           C
ATOM     69  O   ALA B  14      24.025  17.550  11.258  1.00  1.00           O
ATOM     70  CB  ALA B  14      21.133  17.622  13.002  1.00  1.00           C
ATOM     71  N   ALA B  15      23.217  15.556  11.958  1.00  1.00           N
ATOM     72  CA  ALA B  15      24.521  14.919  12.002  1.00  1.00           C
ATOM     73  C   ALA B  15      25.171  14.997  10.619  1.00  1.00           C
ATOM     74  O   ALA B  15      26.340  15.358  10.497  1.00  1.00           O
ATOM     75  CB  ALA B  15      24.369  13.478  12.494  1.00  1.00           C
ATOM     76  N   ALA B  16      24.382  14.654   9.610  1.00  1.00           N
ATOM     77  CA  ALA B  16      24.866  14.682   8.240  1.00  1.00           C
ATOM     78  C   ALA B  16      25.353  16.093   7.904  1.00  1.00           C
ATOM     79  O   ALA B  16      26.437  16.263   7.348  1.00  1.00           O
ATOM     80  CB  ALA B  16      23.758  14.207   7.298  1.00  1.00           C
ATOM     81  N   ALA B  17      24.528  17.069   8.256  1.00  1.00           N
ATOM     82  CA  ALA B  17      24.862  18.459   7.998  1.00  1.00           C
ATOM     83  C   ALA B  17      26.190  18.795   8.678  1.00  1.00           C
ATOM     84  O   ALA B  17      27.071  19.398   8.067  1.00  1.00           O
ATOM     85  CB  ALA B  17      23.719  19.356   8.478  1.00  1.00           C
ATOM     86  N   ALA B  18      26.294  18.388   9.936  1.00  1.00           N
ATOM     87  CA  ALA B  18      27.502  18.638  10.705  1.00  1.00           C
ATOM     88  C   ALA B  18      28.699  18.017   9.984  1.00  1.00           C
ATOM     89  O   ALA B  18      29.736  18.659   9.826  1.00  1.00           O
ATOM     90  CB  ALA B  18      27.326  18.091  12.123  1.00  1.00           C
ATOM     91  N   ALA B  19      28.517  16.772   9.566  1.00  1.00           N
ATOM     92  CA  ALA B  19      29.568  16.057   8.864  1.00  1.00           C
ATOM     93  C   ALA B  19      29.971  16.844   7.615  1.00  1.00           C
ATOM     94  O   ALA B  19      31.157  17.040   7.355  1.00  1.00           O
ATOM     95  CB  ALA B  19      29.091  14.642   8.533  1.00  1.00           C
ATOM     96  N   ALA B  20      28.959  17.273   6.875  1.00  1.00           N
ATOM     97  CA  ALA B  20      29.191  18.036   5.660  1.00  1.00           C
ATOM     98  C   ALA B  20      30.003  19.289   5.995  1.00  1.00           C
ATOM     99  O   ALA B  20      30.979  19.602   5.317  1.00  1.00           O
ATOM    100  CB  ALA B  20      27.852  18.366   5.000  1.00  1.00           C
TER
END
"""

pdb_str_2 = """
CRYST1   20.469   15.134   33.877  90.00  90.00  90.00 P 1
ATOM      1  N   ALA A   1      17.299   8.429  30.537  1.00  1.00
ATOM      2  CA  ALA A   1      16.936   7.187  29.876  1.00  1.00
ATOM      3  C   ALA A   1      15.542   7.329  29.261  1.00  1.00
ATOM      4  O   ALA A   1      15.329   6.968  28.105  1.00  1.00
ATOM      5  CB  ALA A   1      17.017   6.033  30.877  1.00  1.00
ATOM      6  N   ALA A   2      14.628   7.857  30.063  1.00  1.00
ATOM      7  CA  ALA A   2      13.261   8.052  29.612  1.00  1.00
ATOM      8  C   ALA A   2      13.260   8.940  28.366  1.00  1.00
ATOM      9  O   ALA A   2      12.599   8.629  27.377  1.00  1.00
ATOM     10  CB  ALA A   2      12.427   8.643  30.750  1.00  1.00
ATOM     11  N   ALA A   3      14.011  10.029  28.455  1.00  1.00
ATOM     12  CA  ALA A   3      14.105  10.964  27.347  1.00  1.00
ATOM     13  C   ALA A   3      14.614  10.228  26.105  1.00  1.00
ATOM     14  O   ALA A   3      14.058  10.377  25.019  1.00  1.00
ATOM     15  CB  ALA A   3      15.008  12.134  27.742  1.00  1.00
ATOM     16  N   ALA A   4      15.667   9.450  26.309  1.00  1.00
ATOM     17  CA  ALA A   4      16.257   8.690  25.220  1.00  1.00
ATOM     18  C   ALA A   4      15.195   7.774  24.608  1.00  1.00
ATOM     19  O   ALA A   4      15.050   7.712  23.388  1.00  1.00
ATOM     20  CB  ALA A   4      17.469   7.913  25.737  1.00  1.00
ATOM     21  N   ALA A   5      14.478   7.085  25.485  1.00  1.00
ATOM     22  CA  ALA A   5      13.433   6.176  25.046  1.00  1.00
ATOM     23  C   ALA A   5      12.409   6.946  24.210  1.00  1.00
ATOM     24  O   ALA A   5      12.016   6.498  23.134  1.00  1.00
ATOM     25  CB  ALA A   5      12.801   5.498  26.263  1.00  1.00
ATOM     26  N   ALA A   6      12.007   8.094  24.738  1.00  1.00
ATOM     27  CA  ALA A   6      11.036   8.931  24.053  1.00  1.00
ATOM     28  C   ALA A   6      11.570   9.295  22.666  1.00  1.00
ATOM     29  O   ALA A   6      10.851   9.191  21.673  1.00  1.00
ATOM     30  CB  ALA A   6      10.737  10.167  24.905  1.00  1.00
ATOM     31  N   ALA A   7      12.827   9.712  22.642  1.00  1.00
ATOM     32  CA  ALA A   7      13.466  10.091  21.393  1.00  1.00
ATOM     33  C   ALA A   7      13.419   8.910  20.422  1.00  1.00
ATOM     34  O   ALA A   7      13.062   9.072  19.256  1.00  1.00
ATOM     35  CB  ALA A   7      14.895  10.560  21.671  1.00  1.00
ATOM     36  N   ALA A   8      13.784   7.745  20.939  1.00  1.00
ATOM     37  CA  ALA A   8      13.787   6.537  20.132  1.00  1.00
ATOM     38  C   ALA A   8      12.385   6.301  19.568  1.00  1.00
ATOM     39  O   ALA A   8      12.227   6.026  18.379  1.00  1.00
ATOM     40  CB  ALA A   8      14.281   5.360  20.976  1.00  1.00
ATOM     41  N   ALA A   9      11.400   6.417  20.448  1.00  1.00
ATOM     42  CA  ALA A   9      10.016   6.221  20.052  1.00  1.00
ATOM     43  C   ALA A   9       9.667   7.200  18.929  1.00  1.00
ATOM     44  O   ALA A   9       9.078   6.812  17.922  1.00  1.00
ATOM     45  CB  ALA A   9       9.108   6.384  21.272  1.00  1.00
ATOM     46  N   ALA A  10      10.045   8.453  19.142  1.00  1.00
ATOM     47  CA  ALA A  10       9.780   9.491  18.160  1.00  1.00
ATOM     48  C   ALA A  10      10.418   9.101  16.826  1.00  1.00
ATOM     49  O   ALA A  10       9.781   9.190  15.778  1.00  1.00
ATOM     50  CB  ALA A  10      10.295  10.833  18.684  1.00  1.00
ATOM     51  N   ALA A  11      11.671   8.677  16.908  1.00  1.00
ATOM     52  CA  ALA A  11      12.404   8.273  15.720  1.00  1.00
ATOM     53  C   ALA A  11      11.645   7.145  15.017  1.00  1.00
ATOM     54  O   ALA A  11      11.456   7.181  13.802  1.00  1.00
ATOM     55  CB  ALA A  11      13.825   7.865  16.110  1.00  1.00
ATOM     56  N   ALA A  12      11.231   6.169  15.812  1.00  1.00
ATOM     57  CA  ALA A  12      10.497   5.033  15.282  1.00  1.00
ATOM     58  C   ALA A  12       9.237   5.531  14.571  1.00  1.00
ATOM     59  O   ALA A  12       8.940   5.109  13.454  1.00  1.00
ATOM     60  CB  ALA A  12      10.179   4.055  16.415  1.00  1.00
ATOM     61  N   ALA A  13       8.529   6.424  15.248  1.00  1.00
ATOM     62  CA  ALA A  13       7.308   6.985  14.695  1.00  1.00
ATOM     63  C   ALA A  13       7.620   7.655  13.355  1.00  1.00
ATOM     64  O   ALA A  13       6.912   7.445  12.371  1.00  1.00
ATOM     65  CB  ALA A  13       6.690   7.956  15.702  1.00  1.00
ATOM     66  N   ALA A  14       8.682   8.449  13.360  1.00  1.00
ATOM     67  CA  ALA A  14       9.096   9.150  12.157  1.00  1.00
ATOM     68  C   ALA A  14       9.362   8.134  11.044  1.00  1.00
ATOM     69  O   ALA A  14       8.905   8.309   9.916  1.00  1.00
ATOM     70  CB  ALA A  14      10.322  10.012  12.466  1.00  1.00
ATOM     71  N   ALA A  15      10.101   7.093  11.402  1.00  1.00
ATOM     72  CA  ALA A  15      10.433   6.049  10.448  1.00  1.00
ATOM     73  C   ALA A  15       9.143   5.449   9.885  1.00  1.00
ATOM     74  O   ALA A  15       9.009   5.277   8.675  1.00  1.00
ATOM     75  CB  ALA A  15      11.317   5.000  11.126  1.00  1.00
ATOM     76  N   ALA A  16       8.224   5.147  10.792  1.00  1.00
ATOM     77  CA  ALA A  16       6.949   4.570  10.401  1.00  1.00
ATOM     78  C   ALA A  16       6.247   5.511   9.419  1.00  1.00
ATOM     79  O   ALA A  16       5.751   5.075   8.382  1.00  1.00
ATOM     80  CB  ALA A  16       6.108   4.296  11.649  1.00  1.00
ATOM     81  N   ALA A  17       6.229   6.786   9.782  1.00  1.00
ATOM     82  CA  ALA A  17       5.597   7.792   8.946  1.00  1.00
ATOM     83  C   ALA A  17       6.246   7.780   7.561  1.00  1.00
ATOM     84  O   ALA A  17       5.553   7.783   6.545  1.00  1.00
ATOM     85  CB  ALA A  17       5.699   9.159   9.626  1.00  1.00
ATOM     86  N   ALA A  18       7.572   7.767   7.564  1.00  1.00
ATOM     87  CA  ALA A  18       8.323   7.754   6.320  1.00  1.00
ATOM     88  C   ALA A  18       7.913   6.533   5.494  1.00  1.00
ATOM     89  O   ALA A  18       7.651   6.647   4.298  1.00  1.00
ATOM     90  CB  ALA A  18       9.821   7.774   6.628  1.00  1.00
ATOM     91  N   ALA A  19       7.870   5.391   6.166  1.00  1.00
ATOM     92  CA  ALA A  19       7.495   4.151   5.510  1.00  1.00
ATOM     93  C   ALA A  19       6.104   4.304   4.892  1.00  1.00
ATOM     94  O   ALA A  19       5.889   3.940   3.737  1.00  1.00
ATOM     95  CB  ALA A  19       7.564   3.000   6.515  1.00  1.00
ATOM     96  N   ALA A  20       5.194   4.843   5.691  1.00  1.00
ATOM     97  CA  ALA A  20       3.829   5.050   5.238  1.00  1.00
ATOM     98  C   ALA A  20       3.838   5.933   3.988  1.00  1.00
ATOM     99  O   ALA A  20       3.175   5.625   3.000  1.00  1.00
ATOM    100  CB  ALA A  20       3.000   5.653   6.373  1.00  1.00
TER
ATOM      1  N   ALA B   1     -22.152  -6.839  15.994  1.00  1.00           N
ATOM      2  CA  ALA B   1     -21.094  -7.557  15.303  1.00  1.00           C
ATOM      3  C   ALA B   1     -20.690  -6.780  14.049  1.00  1.00           C
ATOM      4  O   ALA B   1     -19.504  -6.581  13.791  1.00  1.00           O
ATOM      5  CB  ALA B   1     -21.565  -8.977  14.984  1.00  1.00           C
ATOM      6  N   ALA B   2     -21.701  -6.360  13.301  1.00  1.00           N
ATOM      7  CA  ALA B   2     -21.466  -5.609  12.080  1.00  1.00           C
ATOM      8  C   ALA B   2     -20.661  -4.349  12.407  1.00  1.00           C
ATOM      9  O   ALA B   2     -19.682  -4.039  11.730  1.00  1.00           O
ATOM     10  CB  ALA B   2     -22.804  -5.288  11.412  1.00  1.00           C
ATOM     11  N   ALA B   3     -21.104  -3.657  13.448  1.00  1.00           N
ATOM     12  CA  ALA B   3     -20.437  -2.438  13.873  1.00  1.00           C
ATOM     13  C   ALA B   3     -18.972  -2.748  14.193  1.00  1.00           C
ATOM     14  O   ALA B   3     -18.073  -2.030  13.760  1.00  1.00           O
ATOM     15  CB  ALA B   3     -21.180  -1.840  15.068  1.00  1.00           C
ATOM     16  N   ALA B   4     -18.780  -3.819  14.950  1.00  1.00           N
ATOM     17  CA  ALA B   4     -17.441  -4.233  15.332  1.00  1.00           C
ATOM     18  C   ALA B   4     -16.607  -4.478  14.073  1.00  1.00           C
ATOM     19  O   ALA B   4     -15.472  -4.014  13.973  1.00  1.00           O
ATOM     20  CB  ALA B   4     -17.525  -5.471  16.226  1.00  1.00           C
ATOM     21  N   ALA B   5     -17.204  -5.207  13.140  1.00  1.00           N
ATOM     22  CA  ALA B   5     -16.531  -5.519  11.891  1.00  1.00           C
ATOM     23  C   ALA B   5     -16.137  -4.218  11.189  1.00  1.00           C
ATOM     24  O   ALA B   5     -15.005  -4.073  10.730  1.00  1.00           O
ATOM     25  CB  ALA B   5     -17.439  -6.396  11.026  1.00  1.00           C
ATOM     26  N   ALA B   6     -17.094  -3.303  11.129  1.00  1.00           N
ATOM     27  CA  ALA B   6     -16.860  -2.018  10.491  1.00  1.00           C
ATOM     28  C   ALA B   6     -15.683  -1.320  11.175  1.00  1.00           C
ATOM     29  O   ALA B   6     -14.785  -0.811  10.506  1.00  1.00           O
ATOM     30  CB  ALA B   6     -18.142  -1.183  10.541  1.00  1.00           C
ATOM     31  N   ALA B   7     -15.725  -1.320  12.499  1.00  1.00           N
ATOM     32  CA  ALA B   7     -14.673  -0.693  13.281  1.00  1.00           C
ATOM     33  C   ALA B   7     -13.329  -1.331  12.924  1.00  1.00           C
ATOM     34  O   ALA B   7     -12.346  -0.630  12.688  1.00  1.00           O
ATOM     35  CB  ALA B   7     -14.999  -0.817  14.770  1.00  1.00           C
ATOM     36  N   ALA B   8     -13.329  -2.657  12.894  1.00  1.00           N
ATOM     37  CA  ALA B   8     -12.122  -3.397  12.569  1.00  1.00           C
ATOM     38  C   ALA B   8     -11.620  -2.967  11.190  1.00  1.00           C
ATOM     39  O   ALA B   8     -10.432  -2.697  11.012  1.00  1.00           O
ATOM     40  CB  ALA B   8     -12.408  -4.898  12.643  1.00  1.00           C
ATOM     41  N   ALA B   9     -12.550  -2.916  10.246  1.00  1.00           N
ATOM     42  CA  ALA B   9     -12.216  -2.522   8.888  1.00  1.00           C
ATOM     43  C   ALA B   9     -11.586  -1.127   8.905  1.00  1.00           C
ATOM     44  O   ALA B   9     -10.556  -0.899   8.274  1.00  1.00           O
ATOM     45  CB  ALA B   9     -13.471  -2.585   8.015  1.00  1.00           C
ATOM     46  N   ALA B  10     -12.235  -0.230   9.634  1.00  1.00           N
ATOM     47  CA  ALA B  10     -11.751   1.136   9.743  1.00  1.00           C
ATOM     48  C   ALA B  10     -10.325   1.126  10.295  1.00  1.00           C
ATOM     49  O   ALA B  10      -9.444   1.800   9.765  1.00  1.00           O
ATOM     50  CB  ALA B  10     -12.709   1.950  10.615  1.00  1.00           C
ATOM     51  N   ALA B  11     -10.141   0.352  11.355  1.00  1.00           N
ATOM     52  CA  ALA B  11      -8.836   0.244  11.987  1.00  1.00           C
ATOM     53  C   ALA B  11      -7.814  -0.240  10.956  1.00  1.00           C
ATOM     54  O   ALA B  11      -6.725   0.320  10.844  1.00  1.00           O
ATOM     55  CB  ALA B  11      -8.929  -0.685  13.197  1.00  1.00           C
ATOM     56  N   ALA B  12      -8.202  -1.278  10.228  1.00  1.00           N
ATOM     57  CA  ALA B  12      -7.334  -1.844   9.210  1.00  1.00           C
ATOM     58  C   ALA B  12      -6.968  -0.759   8.196  1.00  1.00           C
ATOM     59  O   ALA B  12      -5.801  -0.605   7.838  1.00  1.00           O
ATOM     60  CB  ALA B  12      -8.025  -3.044   8.558  1.00  1.00           C
ATOM     61  N   ALA B  13      -7.989  -0.034   7.760  1.00  1.00           N
ATOM     62  CA  ALA B  13      -7.790   1.033   6.794  1.00  1.00           C
ATOM     63  C   ALA B  13      -6.790   2.046   7.357  1.00  1.00           C
ATOM     64  O   ALA B  13      -5.859   2.456   6.666  1.00  1.00           O
ATOM     65  CB  ALA B  13      -9.137   1.671   6.453  1.00  1.00           C
ATOM     66  N   ALA B  14      -7.019   2.421   8.609  1.00  1.00           N
ATOM     67  CA  ALA B  14      -6.150   3.378   9.272  1.00  1.00           C
ATOM     68  C   ALA B  14      -4.715   2.846   9.270  1.00  1.00           C
ATOM     69  O   ALA B  14      -3.779   3.573   8.941  1.00  1.00           O
ATOM     70  CB  ALA B  14      -6.671   3.645  10.685  1.00  1.00           C
ATOM     71  N   ALA B  15      -4.587   1.579   9.641  1.00  1.00           N
ATOM     72  CA  ALA B  15      -3.283   0.942   9.685  1.00  1.00           C
ATOM     73  C   ALA B  15      -2.633   1.020   8.302  1.00  1.00           C
ATOM     74  O   ALA B  15      -1.464   1.381   8.180  1.00  1.00           O
ATOM     75  CB  ALA B  15      -3.435  -0.499  10.177  1.00  1.00           C
ATOM     76  N   ALA B  16      -3.422   0.677   7.293  1.00  1.00           N
ATOM     77  CA  ALA B  16      -2.938   0.705   5.923  1.00  1.00           C
ATOM     78  C   ALA B  16      -2.451   2.116   5.587  1.00  1.00           C
ATOM     79  O   ALA B  16      -1.367   2.286   5.031  1.00  1.00           O
ATOM     80  CB  ALA B  16      -4.046   0.230   4.981  1.00  1.00           C
ATOM     81  N   ALA B  17      -3.276   3.092   5.939  1.00  1.00           N
ATOM     82  CA  ALA B  17      -2.942   4.482   5.681  1.00  1.00           C
ATOM     83  C   ALA B  17      -1.614   4.818   6.361  1.00  1.00           C
ATOM     84  O   ALA B  17      -0.733   5.421   5.750  1.00  1.00           O
ATOM     85  CB  ALA B  17      -4.085   5.379   6.161  1.00  1.00           C
ATOM     86  N   ALA B  18      -1.510   4.411   7.619  1.00  1.00           N
ATOM     87  CA  ALA B  18      -0.302   4.661   8.388  1.00  1.00           C
ATOM     88  C   ALA B  18       0.895   4.040   7.667  1.00  1.00           C
ATOM     89  O   ALA B  18       1.932   4.682   7.509  1.00  1.00           O
ATOM     90  CB  ALA B  18      -0.478   4.114   9.806  1.00  1.00           C
ATOM     91  N   ALA B  19       0.713   2.795   7.249  1.00  1.00           N
ATOM     92  CA  ALA B  19       1.764   2.080   6.547  1.00  1.00           C
ATOM     93  C   ALA B  19       2.167   2.867   5.298  1.00  1.00           C
ATOM     94  O   ALA B  19       3.353   3.063   5.038  1.00  1.00           O
ATOM     95  CB  ALA B  19       1.287   0.665   6.216  1.00  1.00           C
ATOM     96  N   ALA B  20       1.155   3.296   4.558  1.00  1.00           N
ATOM     97  CA  ALA B  20       1.387   4.059   3.343  1.00  1.00           C
ATOM     98  C   ALA B  20       2.199   5.312   3.678  1.00  1.00           C
ATOM     99  O   ALA B  20       3.175   5.625   3.000  1.00  1.00           O
ATOM    100  CB  ALA B  20       0.048   4.389   2.683  1.00  1.00           C
END
"""

pdb_str_3 = """
CRYST1   50.273   31.111   38.194  90.00  90.00  90.00 P 1
ATOM      1  N   ALA A   1      45.103  22.406  32.854  1.00  1.00
ATOM      2  CA  ALA A   1      44.740  21.164  32.193  1.00  1.00
ATOM      3  C   ALA A   1      43.346  21.306  31.578  1.00  1.00
ATOM      4  O   ALA A   1      43.133  20.945  30.422  1.00  1.00
ATOM      5  CB  ALA A   1      44.821  20.010  33.194  1.00  1.00
ATOM      6  N   ALA A   2      42.432  21.834  32.380  1.00  1.00
ATOM      7  CA  ALA A   2      41.065  22.029  31.929  1.00  1.00
ATOM      8  C   ALA A   2      41.064  22.917  30.683  1.00  1.00
ATOM      9  O   ALA A   2      40.403  22.606  29.694  1.00  1.00
ATOM     10  CB  ALA A   2      40.231  22.620  33.067  1.00  1.00
ATOM     11  N   ALA A   3      41.815  24.006  30.772  1.00  1.00
ATOM     12  CA  ALA A   3      41.909  24.941  29.664  1.00  1.00
ATOM     13  C   ALA A   3      42.418  24.205  28.422  1.00  1.00
ATOM     14  O   ALA A   3      41.862  24.354  27.336  1.00  1.00
ATOM     15  CB  ALA A   3      42.812  26.111  30.059  1.00  1.00
ATOM     16  N   ALA A   4      43.471  23.427  28.626  1.00  1.00
ATOM     17  CA  ALA A   4      44.061  22.667  27.537  1.00  1.00
ATOM     18  C   ALA A   4      42.999  21.751  26.925  1.00  1.00
ATOM     19  O   ALA A   4      42.854  21.689  25.705  1.00  1.00
ATOM     20  CB  ALA A   4      45.273  21.890  28.054  1.00  1.00
ATOM     21  N   ALA A   5      42.282  21.062  27.802  1.00  1.00
ATOM     22  CA  ALA A   5      41.237  20.153  27.363  1.00  1.00
ATOM     23  C   ALA A   5      40.213  20.923  26.527  1.00  1.00
ATOM     24  O   ALA A   5      39.820  20.475  25.451  1.00  1.00
ATOM     25  CB  ALA A   5      40.605  19.475  28.580  1.00  1.00
ATOM     26  N   ALA A   6      39.811  22.071  27.055  1.00  1.00
ATOM     27  CA  ALA A   6      38.840  22.908  26.370  1.00  1.00
ATOM     28  C   ALA A   6      39.374  23.272  24.983  1.00  1.00
ATOM     29  O   ALA A   6      38.655  23.168  23.990  1.00  1.00
ATOM     30  CB  ALA A   6      38.541  24.144  27.222  1.00  1.00
TER
ATOM      1  N   ALA B   1       5.652   7.138  18.311  1.00  1.00           N
ATOM      2  CA  ALA B   1       6.710   6.420  17.620  1.00  1.00           C
ATOM      3  C   ALA B   1       7.114   7.197  16.366  1.00  1.00           C
ATOM      4  O   ALA B   1       8.300   7.396  16.108  1.00  1.00           O
ATOM      5  CB  ALA B   1       6.239   5.000  17.301  1.00  1.00           C
ATOM      6  N   ALA B   2       6.103   7.617  15.618  1.00  1.00           N
ATOM      7  CA  ALA B   2       6.338   8.368  14.397  1.00  1.00           C
ATOM      8  C   ALA B   2       7.143   9.628  14.724  1.00  1.00           C
ATOM      9  O   ALA B   2       8.122   9.938  14.047  1.00  1.00           O
ATOM     10  CB  ALA B   2       5.000   8.689  13.729  1.00  1.00           C
ATOM     11  N   ALA B   3       6.700  10.320  15.765  1.00  1.00           N
ATOM     12  CA  ALA B   3       7.367  11.539  16.190  1.00  1.00           C
ATOM     13  C   ALA B   3       8.832  11.229  16.510  1.00  1.00           C
ATOM     14  O   ALA B   3       9.731  11.947  16.077  1.00  1.00           O
ATOM     15  CB  ALA B   3       6.624  12.137  17.385  1.00  1.00           C
ATOM     16  N   ALA B   4       9.024  10.158  17.267  1.00  1.00           N
ATOM     17  CA  ALA B   4      10.363   9.744  17.649  1.00  1.00           C
ATOM     18  C   ALA B   4      11.197   9.499  16.390  1.00  1.00           C
ATOM     19  O   ALA B   4      12.332   9.963  16.290  1.00  1.00           O
ATOM     20  CB  ALA B   4      10.279   8.506  18.543  1.00  1.00           C
ATOM     21  N   ALA B   5      10.600   8.770  15.457  1.00  1.00           N
ATOM     22  CA  ALA B   5      11.273   8.458  14.208  1.00  1.00           C
ATOM     23  C   ALA B   5      11.667   9.759  13.506  1.00  1.00           C
ATOM     24  O   ALA B   5      12.799   9.904  13.047  1.00  1.00           O
ATOM     25  CB  ALA B   5      10.365   7.581  13.343  1.00  1.00           C
ATOM     26  N   ALA B   6      10.710  10.674  13.446  1.00  1.00           N
ATOM     27  CA  ALA B   6      10.944  11.959  12.808  1.00  1.00           C
ATOM     28  C   ALA B   6      12.121  12.657  13.492  1.00  1.00           C
ATOM     29  O   ALA B   6      13.019  13.166  12.823  1.00  1.00           O
ATOM     30  CB  ALA B   6       9.662  12.794  12.858  1.00  1.00           C
TER
END
"""

pdb_str_4 = """
CRYST1   18.000   18.000   18.000  90.00  90.00  90.00 P 1
ATOM      0  O   HOH A   0       5.000   5.000   5.000  1.00 40.00           O
ATOM      2  O   HOH A   2       5.000   7.000   7.000  1.00 40.00           O
ATOM      4  O   HOH A   4       5.000   9.000   9.000  1.00 40.00           O
ATOM      6  O   HOH A   6       5.000  11.000  11.000  1.00 40.00           O
ATOM      8  O   HOH A   8       5.000  13.000  13.000  1.00 40.00           O
TER
ATOM      0  O   HOH B   0       5.000   5.000   5.000  1.00 40.00           O
ATOM      2  O   HOH B   2       7.000   5.000   7.000  1.00 40.00           O
ATOM      4  O   HOH B   4       9.000   5.000   9.000  1.00 40.00           O
ATOM      6  O   HOH B   6      11.000   5.000  11.000  1.00 40.00           O
ATOM      8  O   HOH B   8      13.000   5.000  13.000  1.00 40.00           O
TER
ATOM      0  O   HOH C   0       5.000   5.000   5.000  1.00 40.00           O
ATOM      2  O   HOH C   2       7.000   7.000   5.000  1.00 40.00           O
ATOM      4  O   HOH C   4       9.000   9.000   5.000  1.00 40.00           O
ATOM      6  O   HOH C   6      11.000  11.000   5.000  1.00 40.00           O
ATOM      8  O   HOH C   8      13.000  13.000   5.000  1.00 40.00           O
TER
END
"""

def run_cmd(fn, log, s1, s2):
  cmd = " ".join([
    "phenix.angle",
    "%s"%fn,
    "'%s'"%s1,
    "'%s'"%s2,
    ">%s"%log])
  easy_run.call(cmd)
  return float(easy_run.go(
    command="grep 'Angle :' "+log).stdout_lines[0].split()[2])

def exercise_00(prefix="tst_phenix_angle_cmd_00"):
  for i, pdb_str in enumerate([pdb_str_1, pdb_str_2, pdb_str_3, pdb_str_4]):
    prefix_i = prefix + str(i)
    fn = prefix_i + ".pdb"
    log = "%s.log"%prefix_i
    of = open(fn, "w")
    print >> of, pdb_str
    of.close()
    r = run_cmd(fn=fn, log=log, s1="chain A", s2="chain B")
    if  (i==0 or i==1): assert approx_equal(r, 87, 1)
    elif(i==2):         assert approx_equal(r, 90, 1)
    elif(i==3):         assert approx_equal(r, 60, 0.001)
    else: assert 0
    if(i==3):
      r = run_cmd(fn=fn, log=log, s1="chain A", s2="chain C")
      assert approx_equal(r, 60, 0.001)
      r = run_cmd(fn=fn, log=log, s1="chain B", s2="chain C")
      assert approx_equal(r, 60, 0.001)

def exercise_01(prefix="tst_phenix_angle_cmd_01"):
  fn = prefix + ".pdb"
  log = "%s.log"%prefix
  of = open(fn, "w")
  print >> of, pdb_str_4
  of.close()
  r = run_cmd(fn=fn, log=log, s1="chain A and (resseq 0 or resseq 8)",
    s2="chain B and (resseq 0 or resseq 8)")
  assert approx_equal(r, 60, 0.001)

if (__name__ == "__main__"):
  exercise_00()
  exercise_01()
