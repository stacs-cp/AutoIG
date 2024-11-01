# Use the Conjure base image
FROM ghcr.io/conjure-cp/conjure:main

# Update atp-get
RUN apt-get update


# Doing the default for timezone using frontend=noninteractive
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bash \
    sudo \
    wget \
    curl \
    gnupg \
    software-properties-common \
    unzip

# Installing necessary language dependencies for Python 
RUN sudo apt-get install -y python3-pip
RUN apt install python3-pandas -y
RUN apt install python3-numpy -y
RUN sudo apt install python-is-python3

# Installing R for iRace compatability
RUN sudo apt-get install r-base -y

# Installing Git
RUN sudo apt-get install git-all -y

# Set working dir to root
WORKDIR /

# Clone into AutoIG directory
RUN git clone https://github.com/stacs-cp/AutoIG.git

# Move Conjure into AutoIG bin
RUN mv conjure AutoIG/bin

# Set the working directory
WORKDIR /AutoIG

# Run scripts for additional dependencies one by one
RUN bash bin/install-savilerow.sh 
RUN bash bin/install-mininzinc.sh
RUN bash bin/install-irace.sh
RUN bash bin/install-runsolver.sh 
RUN bash bin/install-ortools.sh
RUN bash bin/install-yuck.sh
RUN bash bin/install-picat.sh

