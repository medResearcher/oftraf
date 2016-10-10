#!/bin/bash

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
# -----------------------------------------------------------------------------
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

BASE_DIR="/opt"
VENV_DIR_OFTRAF="venv_oftraf"

# PROXY value is passed either from Vagrantfile/Dockerfile
#------------------------------------------------------------------------------
if [ ! -z "$1" ]; then
    echo "Creating PROXY variable: $1"
    PROXY=$1
else
    echo "Empty PROXY variable"
    PROXY=""
fi
# Generic provisioning actions
#------------------------------------------------------------------------------
apt-get update && apt-get install -y \
    git \
    unzip \
    wget \
    openssh-client \
    openssh-server \
    bzip2 \
    openssl \
    net-tools

# Python installation and other necessary libraries for pip
#------------------------------------------------------------------------------
apt-get update && apt-get install -y \
    python \
    python3.4 \
    python-dev \
    python3.4-dev \
    python-pip \
    python3-pip \
    python-pypcap \
    python-virtualenv

# Configure pip options
#------------------------------------------------------------------------------
pip_options=""

if [ ! -z "$PROXY" ]; then
    pip_options=" --proxy==$PROXY $pip_options"
fi

pip3 $pip_options install --upgrade pip

# OFTRAF node provisioning actions
#------------------------------------------------------------------------------
mkdir $BASE_DIR/$VENV_DIR_OFTRAF
virtualenv --system-site-packages $BASE_DIR/$VENV_DIR_OFTRAF

wget https://raw.githubusercontent.com/intracom-telecom-sdn/oftraf/virtenv-rqrmnts/deploy/requirements.txt -P $BASE_DIR
source $BASE_DIR/$VENV_DIR_OFTRAF/bin/activate
pip $pip_options install -r $BASE_DIR/requirements.txt
rm -rf $BASE_DIR/requirements.txt
deactivate

git clone -b virtenv-rqrmnts https://github.com/intracom-telecom-sdn/oftraf.git $BASE_DIR"/oftraf"

# This step is required to run jobs with any user
#------------------------------------------------------------------------------
chmod 777 -R $BASE_DIR

