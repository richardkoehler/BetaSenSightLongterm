""" BSSu from source JSON """


import os

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd
import scipy
from cycler import cycler
from scipy.signal import hann
import json

import seaborn as sns
from statannotations.Annotator import Annotator
from itertools import combinations
import scipy
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
from sklearn.preprocessing import LabelEncoder
import fooof
from fooof.plts.spectra import plot_spectrum

# PyPerceive Imports
from .. utils import find_folders as find_folders
from ..utils import loadResults as loadResults  


# channel_map = {'ZERO_AND_THREE_LEFT_RING':"LFP_L_03_STN_MT",
#     'ONE_AND_THREE_LEFT_RING':"LFP_L_13_STN_MT",
#     'ZERO_AND_TWO_LEFT_RING':"LFP_L_02_STN_MT",
#     'ONE_AND_TWO_LEFT_RING':"LFP_L_12_STN_MT",
#     'ZERO_AND_ONE_LEFT_RING':"LFP_L_01_STN_MT",
#     'TWO_AND_THREE_LEFT_RING':"LFP_L_23_STN_MT",
#     'ONE_A_AND_ONE_B_LEFT_SEGMENT':"LFP_L_1A1B_STN_MT",
#     'ONE_B_AND_ONE_C_LEFT_SEGMENT':"LFP_L_1B1C_STN_MT",
#     'ONE_A_AND_ONE_C_LEFT_SEGMENT':"LFP_L_1A1C_STN_MT",
#     'TWO_A_AND_TWO_B_LEFT_SEGMENT':"LFP_L_2A2B_STN_MT",
#     'TWO_B_AND_TWO_C_LEFT_SEGMENT':"LFP_L_2B2C_STN_MT",
#     'TWO_A_AND_TWO_C_LEFT_SEGMENT':"LFP_L_2A2C_STN_MT",
#     'ONE_A_AND_TWO_A_LEFT_SEGMENT':"LFP_L_1A2A_STN_MT",
#     'ONE_B_AND_TWO_B_LEFT_SEGMENT':"LFP_L_1B2B_STN_MT",
#     'ONE_C_AND_TWO_C_LEFT_SEGMENT':"LFP_L_1C2C_STN_MT",
#     'ZERO_AND_THREE_RIGHT_RING':"LFP_R_03_STN_MT",
#     'ONE_AND_THREE_RIGHT_RING':"LFP_R_13_STN_MT",
#     'ZERO_AND_TWO_RIGHT_RING':"LFP_R_02_STN_MT",
#     'ONE_AND_TWO_RIGHT_RING':"LFP_R_12_STN_MT",
#     'ZERO_AND_ONE_RIGHT_RING':"LFP_R_01_STN_MT",
#     'TWO_AND_THREE_RIGHT_RING':"LFP_R_23_STN_MT",
#     'ONE_A_AND_ONE_B_RIGHT_SEGMENT':"LFP_R_1A1B_STN_MT",
#     'ONE_B_AND_ONE_C_RIGHT_SEGMENT':"LFP_R_1B1C_STN_MT",
#     'ONE_A_AND_ONE_C_RIGHT_SEGMENT':"LFP_R_1A1C_STN_MT",
#     'TWO_A_AND_TWO_B_RIGHT_SEGMENT':"LFP_R_2A2B_STN_MT",
#     'TWO_B_AND_TWO_C_RIGHT_SEGMENT':"LFP_R_2B2C_STN_MT",
#     'TWO_A_AND_TWO_C_RIGHT_SEGMENT':"LFP_R_2A2C_STN_MT",
#     'ONE_A_AND_TWO_A_RIGHT_SEGMENT':"LFP_R_1A2A_STN_MT",
#     'ONE_B_AND_TWO_B_RIGHT_SEGMENT':"LFP_R_1B2B_STN_MT",
#     'ONE_C_AND_TWO_C_RIGHT_SEGMENT':"LFP_R_1C2C_STN_MT"
#     }

