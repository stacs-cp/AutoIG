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
# Python itself is already included in Conjure base image
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


# Dummy argument (force from this point onward to not be able to be cached for the Docker build proces)
# This way, there will always be a fresh pull of the repo which is essential, while still ensuring the steps before this can be cached. 
ARG CACHE_BUST
RUN echo "$CACHEBUST"

# Clone into AutoIG directory on Vincent fork
# Not incorrect, but will need to be changed later to clone from stacs-cp/AutoIG instead
RUN git clone -b build/update-docker https://github.com/vincepick/AutoIG.git 

WORKDIR /AutoIG

# Must be installed before ORTools
RUN bash bin/install-mininzinc.sh

# This is non-redundant
RUN bash bin/install-runsolver.sh

# Non Redundant 
RUN bash bin/install-irace.sh 

# RUN bash bin/install-ortools.sh
RUN bash bin/install-yuck.sh
RUN bash bin/install-picat.sh
RUN bash bin/update-or-path.sh
RUN bash bin/update-conjure-paths.sh

# For use during development
RUN apt-get install -y \
    vim \
    file

