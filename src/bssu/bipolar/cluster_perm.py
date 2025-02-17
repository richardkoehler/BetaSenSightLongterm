 # load the json file
import pandas as pd
import os
import numpy as np
import pickle
import matplotlib.pyplot as plt
from cycler import cycler

import scipy.stats as st

import mne
from mne.stats import permutation_cluster_test

from .. utils import find_folders as find_folders
from .. utils import loadResults as loadResults



def cluster_permutation_power_spectra_betw_sessions(
        incl_channels:str,
        signalFilter:str,
        normalization:str
):
    
    """
    Load the file f"power_spectra_{signalFilter}_{incl_channels}_session_comparisons.pickle"
    from the group result folder

    Input:
        - incl_channels: str, e.g. "SegmInter", "SegmIntra", "Ring"
        - signalFilter: str, e.g. "band-pass" or "unfiltered" 
        - normalization: str, e.g. "rawPsd", "normPsdToTotalSum", "normPsdToSum1_100Hz", "normPsdToSum40_90Hz"
    
    1) Get the Dataframes of each session for each session comparison 
        - within each session comparison -> only STNs are included, that have recordings at both sessions (same sample size per comparison)
    
    2) for each comparison make a list with two arrays, one per session
        - use np.vstack to create one big array with power spectra vectors per session
        - only include power up until maximal frequency (90 Hz) by indexing
        - shape of one array/one session = (n_observations, )
    
    3) perform cluster permutation per session comparison:
        - comparisons: ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]
        - number of Permutations = 1000
        
    Output of mne.stats.permutation_cluster_test:
        - F_obs, shape (p[, q][, r]): 
            Statistic (F by default) observed for all variables.

        - clusterslist: 
            List type defined by out_type above.

        - cluster_pvarray
            P-value for each cluster.

        - H0array, shape (n_permutations,)
            Max cluster level stats observed under permutation.


    """

    results_path = find_folders.get_local_path(folder="GroupResults")

    # load all session comparisons
    loaded_session_comparisons = loadResults.load_power_spectra_session_comparison(
        incl_channels=incl_channels,
        signalFilter=signalFilter,
        normalization=normalization)
    
    # get the dataframe for each session comparison
    compare_sessions = ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]
    
    # maximal frequency to perform cluster permutation
    max_freq = 90

    permutation_results = {}
    
    for comparison in compare_sessions:

        two_sessions = comparison.split("_")
        session_1 = two_sessions[0] # e.g."postop"
        session_2 = two_sessions[1] # e.g. "fu3m"

        comparison_df = loaded_session_comparisons[f"{comparison}_df"] 

        # only get part of df with session_1 and df with session_2
        session_1_df = comparison_df.loc[comparison_df.session==session_1]
        session_2_df = comparison_df.loc[comparison_df.session==session_2]

        # from each session df only take the values from column with power spectra only until maximal frequency
        x_session_1 = np.vstack(session_1_df['power_spectrum'].values)[:,:max_freq]
        # e.g. for shape x_18mfu comparison to 12mfu = (10, 90), 10 STNs, 90 values per STN
        x_session_2 = np.vstack(session_2_df['power_spectrum'].values)[:,:max_freq]

        list_for_cluster_permutation = [x_session_1, x_session_2]

        # perform cluster permutation
        F_obs, clusters, cluster_pv, H0 = permutation_cluster_test(list_for_cluster_permutation, n_permutations=1000)

        # get the sample size
        sample_size = len(session_1_df.power_spectrum.values)

        # save results
        permutation_results[f"{comparison}"] = [comparison, F_obs, clusters, cluster_pv, H0, sample_size]

    results_df = pd.DataFrame(permutation_results)
    results_df.rename(index={
        0: "session_comparison",
        1: "F_obs",
        2: "clusters",
        3: "cluster_pv",
        4: "H0",
        5: "sample_size"
    }, inplace=True)
    results_df = results_df.transpose()

    # save the results DF into results path
    results_df_filepath = os.path.join(results_path, f"cluster_permutation_session_comparisons_{incl_channels}_{signalFilter}_{normalization}.pickle")
    with open(results_df_filepath, "wb") as file:
        pickle.dump(results_df, file)
    
    print("file: ", 
          f"cluster_permutation_session_comparisons_{incl_channels}_{signalFilter}_{normalization}.pickle",
          "\nwritten in: ", results_path
          )

    return {
        "results_df": results_df,
        "x_session_1": x_session_1

    }
        
        

