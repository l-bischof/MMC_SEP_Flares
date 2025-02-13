# Modeling Magnetic Connectivity of Solar Energetic Particle Events and Solar Flares

Continuation of a masters thesis by Fabian Kistler (ETH Zurich) supervised by Louise Harra (PMOD & ETH Zurich) and Nils Janiztek (PMOD & ETH Zurich).

## Description:

This project aims to model the accuracy of the magnetic connectivity tool (MCT) [4]. This is done using data from the Spectrometer/Telescope for Imaging X-rays (STIX) [3], which is condensed by the STIX team into the STIX flare list [2] (whereas we use the data from March 18, 2021, to May 31, 2024), and the STEP and EPT sensors of the Energetic Particle Detector (EPD) [5].

This project contains the code used for this project and should allow its user to automate the process of finding magnetically connected flare - SEP electron events. As there are many factors influencing the accuracy of the automated process, it is advised to mainly use this in a pre-selection process or manually refine the results. Scientific advancements in the field of solar physics and improvements of our method will hopefully increase the accuracy of this automated process to a point where these manual steps will not be needed anymore.

## Usage:

1. Go into the *Code* directory and change the variable *download_dir* in *connectivity_tool.py* to the path to your download directory.
   
2. Generate the required datasets with *generate_epd_dataset.py* and *generate_solar_mach_dataset.py*.
   
    a. In *generate_epd_dataset.py* set start and end date* to only generate the dataset for the required time period.
   
    b. Depending on the time period that is wished to be examined, this might take quite a bit of memory space. Hence the upload of the full datasets is omitted.

3. a) Run the script for the STEP sensor *step_comparison.py* after setting the start and end date correctly*.

3. b) Run the script for the EPT sensor *ept_comparison.py* after setting the start and end date correctly* and choosing the wished viewing angle.

\* write the date in the yyyy-mm-dd format

## References:

(1) J. Gieseler, N. Dresing, C. Palmroos, J. L. Freiherr von Forstner, D. J. Price, R. Vainio, A. Kouloumvakos, L. Rodríguez-García, D. Trotta, V. Génot et al., “Solar-mach: An opensource tool to analyze solar magnetic connection configurations,” Frontiers in Astronomy and Space Sciences, vol. 9, p. 1058810, 2023.

(2) L. Hayes, H. Collier, and A. Battaglia, “Solar orbiter/stix science flare list,” URL = [https://github.com/hayesla/stix](https://github.com/hayesla/stix_flarelist_science) flarelist science.

(3) S. Krucker, G. J. Hurford, O. Grimm, S. Kögl, H.-P. Gröbelbauer, L. Etesi, D. Casadei, A. Csillaghy, A. O. Benz, N. G. Arnold et al., “The spectrometer/telescope for imaging x-rays (stix),” Astronomy & Astrophysics, vol. 642, p. A15, 2020.

(4) N. Poirier, A. P. Rouillard, A. Kouloumvakos, A. Przybylak, N. Fargette, R. Pobeda, V. Réville, R. F. Pinto, M. Indurain, and M. Alexandre, “Exploiting white-light observations to improve estimates of magnetic connectivity,” Frontiers in Astronomy and Space Sciences, vol. 8, p. 684734, 2021.

(5) J. Rodríguez-Pacheco, R. Wimmer-Schweingruber, G. Mason, G. Ho, S. Sánchez-Prieto, M. Prieto, C. Martín, H. Seifert, G. Andrews, S. Kulkarni et al., “The energetic particle detector-energetic particle instrument suite for the solar orbiter mission,” Astronomy & Astrophysics, vol. 642, p. A7, 2020.
