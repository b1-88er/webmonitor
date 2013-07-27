#!/bin/bash

export PYTHONPATH=`pwd`:$PYTHONPATH
py.test --twisted -s --maxfail=999 -vv tests/
