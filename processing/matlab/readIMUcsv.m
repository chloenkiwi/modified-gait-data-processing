function IMUdynamic = readIMUcsv(imu_dynamic_path)

    fid = fopen(imu_dynamic_path, 'r');
    headerLine = fgetl(fid);
    fclose(fid);

    headerCells = strsplit(headerLine, ',');

    isQuoteCol = cellfun(@(x) startsWith(x, '"'), headerCells);
    firstQuoteIdx = find(isQuoteCol, 1);

    if isempty(firstQuoteIdx)
        useCols = headerCells;
    else
        useCols = headerCells(1:firstQuoteIdx-1);
    end

    opts = detectImportOptions(imu_dynamic_path);
    opts.VariableNames = useCols;
    opts.SelectedVariableNames = useCols;

    IMUdynamic = readtable(imu_dynamic_path, opts);
end