def cluster_permutation_fooof_power_spectra(
        
):
    """
    Load the file "fooof_model_group_data.json"
    from the group result folder
  
    1) Get the Dataframes for each session comparison and for channel groups seperately
        - within each session comparison -> only STNs are included, that have recordings at both sessions (same sample size per comparison)
    
    2) for each comparison make a list with two arrays, one per session
        - use np.vstack to create one big array with power spectra vectors per session
        - only include power up until maximal frequency (95 Hz) by indexing
        - shape of one array/one session = (n_observations, )
    
    3) perform cluster permutation per session comparison:
        - comparisons: ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]
        - number of Permutations = 1000
        
    Output of mne.stats.permutation_cluster_test:
        - F_obs, shape (p[, q][, r]): 
            Statistic (F by default) observed for all variables.

        - clusterslist: 
            List type defined by out_type above.

        - cluster_pvarray
            P-value for each cluster.

        - H0array, shape (n_permutations,)
            Max cluster level stats observed under permutation.
    
    """
    
    results_path = find_folders.get_local_path(folder="GroupResults")

    # load the group dataframe
    fooof_group_result = loadResults.load_group_fooof_result()

    ################################ Dataframes for each session comparison ################################
    compare_sessions = ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]

    comparisons_storage = {}

    for comparison in compare_sessions:

        two_sessions = comparison.split("_")
        session_1 = two_sessions[0]
        session_2 = two_sessions[1]

        # Dataframe per session
        session_1_df = fooof_group_result.loc[(fooof_group_result["session"]==session_1)]
        session_2_df = fooof_group_result.loc[(fooof_group_result["session"]==session_2)]

        # list of STNs per session
        session_1_stns = list(session_1_df.subject_hemisphere.unique())
        session_2_stns = list(session_2_df.subject_hemisphere.unique())

        # list of STNs included in both sessions
        STN_list = list(set(session_1_stns) & set(session_2_stns))
        STN_list.sort()

        comparison_df = pd.DataFrame()

        for stn in STN_list:

            session_1_compared_to_2 = session_1_df.loc[session_1_df["subject_hemisphere"]==stn]
            session_2_compared_to_1 = session_2_df.loc[session_2_df["subject_hemisphere"]==stn]
            
            comparison_df = pd.concat([comparison_df, session_1_compared_to_2, session_2_compared_to_1])
            

        comparisons_storage[f"{comparison}"] = comparison_df
    

    ################################ CLUSTER PERMUTATION FOR EACH SESSION COMPARISON; SEPERATELY IN CHANNEL GROUPS ################################

    channel_group = ["ring", "segm_inter", "segm_intra"]

        
    # maximal frequency to perform cluster permutation
    max_freq = 95

    permutation_results = {}

    # filter each comparison Dataframe for comparisons and channels in each channel group
    for comp in compare_sessions:

        comparison_df = comparisons_storage[f"{comp}"]

        for group in channel_group:

            if group == "ring":
                channels = ['01', '12', '23']
            
            elif group == "segm_inter":
                channels = ["1A2A", "1B2B", "1C2C"]
            
            elif group == "segm_intra":
                channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

            # dataframe only of one comparison and one channel group
            group_comp_df = comparison_df.loc[comparison_df["bipolar_channel"].isin(channels)]

            two_sessions = comp.split("_")
            session_1 = two_sessions[0] # e.g. postop
            session_2 = two_sessions[1]

            # only get part of df with session_1 and df with session_2
            session_1_df = group_comp_df.loc[group_comp_df.session==session_1]
            session_2_df = group_comp_df.loc[group_comp_df.session==session_2]

            # from each session df only take the values from column with power spectra only until maximal frequency 95
            x_session_1 = np.vstack(session_1_df['fooof_power_spectrum'].values)[:,:max_freq]
            # e.g. for shape x_18mfu comparison to 12mfu = (10, 90), 10 STNs, 90 values per STN
            x_session_2 = np.vstack(session_2_df['fooof_power_spectrum'].values)[:,:max_freq]

            list_for_cluster_permutation = [x_session_1, x_session_2]

            # perform cluster permutation
            F_obs, clusters, cluster_pv, H0 = permutation_cluster_test(list_for_cluster_permutation, n_permutations=1000)

            # get the sample size
            sample_size = len(session_1_df.fooof_power_spectrum.values)

            # save results
            permutation_results[f"{comp}_{group}"] = [comp, group, F_obs, clusters, cluster_pv, H0, sample_size]
    

    results_df = pd.DataFrame(permutation_results)
    results_df.rename(index={
        0: "session_comparison",
        1: "channel_group",
        2: "F_obs",
        3: "clusters",
        4: "cluster_pv",
        5: "H0",
        6: "sample_size"
    }, inplace=True)
    results_df = results_df.transpose()

    # save the results DF into results path
    results_df_filepath = os.path.join(results_path, f"cluster_permutation_fooof_spectra_session_comparisons.pickle")
    with open(results_df_filepath, "wb") as file:
        pickle.dump(results_df, file)
    
    print("file: ", 
          f"cluster_permutation_fooof_spectra_session_comparisons.pickle",
          "\nwritten in: ", results_path
          )

    return {
        "results_df": results_df,
        "comparisons_storage": comparisons_storage
          }
            

