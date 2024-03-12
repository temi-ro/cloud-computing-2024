import matplotlib.pyplot as plt
import numpy as np

# Define the filename
#create dynamic strings 
filename = '/path/to/your/data.txt'

# Initialize lists to hold the extracted data that will contain 7 lists, each of wich contains a variable number of lists with each having 3 elements
qps_data = []
p95_data = []

# Read the file
#do a lopp for i in range(7):
for i in range(1):
    qps_result_config_i =[]
    p95_result_config_i =[]
    for j in range(3):
        filename = '../data/data_part1/part1_' + str(i) + '_' +str(j) +'.txt'
        index=0
        with open(filename, 'r') as file:
            for line in file:
                # Split the line into components based on whitespace
                parts = line.split()

                # We need to check if the line contains the required data
                # This is a simplistic check and assumes that the file format is exactly as shown
                if len(parts) > 1 and parts[0] == 'read':
                    
                    # Convert the target QPS and p95 latency to float and append to the lists
                    # Here we're assuming that the 'target' is in the last column and 'p95' is the 12th from last
                    if(j==0):
                        qps_result_config_i.append([float(parts[-2])])
                        p95_result_config_i.append([float(parts[12])/1000])
                    else:
                        qps_result_config_i[index].append(float(parts[-2]))
                        p95_result_config_i[index].append(float(parts[12])/1000)
                    index+=1
    qps_data.append(qps_result_config_i)
    p95_data.append(p95_result_config_i)
                    
"""                
plot : 
Queries per second (QPS) on the x-axis (the x-axis should range from 0 to 55K).
(note: the actual achieved QPS, not the target QPS)
• 95th percentile latency on the y-axis (the y-axis should range from 0 to 8 ms).
• Label your axes.
• 7 lines, one for each configuration. Add a legend.
• State how many runs you averaged across and include error bars at each point in both
dimensions."""
# Continuing from your script

# Plot the results
plt.figure(figsize=(10, 5))
# Calculate the means, minimums, and maximums, and plot them
for i in range(len(qps_data)):
    # Convert each configuration's list of lists to a numpy array for easier calculations
    qps_array = np.array(qps_data[i])
    p95_array = np.array(p95_data[i])
    
    # Calculate the mean across the runs (axis=1)
    qps_mean = np.mean(qps_array, axis=1)
    p95_mean = np.mean(p95_array, axis=1)

    # Calculate the min and max across the runs (axis=1)
    qps_min = np.min(qps_array, axis=1)
    qps_max = np.max(qps_array, axis=1)
    p95_min = np.min(p95_array, axis=1)
    p95_max = np.max(p95_array, axis=1)
    
    # The error bars should reflect the actual min and max values
    qps_error = [qps_mean - qps_min, qps_max - qps_mean]
    p95_error = [p95_mean - p95_min, p95_max - p95_mean]
    
    # Plot each configuration as a separate line with error bars
    plt.errorbar(qps_mean, p95_mean, xerr=qps_error, yerr=p95_error, fmt='-o', label=f'Configuration {i+1}, averaged across {len(qps_array)} runs')

# Set the limits for the x and y axes
plt.xlim(0, 55000)
plt.ylim(0, 8)

# Label the axes
plt.xlabel('Queries per Second (QPS)')
plt.ylabel('95th Percentile Latency (ms)')

# Add a legend to the plot
plt.legend(title='Configurations')

# Add a title to the plot
plt.title('QPS vs. 95th Percentile Latency with Min/Max Error Bars')

# Show the plot
plt.show()
