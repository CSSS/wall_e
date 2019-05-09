#!/bin/bash

validator(){
	exitCode=$(docker inspect $1 --format='{{.State.ExitCode}}')
	return $exitCode
}
validator $1
