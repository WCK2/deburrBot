import os
import pickle
import gzip


def load_and_print_data(filename):
    with gzip.open(filename, 'rb') as f:
        data_log = pickle.load(f)
    
    # print("Input Points:")
    # print(data_log['input_points'])
    
    # print("\nInput Labels:")
    # print(data_log['input_label'])
    
    # print("\nCoordinate Pairs:")
    # print(data_log['coordinate_pairs'])


    print(f'robot_frame:\n{data_log["robot_frame"]}')
    print(f'robot_tool:\n{data_log["robot_tool"]}')
    print(f'robot_pose:\n{data_log["robot_pose"]}')



filename_log = os.getcwd() + '/assets/data/d435_2024-08-22_14-22-56/' + 'tmobileSAM_data_log_09-28-42.pkl.gz'
filename_log = os.getcwd() + '/assets/data/d435_2024-09-12_13-08-38/' + 'tmobileSAM_data_log_13-08-44.pkl.gz'
load_and_print_data(filename_log)