def highest_beta_channels_fooof(
        fooof_spectrum:str,
        highest_beta_session:str
):
    """
    Load the file "fooof_model_group_data.json"
    from the group result folder

    Input: 
        - fooof_spectrum: 
            "periodic_spectrum"         -> 10**(model._peak_fit + model._ap_fit) - (10**model._ap_fit)
            "periodic_plus_aperiodic"   -> model._peak_fit + model._ap_fit (log(Power))
            "periodic_flat"             -> model._peak_fit

        - highest_beta_session: "highest_postop", "highest_fu3m", "highest_each_session"

    1) calculate beta average for each channel and rank within 1 stn, 1 session and 1 channel group
    
    2) rank beta averages and only select the channels with rank 1.0 

    Output highest_beta_df
        - containing all stns, all sessions, all channels with rank 1.0 within their channel group
    
    """

    # load the group dataframe
    fooof_group_result = loadResults.load_group_fooof_result()

    # create new column: first duplicate column fooof power spectrum, then apply calculation to each row -> average of indices [13:36] so averaging the beta range
    fooof_group_result_copy = fooof_group_result.copy()

    if fooof_spectrum == "periodic_spectrum":
        fooof_group_result_copy["beta_average"] = fooof_group_result_copy["fooof_power_spectrum"]
    
    elif fooof_spectrum == "periodic_plus_aperiodic":
        fooof_group_result_copy["beta_average"] = fooof_group_result_copy["periodic_plus_aperiodic_power_log"]

    elif fooof_spectrum == "periodic_flat":
        fooof_group_result_copy["beta_average"] = fooof_group_result_copy["fooof_periodic_flat"]
    
    
    fooof_group_result_copy["beta_average"] = fooof_group_result_copy["beta_average"].apply(lambda row: np.mean(row[13:36]))


    ################################ WRITE DATAFRAME ONLY WITH HIGHEST BETA CHANNELS PER STN | SESSION | CHANNEL_GROUP ################################
    channel_group = ["ring", "segm_inter", "segm_intra"]
    sessions = ["postop", "fu3m", "fu12m", "fu18m"]

    stn_unique = fooof_group_result_copy.subject_hemisphere.unique().tolist()

    beta_rank_df = pd.DataFrame()

    for stn in stn_unique:

        stn_df = fooof_group_result_copy.loc[fooof_group_result_copy.subject_hemisphere == stn]

        for ses in sessions:

            # check if session exists
            if ses not in stn_df.session.values:
                continue

            else:
                stn_ses_df = stn_df.loc[stn_df.session == ses] # df of only 1 stn and 1 session


            for group in channel_group:

                if group == "ring":
                    channels = ['01', '12', '23']
                    
                elif group == "segm_inter":
                    channels = ["1A2A", "1B2B", "1C2C"]
                
                elif group == "segm_intra":
                    channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

                group_comp_df = stn_ses_df.loc[stn_ses_df["bipolar_channel"].isin(channels)].reset_index() # df of only 1 stn, 1 session and 1 channel group

                # rank beta average of channels within one channel group
                group_comp_df_copy = group_comp_df.copy()
                group_comp_df_copy["beta_rank"] = group_comp_df_copy["beta_average"].rank(ascending=False) 

                # save to ranked_beta_df
                beta_rank_df = pd.concat([beta_rank_df, group_comp_df_copy])
    
    # depending on input: keep only rank 1.0 or keep postop rank 1 or 3MFU rank 1 channel
    if highest_beta_session == "highest_each_session":
        # only keep the row with beta rank 1.0
        highest_beta_df = beta_rank_df.loc[beta_rank_df.beta_rank == 1.0]
    
    elif highest_beta_session == "highest_postop":
        highest_beta_df = pd.DataFrame()
        # for each stn get channel name of beta rank 1 in postop and select the channels for the other timepoints
        for stn in stn_unique:

            stn_data = beta_rank_df.loc[beta_rank_df.subject_hemisphere == stn]
            
            for ses in sessions:
                # check if postop exists
                if "postop" not in stn_data.session.values:
                    continue

                elif ses not in stn_data.session.values:
                    continue
                
                else: 
                    postop_rank1_channels = stn_data.loc[stn_data.session=="postop"]
                    postop_rank1_channels = postop_rank1_channels.loc[postop_rank1_channels.beta_rank == 1.0]

                    stn_ses_data = stn_data.loc[stn_data.session == ses]
                
                for group in channel_group:

                    if group == "ring":
                        channels = ['01', '12', '23']
                    
                    elif group == "segm_inter":
                        channels = ["1A2A", "1B2B", "1C2C"]
                    
                    elif group == "segm_intra":
                        channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

                    group_data = stn_ses_data.loc[stn_ses_data["bipolar_channel"].isin(channels)].reset_index()

                    # get channel name of rank 1 channel in postop in this channel group
                    postop_1_row = postop_rank1_channels.loc[postop_rank1_channels["bipolar_channel"].isin(channels)]
                    postop_1_channelname = postop_1_row.bipolar_channel.values[0]

                    # select only this channel in all the other sessions
                    selected_rows = group_data.loc[group_data.bipolar_channel == postop_1_channelname]
                    highest_beta_df = pd.concat([highest_beta_df, postop_1_row, selected_rows])
        
        # drop index columns 
        # drop duplicated postop rows
        # highest_beta_df = highest_beta_df.drop(column=["level_0", "index"])
        highest_beta_df = highest_beta_df.drop_duplicates(keep="first", subset=["subject_hemisphere", "session", "bipolar_channel"])


    elif highest_beta_session == "highest_fu3m":
        highest_beta_df = pd.DataFrame()
        # for each stn get channel name of beta rank 1 in postop and select the channels for the other timepoints
        for stn in stn_unique:

            stn_data = beta_rank_df.loc[beta_rank_df.subject_hemisphere == stn]
            
            for ses in sessions:

                # # if session is postop, continue, because we´re only interested in follow ups here
                # if ses == "postop":
                #     continue

                # check if fu3m exists
                if "fu3m" not in stn_data.session.values:
                    continue

                elif ses not in stn_data.session.values:
                    continue
                
                else: 
                    fu3m_rank1_channels = stn_data.loc[stn_data.session=="fu3m"]
                    fu3m_rank1_channels = fu3m_rank1_channels.loc[fu3m_rank1_channels.beta_rank == 1.0]

                    stn_ses_data = stn_data.loc[stn_data.session == ses]
                
                for group in channel_group:

                    if group == "ring":
                        channels = ['01', '12', '23']
                    
                    elif group == "segm_inter":
                        channels = ["1A2A", "1B2B", "1C2C"]
                    
                    elif group == "segm_intra":
                        channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

                    group_data = stn_ses_data.loc[stn_ses_data["bipolar_channel"].isin(channels)].reset_index()

                    # get channel name of rank 1 channel in fu3m in this channel group
                    fu3m_1_row = fu3m_rank1_channels.loc[fu3m_rank1_channels["bipolar_channel"].isin(channels)]
                    fu3m_1_channelname = fu3m_1_row.bipolar_channel.values[0]

                    # select only this channel in all the other sessions
                    selected_rows = group_data.loc[group_data.bipolar_channel == fu3m_1_channelname]
                    highest_beta_df = pd.concat([highest_beta_df, fu3m_1_row, selected_rows])
        
        # drop index columns 
        # drop duplicated postop rows
        # highest_beta_df = highest_beta_df.drop(column=["level_0", "index"])
        highest_beta_df = highest_beta_df.drop_duplicates(keep="first", subset=["subject_hemisphere", "session", "bipolar_channel"])



    return highest_beta_df
        
            

            
