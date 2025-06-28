paths <- list(R6="R6_2.5.1.tar.gz", data.table="data.table_1.14.2.tar.gz")
binDir <- "<BIN_DIR>"
for (p in c("R6","data.table")){
    if (!require(p,character.only = TRUE)){
        install.packages(paste(binDir,paths[[p]],sep='/'), lib=binDir)
        library(p,character.only = TRUE, lib.loc=binDir)
    }
}
