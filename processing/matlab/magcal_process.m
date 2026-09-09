trials = {'baseline', 'walk_speed_large', 'walk_speed_small', 'fpa_large', 'fpa_small', 'step_width_large', 'step_width_small', 'trunk_sway_large', 'trunk_sway_small'};  % 'run_baseline', 'run_speed_small', 'run_speed_large', 


subject_names = {getenv('GAIT_SUBJECT')};


for ind=1:length(subject_names)
    subject_name = subject_names{ind};
    subject_mag = load([subject_name, '_mag.mat']);
    subject_mag = subject_mag.subject_mag;
    root = [getenv('GAIT_RAW_ROOT'), filesep];
    processed_folder = [root, subject_name, '/imu_mag_calibrated'];
    mkdir(processed_folder);

folderPath = [root, subject_name, '\imu'];
fileList = dir(folderPath);
csvFiles = dir(fullfile(folderPath, '*.csv'));
    
for j = 1:length(fileList)
    if ~fileList(j).isdir
        [~, name, ext] = fileparts(fileList(j).name);
        if ~startsWith(name, 'IMU')
            imu_path = fullfile(folderPath, fileList(j).name);
            if strcmpi(ext, '.xlsx')
                data = readtable(imu_path);
            elseif strcmpi(ext, '.csv')
                data = readIMUcsv(imu_path);
            end
        
            sensor_num = 8;
    
            for i=1:sensor_num
                mag_cols = {['MagX_', num2str(i)], ['MagY_', num2str(i)], ['MagZ_', num2str(i)]};
                x = data(:, mag_cols);
                x = table2array(x);
                x = double(x);
            
                A = subject_mag.A(:, :, i);
                b = subject_mag.b(:, i)';
                expMFS = subject_mag.expMFS(i);
            
                xCorrected = (x-b)*A;
                xCorrected = xCorrected / expMFS;
                
                data(:, mag_cols) = array2table(xCorrected);
                
            end
            
            imu_path_calibrated = [root, subject_name, '\imu_mag_calibrated\', name, '_calibrated.xlsx'];
            writetable(data, imu_path_calibrated);
        end
    end
end
end
