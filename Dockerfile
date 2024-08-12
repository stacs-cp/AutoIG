# Use the Conjure base image
FROM ghcr.io/conjure-cp/conjure:main

#Update the package list
RUN apt-get update

#Install necessary packages with frontend=noninteractive to avoid interactive prompts
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bash \
    sudo \
    wget \
    curl \
    gnupg \
    software-properties-common \
    unzip

#Install necessary python packages
RUN sudo apt-get install -y python3-pip
RUN apt install python3-pandas -y
RUN apt install python3-numpy -y

#Ensure 'python' command points to Python 3
RUN sudo apt install python-is-python3

#Install R base package for irace
RUN sudo apt-get install r-base -y

#Install Git
RUN sudo apt-get install git-all -y

#Set working directory to root
WORKDIR /

#Clone the AutoIG repository from GitHub
RUN git clone https://github.com/stacs-cp/AutoIG.git

#Move conjure into the AUtoIG bin directory
RUN mv conjure AutoIG/bin

#Set the working directory
WORKDIR /AutoIG

#Run installation scripts for tools used by AutoIG

# Install Savile Row
RUN bash bin/install-savilerow.sh 
# Install Minizinc
RUN bash bin/install-mininzinc.sh 
# Install irace
RUN bash bin/install-irace.sh 
# Install RunSolver
RUN bash bin/install-runsolver.sh 
# Install OR-Tools
RUN bash bin/install-ortools.sh 
# Install Yuck
RUN bash bin/install-yuck.sh
# Install Picat
RUN bash bin/install-picat.sh

# remove minizinc in the base conjure image
RUN rm /root/.local/bin/minizinc
RUN rm /root/.local/bin/fzn-chuffed
RUN rm /root/.local/bin/fzn-cp-sat
RUN rm -rf /root/.local/bin/share

