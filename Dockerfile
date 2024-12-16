# Use the Conjure base image
FROM --platform=linux/amd64 ghcr.io/conjure-cp/conjure:main

# Update atp-get
RUN apt-get update


# Doing the default for timezone using frontend=noninteractive
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bash \
    wget \
    curl \
    gnupg \
    software-properties-common \
    unzip



# Installing necessary language dependencies for Python 
RUN apt install -y python3-pip
RUN apt install python3-pandas -y
RUN apt install python3-numpy -y
RUN apt install python-is-python3

# Installing R for iRace compatability
RUN apt install r-base -y

# Installing Git
RUN apt install git-all -y

# Set working dir to root
WORKDIR /

# Clone into AutoIG directory on Vincent fork
# Will need to be changed later
RUN git clone -b build/update-docker https://github.com/vincepick/AutoIG.git

WORKDIR /AutoIG

# Currently redundant installations
# RUN bash bin/install-mininzinc.sh
RUN bash bin/install-runsolver.sh

# Still need to install iRace
RUN bash bin/install-irace.sh 

# Currently redundant installations
RUN bash bin/install-ortools.sh
RUN bash bin/install-yuck.sh
RUN bash bin/install-picat.sh


# For use during development
RUN apt-get install -y \
    vim
