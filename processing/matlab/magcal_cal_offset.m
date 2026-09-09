clc
clear all;
root = [getenv('GAIT_RAW_ROOT'), filesep];
subject_name = getenv('GAIT_SUBJECT');
imu_dynamic_1_path = [root, subject_name, '\imu\IMU_dynamic_1.xlsx'];
imu_dynamic_2_path = [root, subject_name, '\imu\IMU_dynamic_2.xlsx'];

global sensor_num
sensor_num = 8;

global subject_mag
subject_mag = struct('name', subject_name);
subject_mag.A = zeros(3, 3, sensor_num);
subject_mag.b = zeros(3, sensor_num);
subject_mag.expMFS = zeros(1, sensor_num);

IMUdynamic1 = readtable(imu_dynamic_1_path);

imu_2_start = 1;
imu_2_end = size(IMUdynamic1, 1);

imu_3_start = 1;
imu_3_end = size(IMUdynamic1, 1);

imu_4_start = 1;
imu_4_end = size(IMUdynamic1, 1);

imu_5_start = 1;
imu_5_end = size(IMUdynamic1, 1);

dynamic1_rotation_time = [imu_2_start, imu_2_end; imu_3_start, imu_3_end; imu_4_start, imu_4_end; imu_5_start, imu_5_end];

dynamic1_rotation_column = [{'MagX_2', 'MagY_2', 'MagZ_2'}; {'MagX_3', 'MagY_3', 'MagZ_3'}; {'MagX_4', 'MagY_4', 'MagZ_4'}; {'MagX_5', 'MagY_5', 'MagZ_5'}];

mag_calib(IMUdynamic1, dynamic1_rotation_time, dynamic1_rotation_column)

IMUdynamic2 = readtable(imu_dynamic_2_path);

imu_1_start = 1;
imu_1_end = size(IMUdynamic2, 1);

imu_6_start = 1;
imu_6_end = size(IMUdynamic2, 1);

imu_7_start = 1;
imu_7_end = size(IMUdynamic2, 1);

imu_8_start = 1;
imu_8_end = size(IMUdynamic2, 1);

dynamic2_rotation_time = [imu_1_start, imu_1_end; imu_6_start, imu_6_end; imu_7_start, imu_7_end; imu_8_start, imu_8_end];

dynamic2_rotation_column = [{'MagX_1', 'MagY_1', 'MagZ_1'}; {'MagX_6', 'MagY_6', 'MagZ_6'}; {'MagX_7', 'MagY_7', 'MagZ_7'}; {'MagX_8', 'MagY_8', 'MagZ_8'}];

mag_calib(IMUdynamic2, dynamic2_rotation_time, dynamic2_rotation_column)

save([subject_mag.name, '_mag.mat'], 'subject_mag');

function mag_calib(imu_dynamic_data, rotation_time, rotation_column)
global sensor_num
global subject_mag

for i=1:sensor_num/2
    x = imu_dynamic_data(rotation_time(i,1):rotation_time(i,2), rotation_column(i, :));

    x = table2array(x);

    x = double(x);


    [A,b,expMFS]  = magcal(x);
    xCorrected = (x-b)*A;
    xCorrected = xCorrected / expMFS;
    
    sensor_idx = str2num(rotation_column{i, 1}(6));
    subject_mag.A(:, :, sensor_idx) = A;
    subject_mag.b(:, sensor_idx) = b;
    subject_mag.expMFS(sensor_idx) = expMFS;

    figure(1)
    plot3(x(:, 1),x(:, 2),x(:, 3),'LineStyle','none','Marker','X','MarkerSize',8)
    hold on
    grid(gca,'on')
    plot3(xCorrected(:,1),xCorrected(:,2),xCorrected(:,3),'LineStyle','none','Marker', ...
                'o','MarkerSize',8,'MarkerFaceColor','r') 

    axis equal
    xlabel('uT')
    ylabel('uT')
    zlabel('uT')
    legend('Uncalibrated Samples', 'Calibrated Samples','Location', 'southoutside')
    title("Uncalibrated vs Calibrated" + newline + "Magnetometer Measurements")
    hold off

end
end
