clc
clear all;
root = [getenv('GAIT_RAW_ROOT'), filesep];
subject_names = {getenv('GAIT_SUBJECT')};

for ind=1:length(subject_names)
    subject_name = subject_names{ind};
imu_dynamic_path = [root, subject_name, '\imu\IMU_dynamic.xlsx'];
if ~exist(imu_dynamic_path, 'file')
    imu_dynamic_path = [root, subject_name, '\imu\IMU_dynamic.csv'];
    IMUdynamic = readIMUcsv(imu_dynamic_path);
else
    IMUdynamic = readtable(imu_dynamic_path);
end

global sensor_num
sensor_num = 8;

global subject_mag
subject_mag = struct('name', subject_name);
subject_mag.A = zeros(3, 3, sensor_num);
subject_mag.b = zeros(3, sensor_num);
subject_mag.expMFS = zeros(1, sensor_num);

imu_start = 1;
imu_end = size(IMUdynamic, 1);

for i=1:sensor_num
    imu_column = {['MagX_',num2str(i)], ['MagY_',num2str(i)], ['MagZ_',num2str(i)]};
    x = IMUdynamic(imu_start:imu_end, imu_column);

    x = table2array(x);

    x = double(x);


    [A,b,expMFS]  = magcal(x);
    xCorrected = (x-b)*A;
    xCorrected = xCorrected / expMFS;
    
    subject_mag.A(:, :, i) = A;
    subject_mag.b(:, i) = b;
    subject_mag.expMFS(i) = expMFS;

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

save([subject_mag.name, '_mag.mat'], 'subject_mag');
end
