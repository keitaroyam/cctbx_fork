from __future__ import division
one_letter_given_three_letter = {
"ALA": "A",
"ARG": "R",
"ASN": "N",
"ASP": "D",
"CYS": "C",
"GLN": "Q",
"GLU": "E",
"GLY": "G",
"HIS": "H",
"ILE": "I",
"LEU": "L",
"LYS": "K",
"MET": "M",
"MSE": "M",
"PHE": "F",
"PRO": "P",
"SER": "S",
"THR": "T",
"TRP": "W",
"TYR": "Y",
"VAL": "V",
}

one_letter_given_three_letter_modified_aa  = {
# modified AA
"CSO" : "C", # oxidized Cys
"LLP" : "K", # Lys + PLP
"MLY" : "K", # dimethyllysine
"PTR" : "Y", # phosphotyrosine
"SEP" : "S", # phosphoserine
"TPO" : "T", # phosphothreonine
"TYS" : "Y", # sulfonated tyrosine
}

three_letter_given_one_letter = {
"A": "ALA",
"C": "CYS",
"D": "ASP",
"E": "GLU",
"F": "PHE",
"G": "GLY",
"H": "HIS",
"I": "ILE",
"K": "LYS",
"L": "LEU",
"M": "MET",
"N": "ASN",
"P": "PRO",
"Q": "GLN",
"R": "ARG",
"S": "SER",
"T": "THR",
"V": "VAL",
"W": "TRP",
"Y": "TYR"}

three_letter_l_given_three_letter_d = {
"DAL": "ALA",
"DAR": "ARG",
"DAS": "ASP",
"DCY": "CYS",
"DGL": "GLU",
"DGN": "GLN",
"DHI": "HIS",
"DIL": "ILE",
"DLE": "LEU",
"DLY": "LYS",
"DPN": "PHE",
"DPR": "PRO",
"DSG": "ASN",
"DSN": "SER",
"DTH": "THR",
"DTR": "TRP",
"DTY": "TYR",
"DVA": "VAL",
"MED": "MET"}

three_letter_d_given_three_letter_l = {
"ALA": "DAL",
"ARG": "DAR",
"ASN": "DSG",
"ASP": "DAS",
"CYS": "DCY",
"GLN": "DGN",
"GLU": "DGL",
"HIS": "DHI",
"ILE": "DIL",
"LEU": "DLE",
"LYS": "DLY",
"MET": "MED",
"PHE": "DPN",
"PRO": "DPR",
"SER": "DSN",
"THR": "DTH",
"TRP": "DTR",
"TYR": "DTY",
"VAL": "DVA"}