def cluster_permutation_fooof_power_spectra_highest_beta(
        fooof_spectrum:str,
        highest_beta_session:str,
        min_freq:int,
        max_freq:int
):
    """
    Load the modified FOOOF dataframe with this function: highest_beta_channels_fooof()
    calculates beta average for each channel and rank within 1 stn, 1 session and 1 channel group
    and only selects the channels with rank 1.0 

    Input: 
        - fooof_spectrum: 
            "periodic_spectrum"         -> 10**(model._peak_fit + model._ap_fit) - (10**model._ap_fit)
            "periodic_plus_aperiodic"   -> model._peak_fit + model._ap_fit (log(Power))
            "periodic_flat"             -> model._peak_fit
        
        - highest_beta_session: "highest_postop", "highest_fu3m", "highest_each_session"

        cluster permutation only within a frequency band from min_freq to max_freq
        - min_freq: e.g. 5 Hz 
        - max_freq: e.g. 35 Hz 
  
    1) Get the Dataframes for each session comparison and for channel groups seperately
        - within each session comparison -> only STNs are included, that have recordings at both sessions (same sample size per comparison)
    
    2) for each comparison make a list with two arrays, one per session
        - use np.vstack to create one big array with power spectra vectors per session
        - only include power up until maximal frequency (95 Hz) by indexing
        - shape of one array/one session = (n_observations, )
    
    3) perform cluster permutation per session comparison:
        - comparisons: ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]
        - number of Permutations = 1000
        
    Output of mne.stats.permutation_cluster_test:
        - F_obs, shape (p[, q][, r]): 
            Statistic (F by default) observed for all variables.

        - clusterslist: 
            List type defined by out_type above.

        - cluster_pvarray
            P-value for each cluster.

        - H0array, shape (n_permutations,)
            Max cluster level stats observed under permutation.
    
    """
    
    results_path = find_folders.get_local_path(folder="GroupResults")


    ################################ WRITE DATAFRAME ONLY WITH HIGHEST BETA CHANNELS PER STN | SESSION | CHANNEL_GROUP ################################
    fooof_group_result = highest_beta_channels_fooof(fooof_spectrum=fooof_spectrum,
                                                     highest_beta_session=highest_beta_session)

    # containing all stns, all sessions, all channels rank 1.0 within their channel group


    ################################ Dataframes for each session comparison ################################
    
    compare_sessions = ["postop_fu3m", "postop_fu12m", "postop_fu18m", 
                        "fu3m_fu12m", "fu3m_fu18m", "fu12m_fu18m"]
    
    channel_group = ["ring", "segm_inter", "segm_intra"]

    comparisons_storage = {}

    for comparison in compare_sessions:

        two_sessions = comparison.split("_")
        session_1 = two_sessions[0]
        session_2 = two_sessions[1]

        # Dataframe per session
        session_1_df = fooof_group_result.loc[(fooof_group_result["session"]==session_1)]
        session_2_df = fooof_group_result.loc[(fooof_group_result["session"]==session_2)]

        # list of STNs per session
        session_1_stns = list(session_1_df.subject_hemisphere.unique())
        session_2_stns = list(session_2_df.subject_hemisphere.unique())

        # list of STNs included in both sessions
        STN_list = list(set(session_1_stns) & set(session_2_stns))
        STN_list.sort()

        comparison_df = pd.DataFrame()

        for stn in STN_list:

            session_1_compared_to_2 = session_1_df.loc[session_1_df["subject_hemisphere"]==stn]
            session_2_compared_to_1 = session_2_df.loc[session_2_df["subject_hemisphere"]==stn]
            
            comparison_df = pd.concat([comparison_df, session_1_compared_to_2, session_2_compared_to_1])
            

        comparisons_storage[f"{comparison}"] = comparison_df
    

    ################################ CLUSTER PERMUTATION FOR EACH SESSION COMPARISON; SEPERATELY IN CHANNEL GROUPS ###############################
    
    permutation_results = {}

    # filter each comparison Dataframe for comparisons and channels in each channel group
    for comp in compare_sessions:

        comparison_df = comparisons_storage[f"{comp}"]

        for group in channel_group:

            if group == "ring":
                channels = ['01', '12', '23']
            
            elif group == "segm_inter":
                channels = ["1A2A", "1B2B", "1C2C"]
            
            elif group == "segm_intra":
                channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

            # dataframe only of one comparison and one channel group
            group_comp_df = comparison_df.loc[comparison_df["bipolar_channel"].isin(channels)]

            two_sessions = comp.split("_")
            session_1 = two_sessions[0] # e.g. postop
            session_2 = two_sessions[1]

            # only get part of df with session_1 and df with session_2
            session_1_df = group_comp_df.loc[group_comp_df.session==session_1]
            session_2_df = group_comp_df.loc[group_comp_df.session==session_2]

            if fooof_spectrum == "periodic_spectrum":
                power_column = "fooof_power_spectrum"
        
            elif fooof_spectrum == "periodic_plus_aperiodic":
                power_column = "periodic_plus_aperiodic_power_log"

            elif fooof_spectrum == "periodic_flat":
                power_column = "fooof_periodic_flat"

            # from each session df only take the values from column with power spectra only until maximal frequency 95
            x_session_1 = np.vstack(session_1_df[power_column].values)[:, min_freq:max_freq+1]
            # e.g. for shape x_18mfu comparison to 12mfu = (10, 90), 10 STNs, 90 values per STN
            x_session_2 = np.vstack(session_2_df[power_column].values)[:,min_freq:max_freq+1]

            list_for_cluster_permutation = [x_session_1, x_session_2]

            # perform cluster permutation
            F_obs, clusters, cluster_pv, H0 = permutation_cluster_test(list_for_cluster_permutation, n_permutations=1000)

            # get the sample size
            sample_size = len(session_1_df.fooof_power_spectrum.values)

            # save results
            permutation_results[f"{comp}_{group}"] = [comp, group, F_obs, clusters, cluster_pv, H0, sample_size]
    

    results_df = pd.DataFrame(permutation_results)
    results_df.rename(index={
        0: "session_comparison",
        1: "channel_group",
        2: "F_obs",
        3: "clusters",
        4: "cluster_pv",
        5: "H0",
        6: "sample_size"
    }, inplace=True)
    results_df = results_df.transpose()

    # save the results DF into results path
    results_df_filepath = os.path.join(results_path, f"cluster_permutation_fooof_{highest_beta_session}_beta_{min_freq}_{max_freq}Hz_spectra_session_comparisons.pickle")
    with open(results_df_filepath, "wb") as file:
        pickle.dump(results_df, file)
    
    print("file: ", 
          f"cluster_permutation_fooof_{highest_beta_session}_beta_{min_freq}_{max_freq}Hz_spectra_session_comparisons.pickle",
          "\nwritten in: ", results_path
          )

    return {
        "results_df": results_df,
        "comparisons_storage": comparisons_storage,
        "fooof_group_result": fooof_group_result
          }
            


