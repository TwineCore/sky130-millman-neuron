# PEX R+C (magic) du neurone + contrôle d antenne
gds read ../layout/twine_neuron.gds
load twine_neuron
select top cell
extract do local
extract do capacitance
extract do coupling
extract do resistance
extract all
antennacheck debug
antennacheck
ext2sim labels on
ext2sim
extresist tolerance 10
extresist all
ext2spice lvs
ext2spice cthresh 0.01
ext2spice extresist on
ext2spice -o twine_neuron_pex.spice
quit -noprompt