channel_map = {'ZERO_AND_THREE_LEFT_RING':"03",
    'ONE_AND_THREE_LEFT_RING':"13",
    'ZERO_AND_TWO_LEFT_RING':"02",
    'ONE_AND_TWO_LEFT_RING':"12",
    'ZERO_AND_ONE_LEFT_RING':"01",
    'TWO_AND_THREE_LEFT_RING':"23",
    'ONE_A_AND_ONE_B_LEFT_SEGMENT':"1A1B",
    'ONE_B_AND_ONE_C_LEFT_SEGMENT':"1B1C",
    'ONE_A_AND_ONE_C_LEFT_SEGMENT':"1A1C",
    'TWO_A_AND_TWO_B_LEFT_SEGMENT':"2A2B",
    'TWO_B_AND_TWO_C_LEFT_SEGMENT':"2B2C",
    'TWO_A_AND_TWO_C_LEFT_SEGMENT':"2A2C",
    'ONE_A_AND_TWO_A_LEFT_SEGMENT':"1A2A",
    'ONE_B_AND_TWO_B_LEFT_SEGMENT':"1B2B",
    'ONE_C_AND_TWO_C_LEFT_SEGMENT':"1C2C",
    'ZERO_AND_THREE_RIGHT_RING':"03",
    'ONE_AND_THREE_RIGHT_RING':"13",
    'ZERO_AND_TWO_RIGHT_RING':"02",
    'ONE_AND_TWO_RIGHT_RING':"12",
    'ZERO_AND_ONE_RIGHT_RING':"01",
    'TWO_AND_THREE_RIGHT_RING':"23",
    'ONE_A_AND_ONE_B_RIGHT_SEGMENT':"1A1B",
    'ONE_B_AND_ONE_C_RIGHT_SEGMENT':"1B1C",
    'ONE_A_AND_ONE_C_RIGHT_SEGMENT':"1A1C",
    'TWO_A_AND_TWO_B_RIGHT_SEGMENT':"2A2B",
    'TWO_B_AND_TWO_C_RIGHT_SEGMENT':"2B2C",
    'TWO_A_AND_TWO_C_RIGHT_SEGMENT':"2A2C",
    'ONE_A_AND_TWO_A_RIGHT_SEGMENT':"1A2A",
    'ONE_B_AND_TWO_B_RIGHT_SEGMENT':"1B2B",
    'ONE_C_AND_TWO_C_RIGHT_SEGMENT':"1C2C"
    }


def write_source_df_from_JSON(
        sub: str,
        session: str,
        condition: str,
        json_filename: str
):
    
    """"
    If Perceive runs an Error, this function will be the Fast-Track to run FOOOF and integrate the data into the fooof_model_subXXX.json

    requirement: 
        - the Report JSON file has to be in this path: BetaSenSightLongterm > data > source_json > sub-xx > session > condition > file.json

    Input: 
        - sub: str "030"
        - session: str "fu18or24m" this session name will go straight into the dataframe, make sure it's a usable session name
        - condition: str "m0s0"
        - json_filename

    1) extract from JSON: BSSU raw data and channel names
    2) rename channel names, and get hemisphere
    3) fourier transform by using scipy.signal.spectrogram()
        - unfiltered
        - window = 250
        - noverlap = 0.5
        - fs = 250
    
    4) return as dataframe: 
        - "subject_hemisphere",
        - "session",
        - "bipolar_channel",
        - "raw_time_series",
        - "frequency",
        - "rawPsd" 

    """

    json_path = find_folders.get_local_path(folder="data")
    json_path = os.path.join(json_path, "source_json", f"sub-{sub}", f"{session}", f"{condition}", f"{json_filename}")

    # load the json
    with open(json_path, 'r') as f:
        json_object = json.loads(f.read())
    

    channel_numbers = list(np.arange(0,30)) # list from 0-29, because 30 channels in total
    source_dict = {}


    for nb in channel_numbers:

        channel_original = json_object["LfpMontageTimeDomain"][nb]["Channel"]
        time_domain_original = np.array(json_object["LfpMontageTimeDomain"][nb]["TimeDomainData"])

        # hemisphere
        if "RIGHT" in channel_original:
            sub_hemisphere = f"{sub}_Right"
        
        if "LEFT" in channel_original:
            sub_hemisphere = f"{sub}_Left"

        # rename channel 
        if channel_original in channel_map:
            new_ch_name = channel_map[channel_original]
        
        else:
            print("Channel name not in channel map")
        
        #################### PERFORM FOURIER TRANSFORMATION AND CALCULATE POWER SPECTRAL DENSITY ####################

        window = 250 # with sfreq 250 frequencies will be from 0 to 125 Hz, 125Hz = Nyquist = fs/2
        noverlap = 0.5 # 50% overlap of windows
        fs = 250

        window = hann(window, sym=False) # 250 points in the output window, sym=False for use in spectral analysis

        # compute spectrogram with Fourier Transforms
        f,time_sectors,Sxx = scipy.signal.spectrogram(x=time_domain_original, fs=fs, window=window, noverlap=noverlap,  scaling='density', mode='psd', axis=0)
        # f = frequencies 0-125 Hz (Maximum = Nyquist frequency = sfreq/2)
        # time_sectors = sectors 0.5 - 20.5 s in 1.0 steps (in total 21 time sectors)
        # Sxx = 126 arrays with 21 values each of PSD [µV^2/Hz], for each frequency bin PSD values of each time sector
        # Sxx = 126 frequency rows, 21 time sector columns

        # average all 21 Power spectra of all time sectors 
        average_Sxx = np.mean(Sxx, axis=1) # axis = 1 -> mean of each column: in total 21x126 mean values for each frequency
                

        source_dict[f"{nb}"] = [sub_hemisphere, 
                                session, 
                                new_ch_name, 
                                time_domain_original,
                                f,
                                average_Sxx]
    

    # write a dataframe for this specific subject, session...
    PSD_dataframe = pd.DataFrame(source_dict)
    PSD_dataframe.rename(index={
        0: "subject_hemisphere",
        1: "session",
        2: "bipolar_channel",
        3: "raw_time_series",
        4: "frequency",
        5: "rawPsd" 
        }, inplace=True)
    PSD_dataframe = PSD_dataframe.transpose()

    return PSD_dataframe



