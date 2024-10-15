@REM Yuck launcher script

@echo off

set "APP_HOME=%~dp0\.."
set "LIB_DIR=%APP_HOME%\lib\"
set "YUCK_JAVA_OPTS=-Djava.lang.Integer.IntegerCache.high=10000 -XX:+UseParallelGC"
set "CLASS_PATH=%LIB_DIR%\scala-library-2.13.5.jar;%LIB_DIR%\rtree-1.0.5.jar;%LIB_DIR%\scopt_2.13-3.7.1.jar;%LIB_DIR%\spray-json_2.13-1.3.5.jar;%LIB_DIR%\jgrapht-core-1.4.0.jar;%LIB_DIR%\scala-parser-combinators_2.13-1.1.2.jar;%LIB_DIR%\jheaps-0.11.jar;%LIB_DIR%\yuck-20210501.jar"
set "MAIN_CLASS=yuck.flatzinc.runner.FlatZincRunner"

java %YUCK_JAVA_OPTS% %JAVA_OPTS% -cp %CLASS_PATH% %MAIN_CLASS% %*