def grand_average_power_spectra_fooof_highest_beta(
        std_or_sem:str,
        spectrum_to_plot:str,
        highest_beta_session:str
        
):
    """
    Plot an average power spectrum of FOOOF modeled spectra per session for each channel group.

    Input: 
        - std_or_sem: "std" or "sem" plotting SEM or standard deviation
        - spectrum_to_plot: 
            "periodic_spectrum"         -> 10**(model._peak_fit + model._ap_fit) - (10**model._ap_fit)
            "periodic_plus_aperiodic"   -> model._peak_fit + model._ap_fit (log(Power))
            "periodic_flat"             -> model._peak_fit
        
        - highest_beta_session: "highest_postop", "highest_fu3m", "highest_each_session"


        save figure: "grand_average_FOOOF_{all_or_one}_{group}_{spectrum_to_plot}_{std_or_sem}.png"
    """

    figures_path = find_folders.get_local_path(folder="GroupFigures")

    # load the fooof group result
    if highest_beta_session == "highest_each_session":
        # load the dataframe with only one channel with highest beta per channel group, session and STN
        fooof_group_result = loadResults.load_fooof_highest_beta_channels(fooof_spectrum=spectrum_to_plot)

    elif highest_beta_session == "highest_postop":
        fooof_group_result = highest_beta_channels_fooof(
            fooof_spectrum=spectrum_to_plot,
            highest_beta_session=highest_beta_session
        )
    
    elif highest_beta_session == "highest_fu3m":
        fooof_group_result = highest_beta_channels_fooof(
            fooof_spectrum=spectrum_to_plot,
            highest_beta_session=highest_beta_session
        )

    sessions = ["postop", "fu3m", "fu12m", "fu18m"]
    channel_group = ["ring", "segm_inter", "segm_intra"]

    ############# PLOT THE GRAND AVERAGE POWER SPECTRUM PER SESSION #############
    average_spectra = {}

    # Plot all power spectra in one figure, one color for each session
    for group in channel_group:

        if group == "ring":
            channels = ['01', '12', '23']
        
        elif group == "segm_inter":
            channels = ["1A2A", "1B2B", "1C2C"]
        
        elif group == "segm_intra":
            channels = ['1A1B', '1B1C', '1A1C', '2A2B', '2B2C', '2A2C']

        group_df = fooof_group_result.loc[fooof_group_result["bipolar_channel"].isin(channels)]

        # 4 colors used for the cycle of matplotlib 
        cycler_colors = cycler("color", ["turquoise", "sandybrown", "plum", "cornflowerblue"])
        plt.rc('axes', prop_cycle=cycler_colors)

        fig = plt.figure(layout="tight")

        for ses in sessions:

            session_df = group_df.loc[group_df.session==ses]

            frequencies = np.arange(1, 96) # 1-95 Hz, 1 Hz resolution

            # choose what to plot:
            if spectrum_to_plot == "periodic_spectrum":
                column_name = "fooof_power_spectrum"
                y_label = f"average Power [uV^2/Hz] +- {std_or_sem}"
            
            elif spectrum_to_plot == "periodic_plus_aperiodic":
                column_name = "periodic_plus_aperiodic_power_log"
                y_label = f"average log(Power) +- {std_or_sem}"
            
            elif spectrum_to_plot == "periodic_flat":
                column_name = "fooof_periodic_flat"
                y_label = f"average Power of periodic component +- {std_or_sem}"

            # transform all arrays with 95 values into a new dataframe with 95 columns = 1 column for each position (1-95)
            df_transposed = pd.DataFrame(session_df[column_name].tolist())

            power_spectrum_session_grand_average = df_transposed.apply(lambda x: np.mean(x), axis=0) # mean along columns: for each position (1-95) -> outcome=pd.Series with 95 values

            # CALCULATE STANDARD DEVIATION AND SEM for each position 
            standard_deviation_session = df_transposed.apply(lambda x: np.std(x), axis=0)
            sem_session = df_transposed.apply(lambda x: st.sem(x), axis=0)

            # save and return 
            average_spectra[f"{ses}_{group}"] = [ses, group, frequencies, power_spectrum_session_grand_average, standard_deviation_session, sem_session,
                                            len(session_df.fooof_power_spectrum.values)]
            
            # Plot the grand average power spectrum per session
            plt.plot(frequencies, power_spectrum_session_grand_average, label=ses, linewidth=3)

            # choose plotting sem or std
            if std_or_sem == "sem":
                shadowed = sem_session
            
            if std_or_sem == "std":
                shadowed = standard_deviation_session

            # plot the standard deviation as shaded grey area
            plt.fill_between(frequencies, 
                        power_spectrum_session_grand_average-shadowed,
                        power_spectrum_session_grand_average+shadowed,
                        color="gainsboro", alpha=0.5)

        # TITLE
        if highest_beta_session == "highest_each_session":
            plt.title(f"Grand average FOOOF power spectra of \nthe highest beta channels of the {group} group", fontdict={"size": 18})
            highest_channel = "highest_beta_channels"

        elif highest_beta_session == "highest_postop":
            plt.title(f"Grand average FOOOF power spectra of \nhighest beta channel from baseline (postop) from {group} channels", fontdict={"size": 18})
            highest_channel = "highest_postop_beta_channels"
        
        elif highest_beta_session == "highest_fu3m":
            plt.title(f"Grand average FOOOF power spectra of \nhighest beta channel from baseline (3MFU) from {group} channels", fontdict={"size": 18})
            highest_channel = "highest_fu3m_beta_channels"
        
        # plot settings
        plt.legend(loc= 'upper right', fontsize=14)

        # add lines for freq Bands
        # plt.axvline(x=8, color='dimgrey', linestyle='--')
        plt.axvline(x=13, color='dimgrey', linestyle='--')
        # plt.axvline(x=20, color='dimgrey', linestyle='--')
        plt.axvline(x=35, color='dimgrey', linestyle='--')
        # x1 = 13
        # x2 = 35
        # plt.axvspan(x1, x2, color="whitesmoke")

        plt.xlabel("Frequency [Hz]", fontdict={"size": 14})
        # plt.xlim(1, 95)

        plt.ylabel(y_label, fontdict={"size": 14})
        plt.ylim(-0.05, 3.5)
        plt.grid(False)

        fig.tight_layout()

        fig.savefig(os.path.join(figures_path, f"grand_average_FOOOF_{highest_channel}_{group}_{spectrum_to_plot}_{std_or_sem}.png"),
                bbox_inches = "tight")
        fig.savefig(os.path.join(figures_path, f"grand_average_FOOOF_{highest_channel}_{group}_{spectrum_to_plot}_{std_or_sem}.svg"),
                bbox_inches = "tight", format="svg")

    print("figure: ", 
          f"grand_average_FOOOF_{highest_channel}_{group}_{spectrum_to_plot}_{std_or_sem}.png",
          "\nwritten in: ", figures_path
          )
    
    average_spectra_df = pd.DataFrame(average_spectra)
    average_spectra_df.rename(index={
        0: "session",
        1: "channel_group",
        2: "frequencies",
        3: "power_spectrum_grand_average",
        4: "standard_deviation",
        5: "sem",
        6: "sample_size"
    }, inplace=True)
    average_spectra_df = average_spectra_df.transpose()

    
    return average_spectra_df
    


