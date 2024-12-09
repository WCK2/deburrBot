import os
import gzip
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.ticker as mticker
import pickle
import numpy as np


def load_data_log(filename: str):
    if not filename.endswith('.gz'): filename += '.gz'
    try:
        with gzip.open(filename, 'rb') as f:
            data_log = pickle.load(f)
        print(f"Loaded data from {filename}")
        return data_log
    except Exception as e:
        print(f"Error loading data log: {e}")
        return None


def plot_popup_1(data_log):
    """
    Popup 1: Display z-position, error, derivative, integral, and zstep vs time
    """
    time = np.array(data_log['time'])
    
    fig, ax = plt.subplots(5, 1, figsize=(10, 18))
    fig.suptitle("Force Control Data - Popup 1", fontsize=16)

    # Plot 1: Z-Position vs Time
    z_pos = [pose[2] for pose in data_log['pose']]
    ax[0].plot(time, z_pos, label="Z Position")
    ax[0].set_xlabel("Time (s)")
    ax[0].set_ylabel("Z Position")
    ax[0].set_title("Z Position vs Time")
    ax[0].legend()

    # Plot 2: Error vs Time
    ax[1].plot(time, data_log['error'], color='r', label="Error")
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylabel("Error")
    ax[1].set_title("Error vs Time")
    ax[1].legend()

    # Plot 3: Derivative vs Time
    ax[2].plot(time, data_log['derivative'], color='y', label="Derivative")
    ax[2].set_xlabel("Time (s)")
    ax[2].set_ylabel("Derivative")
    ax[2].set_title("Derivative vs Time")
    ax[2].legend()

    # Plot 4: Integral vs Time
    ax[3].plot(time, data_log['integral'], color='g', label="Integral")
    ax[3].set_xlabel("Time (s)")
    ax[3].set_ylabel("Integral")
    ax[3].set_title("Integral vs Time")
    ax[3].legend()

    # Plot 5: Z-Step vs Time
    ax[4].plot(time, data_log['zstep'], color='b', label="Z Step")
    ax[4].set_xlabel("Time (s)")
    ax[4].set_ylabel("Z Step")
    ax[4].set_title("Z Step vs Time")
    ax[4].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def plot_popup_2(data_log):
    """
    Popup 2: Display XY position with time as color, Z position with abs(error) as color,
    zero forces split into (x, y, z) and (rx, ry, rz), and zstep with abs(error) as color
    """
    time = np.array(data_log['time'])
    error = np.abs(np.array(data_log['error']))
    
    fig, ax = plt.subplots(4, 1, figsize=(12, 24))
    fig.suptitle("Force Control Data - Popup 2", fontsize=16)

    # Plot 1: XY Position with Time as the Color of the Dots
    x_pos = [pose[0] for pose in data_log['pose']]
    y_pos = [pose[1] for pose in data_log['pose']]
    sc1 = ax[0].scatter(x_pos, y_pos, c=time, cmap='viridis', marker='o')
    ax[0].set_title("XY Position Over Time")
    ax[0].set_xlabel("X Position")
    ax[0].set_ylabel("Y Position")
    plt.colorbar(sc1, ax=ax[0], label="Time")

    # Plot 2: Z Position vs Time with abs(Error) as Color
    z_pos = [pose[2] for pose in data_log['pose']]
    sc2 = ax[1].scatter(time, z_pos, c=error, cmap='plasma', marker='o')
    ax[1].set_title("Z Position vs Time with abs(Error) as Color")
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylabel("Z Position")
    plt.colorbar(sc2, ax=ax[1], label="abs(Error)")

    # Plot 3: Zero Forces (x, y, z on primary y-axis, rx, ry, rz on secondary y-axis)
    zero_forces = np.array(data_log['zero_forces'])
    ax[2].plot(time, zero_forces[:, 0], color='r', label="Zero Force X")
    ax[2].plot(time, zero_forces[:, 1], color='g', label="Zero Force Y")
    ax[2].plot(time, zero_forces[:, 2], color='b', label="Zero Force Z")
    ax2 = ax[2].twinx()
    ax2.plot(time, zero_forces[:, 3], color='c', label="Zero Force Rx", linestyle='--')
    ax2.plot(time, zero_forces[:, 4], color='m', label="Zero Force Ry", linestyle='--')
    ax2.plot(time, zero_forces[:, 5], color='y', label="Zero Force Rz", linestyle='--')
    ax[2].set_title("Zero Forces vs Time")
    ax[2].set_xlabel("Time (s)")
    ax[2].set_ylabel("Zero Forces (X, Y, Z)")
    ax2.set_ylabel("Zero Forces (Rx, Ry, Rz)")
    ax[2].legend(loc="upper left")
    ax2.legend(loc="upper right")

    # Plot 4: Z-Step vs Time with abs(Error) as Color
    zstep = np.array(data_log['zstep'])
    sc4 = ax[3].scatter(time, zstep, c=error, cmap='cool', marker='o')
    ax[3].set_title("Z Step vs Time with abs(Error) as Color")
    ax[3].set_xlabel("Time (s)")
    ax[3].set_ylabel("Z Step")
    plt.colorbar(sc4, ax=ax[3], label="abs(Error)")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def plot_data_log(data_log):
    # Popup 1: Z Position, Error, Derivative, Integral, Z Step vs Time
    fig1, axs1 = plt.subplots(5, 1, figsize=(10, 12))

    time = np.array(data_log['time'])
    z_position = np.array([pose[2] for pose in data_log['pose']])
    error = np.array(data_log['error'])
    derivative = np.array(data_log['derivative'])
    integral = np.array(data_log['integral'])
    zstep = np.array(data_log['zstep'])

    axs1[0].plot(time, z_position, label='Z Position')
    axs1[0].set_title("Z Position vs Time")
    axs1[0].set_ylabel("Z Position")
    axs1[0].legend()

    axs1[1].plot(time, error, color='red', label='Error')
    axs1[1].set_title("Error vs Time")
    axs1[1].set_ylabel("Error")
    axs1[1].legend()

    axs1[2].plot(time, derivative, color='yellow', label='Derivative')
    axs1[2].set_title("Derivative vs Time")
    axs1[2].set_ylabel("Derivative")
    axs1[2].legend()

    axs1[3].plot(time, integral, color='green', label='Integral')
    axs1[3].set_title("Integral vs Time")
    axs1[3].set_ylabel("Integral")
    axs1[3].legend()

    axs1[4].plot(time, zstep, color='blue', label='Z Step')
    axs1[4].set_title("Z Step vs Time")
    axs1[4].set_ylabel("Z Step")
    axs1[4].legend()

    for ax in axs1:
        ax.xaxis.get_offset_text().set_visible(False)  # Hide the scientific notation in the corner

    # Apply tight_layout to avoid overlaps
    fig1.suptitle('Force Control Data - Popup 1', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

    # Popup 2: XY Position Over Time, Z Position vs Time with abs(Error) as color, Zero Forces vs Time, Z Step vs Time with abs(Error) as color
    fig2, axs2 = plt.subplots(4, 1, figsize=(10, 16))

    x_position = np.array([pose[0] for pose in data_log['pose']])
    y_position = np.array([pose[1] for pose in data_log['pose']])
    z_position = np.array([pose[2] for pose in data_log['pose']])
    zero_forces = np.array(data_log['zero_forces'])

    # Plot 1: XY Position with Time as color
    scatter = axs2[0].scatter(x_position, y_position, c=time, cmap=cm.viridis)
    axs2[0].set_title("XY Position Over Time")
    axs2[0].set_xlabel("X Position")
    axs2[0].set_ylabel("Y Position")
    cbar = fig2.colorbar(scatter, ax=axs2[0])
    cbar.set_label('Time')

    # Plot 2: Z Position vs Time with abs(Error) as color
    scatter = axs2[1].scatter(time, z_position, c=np.abs(error), cmap=cm.plasma)
    axs2[1].set_title("Z Position vs Time with abs(Error) as Color")
    axs2[1].set_xlabel("Time (s)")
    axs2[1].set_ylabel("Z Position")
    cbar = fig2.colorbar(scatter, ax=axs2[1])
    cbar.set_label('abs(Error)')

    # Plot 3: Zero Forces vs Time (with primary and secondary y-axes)
    ax3 = axs2[2]
    ax4 = ax3.twinx()  # Secondary y-axis

    ax3.plot(time, zero_forces[:, 0], color='red', label='Zero Force X')
    ax3.plot(time, zero_forces[:, 1], color='green', label='Zero Force Y')
    ax3.plot(time, zero_forces[:, 2], color='blue', label='Zero Force Z')

    ax4.plot(time, zero_forces[:, 3], color='cyan', linestyle='--', label='Zero Force Rx')
    ax4.plot(time, zero_forces[:, 4], color='magenta', linestyle='--', label='Zero Force Ry')
    ax4.plot(time, zero_forces[:, 5], color='orange', linestyle='--', label='Zero Force Rz')

    ax3.set_title("Zero Forces vs Time")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Zero Forces (X, Y, Z)")
    ax4.set_ylabel("Zero Forces (Rx, Ry, Rz)")

    # Create a combined legend for both y-axes
    lines_3, labels_3 = ax3.get_legend_handles_labels()
    lines_4, labels_4 = ax4.get_legend_handles_labels()
    axs2[2].legend(lines_3 + lines_4, labels_3 + labels_4, loc='upper right')

    # Plot 4: Z Step vs Time with abs(Error) as color
    scatter = axs2[3].scatter(time, zstep, c=np.abs(error), cmap=cm.plasma)
    axs2[3].set_title("Z Step vs Time with abs(Error) as Color")
    axs2[3].set_xlabel("Time (s)")
    axs2[3].set_ylabel("Z Step")
    cbar = fig2.colorbar(scatter, ax=axs2[3])
    cbar.set_label('abs(Error)')

    for ax in axs2:
        ax.xaxis.get_offset_text().set_visible(False)  # Hide the scientific notation in the corner

    # Adjust spacing manually between subplots
    fig2.suptitle('Force Control Data - Popup 2', fontsize=16)
    plt.subplots_adjust(hspace=0.6)  # Increase vertical spacing between plots
    plt.show()




if __name__ == "__main__":
    prepath = os.getcwd() + '/assets/temp/'
    fname = 'data_log_2024-09-16_08-27-35.pkl.gz'

    #? Teat: rear side of Lock Tab Holding Tray components
    # fname = 'data_log_2024-09-16_09-42-17.pkl'
    # fname = 'data_log_2024-09-16_09-43-23.pkl'
    # fname = 'data_log_2024-09-16_09-44-41.pkl'
    # fname = 'data_log_2024-09-16_09-45-36.pkl'
    # fname = 'data_log_2024-09-16_09-46-35.pkl'

    

    data_log = load_data_log(prepath + fname)
    
    if data_log:
        # plot_popup_1(data_log)
        # plot_popup_2(data_log)
        plot_data_log(data_log)

