#!/bin/bash


sam build
sam deploy --no-confirm-changeset --disable-rollback