def write_missing_FOOOF_data_add_to_old_FOOOF(
        sub: str,
        session: str,
        condition: str,
        json_filename: str
):
    
    """"
    If Perceive runs an Error, this function will be the Fast-Track to run FOOOF and integrate the data into the fooof_model_subXXX.json

    requirement: 
        - the Report JSON file has to be in this path: BetaSenSightLongterm > data > source_json > sub-xx > session > condition > file.json

    Input: 
        - sub: str "030"
        - session: str "fu18m" -> don't use fu18or24m here! allowed: "postop", "fu3m", "fu12m", "fu18m", "fu24m"
        - condition: str "m0s0"
        - json_filename

    1) extract from JSON: BSSU raw data and channel names
    2) rename channel names, and get hemisphere
    3) fourier transform by using scipy.signal.spectrogram()
        - unfiltered
        - window = 250
        - noverlap = 0.5
        - fs = 250
    
    4) return as dataframe: 
        - "subject_hemisphere",
        - "session",
        - "bipolar_channel",
        - "raw_time_series",
        - "frequency",
        - "rawPsd" 
    
        
    Here every channel will be fitted with FOOOF.
    FOOOF Figures will be saved in the subject figures folder

    the new FOOOF dataframe will be concatenated to the existing FOOOF subject JSON file: "fooof_model_subXXX.json"
    and saved as new "fooof_model_subXXX.json" into the results subject folder

    """

     # get path to results folder of each subject
    local_figures_path = find_folders.get_local_path(folder="figures", sub=sub)
    local_results_path = find_folders.get_local_path(folder="results", sub=sub)


    # load the source dataframe written with the function above
    source_dataframe = write_source_df_from_JSON(
        sub=sub,
        session=session,
        condition=condition,
        json_filename=json_filename
    )


    # FOOOF parameter:
    freq_range = [1, 95] # frequency range to fit FOOOF model


    # loop over dataframe and run FOOOF for each row (so each channel), add new columns with FOOOF results
    fooof_results = {}

    for index, row in source_dataframe.iterrows():

        sub_hem = source_dataframe["subject_hemisphere"].values[int(index)]
        ses = source_dataframe["session"].values[int(index)]
        chan = source_dataframe["bipolar_channel"].values[int(index)]

        freqs = source_dataframe["frequency"].values[int(index)]
        power_spectrum = source_dataframe["rawPsd"].values[int(index)]

        ############ SET PLOT LAYOUT ############
        fig, ax = plt.subplots(4,1, figsize=(7,20))

        # Plot the unfiltered Power spectrum in first ax
        plot_spectrum(freqs, power_spectrum, log_freqs=False, log_powers=False,
                        ax=ax[0])
        ax[0].grid(False)

        ############ SET FOOOF MODEL ############

        model = fooof.FOOOF(
                peak_width_limits=[2, 15.0],
                max_n_peaks=6,
                min_peak_height=0.2,
                peak_threshold=2.0,
                aperiodic_mode="fixed", # fitting without knee component
                verbose=True,
            )

        # run FOOOF
        # always fit a large Frequency band, later you can select Peaks within specific freq bands
        model.fit(freqs=freqs, power_spectrum=power_spectrum, freq_range=freq_range)

        # Plot an example power spectrum, with a model fit in second ax
        # model.plot(plot_peaks='shade', peak_kwargs={'color' : 'green'}, ax=ax[1])
        model.plot(ax=ax[1], plt_log=True) # to evaluate the aperiodic component
        model.plot(ax=ax[2], plt_log=False) # To see the periodic component better without log in frequency axis
        ax[1].grid(False)
        ax[2].grid(False)


        # plot only the fooof spectrum of the periodic component
        fooof_power_spectrum = 10**(model._peak_fit + model._ap_fit) - (10**model._ap_fit)
        plot_spectrum(np.arange(1, (len(fooof_power_spectrum)+1)), fooof_power_spectrum, log_freqs=False, log_powers=False, ax=ax[3])
        # frequencies: 1-95 Hz with 1 Hz resolution

        # titles
        #fig.suptitle(f"sub {subject}, {hemisphere} hemisphere, {ses}, bipolar channel: {chan}",
        #                        fontsize=25)
        
        ax[0].set_title("unfiltered, raw power spectrum", fontsize=20, y=0.97, pad=-20)
        ax[3].set_title("power spectrum of periodic component", fontsize=20)

        # mark beta band
        x1 = 13
        x2 = 35
        ax[3].axvspan(x1, x2, color="whitesmoke")
        ax[3].grid(False)
        
        fig.tight_layout()
        fig.savefig(os.path.join(local_figures_path, f"fooof_model_sub{sub_hem}_{ses}_{chan}.svg"), bbox_inches="tight", format="svg")
        fig.savefig(os.path.join(local_figures_path, f"fooof_model_sub{sub_hem}_{ses}_{chan}.png"), bbox_inches="tight")


        # extract parameters from the chosen model
        # model.print_results()

        ############ SAVE APERIODIC PARAMETERS ############
        # goodness of fit
        err = model.get_params('error')
        r_sq = model.r_squared_

        # aperiodic components
        exp = model.get_params('aperiodic_params', 'exponent')
        offset = model.get_params('aperiodic_params', 'offset')

        # periodic component
        log_power_fooof_periodic_plus_aperiodic = model._peak_fit + model._ap_fit # periodic+aperiodic component in log Power axis
        fooof_periodic_component = model._peak_fit # just periodic component, flattened spectrum
        
        ############ SAVE ALL PEAKS IN ALPHA; HIGH AND LOW BETA ############

        number_peaks = model.n_peaks_

        # get the highest Peak of each frequency band as an array: CF center frequency, Power, BandWidth
        alpha_peak = fooof.analysis.get_band_peak_fm(
            model,
            band=(8.0, 12.0),
            select_highest=True,
            attribute="peak_params"
            )

        low_beta_peak = fooof.analysis.get_band_peak_fm(
            model,
            band=(13.0, 20.0),
            select_highest=True,
            attribute="peak_params",
            )

        high_beta_peak = fooof.analysis.get_band_peak_fm(
            model,
            band=(21.0, 35.0),
            select_highest=True,
            attribute="peak_params",
            )

        beta_peak = fooof.analysis.get_band_peak_fm(
            model,
            band=(13.0, 35.0),
            select_highest=True,
            attribute="peak_params",
            )

        gamma_peak = fooof.analysis.get_band_peak_fm(
            model,
            band=(60.0, 90.0),
            select_highest=True,
            attribute="peak_params",
            )
        
        fooof_results[index] = [sub_hem, ses, chan,
                                err, r_sq, exp, offset, 
                                fooof_power_spectrum, log_power_fooof_periodic_plus_aperiodic, fooof_periodic_component,
                                number_peaks, alpha_peak, low_beta_peak, high_beta_peak, beta_peak, gamma_peak]

        
    # store results in a DataFrame
    fooof_results_df = pd.DataFrame(fooof_results)  
    fooof_results_df.rename(index={0: "subject_hemisphere", 
                                1: "session", 
                                2: "bipolar_channel", 
                                3: "fooof_error", 
                                4: "fooof_r_sq", 
                                5: "fooof_exponent", 
                                6: "fooof_offset", 
                                7: "fooof_power_spectrum", 
                                8: "periodic_plus_aperiodic_power_log",
                                9: "fooof_periodic_flat",
                                10: "fooof_number_peaks",
                                11: "alpha_peak_CF_power_bandWidth",
                                12: "low_beta_peak_CF_power_bandWidth",
                                13: "high_beta_peak_CF_power_bandWidth",
                                14: "beta_peak_CF_power_bandWidth",
                                15: "gamma_peak_CF_power_bandWidth",
                                }, 
                            inplace=True)
                    
    fooof_results_df = fooof_results_df.transpose()    

    # add the new fooof dataframe to the existing dataframe of the given subject: "fooof_model_subXXX.json"
    existing_fooof_json = loadResults.load_fooof_json(subject=sub)

    new_concatenated_fooof = pd.concat([existing_fooof_json, fooof_results_df])
    
    # save DF in subject results folder
    new_concatenated_fooof.to_json(os.path.join(local_results_path, f"fooof_model_sub{sub}.json"))
    	


    return new_concatenated_fooof










