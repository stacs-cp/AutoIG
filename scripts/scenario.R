trainInstancesDir <- ''
repairConfiguration <- function(id, allConfigurations, parameters, digits, nConfsPreviousRaces=0){
    outputDir <- './detailed-output/'
    configuration <- allConfigurations[id-nConfsPreviousRaces,]

    require(data.table)

    # if there is no repairing model, just return the current configuration
    repairModel <- paste(outputDir,'/repair.eprime',sep='')
    if (!file.exists(repairModel))
        return (configuration)

    # just for debug
    start_time <- Sys.time()
    originalConfiguration <- configuration
    
    # prefix name for all generated files
    baseFileName <- id

    # check if repairing results are already available
    outFile <- paste(outputDir,'/repairout-',baseFileName,sep='')
    if (file.exists(outFile)){
        configuration <- fread(outFile)
        return (configuration)
    }

    # make sure min<=max in configuration
    lsParams <- sort(parameters$names)
    for (param in lsParams){
        maxParam <- NA
        if (endsWith(param,'_min')){
            maxParam <- paste(substr(param,1,nchar(param)-3),'max',sep='')
        } else if (endsWith(param,'Min')){
            maxParam <- paste(substr(param,1,nchar(param)-3),'Max',sep='')
        }
        if (!is.na(maxParam)){
            minVal <- min(configuration[[param]],configuration[[maxParam]])
            maxVal <- max(configuration[[param]],configuration[[maxParam]])
            configuration[[param]] <- minVal
            configuration[[maxParam]] <- maxVal
        }
    }

    # write down essence param file
    paramFile <- paste(outputDir,'/repair-',baseFileName,'.param',sep='')
    lsLines <- c()
    for (paramName in colnames(configuration)){
        if (!(paramName %in% c('.ID.','.PARENT.'))){
            val <- configuration[[paramName]]
            lsLines <- c(lsLines, paste('letting', paramName, 'be', val))
        }
    }
    writeLines(lsLines, con <- file(paramFile))
    close(con)

    # solve 
    seed <- as.integer(id)
    cmd <- paste('conjure solve repair.essence ', 
                paramFile, 
                ' -o ', outputDir, 
                ' --use-existing-model repair.eprime ',
                ' --solver-options "-timelimit 120 -varorder domoverwdeg -randomiseorder', '-randomseed', seed, '"',
                ' --copy-solutions=off')
    cat(cmd,'\n')
    exitCode <- system(cmd, intern=FALSE, wait=TRUE)
    if (exitCode != 0){
        cat("ERROR while repairing configuration \n")
        print(configuration)
        return (NULL)
    }

    # read results
    solutionFile <- paste(outputDir, '/repair-repair-', baseFileName, '-solution000001.solution',sep='')
    lsLines <- readLines(con<-file(solutionFile))
    close(con)
    lsLines <- gsub('repaired_','',lsLines)
    lsLines <- lsLines[grep('letting ',lsLines)]

    # delete unneccessary files generated
    baseTempName <- paste(outputDir,'/repair-repair-',baseFileName,sep='')
    for (endName in c('.eprime-info','.eprime-infor','.eprime-minion','.eprime-param','-solution000001.eprime-solution','-solution000001.solution')){
        file.remove(paste(baseTempName,endName,sep=''))
    }
    file.remove(paramFile)

    # convert results to configuration
    # NOTE: only work for integer values
    for (paramName in colnames(configuration)){
        if (!(paramName %in% c('.ID.','.PARENT.'))){
            pattern <- paste('letting ',paramName,' be ',sep='')
            s <- lsLines[grep(pattern, lsLines)]
            newVal <- as.integer(trimws(strsplit(s,' be ')[[1]][2]))
            configuration[[paramName]] <- newVal
            }
    }

    
    #DEBUG
    cat("\nBefore repair: \n")
    print(originalConfiguration)
    cat("After repair: \n")
    print(configuration)
    cat("\n")
    end_time <- Sys.time()
    cat("\nRepairing time: ", round(end_time-start_time,2), " seconds\n")

    # save results in case the tuning is resumed
    write.csv(configuration,file=outFile,row.names=FALSE)
    
    return (configuration)
}
